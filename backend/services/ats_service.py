import os
import re
import PyPDF2
import docx
from typing import Dict, List, Optional
from services.gemini_service import GeminiService


class ATSService:
    def __init__(self):
        self.gemini_service = GeminiService()

    # ------------------------------------------------------------------
    # File parsing (still deterministic — that's fine)
    # ------------------------------------------------------------------

    def parse_resume_pdf(self, file_path: str) -> str:
        try:
            text = ""
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() or ""
            return text.strip()
        except Exception as e:
            print(f"[ATSService] PDF parse error: {e}")
            return ""

    def parse_resume_docx(self, file_path: str) -> str:
        try:
            doc = docx.Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs).strip()
        except Exception as e:
            print(f"[ATSService] DOCX parse error: {e}")
            return ""

    def parse_resume(self, file_path: str) -> str:
        """Dispatch to the right parser based on file extension."""
        if not file_path:
            return ""
        if file_path.lower().endswith(".pdf"):
            return self.parse_resume_pdf(file_path)
        if file_path.lower().endswith((".docx", ".doc")):
            return self.parse_resume_docx(file_path)
        return ""

    # Lightweight regex for contact info — no need to burn LLM tokens on this
    def extract_email(self, text: str) -> Optional[str]:
        matches = re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", text)
        return matches[0] if matches else None

    def extract_phone(self, text: str) -> Optional[str]:
        matches = re.findall(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
        return matches[0] if matches else None

    # ------------------------------------------------------------------
    # LLM: analyze resume text
    # ------------------------------------------------------------------

    def analyze_resume_with_ai(self, resume_text: str) -> Dict:
        """
        Full LLM analysis of a resume.
        Returns structured JSON with skills, experience, achievements, etc.
        """
        prompt = f"""
You are an expert technical recruiter and career advisor.

Analyze the following resume text in depth and extract structured information.
Be thorough — infer skills from context (e.g. "built Django REST APIs" implies Python, REST, Django).

Resume:
\"\"\"
{resume_text[:6000]}
\"\"\"

Respond ONLY with valid JSON — no markdown fences:
{{
    "skills": ["skill1", "skill2", ...],
    "experience_years": <integer, estimate if not explicit>,
    "strengths": ["strength1", ...],
    "roles": ["role1", ...],
    "education": ["degree/institution", ...],
    "certifications": ["cert1", ...],
    "key_achievements": ["achievement1", ...],
    "recommended_roles": ["role1", ...],
    "summary": "2-3 sentence professional summary",
    "seniority_level": "junior|mid|senior|lead|principal"
}}
"""
        try:
            response = self.gemini_service.client.models.generate_content(
                model=self.gemini_service.model,
                contents=prompt,
            )
            result = self.gemini_service._extract_json(response.text)
            return result or {}
        except Exception as e:
            print(f"[ATSService] AI resume analysis error: {e}")
            return {}

    # ------------------------------------------------------------------
    # LLM: ATS compatibility score
    # ------------------------------------------------------------------

    def calculate_ats_score(self, candidate_text: str, job_description: str) -> Dict:
        """
        Ask Gemini to reason about fit between a candidate profile/resume and a
        job description. Returns a rich scoring object.

        Why LLM instead of cosine similarity:
        - Cosine similarity measures surface word overlap, not semantic fit.
        - An LLM understands that "NumPy/Pandas data wrangling" is highly relevant
          to "data pipeline engineering", even if those exact words don't appear.
        - It can weight mandatory vs. nice-to-have skills, catch red flags, and
          give actionable reasoning — NLP can't do any of that.
        """
        prompt = f"""
You are a senior technical recruiter evaluating a candidate for a startup project.

--- Candidate Profile / Resume ---
{candidate_text[:4000]}

--- Job / Project Description ---
{job_description[:3000]}

Evaluate the candidate's fit comprehensively. Consider:
1. Technical skill overlap (including inferred/implied skills)
2. Experience level appropriateness
3. Domain knowledge alignment
4. Soft skills and leadership signals
5. Gaps or concerns

Respond ONLY with valid JSON — no markdown fences:
{{
    "overall_score": <integer 0-100>,
    "technical_fit": <integer 0-100>,
    "experience_fit": <integer 0-100>,
    "domain_fit": <integer 0-100>,
    "matched_skills": ["skill1", ...],
    "missing_skills": ["skill1", ...],
    "inferred_skills": ["skill that was implied but not stated", ...],
    "strengths": ["strength1", ...],
    "gaps": ["gap1", ...],
    "overall_reasoning": "2-3 sentence explanation of the score"
}}
"""
        try:
            response = self.gemini_service.client.models.generate_content(
                model=self.gemini_service.model,
                contents=prompt,
            )
            result = self.gemini_service._extract_json(response.text)
            return result or {
                "overall_score": 0,
                "technical_fit": 0,
                "experience_fit": 0,
                "domain_fit": 0,
                "matched_skills": [],
                "missing_skills": [],
                "inferred_skills": [],
                "strengths": [],
                "gaps": [],
                "overall_reasoning": "Unable to score at this time.",
            }
        except Exception as e:
            print(f"[ATSService] ATS score error: {e}")
            return {"overall_score": 0, "overall_reasoning": str(e)}

    # ------------------------------------------------------------------
    # LLM: optimization tips
    # ------------------------------------------------------------------

    def generate_profile_optimization_tips(
        self, candidate_text: str, job_description: str
    ) -> List[str]:
        """
        Use Gemini to generate actionable, specific tips for improving the
        candidate's profile/resume for a given role.
        """
        prompt = f"""
You are an expert ATS optimization coach and career advisor.

Candidate Profile / Resume:
{candidate_text[:3000]}

Target Job / Project Description:
{job_description[:2000]}

Generate 6-8 highly specific, actionable tips to improve this candidate's ATS score
and overall fit for the role. Be concrete — name specific skills, certifications,
keywords, and phrasing improvements.

Respond ONLY with valid JSON — no markdown fences:
{{
    "optimization_tips": [
        "tip1",
        "tip2",
        ...
    ]
}}
"""
        try:
            response = self.gemini_service.client.models.generate_content(
                model=self.gemini_service.model,
                contents=prompt,
            )
            result = self.gemini_service._extract_json(response.text)
            return result.get("optimization_tips", []) if result else []
        except Exception as e:
            print(f"[ATSService] Optimization tips error: {e}")
            return []

    # ------------------------------------------------------------------
    # LLM: skill extraction (for quick skill tagging without full analysis)
    # ------------------------------------------------------------------

    def extract_skills_with_ai(self, text: str) -> List[str]:
        """
        Extract skills from any text (bio, resume snippet, project description)
        using the LLM so we catch implied and abbreviated skills too.
        """
        prompt = f"""
Extract ALL technical and professional skills mentioned or implied in the following text.
Include: programming languages, frameworks, tools, methodologies, platforms, soft skills
if they are professionally significant, and domain expertise.

Text:
\"\"\"
{text[:3000]}
\"\"\"

Respond ONLY with valid JSON — no markdown fences:
{{
    "skills": ["skill1", "skill2", ...]
}}
"""
        try:
            response = self.gemini_service.client.models.generate_content(
                model=self.gemini_service.model,
                contents=prompt,
            )
            result = self.gemini_service._extract_json(response.text)
            return result.get("skills", []) if result else []
        except Exception as e:
            print(f"[ATSService] Skill extraction error: {e}")
            return []

    # ------------------------------------------------------------------
    # Comprehensive analysis (called on resume upload)
    # ------------------------------------------------------------------

    def comprehensive_profile_analysis(
        self, user_data: Dict, resume_path: Optional[str] = None
    ) -> Dict:
        """
        Full analysis pipeline:
        1. Parse resume file → raw text
        2. Gemini extracts structured info
        3. Merge with existing profile skills
        4. Return everything to the caller (route saves what it needs)
        """
        analysis = {
            "basic_info": {
                "name": user_data.get("name", ""),
                "email": user_data.get("email", ""),
                "bio": user_data.get("bio", ""),
                "skills": user_data.get("skills", []),
                "experience_years": user_data.get("experience_years", 0),
            },
            "resume_text": "",
            "resume_analysis": {},
            "ai_insights": {},
            "merged_skills": user_data.get("skills", []),
            "recommendations": [],
        }

        if not resume_path:
            return analysis

        resume_text = self.parse_resume(resume_path)
        if not resume_text:
            return analysis

        analysis["resume_text"] = resume_text

        # Contact extraction (cheap regex)
        analysis["resume_analysis"] = {
            "text_preview": resume_text[:500] + "..." if len(resume_text) > 500 else resume_text,
            "email": self.extract_email(resume_text),
            "phone": self.extract_phone(resume_text),
        }

        # Full LLM analysis
        ai_insights = self.analyze_resume_with_ai(resume_text)
        analysis["ai_insights"] = ai_insights

        if ai_insights:
            analysis["resume_analysis"]["estimated_experience"] = ai_insights.get(
                "experience_years", 0
            )

            # Merge skills: existing profile + extracted from resume, deduped
            extracted_skills = ai_insights.get("skills", [])
            existing_skills = user_data.get("skills", [])
            merged = list({s.strip() for s in existing_skills + extracted_skills if s.strip()})
            analysis["merged_skills"] = merged

            analysis["recommendations"] = ai_insights.get("key_achievements", [])

        return analysis