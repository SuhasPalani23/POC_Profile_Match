"""OpenAI-powered LLM service for post analysis and founder profiling chatbot."""

import json
import re
from openai import OpenAI
from config import Config

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=Config.OPENAI_API_KEY)
    return _client


def analyze_posts_deeply(posts_items, profile_context=None):
    """
    Analyze LinkedIn posts to extract areas of interest, certifications,
    skills, expertise signals, and any other discoverable attributes.
    Returns a dict of auto-discovered fields.
    """
    if not posts_items:
        return {}

    posts_text = []
    for post in (posts_items or [])[:25]:
        text = post.get('text') or post.get('content') or post.get('postContent') or ''
        if text:
            posts_text.append(text[:800])

    if not posts_text:
        return {}

    profile_hint = ""
    if profile_context:
        profile_hint = f"\nProfile context: {json.dumps(profile_context, ensure_ascii=False)[:2000]}"

    prompt = f"""You are an expert talent analyst. Analyze the following LinkedIn posts and extract every possible insight about this person.
{profile_hint}

POSTS:
{chr(10).join(f'--- Post {i+1} ---{chr(10)}{t}' for i, t in enumerate(posts_text))}

Extract and return a JSON object with these fields:
{{
  "areasOfInterest": ["topic1", "topic2", ...],
  "certifications": ["cert1", "cert2", ...],
  "discoveredSkills": ["skill1", "skill2", ...],
  "tools": ["tool1", "tool2", ...],
  "coreDomains": ["domain1", "domain2", ...],
  "industryFocus": ["industry1", "industry2", ...],
  "thoughtLeadershipTopics": ["topic1", ...],
  "communityInvolvement": ["community1", ...],
  "projectsMentioned": ["project1", ...],
  "achievementSignals": ["achievement1", ...],
  "contentStyle": "descriptive phrase about their posting style",
  "expertiseLevel": "beginner|intermediate|advanced|expert",
  "dynamicFields": {{
    "field_name_in_snake_case": "value extracted from posts",
    ...
  }}
}}

Rules:
- Extract REAL data from the posts, do not hallucinate
- `dynamicFields` should contain any interesting attributes discovered that don't fit standard fields
  (e.g., "mentoring_experience": "Active mentor at TechStars", "open_source_contributor": "true")
- Return ONLY valid JSON, no markdown, no explanation
- Use empty arrays [] for fields with no data, empty string "" for string fields with no data
- `discoveredSkills` should be technical and professional skills mentioned/demonstrated in posts
- `certifications` only if explicitly mentioned"""

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content.strip())
    except Exception as e:
        print(f"[openai_service] Post analysis error: {e}")
        return {}


STANDARD_PROFILE_FIELDS = [
    "firstName", "lastName", "name", "headline", "about", "aboutMe",
    "currentPosition", "currentCompany", "city", "state", "country", "location",
    "email", "phone", "github", "linkedinUrl", "totalYearsExperience",
    "skills", "tools", "languages", "coreDomains", "interests",
    "industryInclination", "skillStrength", "careerGoals", "preferredRole",
    "preferredIndustry", "strengths", "weaknesses", "workStyle", "hobbies",
    "openToWork", "projectHighlights", "domainDepth", "collaborationStyle",
    "learningGoals",
]


def _build_chatbot_messages(chat_history, system_prompt):
    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history:
        role = "user" if msg.get("role") == "user" else "assistant"
        messages.append({"role": role, "content": msg.get("text", "")})
    return messages


# Phrases that signal a premature wrap-up. When the LLM emits any of these
# while ACTIVE mode is still the rule, we consider the output hallucinated
# and retry with a stricter instruction. Checked case-insensitively.
#
# NOTE: bare "thank you for" / "thanks for" are NOT included here — they fire
# on perfectly legitimate acks ("Thanks for sharing your full name..."),
# which was tripping the guard on every identity turn and forcing the
# deterministic fallback question. Only unambiguous closing phrases go here.
_ACTIVE_MODE_FAREWELL_MARKERS = (
    "thank you for your time", "thanks for your time",
    "thank you for taking the time", "thanks for taking the time",
    "appreciate you taking the time",
    "that's all i need", "that's all i needed", "all i needed",
    "we're all set", "we are all set", "you're all set", "you are all set",
    "interview complete", "interview is complete",
    "wrapping up", "we have enough",
    "profile is ready", "ready for matching",
    "all the information i need",
)


def _is_hallucinated_active_message(text, is_active_mode):
    """
    True when the chat-mode LLM produced a closing-style message while
    ACTIVE mode is in effect, or when the message fails to ask anything.
    A valid ACTIVE-mode reply must acknowledge briefly and ASK a question —
    so we require at least one '?' and forbid farewell markers.
    """
    if not is_active_mode:
        return False
    if not text:
        return True
    lowered = text.lower()
    if any(marker in lowered for marker in _ACTIVE_MODE_FAREWELL_MARKERS):
        return True
    if "?" not in text:
        return True
    return False


