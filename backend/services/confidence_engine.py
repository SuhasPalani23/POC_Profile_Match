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
SOFT_MAX_TURNS = 40     # normal ceiling (~20 user replies, enough to cover all buckets)
HARD_MAX_TURNS = 50     # absolute ceiling


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
        "minimum": 0.85,
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


def get_next_topic(profile_data, extra_fields, discovered_fields=None, chat_history=None):
    """
    Pick the next bucket to focus on. Walks buckets in priority order and
    returns the first one still below its minimum. If every bucket is above
    its minimum, return wrap_up.
    """
    profile_data = profile_data or {}
    extra_fields = extra_fields or {}
    discovered_fields = discovered_fields or {}

    for bucket in BUCKETS:
        score = _bucket_score(bucket, profile_data, extra_fields, discovered_fields)
        if score < bucket["minimum"]:
            missing = _bucket_missing_fields(bucket, profile_data, extra_fields, discovered_fields)
            return {
                "type": bucket["name"],
                "bucket_label": bucket["label"],
                "signal": bucket["label"],
                "target": bucket["name"],
                "score": score,
                "minimum": bucket["minimum"],
                "missing_fields": missing,
                "description": bucket["description"],
                "evidence": (
                    f"{bucket['label']} bucket is at {round(score * 100)}% — "
                    f"below the {round(bucket['minimum'] * 100)}% minimum. "
                    f"Missing fields: {', '.join(missing) if missing else 'coverage is thin'}."
                ),
            }

    return {
        "type": "wrap_up",
        "bucket_label": "Wrap Up",
        "signal": "final summary",
        "target": "",
        "score": 1.0,
        "minimum": 1.0,
        "missing_fields": [],
        "description": "all buckets reached their minimum — time to wrap up",
        "evidence": "Every bucket has enough signal for matching.",
    }


def _build_progress_summary(confidence, turn_count, bucket_scores):
    lines = [f"Profile confidence: {round(confidence * 100)}% (target: {round(STOP_THRESHOLD * 100)}%)"]
    lines.append(f"Turn {turn_count} (min to finish: {MIN_TURNS}, soft cap: {SOFT_MAX_TURNS}).")
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
                          is_resume_mode=False, all_buckets_met=False):
    """
    Primary stop: all buckets reached their minimum (next_topic_type == 'wrap_up').
    The chatbot must cover every bucket before closing.

    Escape hatch: SOFT_MAX_TURNS (40) / HARD_MAX_TURNS (50) for cases where
    a few niche fields are never answered despite repeated asking.
    """
    if is_resume_mode:
        return False
    if turn_count >= HARD_MAX_TURNS:
        return True
    if next_topic_type == "wrap_up" or all_buckets_met:
        return True
    if turn_count < MIN_TURNS:
        return False
    if turn_count >= SOFT_MAX_TURNS:
        return True
    return False


def build_interview_context(
    profile_data,
    extra_fields,
    discovered_fields=None,
    turn_count=0,
    chat_history=None,
):
    confidence, metrics = calculate_confidence(profile_data, extra_fields, discovered_fields, chat_history)
    next_topic = get_next_topic(profile_data, extra_fields, discovered_fields, chat_history)
    bucket_scores = metrics["section_scores"]

    all_buckets_met = all(
        bucket_scores.get(b["name"], 0.0) >= b["minimum"] for b in BUCKETS
    )
    stop = should_stop_interview(
        confidence,
        turn_count,
        next_topic.get("type", ""),
        False,
        all_buckets_met=all_buckets_met,
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
