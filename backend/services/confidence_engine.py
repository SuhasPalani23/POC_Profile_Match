"""
Bucket-driven interview engine.

Five buckets (topic-wise):
  1. identity
  2. professional_background
  3. topic_depth
  4. market_fit
  5. founder_fit

For each bucket we know which canonical fields "count" toward filling it.
Confidence = weighted sum across buckets. The router picks the weakest
bucket below its minimum and points the LLM at it, including the list of
specific missing fields. The LLM then composes its own question — no
hardcoded seeds anywhere.

Stop rules:
  - Always below MIN_TURNS => keep going.
  - Any bucket still below its minimum => keep going (unless hard cap).
  - Confidence >= STOP_THRESHOLD and MIN_TURNS met => wrap up.
  - Hard cap HARD_MAX_TURNS => wrap up no matter what.
"""

from __future__ import annotations

STOP_THRESHOLD = 0.80   # lowered from 0.85 so it aligns with bucket-minimum math
MIN_TURNS = 6           # 3 user replies minimum
HARD_MAX_TURNS = 35     # absolute ceiling
# If this many consecutive assistant turns extract zero fields while we're
# already past STOP_THRESHOLD, we treat the interview as stuck and wrap up.
# This is the exact failure from the 2026-04-21 demo: confidence plateaued at
# 91% while two niche founder_fit fields never got extracted despite repeated
# asking — chatbot kept looping, LLM hallucinated a goodbye, UI never closed.
STUCK_EMPTY_TURNS = 3
# Weaker stuck-detector: if the bot extracts nothing for this many turns in a
# row regardless of confidence, rotate off the current bucket. Prevents the
# topic_depth death-loop seen on 2026-04-22 where short answers ("development",
# "team lead", "to get this done") repeatedly failed extraction, the router
# kept returning the same bucket, and the LLM rephrased the same questions.
BUCKET_ROTATE_EMPTY_TURNS = 4


# Ordered — this is the order the router walks through them.
# Minimums tightened so that hitting every bucket's minimum weighted-sums
# to ~80%, matching STOP_THRESHOLD. "about" removed from identity because
# About Me is reserved for the post-chat AI summary and would otherwise
# block identity from ever reaching 100%.
BUCKETS = [
    {
        "name": "identity",
        "label": "Identity",
        "weight": 0.10,
        "minimum": 1.00,
        "fields": ["firstName", "lastName", "headline", "location"],
        "description": "who they are — name, headline, where they're based",
    },
    {
        "name": "professional_background",
        "label": "Professional Background",
        "weight": 0.20,
        "minimum": 0.85,
        "fields": [
            "currentPosition", "currentCompany", "skills", "tools",
            "totalYearsExperience", "coreDomains",
        ],
        "description": "their job, tools, tech stack, years of experience",
    },
    {
        "name": "topic_depth",
        "label": "Topic Depth",
        "weight": 0.20,
        "minimum": 0.70,
        "fields": [
            "projectHighlights", "domainDepth", "learningGoals",
            "strengths", "collaborationStyle", "workStyle",
        ],
        "description": "concrete shipped work, project depth, how they work",
    },
    {
        "name": "market_fit",
        "label": "Market Fit",
        "weight": 0.20,
        "minimum": 0.70,
        "fields": [
            "preferredIndustry", "preferredRole", "industryInclination",
            "interests", "careerGoals",
        ],
        "description": "industry/role they want to build in, who they want to serve",
    },
    {
        "name": "founder_fit",
        "label": "Founder Fit",
        "weight": 0.30,
        "minimum": 0.70,
        "fields": [
            "hours_per_week", "equity_expectations", "compensation_expectations",
            "risk_tolerance", "financial_runway", "urgency_to_start",
            "previous_startup_exp", "cofounder_role_needed", "ideal_cofounder",
            "deal_breakers",
        ],
        "description": "startup logistics — hours, equity, risk, runway, cofounder preferences",
    },
]