def _build_focus_fallback_question(focus_missing, focus_label):
    """
    Deterministic question used when both the primary LLM call and the
    retry produce hallucinated content. Picks the first missing field in
    the focus bucket and writes a plain direct question. No model call,
    no randomness — guaranteed correct behaviour.
    """
    if not focus_missing:
        return (
            f"Let's keep going — can you share a bit more about your "
            f"{focus_label.lower()}?"
        )
    field = focus_missing[0]
    prompts = {
        "hours_per_week": "How many hours per week can you realistically commit to a startup?",
        "equity_expectations": "What kind of equity would you expect from a co-founder role?",
        "compensation_expectations": "What does compensation need to look like for you early on?",
        "risk_tolerance": "How would you describe your risk tolerance — are you okay with no salary for a while?",
        "financial_runway": "How many months of personal runway do you have right now?",
        "urgency_to_start": "How soon are you looking to start — weeks, months, or longer?",
        "previous_startup_exp": "Have you worked on a startup or venture before? Tell me briefly.",
        "cofounder_role_needed": "What kind of co-founder role would you need filled alongside you?",
        "ideal_cofounder": "What does your ideal co-founder look like — background, mindset, skills?",
        "deal_breakers": "Are there any deal-breakers for you in a co-founder relationship?",
        "firstName": "What's your first name?",
        "lastName": "What's your last name?",
        "headline": "How would you describe yourself in one line?",
        "location": "Where are you based right now?",
        "currentPosition": "What's your current role or title?",
        "currentCompany": "Where do you currently work?",
        "skills": "What are your top three skills?",
        "tools": "What are the main tools or technologies you work with day-to-day?",
        "totalYearsExperience": "How many years of professional experience do you have?",
        "coreDomains": "Which domains do you work in — fintech, healthtech, SaaS, etc.?",
        "projectHighlights": "Tell me about one project you've shipped that you're most proud of.",
        "domainDepth": "Where would you say your deepest technical or domain expertise lies?",
        "learningGoals": "What are you actively trying to learn or get better at right now?",
        "strengths": "What do people consistently say are your biggest strengths?",
        "collaborationStyle": "How do you prefer to collaborate — solo focus, pair, or team-driven?",
        "workStyle": "Describe your working style — remote, in-person, async, sync?",
        "preferredIndustry": "Which industry do you most want to build in?",
        "preferredRole": "What role do you see yourself playing in a new venture?",
        "industryInclination": "Which industries are you most drawn to?",
        "interests": "Outside of work, what are you genuinely interested in?",
        "careerGoals": "What are your career goals over the next 2-3 years?",
    }
    return prompts.get(
        field,
        f"Can you share details about your {field.replace('_', ' ')}?",
    )


def _recent_bot_questions(chat_history, n=5):
    """Deterministic list of the last `n` questions the bot asked, oldest first.

    The LLM has chat_history in its prompt already, but evidence from real
    transcripts (see the 2026-04-22 ML-engineer session) shows it drifts and
    re-asks coreDomains / domainDepth / workStyle when the user's answers
    are too short to extract. A tight, explicit enumeration of recent
    questions makes the "do not repeat" rule literal instead of aspirational.
    """
    questions = []
    for msg in chat_history or []:
        if (msg or {}).get("role") != "model":
            continue
        text = ((msg or {}).get("text") or "").strip()
        if not text or "?" not in text:
            continue
        # Keep only the question clause — the acknowledgment prefix isn't
        # what we need to block. Split on "?" and take the sentence ending
        # with the last "?" in the message.
        q = text.rsplit("?", 1)[0]
        q = q.split(". ")[-1].strip()
        if q:
            questions.append(q + "?")
    return questions[-n:]


