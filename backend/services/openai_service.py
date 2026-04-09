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


def founder_chatbot_respond(chat_history, profile_context, discovered_fields, extra_fields):
    """
    LLM-driven chatbot that interviews the user as a founder/cofounder.
    Collects information dynamically and creates new fields on the fly.
    """
    filled_extra = {k: v for k, v in (extra_fields or {}).items() if v not in [None, "", [], {}]}
    discovered_summary = json.dumps(discovered_fields or {}, ensure_ascii=False)[:3000]
    profile_summary = json.dumps(
        {k: v for k, v in (profile_context or {}).items() if v not in [None, "", [], {}]},
        ensure_ascii=False
    )[:4000]

    system_prompt = f"""You are an expert startup advisor and talent profiling assistant. Your job is to interview this person to understand their founder/cofounder mindset and capabilities.

ALREADY KNOWN PROFILE:
{profile_summary}

DISCOVERED FROM LINKEDIN POSTS:
{discovered_summary}

ALREADY COLLECTED EXTRA FIELDS:
{json.dumps(filled_extra, ensure_ascii=False) if filled_extra else "None yet"}

YOUR GOAL:
- Collect as much information as possible about this person's founder/cofounder profile
- Ask questions ONE AT A TIME in a conversational, friendly way
- Focus on these key areas (but adapt based on conversation):
  * Hours per week they can commit
  * Equity expectations vs compensation preferences
  * Risk tolerance for startups
  * Previous startup/founding experience
  * Leadership style
  * Technical vs business orientation
  * Geographic preferences for team/work
  * Industry preferences for co-founding
  * Stage preference (idea, MVP, growth, scale)
  * What they bring to the table (unique value)
  * What they're looking for in a co-founder
  * Timeline/urgency to start something
  * Financial runway (how long can they go without salary)
  * Domain expertise areas
  * Network strength
  * Decision-making style
  * Conflict resolution approach

RESPONSE FORMAT - Return ONLY this JSON:
{{
  "message": "Your conversational response to the user",
  "extractedFields": {{
    "field_name_in_snake_case": "extracted value from user's answer"
  }},
  "nextQuestion": "The next question to ask (empty string if done)",
  "conversationComplete": false,
  "fieldLabels": {{
    "field_name_in_snake_case": "Human Readable Label"
  }}
}}

CRITICAL RULES:
- EVERY user message MUST result in at least one field in `extractedFields`. If the user says "40", extract it as the answer to whatever you just asked.
- `extractedFields` must ALWAYS capture structured data from the user's latest response. NEVER return an empty `extractedFields` if the user gave any answer.
- Field names should be descriptive snake_case (e.g., "hours_per_week", "equity_preference", "risk_tolerance")
- `fieldLabels` MUST have a human-readable label for EVERY key in `extractedFields`
- Examples:
  - User says "40" after you ask about hours → extractedFields: {{"hours_per_week": "40"}}, fieldLabels: {{"hours_per_week": "Hours Per Week"}}
  - User says "compensation" after equity question → extractedFields: {{"compensation_preference": "compensation over equity"}}, fieldLabels: {{"compensation_preference": "Compensation Preference"}}
  - User says "high risk" → extractedFields: {{"risk_tolerance": "high"}}, fieldLabels: {{"risk_tolerance": "Risk Tolerance"}}
- Ask follow-up questions based on interesting answers
- Be warm, professional, and genuinely curious
- If the user seems done or has answered enough (15+ fields collected), wrap up gracefully
- Set `conversationComplete` to true only when you've collected substantial info
- Return ONLY valid JSON"""

    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history:
        role = "user" if msg.get('role') == "user" else "assistant"
        content = msg.get('text', '')
        messages.append({"role": role, "content": content})

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.4,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        raw = response.choices[0].message.content.strip()
        return json.loads(raw)
    except Exception as e:
        print(f"[openai_service] Chatbot error: {e}")
        return {
            "message": "I had a brief hiccup. Could you repeat that?",
            "extractedFields": {},
            "nextQuestion": "",
            "conversationComplete": False,
            "fieldLabels": {},
        }


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