def _field_filled(field, profile_data, extra_fields, discovered_fields):
    """Does this field have a non-empty value anywhere?"""
    for source in (profile_data, extra_fields, discovered_fields):
        value = (source or {}).get(field)
        if value in [None, "", [], {}]:
            continue
        # string with only whitespace counts as empty
        if isinstance(value, str) and not value.strip():
            continue
        return True
    return False


def _bucket_score(bucket, profile_data, extra_fields, discovered_fields):
    fields = bucket["fields"]
    filled = sum(
        1 for f in fields
        if _field_filled(f, profile_data, extra_fields, discovered_fields)
    )
    return round(filled / max(len(fields), 1), 4)


def _bucket_missing_fields(bucket, profile_data, extra_fields, discovered_fields):
    return [
        f for f in bucket["fields"]
        if not _field_filled(f, profile_data, extra_fields, discovered_fields)
    ]


def calculate_confidence(profile_data, extra_fields, discovered_fields=None, chat_history=None):
    """
    Overall confidence = sum of bucket_score * bucket_weight (weights sum to 1.0).
    Returns (confidence, metrics).
    """
    profile_data = profile_data or {}
    extra_fields = extra_fields or {}
    discovered_fields = discovered_fields or {}

    bucket_scores = {}
    overall = 0.0
    for bucket in BUCKETS:
        score = _bucket_score(bucket, profile_data, extra_fields, discovered_fields)
        bucket_scores[bucket["name"]] = score
        overall += score * bucket["weight"]

    overall = round(min(1.0, overall), 4)
    return overall, {
        "section_scores": bucket_scores,
        "bucket_minimums": {b["name"]: b["minimum"] for b in BUCKETS},
    }


def get_next_topic(profile_data, extra_fields, discovered_fields=None, chat_history=None, consecutive_empty_turns=0, asked_fields=None):
    """
    Pick the next bucket + target field to ask about.

    Contract: ONE question per field, NEVER repeat. We walk EVERY bucket in
    order (identity → professional_background → topic_depth → market_fit →
    founder_fit) and, inside each, pick the first field that hasn't been
    asked yet. Confidence / bucket minimums are NOT a gate anymore — even if
    a bucket is already "above minimum" it still has to be asked about if it
    contains unasked fields, and even if a bucket never reaches minimum we
    still march forward to the next bucket after asking everything in this
    one. "User gave a lousy answer" is the user's problem; we record what
    they said, move on, and let the final confidence score reflect reality.

    Wrap-up fires iff every canonical field in every bucket has been asked
    exactly once.

    `asked_fields` is the persisted set of field keys the bot has already
    posed a question about.
    """
    profile_data = profile_data or {}
    extra_fields = extra_fields or {}
    discovered_fields = discovered_fields or {}
    asked_fields = set(asked_fields or [])

    def _unasked(bucket):
        return [
            f for f in bucket["fields"]
            if f not in asked_fields
            and not _field_filled(f, profile_data, extra_fields, discovered_fields)
        ]

    # Walk buckets in priority order. First bucket with any unasked field
    # wins — regardless of that bucket's score vs. its minimum. This is the
    # "keep going until founder_fit is done" guarantee.
    for bucket in BUCKETS:
        unasked = _unasked(bucket)
        if not unasked:
            continue
        target_field = unasked[0]
        score = _bucket_score(bucket, profile_data, extra_fields, discovered_fields)
        return {
            "type": bucket["name"],
            "bucket_label": bucket["label"],
            "signal": bucket["label"],
            "target": bucket["name"],
            "target_field": target_field,
            "score": score,
            "minimum": bucket["minimum"],
            "missing_fields": unasked,
            "description": bucket["description"],
            "evidence": (
                f"{bucket['label']} bucket at {round(score * 100)}% "
                f"(minimum {round(bucket['minimum'] * 100)}%). "
                f"Next unasked field: {target_field}."
            ),
        }

    return {
        "type": "wrap_up",
        "bucket_label": "Wrap Up",
        "signal": "final summary",
        "target": "",
        "target_field": None,
        "score": 1.0,
        "minimum": 1.0,
        "missing_fields": [],
        "description": "every field in every bucket has been asked once — wrapping up",
        "evidence": "Every field has been asked at most once. Done.",
    }