def _generate_chat_message(chat_history, profile_summary, discovered_summary, filled_extra, mode_block, manual_block, focus_missing=None, focus_label=""):
    """
    Low-temp conversational pass with hallucination guards.

    Guards in order:
      1. Temperature 0.2 for stability.
      2. If the output is a premature farewell or fails to ask a question
         while ACTIVE mode is in effect, retry once with a stricter prompt.
      3. If the retry still hallucinates, replace the message with a
         deterministic fallback question targeting the focus bucket's
         first missing field — zero model involvement at that point.
    """
    is_active_mode = "ACTIVE INTERVIEW" in (mode_block or "")
    recent_questions = _recent_bot_questions(chat_history, n=5)
    if recent_questions:
        recent_q_block = "\n".join(f"  - {q}" for q in recent_questions)
    else:
        recent_q_block = "  (none yet — this is an early turn)"

    # Deterministic "already filled" list so the LLM can see which canonical
    # fields it MUST NOT ask about again. Built from filled_extra + anything
    # non-empty in the LinkedIn profile snapshot.
    filled_keys = sorted({
        k for k, v in (filled_extra or {}).items()
        if v not in [None, "", [], {}]
    })
    filled_block = ", ".join(filled_keys) if filled_keys else "(none yet)"

    system_prompt = f"""You are an elite talent strategist and profile interviewer.
Your only job right now is to respond conversationally and ask the next question.
Field extraction is handled by a separate pass.

{mode_block}
{manual_block}

What we already know about the user:
LinkedIn / scraped profile:
{profile_summary}

Signals from LinkedIn posts:
{discovered_summary if discovered_summary != '{}' else 'None yet.'}

Answers collected so far:
{json.dumps(filled_extra, ensure_ascii=False) if filled_extra else 'None yet.'}

FIELDS ALREADY FILLED (do NOT ask about any of these again, even with different wording):
  {filled_block}

RECENT QUESTIONS YOU ALREADY ASKED (never repeat or rephrase any of these):
{recent_q_block}

Rules:
1. Acknowledge what the user just said in ONE short clause, then ask ONE question.
2. Never re-ask anything already covered in the profile, extra fields, or earlier chat.
   This is LITERAL — the lists above ("FIELDS ALREADY FILLED" and "RECENT
   QUESTIONS") are the ground truth. If the user's last reply was too vague
   to extract anything, acknowledge it briefly and move to the NEXT field in
   the focus bucket's missing list — DO NOT rephrase the same question.
3. Stay locked onto the bucket you were handed in the focus area. Do NOT drift
   to another bucket until the router tells you to. But within the bucket,
   always pick a missing field that is NOT already in the "FIELDS ALREADY
   FILLED" list and is NOT the subject of any "RECENT QUESTIONS" entry.
4. Keep the message to max two sentences.
5. When the focus bucket is founder_fit, ask concrete questions about the
   specific missing fields listed (hours, equity, runway, etc.).
6. Your `message` MUST end with a single question mark. No exceptions while
   ACTIVE mode is in effect. If you cannot think of a question, ask directly
   about the first missing field listed in the focus bucket above.
7. NEVER invent facts about the user. Only reference things explicitly
   present in the profile snapshot, discovered signals, or earlier chat.

Return ONLY valid JSON with this exact shape:
{{"message": "your reply plus the next question", "nextQuestion": "the standalone question"}}"""

    client = _get_client()

    def _call(temp):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=_build_chatbot_messages(chat_history, system_prompt),
            temperature=temp,
            max_tokens=400,
            response_format={"type": "json_object"},
        )
        data = json.loads(response.choices[0].message.content.strip())
        return {
            "message": (data.get("message") or "").strip(),
            "nextQuestion": (data.get("nextQuestion") or "").strip(),
        }

    result = _call(0.2)

    # Guard 1: detect hallucinated farewell or missing-question output.
    if _is_hallucinated_active_message(result["message"], is_active_mode):
        print(
            f"[chatbot_guard] primary LLM call produced hallucinated ACTIVE-mode "
            f"output: {result['message'][:120]!r} — retrying with stricter prompt"
        )
        try:
            retry = _call(0.0)
            if not _is_hallucinated_active_message(retry["message"], is_active_mode):
                return retry
            print(
                f"[chatbot_guard] retry still hallucinated: {retry['message'][:120]!r} — "
                f"falling back to deterministic focus question"
            )
        except Exception as e:
            print(f"[chatbot_guard] retry call failed: {e}")

        # Guard 2: deterministic fallback — no model involvement.
        fallback = _build_focus_fallback_question(focus_missing or [], focus_label or "")
        return {"message": fallback, "nextQuestion": fallback}

    return result


