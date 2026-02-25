from google import genai
from config import Config
import json
import re


class GeminiService:
    def __init__(self):
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
        self.model = "gemini-2.5-flash"

    # ----------------------------
    # Utility: Safe JSON extraction
    # ----------------------------
    def _extract_json(self, text):
        try:
            text = re.sub(r"```json|```", "", text).strip()
            start = text.find("{")
            end = text.rfind("}") + 1
            if start == -1 or end == 0:
                return None
            json_str = text[start:end]
            return json.loads(json_str)
        except Exception as e:
            print("JSON extraction error:", e)
            return None

    # --------------------------------------
    # Analyze project to determine team needs
    # --------------------------------------
    def analyze_project_needs(self, project_description):
        prompt = f"""
You are an expert startup advisor.

Analyze this startup project description and identify:

1. Required technical skills
2. Required roles (e.g., SDE, Data Scientist, Business Analyst, Cloud Engineer, Security Expert, Data Engineer)
3. Key competencies needed
4. The founding mindset qualities that would complement the founder

Project Description:
{project_description}

Respond ONLY in valid JSON format:

{{
    "required_skills": ["skill1", "skill2"],
    "required_roles": ["role1", "role2"],
    "key_competencies": ["competency1", "competency2"],
    "founding_qualities": ["quality1", "quality2"]
}}
"""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            result = self._extract_json(response.text)
            if result:
                return result
            return {
                "required_skills": [],
                "required_roles": [],
                "key_competencies": [],
                "founding_qualities": []
            }
        except Exception as e:
            print(f"Error analyzing project: {e}")
            return {
                "required_skills": [],
                "required_roles": [],
                "key_competencies": [],
                "founding_qualities": []
            }

    # --------------------------------------
    # ATS-style candidate ranking for a project
    # --------------------------------------
    def rank_candidates(self, project, candidates, project_analysis=None):
        """
        ATS-style scoring of candidates against a project.

        match_percentage is the ATS score — it reflects genuine fit using the
        full candidate profile: listed skills, bio, experience years, AND
        resume text (if uploaded). This is what founders see on the match cards.

        project_analysis: pre-extracted required_skills/roles from analyze_project_needs().
        Passing it in keeps scoring consistent with the Pinecone search query and
        avoids Gemini re-deriving requirements from scratch with potentially different results.
        """

        # Build requirements context from pre-analysis if available
        requirements_context = ""
        if project_analysis:
            req_skills = project_analysis.get("required_skills", [])
            req_roles = project_analysis.get("required_roles", [])
            key_competencies = project_analysis.get("key_competencies", [])
            requirements_context = f"""
Pre-analyzed Project Requirements:
- Required Skills: {', '.join(req_skills) if req_skills else 'Derive from description'}
- Required Roles: {', '.join(req_roles) if req_roles else 'Derive from description'}
- Key Competencies: {', '.join(key_competencies) if key_competencies else 'Derive from description'}
"""

        # Build candidate blocks — include resume_text if present
        candidate_blocks = ""
        for i, candidate in enumerate(candidates):
            resume_section = ""
            if candidate.get("resume_text"):
                # Truncate to keep prompt size manageable — 1500 chars per candidate is enough
                resume_section = f"\nResume Content:\n{candidate['resume_text'][:1500]}"

            candidate_blocks += f"""
Candidate {i}:
- Name: {candidate.get('name', '')}
- Professional Title: {candidate.get('professional_title', '')}
- Skills: {', '.join(candidate.get('skills', []))}
- Experience: {candidate.get('experience_years', 0)} years
- Bio: {candidate.get('bio', '')}{resume_section}
"""

        prompt = f"""
You are a senior technical recruiter performing ATS (Applicant Tracking System) scoring
for a startup team formation platform.

Your task: score each candidate's fit for this project and assign a match_percentage
that the founder will see. Be accurate and differentiated — avoid clustering scores.

Project Title: {project.get('title', '')}
Project Description:
{project.get('description', '')}
{requirements_context}

Score each candidate on these criteria:
1. Technical skill match — do their skills (listed + inferred from resume/bio) cover what's needed? (40%)
2. Experience level fit — is their seniority appropriate for a startup role? (20%)
3. Domain/industry alignment — relevant background for this specific project? (25%)
4. Execution signals — bio, resume, achievements suggest they can build and ship? (15%)

Important:
- If a candidate has uploaded a resume, use that content heavily — it contains richer signal than the skills list alone
- Infer implied skills (e.g. "built Kafka pipelines" implies Kafka, distributed systems, Python/Java)
- Penalise candidates who are clearly mismatched in role or domain even if they have some overlapping skills
- Spread scores across the full range — a poor fit should score 20-40%, a strong fit 75-95%

Candidates:
{candidate_blocks}

Respond ONLY in valid JSON:

{{
    "rankings": [
        {{
            "candidate_index": 0,
            "match_percentage": 85,
            "reasoning": "2-3 sentence explanation of why this score — reference specific skills or resume content",
            "strengths": ["specific strength 1", "specific strength 2"],
            "concerns": ["specific gap or concern 1"]
        }}
    ]
}}

Sort rankings by match_percentage descending.
"""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            result = self._extract_json(response.text)

            if result and "rankings" in result:
                rankings = sorted(
                    result["rankings"],
                    key=lambda x: x.get("match_percentage", 0),
                    reverse=True
                )
                return rankings

            return []

        except Exception as e:
            print(f"Error ranking candidates: {e}")
            return []