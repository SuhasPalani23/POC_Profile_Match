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


def _generate_chat_message(chat_history, profile_summary, discovered_summary, filled_extra, mode_block, manual_block):
    """Conversational pass — returns just message + nextQuestion as JSON. Higher temp."""
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

Rules:
1. Acknowledge what the user just said in ONE short clause, then ask ONE question.
2. Never re-ask anything already covered in the profile, extra fields, or earlier chat.
3. Stay locked onto the bucket you were handed in the focus area. Do NOT drift
   to another bucket until the router tells you to.
4. Keep the message to max two sentences.
5. When the focus bucket is founder_fit, ask concrete questions about the
   specific missing fields listed (hours, equity, runway, etc.).

Return ONLY valid JSON with this exact shape:
{{"message": "your reply plus the next question", "nextQuestion": "the standalone question"}}"""

    client = _get_client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=_build_chatbot_messages(chat_history, system_prompt),
        temperature=0.55,
        max_tokens=400,
        response_format={"type": "json_object"},
    )
    data = json.loads(response.choices[0].message.content.strip())
    return {
        "message": (data.get("message") or "").strip(),
        "nextQuestion": (data.get("nextQuestion") or "").strip(),
    }


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
        temperature=0.1,
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

    if is_resume_mode:
        mode_block = """CONVERSATION MODE: RESUME MODE (profile already complete)
Stay active and helpful. Accept follow-up info, corrections, or new facts.
If the user adds something new, acknowledge it and ask one smart follow-up."""
    elif should_stop or focus_type == "wrap_up":
        mode_block = """CONVERSATION MODE: INTERVIEW COMPLETE
Every bucket (identity, professional background, topic depth, market fit,
founder fit) has reached its minimum coverage. Write a warm closing message:
- Summarise the 2-3 most interesting things you learned.
- Say the profile is ready for matching.
- Invite the user to add more later via this chat.
Leave nextQuestion empty."""
    else:
        missing_line = ", ".join(focus_missing[:6]) if focus_missing else "coverage is thin overall"
        mode_block = f"""CONVERSATION MODE: ACTIVE INTERVIEW
{progress_summary or f"Profile confidence: {round((confidence_score or 0) * 100)}% (target: 85%)"}

CURRENT FOCUS BUCKET: {focus_label} ({focus_type})
What this bucket is about: {focus_description}
Why we are here: {focus_reason}
Specific fields still missing in this bucket: {missing_line}

Ask ONE question that will fill one of the missing fields above. Be concrete.
Do NOT drift to other buckets — the router will move you on when this one
is filled. If the focus bucket is "founder_fit", ask a direct question about
the specific missing founder-fit field (e.g. if hours_per_week is missing,
ask "How many hours per week can you realistically commit to a startup?").
Never re-ask anything already in the profile or earlier in the chat.
IMPORTANT: Do NOT wrap up, say goodbye, or end the conversation. The interview
is NOT complete yet — there are still missing fields to collect. Keep asking."""

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


def enrich_profile_from_chat(profile_data, extra_fields, discovered_fields=None, resume_text=None):
    """
    Called ONCE when the chatbot interview wraps up. Uses everything we now
    know (LinkedIn scrape + resume + chatbot answers) to:
      - rewrite About Me in first person
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

    payload = {
        "profile": clean_profile,
        "chatbot_answers": clean_extra,
        "post_signals": discovered_fields or {},
        "resume_excerpt": (resume_text or "")[:3000],
    }

    system_prompt = """You are a senior career writer and profile enricher.
You are given someone's LinkedIn data, their resume excerpt, LinkedIn post
signals, and a set of structured answers they gave during a chatbot interview.

Produce a refreshed profile that blends all sources. Return JSON ONLY, with
this schema:

{
  "aboutMe": "4-5 sentence first-person About Me blending what LinkedIn shows with what the chatbot revealed (goals, founder fit, signature work). Plain text, no headings, no quotes.",
  "headline": "A concise professional headline (max 120 chars) — only change if the existing one is generic or missing.",
  "strengths": "One-line summary of what makes them useful on a startup team. Blend LinkedIn evidence with what they said in chat.",
  "workStyle": "How they like to work (team setup, remote/hybrid, hands-on vs lead).",
  "careerGoals": "What they want next — role, stage of company, domain.",
  "preferredRole": "Target role in a startup / product team.",
  "preferredIndustry": "Industry they most want to build in."
}

Rules:
- Every field is OPTIONAL. Omit a key entirely rather than invent content.
- Never contradict an existing non-empty field. You may expand or refine, not overwrite facts.
- aboutMe must ALWAYS be produced if there is meaningful content; it's the one field that gets rewritten every time."""

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False, default=str)[:8000]},
            ],
            temperature=0.4,
            max_tokens=700,
            response_format={"type": "json_object"},
        )
        raw = (response.choices[0].message.content or "").strip()
        data = json.loads(raw) if raw else {}
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