def _extract_fields_from_answer(last_user_text, profile_summary, filled_extra, focus_signal, focus_fields=None):
    """Deterministic, low-temp field extraction from the user's latest answer.
    Returns a JSON object with extractedFields and fieldLabels."""
    if not (last_user_text or "").strip():
        return {"extractedFields": {}, "fieldLabels": {}}

    focus_fields = focus_fields or []
    priority_hint = ""
    if focus_fields:
        priority_hint = (
            "\nThe interview is currently focused on this bucket. These are the "
            "specific missing fields the question was trying to fill — prefer "
            "these field names if the answer fits:\n  "
            + ", ".join(focus_fields)
        )

    system_prompt = f"""You extract structured profile fields from ONE user answer and return JSON.
Be conservative — emit a field only when the user actually states the information.
Never invent or infer from profile context alone. Greetings or short non-answers
must return empty objects.

CRITICAL: Negative, "no", "none", "never", "not yet", "0", or "n/a" answers
ARE valid answers — extract them. They tell us just as much as positive
answers. Examples for the focused field:
  - User: "no" / "no experience" / "none" / "never done a startup"
      → previous_startup_exp: "No prior startup experience"
  - User: "I don't have savings" / "no runway"
      → financial_runway: "No personal runway"
  - User: "no deal breakers" / "nothing comes to mind"
      → deal_breakers: "None stated"
  - User: "whatever works" / "flexible" / "open"
      → (the currently focused field): "Flexible / open to discussion"
Never return an empty object just because the answer was short or negative.
If the user's answer is clearly responding to the focused field, you MUST
emit that focused field with a normalized value — even if the value is a
"no". Returning nothing is ONLY allowed for pure greetings or off-topic
chit-chat ("hi", "thanks", "lol").

Known profile snapshot (do NOT re-extract what is already here):
{profile_summary}

Known answers already collected:
{json.dumps(filled_extra, ensure_ascii=False) if filled_extra else 'None yet.'}

Current interview focus: {focus_signal or 'professional background'}{priority_hint}

Use standard camelCase field names when a clean match exists:
{", ".join(STANDARD_PROFILE_FIELDS)}

Founder-fit fields use snake_case names:
  hours_per_week, equity_expectations, compensation_expectations,
  risk_tolerance, financial_runway, urgency_to_start, previous_startup_exp,
  cofounder_role_needed, ideal_cofounder, deal_breakers

For anything that fits none of the above, use a short snake_case custom key.
Every key in extractedFields must have a human-readable label in fieldLabels.

Return a JSON object with exactly this shape:
{{"extractedFields": {{}}, "fieldLabels": {{}}}}
If nothing substantive to extract, both objects must be empty."""

    client = _get_client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User's latest answer (return JSON):\n{last_user_text}"},
        ],
        temperature=0.0,
        max_tokens=500,
        response_format={"type": "json_object"},
    )
    data = json.loads(response.choices[0].message.content.strip())
    extracted = data.get("extractedFields") or {}
    labels = data.get("fieldLabels") or {}
    for key in list(extracted.keys()):
        if key not in labels or not labels[key]:
            labels[key] = key.replace("_", " ").title()
    return {"extractedFields": extracted, "fieldLabels": labels}