def _build_progress_summary(confidence, turn_count, bucket_scores):
    lines = [f"Profile confidence: {round(confidence * 100)}% (target: {round(STOP_THRESHOLD * 100)}%)"]
    lines.append(f"Turn {turn_count} (min to finish: {MIN_TURNS}, hard cap: {HARD_MAX_TURNS}).")
    lines.append("Bucket coverage:")
    for bucket in BUCKETS:
        score = bucket_scores.get(bucket["name"], 0.0)
        mark = "OK" if score >= bucket["minimum"] else "NEEDS WORK"
        lines.append(
            f"  - {bucket['label']}: {round(score * 100)}% [{mark}] "
            f"(minimum {round(bucket['minimum'] * 100)}%)"
        )
    return "\n".join(lines)


def should_stop_interview(confidence_score, turn_count, next_topic_type="",
                          is_resume_mode=False, all_buckets_met=False,
                          consecutive_empty_turns=0, untouched_buckets=0):
    """
    The ONLY legitimate reasons to stop:
      1. `next_topic_type == 'wrap_up'` — every field in every bucket has
         already been asked exactly once. This is the natural end.
      2. `turn_count >= HARD_MAX_TURNS` — absolute safety rail to prevent a
         runaway if something goes wrong upstream.

    Confidence score and per-bucket minimums are NOT stop signals anymore.
    If the user gave lousy answers and the score is low, that's the user's
    problem; we still cover founder_fit and wrap up with a crisp About Me
    summarising whatever they did share. The score gets recorded as-is.

    `confidence_score`, `all_buckets_met`, `consecutive_empty_turns`, and
    `untouched_buckets` are kept in the signature for call-site stability
    (route layer passes them in) but deliberately unused.
    """
    del confidence_score, all_buckets_met, consecutive_empty_turns, untouched_buckets
    if is_resume_mode:
        return False
    if turn_count >= HARD_MAX_TURNS:
        return True
    if next_topic_type == "wrap_up":
        return True
    return False


def build_interview_context(
    profile_data,
    extra_fields,
    discovered_fields=None,
    turn_count=0,
    chat_history=None,
    consecutive_empty_turns=0,
    asked_fields=None,
):
    confidence, metrics = calculate_confidence(profile_data, extra_fields, discovered_fields, chat_history)
    next_topic = get_next_topic(
        profile_data, extra_fields, discovered_fields, chat_history,
        consecutive_empty_turns=consecutive_empty_turns,
        asked_fields=asked_fields,
    )
    bucket_scores = metrics["section_scores"]

    all_buckets_met = all(
        bucket_scores.get(b["name"], 0.0) >= b["minimum"] for b in BUCKETS
    )
    # Count buckets that have received zero signal. Used to refuse a
    # premature wrap-up while whole topics (e.g., market_fit / founder_fit)
    # have never been asked about.
    untouched_buckets = sum(
        1 for b in BUCKETS if bucket_scores.get(b["name"], 0.0) <= 0.0
    )
    stop = should_stop_interview(
        confidence,
        turn_count,
        next_topic.get("type", ""),
        False,
        all_buckets_met=all_buckets_met,
        consecutive_empty_turns=consecutive_empty_turns,
        untouched_buckets=untouched_buckets,
    )
    progress_summary = _build_progress_summary(confidence, turn_count, bucket_scores)

    return {
        "confidence_score": confidence,
        "metrics": metrics,
        "should_stop": stop,
        "progress_summary": progress_summary,
        "next_focus": next_topic,
        "focus_signal": next_topic.get("signal", ""),
        "all_buckets_met": all_buckets_met,
        "turns_remaining": max(0, HARD_MAX_TURNS - turn_count),
    }
