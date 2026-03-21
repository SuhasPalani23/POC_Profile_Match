from groq import Groq
from config import Config
import json
import re


class LlamaService:
    def __init__(self):
        self.client = Groq(api_key=Config.GROQ_API_KEY)
        self.model = "llama-3.1-8b-instant"

    def _extract_json(self, text):
        try:
            text = re.sub(r"```json|```", "", text).strip()
            start = text.find("{")
            end = text.rfind("}") + 1
            if start == -1 or end == 0:
                start = text.find("[")
                end = text.rfind("]") + 1
                if start == -1 or end == 0:
                    return None
            json_str = text[start:end]
            return json.loads(json_str)
        except Exception as e:
            print("JSON extraction error:", e)
            return None

    def generate_json(self, prompt: str):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            return self._extract_json(response.choices[0].message.content)
        except Exception as e:
            print(f"LLM Error: {e}")
            return None

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
        result = self.generate_json(prompt)
        if result:
            return result
        return {
            "required_skills": [],
            "required_roles": [],
            "key_competencies": [],
            "founding_qualities": [],
        }

    def rank_candidates(self, project, candidates, project_analysis=None):
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

        candidate_blocks = ""
        for i, candidate in enumerate(candidates):
            resume_section = ""
            if candidate.get("resume_text"):
                resume_section = f"\nResume Content:\n{candidate['resume_text']}"

            candidate_blocks += f"""
Candidate {i}:
- Name: {candidate.get('name', '')}
- Professional Title: {candidate.get('professional_title', '')}
- Skills: {', '.join(candidate.get('skills', []))}
- Experience: {candidate.get('experience_years', 0)} years
- Bio: {candidate.get('bio', '')}{resume_section}
"""

        prompt = f"""
You are a senior technical recruiter performing ATS scoring
for a startup team formation platform.

Your task: score each candidate's fit for this project and assign a match_percentage.

Project Title: {project.get('title', '')}
Project Description:
{project.get('description', '')}
{requirements_context}

Score each candidate on these criteria:
1. Technical skill match (40%)
2. Experience level fit (20%)
3. Domain/industry alignment (25%)
4. Execution signals (15%)

Candidates:
{candidate_blocks}

Respond ONLY in valid JSON:
{{
    "rankings": [
        {{
            "candidate_index": 0,
            "match_percentage": 85,
            "reasoning": "2-3 sentence explanation of why this score",
            "strengths": ["specific strength 1"],
            "concerns": ["specific gap 1"]
        }}
    ]
}}

Sort rankings by match_percentage descending. Include every candidate exactly once.
"""
        result = self.generate_json(prompt)
        if result and "rankings" in result:
            return sorted(result["rankings"], key=lambda x: x.get("match_percentage", 0), reverse=True)
        return []
