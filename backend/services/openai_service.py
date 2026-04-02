"""OpenAI-powered LLM service for post analysis and founder profiling chatbot."""

import json
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