def employee_chatbot_respond(
    chat_history,
    profile_context,
    discovered_fields,
    extra_fields,
    is_resume_mode=False,
    confidence_score=None,
    weakest_dimension=None,
    progress_summary=None,
    should_stop=False,
    question_focus=None,
):
    """
    Two-call chatbot: a chatty message + a conservative extraction pass.
    Backend (route layer) decides when conversation_complete flips.
    """
    # Strip things that are irrelevant to the LLM and can break json.dumps
    # (datetime, ObjectId, password hash, internal housekeeping).
    _hidden = {
        "_id", "password", "created_at", "updated_at", "scrapedAt",
        "vector_status", "vector_status_updated_at", "vector_status_error",
        "profileConfidenceScore", "dimensionScores", "profileCompletionScore",
        "resume_file_id", "resume_text",
    }
    filled_extra = {
        k: v for k, v in (extra_fields or {}).items()
        if v not in [None, "", [], {}] and k not in _hidden
    }
    clean_profile = {
        k: v for k, v in (profile_context or {}).items()
        if v not in [None, "", [], {}] and k not in _hidden
    }
    # default=str handles any stray datetime / ObjectId gracefully.
    discovered_summary = json.dumps(discovered_fields or {}, ensure_ascii=False, default=str)[:3000]
    profile_summary = json.dumps(clean_profile, ensure_ascii=False, default=str)[:4000]
    turn_count = len(chat_history)

    focus = question_focus or {}
    focus_signal = focus.get("signal", "") or weakest_dimension or "professional background"
    focus_type = focus.get("type", "topic_followup")
    focus_label = focus.get("bucket_label", focus_type.replace("_", " ").title())
    focus_reason = focus.get("evidence", "") or "it is the strongest remaining clue."
    focus_description = focus.get("description", "")
    focus_missing = focus.get("missing_fields", []) or []
    target_field = focus.get("target_field") or (focus_missing[0] if focus_missing else None)

    if is_resume_mode:
        mode_block = """CONVERSATION MODE: RESUME MODE (profile already complete)
Stay active and helpful. Accept follow-up info, corrections, or new facts.
If the user adds something new, acknowledge it and ask one smart follow-up."""
    elif should_stop or focus_type == "wrap_up":
        mode_block = """CONVERSATION MODE: INTERVIEW COMPLETE
Every bucket (identity, professional background, topic depth, market fit,
founder fit) has reached its minimum coverage. Write a warm closing message:
- Thank the user for their time.
- Briefly mention 1-2 of the most interesting things you learned (optional,
  keep it short if you include it).
- Say the profile is ready for matching.
- Do NOT invite the user to add more via this chat — the chat is being
  locked and the input is disabled. Do NOT say "you can add more later",
  "feel free to share more", "reach out anytime here", or any variant
  suggesting further chat interaction is possible.
- Do NOT ask any question. Do NOT tell the user to close the chat.
Leave nextQuestion empty."""
    else:
        missing_line = ", ".join(focus_missing[:6]) if focus_missing else "coverage is thin overall"
        target_line = (
            f"THE EXACT FIELD TO ASK ABOUT THIS TURN: {target_field}\n"
            "Your question MUST be scoped to this single field and nothing else. "
            "Do NOT combine multiple fields into one question. Do NOT pick a "
            "different field from the missing list."
            if target_field else
            "No specific target field — ask a broad question about the bucket."
        )
        mode_block = f"""CONVERSATION MODE: ACTIVE INTERVIEW
{progress_summary or f"Profile confidence: {round((confidence_score or 0) * 100)}% (target: 85%)"}

CURRENT FOCUS BUCKET: {focus_label} ({focus_type})
What this bucket is about: {focus_description}
Why we are here: {focus_reason}
Specific fields still missing in this bucket: {missing_line}

{target_line}

Ask ONE question that fills the target field above. Be concrete.
Do NOT drift to other buckets — the router will move you on when this one
is filled. If the focus bucket is "founder_fit", ask a direct question about
the specific target founder-fit field (e.g. if target is hours_per_week,
ask "How many hours per week can you realistically commit to a startup?").
Never re-ask anything already in the profile or earlier in the chat.
Whatever the user replies — even if short, vague, or off-topic — ACCEPT it
and move on; the router will pick the next field next turn. Do NOT try to
"fish" for a better answer by rephrasing the same question.

ABSOLUTE RULES — VIOLATING ANY OF THESE WILL BREAK THE SYSTEM:
1. Do NOT start your reply with "Thank you" or "Thanks" when the focus is
   still founder_fit or any other bucket. The final wrap-up message is
   produced separately by the system, NOT by you.
2. Do NOT say "that's all I need", "we're all set", "interview complete",
   "we have enough", or any variant of goodbye. The interview is NOT done.
3. Do NOT summarise the user's profile. Do NOT say what you've learned so
   far. Just acknowledge the last answer briefly and ask the next question.
4. If the user's last answer was "no", "none", "no experience", or any
   negative — that IS a valid answer. Acknowledge it ("Got it — no prior
   startup experience.") and move on to the next missing field. Never
   interpret a "no" as a signal that the interview is over.
5. You are ONLY allowed to write a closing message when CONVERSATION MODE
   is explicitly set to INTERVIEW COMPLETE above. Right now it is not."""

    manual_block = ""

    last_user_text = ""
    for msg in reversed(chat_history):
        if msg.get("role") == "user":
            last_user_text = msg.get("text", "")
            break

    try:
        chat_result = _generate_chat_message(
            chat_history=chat_history,
            profile_summary=profile_summary,
            discovered_summary=discovered_summary,
            filled_extra=filled_extra,
            mode_block=mode_block,
            manual_block=manual_block,
            focus_missing=focus_missing,
            focus_label=focus_label,
        )
    except Exception as e:
        print(f"[openai_service] Chat message error: {e}")
        chat_result = {
            "message": "I had a brief hiccup. Could you say that again?",
            "nextQuestion": "",
        }

    extracted_fields = {}
    field_labels = {}
    if last_user_text and not should_stop:
        try:
            extraction = _extract_fields_from_answer(
                last_user_text=last_user_text,
                profile_summary=profile_summary,
                filled_extra=filled_extra,
                focus_signal=focus_signal,
                focus_fields=focus_missing,
            )
            extracted_fields = extraction.get("extractedFields") or {}
            field_labels = extraction.get("fieldLabels") or {}
        except Exception as e:
            print(f"[openai_service] Extraction error: {e}")

    if is_resume_mode:
        conv_complete = False
    elif should_stop:
        conv_complete = True
    else:
        conv_complete = False

    return {
        "message": chat_result["message"],
        "nextQuestion": chat_result["nextQuestion"],
        "extractedFields": extracted_fields,
        "fieldLabels": field_labels,
        "conversationComplete": conv_complete,
    }


_SANITIZE_HIDDEN = {
    "_id", "password", "created_at", "updated_at", "scrapedAt",
    "vector_status", "vector_status_updated_at", "vector_status_error",
    "profileConfidenceScore", "dimensionScores", "profileCompletionScore",
    "resume_file_id",
    "chatHistory", "chatbotFieldKeys", "dynamicFieldLabels",
}


