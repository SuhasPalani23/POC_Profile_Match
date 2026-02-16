from google import genai
from config import Config
import json
import re


class GeminiService:
    def __init__(self):
        """
        Initialize Gemini client using new google-genai SDK
        """
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
        self.model = "gemini-2.5-flash"

    # ----------------------------
    # Utility: Safe JSON extraction
    # ----------------------------
    def _extract_json(self, text):
        """
        Extract first valid JSON object from model response
        """
        try:
            # Remove markdown code blocks if present
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

            # Fallback structure
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
    # Rank candidates for a project
    # --------------------------------------
    def rank_candidates(self, project, candidates):
        prompt = f"""
You are an AI matching system for startup team formation.

Evaluate and rank candidates for the given startup project.

Project Title: {project.get('title', '')}
Project Description: {project.get('description', '')}

Candidates:
"""

        for i, candidate in enumerate(candidates):
            prompt += f"""
Candidate {i}:
Name: {candidate.get('name', '')}
Role: {candidate.get('role', 'user')}
Skills: {', '.join(candidate.get('skills', []))}
Bio: {candidate.get('bio', '')}
"""

        prompt += """

For each candidate provide:

1. match_percentage (0-100)
2. reasoning
3. strengths (array)
4. concerns (array)

Respond ONLY in valid JSON:

{
    "rankings": [
        {
            "candidate_index": 0,
            "match_percentage": 85,
            "reasoning": "Why they match",
            "strengths": ["..."],
            "concerns": ["..."]
        }
    ]
}

Sort rankings by match_percentage in descending order.
"""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )

            result = self._extract_json(response.text)

            if result and "rankings" in result:
                rankings = result["rankings"]

                # Ensure sorted descending
                rankings = sorted(
                    rankings,
                    key=lambda x: x.get("match_percentage", 0),
                    reverse=True
                )

                return rankings

            return []

        except Exception as e:
            print(f"Error ranking candidates: {e}")
            return []
