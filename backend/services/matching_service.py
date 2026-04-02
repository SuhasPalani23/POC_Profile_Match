from datetime import datetime

from db import get_collection
from models.user import User
from services.llama_service import LlamaService
from services.vector_service import VectorService


def feedback_collection():
    return get_collection("matching_feedback")


class MatchingService:
    def __init__(self):
        self.vector_service = VectorService()
        self.llama_service = LlamaService()
        self.default_weights = {
            "vector_similarity": 0.25,
            "skills_overlap": 0.20,
            "experience_fit": 0.10,
            "role_fit": 0.10,
            "founder_fit": 0.35,
        }

    def store_feedback(self, project_id: str, founder_id: str, candidate_id: str, feedback: str):
        doc = {
            "project_id": project_id,
            "founder_id": founder_id,
            "candidate_id": candidate_id,
            "feedback": feedback,
            "created_at": datetime.utcnow(),
        }
        result = feedback_collection().insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        return doc

    def _normalize_vector_score(self, value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    def _skills_overlap_score(self, required_skills: list, candidate_skills: list) -> float:
        """Fuzzy skill matching — partial and substring matches count."""
        req = [s.strip().lower() for s in required_skills if s]
        cand = [s.strip().lower() for s in candidate_skills if s]
        if not req:
            return 1.0

        matched = 0
        for r in req:
            # Exact match
            if r in cand:
                matched += 1
                continue
            # Substring match: "react" matches "react.js", "python" matches "python (programming language)"
            if any(r in c or c in r for c in cand):
                matched += 0.8
                continue
            # Token overlap: "machine learning" partially matches "ml" or "deep learning"
            r_tokens = set(r.split())
            for c in cand:
                c_tokens = set(c.split())
                overlap = r_tokens & c_tokens
                if overlap and len(overlap) >= len(r_tokens) * 0.5:
                    matched += 0.6
                    break

        return min(1.0, matched / len(req))

    def _experience_fit_score(self, project_desc: str, candidate_experience: int) -> float:
        desc = (project_desc or "").lower()
        target_years = 0
        for token in desc.replace("+", " ").split():
            if token.isdigit():
                target_years = int(token)
                break
        if target_years <= 0:
            return 0.85 if candidate_experience > 0 else 0.6
        if candidate_experience >= target_years:
            return 1.0
        return max(0.4, candidate_experience / target_years)

    def _role_fit_score(self, required_roles: list, candidate_title: str) -> float:
        roles = [r.lower() for r in (required_roles or []) if r]
        if not roles:
            return 0.7
        title = (candidate_title or "").lower()
        # Exact role match
        if any(role in title for role in roles):
            return 1.0
        # Fuzzy: check if any token from required roles appears in title
        for role in roles:
            role_tokens = set(role.split())
            title_tokens = set(title.split())
            if role_tokens & title_tokens:
                return 0.75
        return 0.4

    def _founder_fit_score(self, candidate: dict) -> float:
        """Score based on founder-profile completeness and quality from chatbot data."""
        extra = candidate.get("extraFields", {})
        chatbot_keys = candidate.get("chatbotFieldKeys", [])
        if not extra and not chatbot_keys:
            return 0.3  # No founder profiling done

        score = 0.0
        total_checks = 0

        # Hours commitment (higher = better for startups)
        hours = extra.get("hours_per_week", "")
        if hours:
            total_checks += 1
            try:
                h = int(str(hours).strip())
                score += min(1.0, h / 40)
            except ValueError:
                score += 0.5

        # Risk tolerance
        risk = str(extra.get("risk_tolerance", "")).lower()
        if risk:
            total_checks += 1
            risk_scores = {"high": 1.0, "moderate": 0.7, "medium": 0.7, "low": 0.4}
            score += risk_scores.get(risk, 0.5)

        # Previous startup experience
        startup_exp = str(extra.get("previous_startup_experience", "")).lower()
        if startup_exp:
            total_checks += 1
            score += 0.9 if startup_exp not in ["no", "none", ""] else 0.5

        # Urgency/timeline
        urgency = str(extra.get("urgency_to_start", extra.get("timeline_to_start", ""))).lower()
        if urgency:
            total_checks += 1
            if "immediate" in urgency or "now" in urgency or "asap" in urgency:
                score += 1.0
            elif "month" in urgency and any(c.isdigit() for c in urgency):
                score += 0.7
            else:
                score += 0.5

        # Financial runway
        runway = str(extra.get("financial_runway", "")).lower()
        if runway:
            total_checks += 1
            try:
                months = int(''.join(c for c in runway if c.isdigit()) or '0')
                score += min(1.0, months / 6)
            except ValueError:
                score += 0.4

        # Leadership & collaboration style
        leadership = str(extra.get("leadership_style", "")).lower()
        if leadership:
            total_checks += 1
            if "collaborative" in leadership or "team" in leadership or "hands" in leadership:
                score += 0.9
            else:
                score += 0.6

        # Domain expertise
        domain = extra.get("domain_expertise", "") or extra.get("domain_expertise_areas", "")
        if domain:
            total_checks += 1
            score += 0.8

        # Profile completeness bonus
        chatbot_count = len(chatbot_keys)
        if chatbot_count >= 10:
            total_checks += 1
            score += 1.0
        elif chatbot_count >= 5:
            total_checks += 1
            score += 0.7

        if total_checks == 0:
            return 0.3
        return min(1.0, score / total_checks)

    def _weighted_score(self, subscores: dict) -> float:
        return sum(self.default_weights.get(key, 0) * subscores.get(key, 0) for key in self.default_weights)

    def _build_candidate_block(self, idx: int, candidate: dict) -> str:
        """Build a rich candidate description for the LLM including founder profile data."""
        extra = candidate.get("extraFields", {})

        # Core info
        block = f"""
Candidate {idx}:
- Name: {candidate.get('name', '')}
- Professional Title: {candidate.get('professional_title', '')}
- Skills: {', '.join(candidate.get('skills', [])[:25])}
- Experience: {candidate.get('experience_years', 0)} years
- Bio: {candidate.get('bio', '')[:400]}
- Core Domains: {', '.join(candidate.get('coreDomains', [])[:6])}
- Interests: {', '.join(candidate.get('interests', [])[:6])}
- Career Goals: {candidate.get('careerGoals', '')[:200]}
- Strengths: {candidate.get('strengths', '')}
- Work Style: {candidate.get('workStyle', '')}"""

        # Founder profile from chatbot
        founder_fields = {
            "hours_per_week": "Weekly Commitment",
            "equity_preference": "Equity/Compensation Preference",
            "risk_tolerance": "Risk Tolerance",
            "previous_startup_experience": "Startup Experience",
            "leadership_style": "Leadership Style",
            "stage_preference": "Preferred Stage",
            "unique_value": "Unique Value Proposition",
            "co_founder_expectations": "Co-Founder Expectations",
            "geographic_preferences": "Location Preference",
            "industry_preferences": "Industry Preference",
            "financial_runway": "Financial Runway",
            "domain_expertise": "Domain Expertise",
            "urgency_to_start": "Timeline to Start",
            "technical_or_business_orientation": "Technical/Business Orientation",
            "decision_making_style": "Decision Style",
            "conflict_resolution_approach": "Conflict Resolution",
            "network_strength": "Network Strength",
        }
        founder_parts = []
        for key, label in founder_fields.items():
            val = extra.get(key, "")
            if val and val not in [[], {}, ""]:
                display = ", ".join(val) if isinstance(val, list) else str(val)
                founder_parts.append(f"{label}: {display}")

        if founder_parts:
            block += f"\n- Founder Profile: {' | '.join(founder_parts)}"

        # Resume snippet
        if candidate.get("resume_text"):
            block += f"\n- Resume: {candidate['resume_text'][:1000]}"

        return block

    def find_matches(self, project: dict, founder_id: str, top_k: int = 10) -> list:
        project_analysis = self.llama_service.analyze_project_needs(project["description"])
        required_skills = project_analysis.get("required_skills", []) or project.get("required_skills", [])
        required_roles = project_analysis.get("required_roles", [])

        skills_text = ", ".join(required_skills)
        roles_text = ", ".join(required_roles)
        search_query = f"{project['description']} Required skills: {skills_text}. Roles: {roles_text}"

        vector_results = self.vector_service.search(query_text=search_query, k=top_k, exclude_ids=[founder_id])
        if not vector_results:
            return []

        candidates = []
        for result in vector_results:
            user = User.find_by_id(result["user_id"])
            if user:
                user["vector_similarity"] = result["similarity_score"]
                candidates.append(user)
        if not candidates:
            return []

        # Build rich candidate blocks for LLM
        candidate_blocks = ""
        for i, candidate in enumerate(candidates[:10]):
            candidate_blocks += self._build_candidate_block(i, candidate)

        # Get founder's own profile for compatibility matching
        founder = User.find_by_id(founder_id)
        founder_context = ""
        if founder:
            founder_extra = founder.get("extraFields", {})
            founder_parts = []
            for key in ["leadership_style", "stage_preference", "industry_preferences", "equity_preference", "risk_tolerance"]:
                val = founder_extra.get(key, "")
                if val:
                    founder_parts.append(f"{key.replace('_', ' ').title()}: {val}")
            if founder_parts:
                founder_context = f"\nFounder's Preferences: {' | '.join(founder_parts)}"

        rankings = self._rank_with_llm(project, candidate_blocks, project_analysis, founder_context)
        rank_map = {
            ranking.get("candidate_index"): ranking
            for ranking in rankings
            if isinstance(ranking.get("candidate_index"), int)
        }

        matches = []
        seen_user_ids = set()
        for idx, candidate in enumerate(candidates[:10]):
            user_id = candidate["_id"]
            if user_id in seen_user_ids:
                continue
            seen_user_ids.add(user_id)

            ranking = rank_map.get(idx, {})
            subscores = {
                "vector_similarity": self._normalize_vector_score(candidate.get("vector_similarity", 0)),
                "skills_overlap": self._skills_overlap_score(required_skills, candidate.get("skills", [])),
                "experience_fit": self._experience_fit_score(project.get("description", ""), candidate.get("experience_years", 0) or 0),
                "role_fit": self._role_fit_score(required_roles, candidate.get("professional_title", "")),
                "founder_fit": self._founder_fit_score(candidate),
            }
            weighted = self._weighted_score(subscores)

            # LLM gets 50% weight, deterministic gets 50%
            llm_percentage = max(0, min(100, int(ranking.get("match_percentage", round(weighted * 100)))))
            final_percentage = int(round((weighted * 100 * 0.5) + (llm_percentage * 0.5)))

            matches.append(
                {
                    "user_id": user_id,
                    "name": candidate.get("name", ""),
                    "email": candidate.get("email", ""),
                    "role": candidate.get("role", "user"),
                    "is_founder": candidate.get("role", "user") == "founder",
                    "professional_title": candidate.get("professional_title", ""),
                    "skills": candidate.get("skills", []),
                    "bio": candidate.get("bio", ""),
                    "linkedin": candidate.get("linkedin", ""),
                    "resume": candidate.get("resume", ""),
                    "experience_years": candidate.get("experience_years", 0),
                    "match_percentage": final_percentage,
                    "reasoning": ranking.get("reasoning", ""),
                    "strengths": ranking.get("strengths", []),
                    "concerns": ranking.get("concerns", []),
                    "vector_similarity": candidate.get("vector_similarity", 0),
                    "founder_profile": {
                        k: v for k, v in candidate.get("extraFields", {}).items()
                        if v and v not in [[], {}, ""]
                    },
                    "explanation": {
                        "subscores": {
                            "vector_similarity": round(subscores["vector_similarity"] * 100, 2),
                            "skills_overlap": round(subscores["skills_overlap"] * 100, 2),
                            "experience_fit": round(subscores["experience_fit"] * 100, 2),
                            "role_fit": round(subscores["role_fit"] * 100, 2),
                            "founder_fit": round(subscores["founder_fit"] * 100, 2),
                        },
                        "weights": self.default_weights,
                        "llm_match_percentage": llm_percentage,
                        "final_match_percentage": final_percentage,
                    },
                }
            )

        matches.sort(key=lambda m: m["match_percentage"], reverse=True)
        return matches[:5]

    def _rank_with_llm(self, project, candidate_blocks, project_analysis, founder_context=""):
        requirements_context = ""
        if project_analysis:
            req_skills = project_analysis.get("required_skills", [])
            req_roles = project_analysis.get("required_roles", [])
            key_competencies = project_analysis.get("key_competencies", [])
            founding_qualities = project_analysis.get("founding_qualities", [])
            requirements_context = f"""
Pre-analyzed Project Requirements:
- Required Skills: {', '.join(req_skills) if req_skills else 'Derive from description'}
- Required Roles: {', '.join(req_roles) if req_roles else 'Derive from description'}
- Key Competencies: {', '.join(key_competencies) if key_competencies else 'Derive from description'}
- Founding Qualities Needed: {', '.join(founding_qualities) if founding_qualities else 'Derive from description'}
"""

        prompt = f"""
You are a senior startup advisor scoring candidates for a co-founder matching platform.

Your task: score each candidate's overall fit for this project as a potential co-founder or key team member.

Project Title: {project.get('title', '')}
Project Description:
{project.get('description', '')[:3000]}
{requirements_context}
{founder_context}

Score each candidate holistically on these criteria:
1. Technical skill match (25%) — do their skills align with what the project needs?
2. Domain & industry alignment (20%) — do they have relevant domain expertise?
3. Founder mindset & commitment (30%) — hours/week, risk tolerance, financial runway, urgency, leadership style
4. Team compatibility (15%) — work style, collaboration preference, conflict resolution
5. Experience & execution signals (10%) — past experience, achievements, projects

IMPORTANT:
- Candidates who completed a founder profile (hours_per_week, equity preference, etc.) should score higher on founder mindset
- A candidate with 40 hrs/week, high risk tolerance, immediate start, and relevant domain expertise is a strong co-founder
- Consider compatibility with the founder's preferences if provided
- Be generous but fair — most candidates on a co-founder platform are already self-selected

Candidates:
{candidate_blocks}

Respond ONLY in valid JSON:
{{
    "rankings": [
        {{
            "candidate_index": 0,
            "match_percentage": 85,
            "reasoning": "2-3 sentence explanation focusing on co-founder fit",
            "strengths": ["specific strength 1", "specific strength 2"],
            "concerns": ["specific gap or concern"]
        }}
    ]
}}

Sort rankings by match_percentage descending. Include every candidate exactly once.
Score range guidance: 80-100 = excellent co-founder fit, 60-79 = good potential, 40-59 = moderate fit, below 40 = weak fit.
"""
        result = self.llama_service.generate_json(prompt)
        if result and "rankings" in result:
            return sorted(result["rankings"], key=lambda x: x.get("match_percentage", 0), reverse=True)
        return []