def enrich_profile_from_chat(profile_data, extra_fields, discovered_fields=None, resume_text=None, chat_history=None):
    """
    Called ONCE when the chatbot interview wraps up. Uses everything we now
    know (LinkedIn scrape + resume + chatbot answers + raw chat transcript)
    to:
      - rewrite About Me in first person (5-6 sentences)
      - fill or refine missing Basic Info fields (headline, strengths,
        workStyle, careerGoals, preferredRole, preferredIndustry, etc.)

    Returns a dict of fields to merge onto the user doc. Empty dict on failure.
    The caller never overwrites a field the user manually typed — it only
    writes fields that were previously empty or that the LLM materially
    improves (e.g. About Me always gets rewritten because chat adds context).
    """
    clean_profile = {
        k: v for k, v in (profile_data or {}).items()
        if v not in [None, "", [], {}] and k not in _SANITIZE_HIDDEN
    }
    clean_extra = {
        k: v for k, v in (extra_fields or {}).items()
        if v not in [None, "", [], {}] and k not in _SANITIZE_HIDDEN
    }

    # Compact the raw transcript so the LLM can read the user's own words,
    # not just the normalised extracted fields. This is where tone,
    # motivation, and specific founder-fit nuance lives — the earlier
    # version passed only extracted fields, which stripped most of it out.
    transcript_lines = []
    for msg in (chat_history or []):
        role = (msg or {}).get("role")
        text = ((msg or {}).get("text") or "").strip()
        if not text:
            continue
        tag = "USER" if role == "user" else "BOT"
        transcript_lines.append(f"{tag}: {text}")
    transcript_block = "\n".join(transcript_lines)[-5000:]

    # Pass each source as its own explicitly labelled block instead of
    # jamming everything into one opaque JSON blob. Separate sections help
    # the LLM weigh chatbot data on equal footing with LinkedIn data.
    profile_block = json.dumps(clean_profile, ensure_ascii=False, default=str)[:6000]
    chatbot_block = json.dumps(clean_extra, ensure_ascii=False, default=str)[:4000]
    signals_block = json.dumps(discovered_fields or {}, ensure_ascii=False, default=str)[:2500]
    resume_block = (resume_text or "")[:3000]

    user_content = (
        "===== LINKEDIN / PROFILE FIELDS =====\n"
        f"{profile_block}\n\n"
        "===== CHATBOT-EXTRACTED STRUCTURED ANSWERS =====\n"
        f"{chatbot_block}\n\n"
        "===== CHATBOT RAW TRANSCRIPT (user's own words) =====\n"
        f"{transcript_block or 'No transcript available.'}\n\n"
        "===== LINKEDIN POST SIGNALS =====\n"
        f"{signals_block}\n\n"
        "===== RESUME EXCERPT =====\n"
        f"{resume_block or 'No resume.'}"
    )

    system_prompt = """You are a senior career writer and profile enricher.
You are given FIVE distinct sources of truth about one person, each in its own
labelled block:
  1. LINKEDIN / PROFILE FIELDS — the structured profile scraped + cleaned
  2. CHATBOT-EXTRACTED STRUCTURED ANSWERS — specific fields the interviewer
     captured (founder-fit fields, goals, work style, deal-breakers, etc.)
  3. CHATBOT RAW TRANSCRIPT — the user's own words during the interview;
     this reveals motivation, tone, and nuance that the structured fields
     flatten out
  4. LINKEDIN POST SIGNALS — themes/topics inferred from their posts
  5. RESUME EXCERPT — supporting evidence for experience and skills

Produce a refreshed profile that genuinely blends ALL FIVE sources. Return
JSON ONLY, with this schema:

{
  "aboutMe": "FIVE TO SIX sentence first-person About Me (crisp, no filler). REQUIRED structure: (a) who they are + what they do now (from LinkedIn/resume); (b) their signature work or technical depth (specific projects/tech from LinkedIn/resume/posts); (c) what they want next — role + stage + domain (from chatbot answers); (d) their working/collaboration style (from chatbot answers); (e) their founder-fit signals — commitment, risk, ideal co-founder (from chatbot answers); (f) one closing line on motivation or deal-breakers (from chatbot answers). Plain text, no headings, no quotes.",
  "headline": "Concise professional headline (max 120 chars) — only change if the existing one is generic or missing.",
  "strengths": "One-line summary blending LinkedIn evidence with what they said in chat.",
  "workStyle": "How they like to work (team setup, remote/hybrid, hands-on vs lead) — prefer chatbot answers.",
  "careerGoals": "What they want next — role, stage of company, domain — prefer chatbot answers.",
  "preferredRole": "Target role in a startup / product team — prefer chatbot answers.",
  "preferredIndustry": "Industry they most want to build in — prefer chatbot answers."
}

Rules:
- Every field EXCEPT aboutMe is optional. Omit a key entirely rather than invent content.
- aboutMe is REQUIRED. It must be 5-6 sentences and MUST incorporate at
  least THREE specific details taken from the CHATBOT sources (extracted
  answers + transcript). If you produce an About Me that could have been
  written from LinkedIn alone, you have failed the task.
- Never contradict an existing non-empty field. You may expand or refine, not overwrite facts.
- ANTI-HALLUCINATION: Only reference companies, projects, technologies,
  years, roles, and traits that appear LITERALLY in the sources above. Do
  NOT invent accomplishments, titles, years of experience, company
  names, or project names. If the data doesn't support a claim, leave
  it out. Vague beats wrong.
- First person voice throughout aboutMe ("I build...", "I'm drawn to...")."""

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content[:15000]},
            ],
            temperature=0.2,
            max_tokens=800,
            response_format={"type": "json_object"},
        )
        raw = (response.choices[0].message.content or "").strip()
        data = json.loads(raw) if raw else {}
        about = (data or {}).get("aboutMe") or ""
        print(
            f"[enrich_profile_from_chat] sources used: "
            f"profile_fields={len(clean_profile)} chatbot_fields={len(clean_extra)} "
            f"transcript_chars={len(transcript_block)} resume_chars={len(resume_block)} "
            f"aboutMe_sentences={about.count('.') + about.count('!') + about.count('?')}"
        )
    except Exception as e:
        print(f"[openai_service] enrich_profile_from_chat error: {e}")
        return {}

    allowed = {"aboutMe", "headline", "strengths", "workStyle",
               "careerGoals", "preferredRole", "preferredIndustry"}
    result = {}
    for key, value in (data or {}).items():
        if key not in allowed:
            continue
        if isinstance(value, str):
            value = value.strip().strip('"').strip("'")
        if value in [None, "", [], {}]:
            continue
        # Don't overwrite non-empty existing values EXCEPT aboutMe (always rewrite).
        if key != "aboutMe" and clean_profile.get(key) not in [None, "", [], {}]:
            continue
        result[key] = value
    # Mirror aboutMe into about so both forms of the field stay in sync.
    if result.get("aboutMe"):
        result["about"] = result["aboutMe"]
    return result


