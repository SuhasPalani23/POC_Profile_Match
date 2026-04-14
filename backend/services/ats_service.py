import os
import re
import PyPDF2
import docx
from typing import Dict, List, Optional
from services.llm_service import LLMService


class ATSService:
    def __init__(self):
        self.llm_service = LLMService()

    # ------------------------------------------------------------------
    # File parsing
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
        if not file_path:
            return ""
        if file_path.lower().endswith(".pdf"):
            return self.parse_resume_pdf(file_path)
        if file_path.lower().endswith((".docx", ".doc")):
            return self.parse_resume_docx(file_path)
        return ""

    def extract_email(self, text: str) -> Optional[str]:
        matches = re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", text)
        return matches[0] if matches else None

    def extract_phone(self, text: str) -> Optional[str]:
        matches = re.findall(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
        return matches[0] if matches else None

    # ------------------------------------------------------------------
    # Build comprehensive candidate text from ALL profile fields
    # ------------------------------------------------------------------

    def build_candidate_text(self, user: Dict) -> str:
        """Build a rich text representation of a candidate using ALL available data."""
        parts = []

        # Core identity
        if user.get("name"):
            parts.append(f"Name: {user['name']}")
        if user.get("professional_title") or user.get("headline"):
            parts.append(f"Title: {user.get('professional_title') or user.get('headline')}")
        if user.get("currentPosition"):
            parts.append(f"Current Role: {user['currentPosition']} at {user.get('currentCompany', '')}")
        if user.get("experience_years") or user.get("totalYearsExperience"):
            parts.append(f"Experience: {user.get('experience_years') or user.get('totalYearsExperience')} years")
        if user.get("location"):
            parts.append(f"Location: {user['location']}")

        # Bio / About
        if user.get("about") or user.get("bio"):
            parts.append(f"About: {(user.get('about') or user.get('bio', ''))[:800]}")

        # Skills & Tools
        skills = user.get("skills", [])
        if skills:
            parts.append(f"Skills: {', '.join(skills[:30])}")
        tools = user.get("tools", [])
        if tools:
            parts.append(f"Tools & Technologies: {', '.join(tools[:20])}")

        # Domains & Interests
        domains = user.get("coreDomains", [])
        if domains:
            parts.append(f"Core Domains: {', '.join(domains[:8])}")
        interests = user.get("interests", [])
        if interests:
            parts.append(f"Interests: {', '.join(interests[:8])}")

        # Career
        if user.get("careerGoals"):
            parts.append(f"Career Goals: {user['careerGoals']}")
        if user.get("preferredRole"):
            parts.append(f"Preferred Role: {user['preferredRole']}")
        if user.get("preferredIndustry") or user.get("industryInclination"):
            parts.append(f"Industry Preference: {user.get('preferredIndustry') or user.get('industryInclination')}")
        if user.get("skillStrength"):
            parts.append(f"Skill Level: {user['skillStrength']}")
        if user.get("workStyle"):
            parts.append(f"Work Style: {user['workStyle']}")
        if user.get("strengths"):
            parts.append(f"Strengths: {user['strengths']}")

        # Education
        education = user.get("education", [])
        if education:
            edu_parts = []
            for e in education[:3]:
                if isinstance(e, dict):
                    edu_parts.append(f"{e.get('degree', '')} - {e.get('school', '')} ({e.get('duration', '')})")
                elif isinstance(e, str):
                    edu_parts.append(e)
            if edu_parts:
                parts.append(f"Education: {'; '.join(edu_parts)}")

        # Certifications
        certs = user.get("certifications", [])
        if certs:
            cert_names = []
            for c in certs[:5]:
                if isinstance(c, dict):
                    cert_names.append(f"{c.get('name', '')} ({c.get('issuer', '')})")
                elif isinstance(c, str):
                    cert_names.append(c)
            if cert_names:
                parts.append(f"Certifications: {'; '.join(cert_names)}")

        # Experience history
        experience = user.get("experience", [])
        if experience:
            exp_parts = []
            for exp in experience[:5]:
                if isinstance(exp, dict):
                    title = exp.get("title", "")
                    company = exp.get("company", "")
                    duration = exp.get("duration", "")
                    desc = exp.get("description", "")[:200]
                    exp_parts.append(f"{title} at {company} ({duration}){': ' + desc if desc else ''}")
            if exp_parts:
                parts.append(f"Work History:\n" + "\n".join(f"  - {e}" for e in exp_parts))

        # Founder profile (chatbot collected data)
        extra = user.get("extraFields", {})
        if extra:
            founder_parts = []
            founder_fields = {
                "hours_per_week": "Weekly Commitment",
                "equity_preference": "Equity/Comp Preference",
                "compensation_preference": "Compensation Preference",
                "risk_tolerance": "Risk Tolerance",
                "previous_startup_experience": "Startup Experience",
                "leadership_style": "Leadership Style",
                "technical_or_business_orientation": "Technical/Business Focus",
                "stage_preference": "Preferred Startup Stage",
                "unique_value": "Unique Value",
                "co_founder_expectations": "Co-Founder Expectations",
                "co_founder_qualities": "Co-Founder Qualities",
                "looking_for_cofounder": "Looking For in Co-Founder",
                "geographic_preferences": "Location Preference",
                "industry_preferences": "Industry Focus",
                "financial_runway": "Financial Runway",
                "domain_expertise": "Domain Expertise",
                "urgency_to_start": "Timeline",
                "decision_making_style": "Decision Style",
                "conflict_resolution_approach": "Conflict Resolution",
                "network_strength": "Network Strength",
            }
            for key, label in founder_fields.items():
                val = extra.get(key, "")
                if val and val not in [[], {}, ""]:
                    display = ", ".join(val) if isinstance(val, list) else str(val)
                    founder_parts.append(f"{label}: {display}")

            # Also include scrape-discovered insights
            insight_fields = {
                "achievementSignals": "Achievements",
                "communityInvolvement": "Community",
                "projectsMentioned": "Projects",
                "thoughtLeadershipTopics": "Thought Leadership",
                "industryFocus": "Industry Focus Areas",
            }
            for key, label in insight_fields.items():
                val = extra.get(key, "")
                if val and val not in [[], {}, ""]:
                    display = ", ".join(val) if isinstance(val, list) else str(val)
                    founder_parts.append(f"{label}: {display}")

            if founder_parts:
                parts.append(f"Founder Profile:\n" + "\n".join(f"  - {p}" for p in founder_parts))

        # Resume text
        if user.get("resume_text"):
            parts.append(f"Resume:\n{user['resume_text'][:3000]}")

        return "\n".join(filter(None, parts))

    # ------------------------------------------------------------------
    # LLM: analyze resume text
    # ------------------------------------------------------------------

    def analyze_resume_with_ai(self, resume_text: str) -> Dict:
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
            result = self.llm_service.generate_json(prompt)
            return result or {}
        except Exception as e:
            print(f"[ATSService] AI resume analysis error: {e}")
            return {}

    # ------------------------------------------------------------------
    # LLM: ATS compatibility score (considers ALL profile data)
    # ------------------------------------------------------------------

    def calculate_ats_score(self, candidate_text: str, job_description: str) -> Dict:
        """
        Comprehensive ATS scoring using the FULL candidate profile
        (skills, experience, resume, founder profile, chatbot answers, etc.)
        against a project description.
        """
        prompt = f"""
You are a senior startup advisor evaluating a candidate for a co-founder matching platform.

--- FULL CANDIDATE PROFILE ---
{candidate_text[:6000]}

--- PROJECT / JOB DESCRIPTION ---
{job_description[:3000]}

Evaluate this candidate COMPREHENSIVELY considering:
1. Technical skill match — do their skills align with the project needs?
2. Experience & seniority — is their experience level appropriate?
3. Domain & industry alignment — do they have relevant domain knowledge?
4. Founder mindset — hours commitment, risk tolerance, financial runway, urgency
5. Team fit — leadership style, work style, collaboration approach
6. Co-founder compatibility — what they bring vs what's needed
7. Certifications & education relevance
8. Achievement signals & execution capability
9. Geographic & stage preferences alignment

Be thorough and consider both explicit and inferred/implied qualifications.
A candidate who has completed their founder profile (hours, equity, risk tolerance, etc.)
should get credit for that — it shows commitment and self-awareness.

Respond ONLY with valid JSON — no markdown fences:
{{
    "overall_score": <integer 0-100>,
    "technical_fit": <integer 0-100>,
    "experience_fit": <integer 0-100>,
    "domain_fit": <integer 0-100>,
    "founder_mindset_fit": <integer 0-100>,
    "team_compatibility_fit": <integer 0-100>,
    "matched_skills": ["skill1", ...],
    "missing_skills": ["skill1", ...],
    "inferred_skills": ["skill implied but not stated", ...],
    "strengths": ["specific strength relevant to this project", ...],
    "gaps": ["specific gap or concern", ...],
    "founder_highlights": ["relevant founder trait for this project", ...],
    "overall_reasoning": "3-4 sentence explanation covering technical fit AND founder fit"
}}

Score guidance:
- 85-100: Exceptional match — strong skills + strong founder profile + domain alignment
- 70-84: Good match — solid skills, some founder traits align well
- 55-69: Moderate match — partial skill overlap or missing founder profile data
- Below 55: Weak match — significant gaps in skills or founder fit
"""
        try:
            result = self.llm_service.generate_json(prompt)
            return result or {
                "overall_score": 0,
                "technical_fit": 0,
                "experience_fit": 0,
                "domain_fit": 0,
                "founder_mindset_fit": 0,
                "team_compatibility_fit": 0,
                "matched_skills": [],
                "missing_skills": [],
                "inferred_skills": [],
                "strengths": [],
                "gaps": [],
                "founder_highlights": [],
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
        prompt = f"""
You are an expert startup co-founder matching advisor.

Candidate Full Profile:
{candidate_text[:4000]}

Target Project Description:
{job_description[:2000]}

Generate 6-8 highly specific, actionable tips to improve this candidate's match score
for this project. Consider:
- Technical skills they should highlight or acquire
- Founder profile improvements (if missing: hours commitment, equity stance, risk tolerance)
- Domain expertise they should emphasize
- Certifications or education that would strengthen their case
- How to better present their experience for this specific project
- Co-founder traits to develop or showcase

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
            result = self.llm_service.generate_json(prompt)
            return result.get("optimization_tips", []) if result else []
        except Exception as e:
            print(f"[ATSService] Optimization tips error: {e}")
            return []

    # ------------------------------------------------------------------
    # LLM: skill extraction
    # ------------------------------------------------------------------

    def extract_skills_with_ai(self, text: str) -> List[str]:
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
            result = self.llm_service.generate_json(prompt)
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
        analysis = {
            "basic_info": {
                "name": user_data.get("name", ""),
                "email": user_data.get("email", ""),
                "bio": user_data.get("bio", ""),
                "skills": user_data.get("skills", []),
                "experience_years": user_data.get("experience_years", 0),
                "headline": user_data.get("headline", ""),
                "coreDomains": user_data.get("coreDomains", []),
                "tools": user_data.get("tools", []),
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

        analysis["resume_analysis"] = {
            "text_preview": resume_text[:500] + "..." if len(resume_text) > 500 else resume_text,
            "email": self.extract_email(resume_text),
            "phone": self.extract_phone(resume_text),
        }

        ai_insights = self.analyze_resume_with_ai(resume_text)
        analysis["ai_insights"] = ai_insights

        if ai_insights:
            analysis["resume_analysis"]["estimated_experience"] = ai_insights.get(
                "experience_years", 0
            )

            extracted_skills = ai_insights.get("skills", [])
            existing_skills = user_data.get("skills", [])
            tools = user_data.get("tools", [])
            merged = list({s.strip() for s in existing_skills + extracted_skills + tools if s.strip()})
            analysis["merged_skills"] = merged

            analysis["recommendations"] = ai_insights.get("key_achievements", [])

        return analysis