# Backward-compatible alias — still returns just the About Me string so older
# callers (if any) keep working.
def generate_about_me(profile_data, extra_fields, discovered_fields=None):
    enriched = enrich_profile_from_chat(profile_data, extra_fields, discovered_fields)
    return enriched.get("aboutMe", "")


def normalize_profile_data(linkedin_data, resume_data, questionnaire_data):
    """
    Uses the custom fine-tuned model to merge and normalize data 
    from multiple sources into a canonical profile.
    """
    system_prompt = (
        "You are an expert AI recruiter and data normalizer. "
        "Your job is to take raw, messy data from LinkedIn, Resumes, and User Questionnaires, "
        "and synthesize it into a clean, canonical JSON profile. This normalized profile will be "
        "used for high-accuracy startup compatibility matching. Return ONLY valid JSON.\n\n"
        "EXPECTED JSON SCHEMA:\n"
        "{\n"
        "  \"canonical_skills\": [], // Extract ALL skills, tools, and technical terms from all fields (including unique_value)\n"
        "  \"core_domains\": [], // The overarching domains\n"
        "  \"primary_role\": \"\", // Best guess at their main title\n"
        "  \"unified_profile_summary\": \"\",\n"
        "  \"total_experience_years\": 0,\n"
        "  \"startup_compatibility_flags\": []\n"
        "}\n\n"
        "CRITICAL RULE: DO NOT hallucinate. Include EXACT specialized skills (like RAG, Vectors, FastAPI, LLMs, React) found in the input payload!"
    )
    
    user_payload = {
        "linkedin": linkedin_data or {},
        "resume": resume_data or {},
        "questionnaire": questionnaire_data or {}
    }

    def _split_terms(value):
        if not value:
            return []
        if isinstance(value, list):
            out = []
            for item in value:
                out.extend(_split_terms(item))
            return out
        if isinstance(value, dict):
            out = []
            for item in value.values():
                out.extend(_split_terms(item))
            return out

        text = str(value)
        parts = re.split(r"[\n,;/|]+", text)
        cleaned = []
        for part in parts:
            term = re.sub(r"\s+", " ", part).strip(" -*:\t")
            if 1 <= len(term) <= 80:
                cleaned.append(term)
        return cleaned

    def _extract_keywords(*values):
        text = " ".join(str(v) for v in values if v)
        if not text:
            return []

        patterns = [
            r"\bRAG\b",
            r"\bLLM(?:s)?\b",
            r"\bFastAPI\b",
            r"\bReact(?:\.js)?\b",
            r"\bNode(?:\.js)?\b",
            r"\bMongoDB\b",
            r"\bPinecone\b",
            r"\bChromaDB\b",
            r"\bVector DB\b",
            r"\bVector Database(?:s)?\b",
            r"\bOpenAI\b",
            r"\bGenerative AI\b",
            r"\bMachine Learning\b",
            r"\bDeep Learning\b",
            r"\bNatural Language Processing\b",
            r"\bComputer Vision\b",
            r"\bPython\b",
            r"\bTensorFlow\b",
            r"\bPyTorch\b",
            r"\bScikit-learn\b",
            r"\bSQL\b",
            r"\bMySQL\b",
            r"\bStreamlit\b",
            r"\bTableau\b",
            r"\bPower BI\b",
            r"\bAWS\b",
            r"\bJupyter(?: Notebook)?\b",
            r"\bOpenCV\b",
            r"\bGemini\b",
            r"\bVertex AI\b",
            r"\bResponsive Design\b",
            r"\bJavaScript\b",
            r"\bHTML\b",
            r"\bCSS\b",
        ]

        found = []
        for pattern in patterns:
            for match in re.findall(pattern, text, flags=re.IGNORECASE):
                found.append(match)
        return found

    def _dedupe_keep_order(values):
        seen = set()
        out = []
        for value in values:
            cleaned = re.sub(r"\s+", " ", str(value or "")).strip(" ,")
            if not cleaned:
                continue
            key = cleaned.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(cleaned)
        return out

    deterministic_skills = _dedupe_keep_order(
        _split_terms((linkedin_data or {}).get("skills"))
        + _split_terms((linkedin_data or {}).get("tools"))
        + _split_terms((resume_data or {}).get("skills"))
        + _split_terms((resume_data or {}).get("tools"))
        + _split_terms((questionnaire_data or {}).get("unique_value"))
        + _split_terms((questionnaire_data or {}).get("domain_expertise"))
        + _split_terms((questionnaire_data or {}).get("co_founder_expectations"))
        + _extract_keywords(
            (linkedin_data or {}).get("about"),
            (linkedin_data or {}).get("aboutMe"),
            (linkedin_data or {}).get("headline"),
            (linkedin_data or {}).get("currentPosition"),
            (resume_data or {}).get("resume_text"),
            (resume_data or {}).get("bio"),
            (questionnaire_data or {}).get("unique_value"),
            (questionnaire_data or {}).get("domain_expertise"),
        )
    )
    deterministic_domains = _dedupe_keep_order(
        _split_terms((linkedin_data or {}).get("coreDomains"))
        + _split_terms((linkedin_data or {}).get("interests"))
        + _split_terms((questionnaire_data or {}).get("industry_preferences"))
        + _split_terms((questionnaire_data or {}).get("domain_expertise"))
        + _extract_keywords(
            (linkedin_data or {}).get("about"),
            (linkedin_data or {}).get("headline"),
            (resume_data or {}).get("bio"),
            (questionnaire_data or {}).get("unique_value"),
        )
    )
    summary_parts = [
        (linkedin_data or {}).get("headline"),
        (linkedin_data or {}).get("about"),
        (linkedin_data or {}).get("aboutMe"),
        (resume_data or {}).get("bio"),
        (questionnaire_data or {}).get("unique_value"),
    ]
    fallback_summary = " ".join(str(part).strip() for part in summary_parts if part).strip()
    fallback_role = (
        (linkedin_data or {}).get("professional_title")
        or (linkedin_data or {}).get("currentPosition")
        or (linkedin_data or {}).get("headline")
        or ""
    )
    fallback_experience = (
        (linkedin_data or {}).get("experience_years")
        or (linkedin_data or {}).get("totalYearsExperience")
        or (resume_data or {}).get("experience_years")
        or 0
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)}
    ]
    
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.1,  
            response_format={"type": "json_object"}
        )
        raw = response.choices[0].message.content.strip()
        normalized = json.loads(raw)
        normalized["canonical_skills"] = _dedupe_keep_order(
            (normalized.get("canonical_skills") or []) + deterministic_skills
        )
        normalized["core_domains"] = _dedupe_keep_order(
            (normalized.get("core_domains") or []) + deterministic_domains
        )
        if not normalized.get("primary_role"):
            normalized["primary_role"] = fallback_role
        if not normalized.get("unified_profile_summary"):
            normalized["unified_profile_summary"] = fallback_summary[:1200]
        if not normalized.get("total_experience_years"):
            try:
                normalized["total_experience_years"] = int(re.search(r"\d+", str(fallback_experience)).group())
            except Exception:
                normalized["total_experience_years"] = 0
        normalized["startup_compatibility_flags"] = _dedupe_keep_order(
            normalized.get("startup_compatibility_flags") or []
        )
        return normalized
    except Exception as e:
        print(f"[openai_service] Normalization error: {e}")
        return {
            "canonical_skills": deterministic_skills,
            "core_domains": deterministic_domains,
            "primary_role": fallback_role,
            "unified_profile_summary": fallback_summary[:1200],
            "total_experience_years": int(re.search(r"\d+", str(fallback_experience)).group()) if re.search(r"\d+", str(fallback_experience)) else 0,
            "startup_compatibility_flags": [],
        }
