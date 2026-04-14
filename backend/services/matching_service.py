from datetime import datetime

from db import get_collection
from models.user import User
from services.candidate_profile_builder import CandidateProfileBuilder
from services.llm_service import LLMService
from services.matching_taxonomy import dedupe_terms, keyword_weight, normalize_term
from services.project_requirement_builder import ProjectRequirementBuilder
from services.vector_service import VectorService


def feedback_collection():
    return get_collection("matching_feedback")


class MatchingService:
    def __init__(self):
        self.vector_service = VectorService()
        self.llm_service = LLMService()
        self.candidate_builder = CandidateProfileBuilder()
        self.project_builder = ProjectRequirementBuilder()
        self.default_weights = {
            "hard_match_score": 0.34,
            "rare_keyword_score": 0.18,
            "critical_match_score": 0.12,
            "domain_score": 0.12,
            "role_score": 0.08,
            "experience_score": 0.08,
            "founder_fit_score": 0.08,
            "confidence_score": 0.08,
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
        val = float(value)
        mapped = (val - 0.20) / (0.80 - 0.20)
        return max(0.0, min(1.0, mapped))

    def _weighted_overlap(self, required_terms: list, candidate_terms: list):
        required = dedupe_terms([normalize_term(term) for term in required_terms if term])
        candidate = {normalize_term(term) for term in candidate_terms if term}
        if not required:
            return 1.0, [], []

        total = 0.0
        matched = 0.0
        matched_terms = []
        missing_terms = []
        for term in required:
            weight = keyword_weight(term)
            total += weight
            if term in candidate:
                matched += weight
                matched_terms.append(term)
            else:
                missing_terms.append(term)
        return min(1.0, matched / max(1.0, total)), matched_terms, missing_terms

    def _role_score(self, required_roles: list, candidate_roles: list, candidate_title: str):
        normalized_required = {normalize_term(role) for role in required_roles if role}
        normalized_candidate = {normalize_term(role) for role in candidate_roles if role}
        title = normalize_term(candidate_title)
        if not normalized_required:
            return 0.7, [], []

        matched = []
        missing = []
        for role in normalized_required:
            if role in normalized_candidate or (role and role in title):
                matched.append(role)
            else:
                missing.append(role)
        score = len(matched) / max(1, len(normalized_required))
        return max(0.35, score), matched, missing

    def _experience_score(self, minimum_years: int, candidate_years: int) -> float:
        if minimum_years <= 0:
            return 0.85 if candidate_years > 0 else 0.6
        if candidate_years >= minimum_years:
            return 1.0
        return max(0.35, candidate_years / max(1, minimum_years))

    def _founder_fit_score(self, founder_preferences: dict, candidate_fields: dict) -> float:
        if not candidate_fields:
            return 0.35

        score = 0.0
        checks = 0

        hours = candidate_fields.get("hours_per_week")
        if hours:
            checks += 1
            try:
                score += min(1.0, int(str(hours).strip()) / 40)
            except ValueError:
                score += 0.55

        risk = str(candidate_fields.get("risk_tolerance", "")).lower()
        if risk:
            checks += 1
            score += {"high": 1.0, "moderate": 0.75, "medium": 0.75, "low": 0.45}.get(risk, 0.55)

        leadership = str(candidate_fields.get("leadership_style", "")).lower()
        if leadership:
            checks += 1
            founder_leadership = str(founder_preferences.get("leadership_style", "")).lower()
            if founder_leadership and founder_leadership in leadership:
                score += 1.0
            elif "team" in leadership or "collaborative" in leadership:
                score += 0.9
            else:
                score += 0.6

        technical_orientation = str(
            candidate_fields.get("technical_vs_business_orientation")
            or candidate_fields.get("technical_orientation")
            or ""
        ).lower()
        if technical_orientation:
            checks += 1
            founder_orientation = str(founder_preferences.get("technical_orientation", "")).lower()
            if founder_orientation and founder_orientation in technical_orientation:
                score += 1.0
            elif "technical" in technical_orientation:
                score += 0.9
            else:
                score += 0.65

        domain_expertise = candidate_fields.get("domain_expertise") or candidate_fields.get("domain_expertise_areas")
        if domain_expertise:
            checks += 1
            score += 0.85

        if checks == 0:
            return 0.35
        return min(1.0, score / checks)

    def _confidence_score(self, candidate_profile: dict, hard_match_score: float, rare_keyword_score: float) -> float:
        inputs = candidate_profile["confidence_inputs"]
        score = 0.0
        score += 0.25 if inputs["has_resume"] else 0.0
        score += 0.20 if inputs["has_normalized_profile"] else 0.0
        score += min(0.20, inputs["evidence_count"] * 0.04)
        score += min(0.20, inputs["term_count"] / 80)
        score += min(0.15, inputs["domain_count"] / 20)
        score += 0.10 if hard_match_score >= 0.7 else 0.0
        score += 0.10 if rare_keyword_score >= 0.6 else 0.0
        return min(1.0, score)

    def _ai_depth_score(self, requirements: dict, candidate_profile: dict) -> float:
        project_ai_terms = {
            term for term in requirements["critical_terms"]
            if term in {"rag", "llms", "openai", "generative ai", "nlp", "machine learning", "deep learning", "vector databases", "pinecone", "chromadb", "fastapi"}
        }
        if not project_ai_terms:
            return 0.8

        candidate_ai_terms = set(candidate_profile.get("ai_depth_terms", []))
        overlap = len(project_ai_terms & candidate_ai_terms) / max(1, len(project_ai_terms))

        title = normalize_term(candidate_profile["title"])
        looks_generic_full_stack = "full stack" in title or "software engineer" in title
        if looks_generic_full_stack and overlap < 0.45:
            return max(0.2, overlap * 0.7)
        return max(0.3, overlap)

    def _weighted_score(self, subscores: dict) -> float:
        return sum(self.default_weights.get(key, 0) * subscores.get(key, 0) for key in self.default_weights)

    def _calibrate_score_band(self, scored_matches: list) -> list:
        if not scored_matches:
            return scored_matches

        weighted_values = [item["_deterministic_match"]["weighted"] for item in scored_matches]
        max_weight = max(weighted_values)
        min_weight = min(weighted_values)
        spread = max(0.001, max_weight - min_weight)

        for index, item in enumerate(scored_matches):
            precomputed = item["_deterministic_match"]
            subscores = precomputed["subscores"]
            weighted = precomputed["weighted"]
            normalized_rank_score = (weighted - min_weight) / spread if spread > 0 else 1.0

            anchor_floor = 60
            anchor_ceiling = 98
            calibrated = anchor_floor + (normalized_rank_score * (anchor_ceiling - anchor_floor))

            critical_bonus = 0.0
            if subscores["critical_match_score"] >= 0.95:
                critical_bonus += 4.0
            elif subscores["critical_match_score"] >= 0.80:
                critical_bonus += 2.0

            if subscores["hard_match_score"] < 0.60:
                calibrated -= 8.0
            if subscores["critical_match_score"] < 0.50:
                calibrated -= 6.0
            if subscores["rare_keyword_score"] < 0.40:
                calibrated -= 4.0

            if index == 0 and subscores["hard_match_score"] >= 0.80 and subscores["critical_match_score"] >= 0.75:
                calibrated = max(calibrated, 96.0)

            item["_deterministic_match"]["final_percentage"] = max(
                60,
                min(99, int(round(calibrated + critical_bonus)))
            )

        scored_matches.sort(
            key=lambda item: (
                item["_deterministic_match"]["final_percentage"],
                item["_deterministic_match"]["weighted"],
            ),
            reverse=True,
        )
        return scored_matches

    def _build_scored_candidate(self, candidate: dict, requirements: dict) -> dict:
        candidate_profile = self.candidate_builder.build(candidate)

        hard_match_score, matched_terms, missing_terms = self._weighted_overlap(
            requirements["exact_terms"],
            candidate_profile["exact_terms"],
        )
        rare_keyword_score, matched_rare_terms, missing_rare_terms = self._weighted_overlap(
            requirements["rare_terms"],
            candidate_profile["exact_terms"],
        )
        critical_match_score, matched_critical_terms, missing_critical_terms = self._weighted_overlap(
            requirements["critical_terms"],
            candidate_profile["exact_terms"],
        )
        domain_score, matched_domains, missing_domains = self._weighted_overlap(
            requirements["domain_terms"],
            candidate_profile["domain_terms"] + candidate_profile["exact_terms"],
        )
        role_score, matched_roles, missing_roles = self._role_score(
            requirements["role_terms"],
            candidate_profile["role_terms"],
            candidate_profile["title"],
        )
        experience_score = self._experience_score(
            requirements["minimum_years"],
            candidate_profile["years_experience"],
        )
        founder_fit_score = self._founder_fit_score(
            requirements["founder_preferences"],
            candidate_profile["founder_fields"],
        )
        confidence_score = self._confidence_score(candidate_profile, hard_match_score, rare_keyword_score)
        ai_depth_score = self._ai_depth_score(requirements, candidate_profile)

        subscores = {
            "hard_match_score": hard_match_score,
            "rare_keyword_score": rare_keyword_score,
            "critical_match_score": critical_match_score,
            "domain_score": domain_score,
            "role_score": role_score,
            "experience_score": experience_score,
            "founder_fit_score": founder_fit_score,
            "confidence_score": confidence_score,
            "ai_depth_score": ai_depth_score,
            "retrieval_score": self._normalize_vector_score(candidate_profile["vector_similarity"]),
        }
        weighted = self._weighted_score(subscores)
        final_percentage = int(round(weighted * 100))

        if hard_match_score >= 0.90 and critical_match_score >= 0.85:
            final_percentage = max(final_percentage, 97)
        elif hard_match_score >= 0.80 and critical_match_score >= 0.70:
            final_percentage = max(final_percentage, 93)
        elif critical_match_score < 0.45:
            final_percentage = min(final_percentage, 74)

        if ai_depth_score < 0.35:
            final_percentage = min(final_percentage, 68)
        elif ai_depth_score < 0.50:
            final_percentage = min(final_percentage, 78)

        return {
            "candidate_profile": candidate_profile,
            "subscores": subscores,
            "weighted": weighted,
            "final_percentage": max(0, min(100, final_percentage)),
            "matched_terms": matched_terms,
            "missing_terms": missing_terms[:12],
            "matched_rare_terms": matched_rare_terms,
            "missing_rare_terms": missing_rare_terms[:10],
            "matched_critical_terms": matched_critical_terms,
            "missing_critical_terms": missing_critical_terms[:10],
            "matched_domains": matched_domains,
            "missing_domains": missing_domains[:8],
            "matched_roles": matched_roles,
            "missing_roles": missing_roles[:8],
        }

    def find_matches(self, project: dict, founder_id: str, top_k: int = 10) -> list:
        requirements = self.project_builder.build(project)
        search_query = f"{requirements['title']}\n{requirements['description']}\nRequired: {', '.join(requirements['exact_terms'])}"
        vector_results = self.vector_service.search(query_text=search_query, k=max(30, top_k * 6), exclude_ids=[founder_id])
        if not vector_results:
            return []

        scored_candidates = []
        for result in vector_results:
            candidate = User.find_by_id(result["user_id"])
            if not candidate:
                continue
            candidate["vector_similarity"] = result["similarity_score"]
            candidate["_deterministic_match"] = self._build_scored_candidate(candidate, requirements)
            scored_candidates.append(candidate)

        if not scored_candidates:
            return []

        scored_candidates.sort(
            key=lambda item: (
                item["_deterministic_match"]["weighted"],
                item["_deterministic_match"]["subscores"]["ai_depth_score"],
                item["_deterministic_match"]["subscores"]["critical_match_score"],
                item["_deterministic_match"]["subscores"]["rare_keyword_score"],
                item["_deterministic_match"]["subscores"]["hard_match_score"],
                item["_deterministic_match"]["subscores"]["confidence_score"],
            ),
            reverse=True,
        )
        candidates = scored_candidates[: max(10, top_k * 2)]
        candidates = self._calibrate_score_band(candidates)

        matches = []
        seen_user_ids = set()
        for candidate in candidates[:10]:
            user_id = candidate["_id"]
            if user_id in seen_user_ids:
                continue
            seen_user_ids.add(user_id)

            precomputed = candidate.get("_deterministic_match") or self._build_scored_candidate(candidate, requirements)
            candidate_profile = precomputed["candidate_profile"]
            subscores = precomputed["subscores"]
            final_percentage = precomputed["final_percentage"]
            reasoning, strengths, concerns = self._build_explanation(requirements, candidate_profile, precomputed)

            matches.append(
                {
                    "user_id": user_id,
                    "name": candidate_profile["name"],
                    "email": candidate_profile["email"],
                    "role": candidate_profile["role"],
                    "is_founder": candidate_profile["is_founder"],
                    "professional_title": candidate_profile["title"],
                    "skills": candidate_profile["skills_display"],
                    "bio": candidate_profile["bio"],
                    "linkedin": candidate_profile["linkedin"],
                    "resume": candidate_profile["resume"],
                    "experience_years": candidate_profile["years_experience"],
                    "match_percentage": final_percentage,
                    "reasoning": reasoning,
                    "strengths": strengths,
                    "concerns": concerns,
                    "vector_similarity": candidate_profile["vector_similarity"],
                    "founder_profile": {
                        k: v for k, v in candidate_profile["founder_fields"].items()
                        if v and v not in [[], {}, ""]
                    },
                    "explanation": {
                        "subscores": {
                            "hard_match_score": round(subscores["hard_match_score"] * 100, 2),
                            "rare_keyword_score": round(subscores["rare_keyword_score"] * 100, 2),
                            "critical_match_score": round(subscores["critical_match_score"] * 100, 2),
                            "domain_score": round(subscores["domain_score"] * 100, 2),
                            "role_score": round(subscores["role_score"] * 100, 2),
                            "experience_score": round(subscores["experience_score"] * 100, 2),
                            "founder_fit_score": round(subscores["founder_fit_score"] * 100, 2),
                            "confidence_score": round(subscores["confidence_score"] * 100, 2),
                            "ai_depth_score": round(subscores["ai_depth_score"] * 100, 2),
                            "retrieval_score": round(subscores["retrieval_score"] * 100, 2),
                        },
                        "weights": self.default_weights,
                        "final_match_percentage": final_percentage,
                        "matched_requirements": {
                            "terms": precomputed["matched_terms"],
                            "rare_terms": precomputed["matched_rare_terms"],
                            "critical_terms": precomputed["matched_critical_terms"],
                            "domains": precomputed["matched_domains"],
                            "roles": precomputed["matched_roles"],
                        },
                        "missing_requirements": {
                            "terms": precomputed["missing_terms"],
                            "rare_terms": precomputed["missing_rare_terms"],
                            "critical_terms": precomputed["missing_critical_terms"],
                            "domains": precomputed["missing_domains"],
                            "roles": precomputed["missing_roles"],
                        },
                    },
                }
            )

        matches.sort(key=lambda item: item["match_percentage"], reverse=True)
        return matches[:5]

    def _build_explanation(self, requirements: dict, candidate_profile: dict, precomputed: dict):
        prompt = f"""
You are writing a concise explanation for a deterministic co-founder matching system.

Project:
- Title: {requirements['title']}
- Core requirements: {', '.join(requirements['exact_terms'][:20])}
- Domains: {', '.join(requirements['domain_terms'][:10])}

Candidate:
- Name: {candidate_profile['name']}
- Title: {candidate_profile['title']}
- Experience: {candidate_profile['years_experience']} years
- Skills: {', '.join(candidate_profile['exact_terms'][:25])}
- Domains: {', '.join(candidate_profile['domain_terms'][:10])}

Deterministic score: {precomputed['final_percentage']}%
Matched requirements: {', '.join(precomputed['matched_terms'][:12])}
Missing requirements: {', '.join(precomputed['missing_terms'][:8])}
Matched rare terms: {', '.join(precomputed['matched_rare_terms'][:8])}

Return ONLY valid JSON:
{{
  "reasoning": "2 short sentences, grounded in the deterministic evidence, with no generic praise",
  "strengths": ["specific strength", "specific strength"],
  "concerns": ["specific concern"]
}}
"""
        result = self.llm_service.generate_json(prompt)
        if result:
            return (
                result.get("reasoning", ""),
                result.get("strengths", [])[:3],
                result.get("concerns", [])[:3],
            )

        strengths = precomputed["matched_critical_terms"][:3] or precomputed["matched_rare_terms"][:3] or precomputed["matched_terms"][:3]
        concerns = precomputed["missing_critical_terms"][:2] or precomputed["missing_rare_terms"][:2] or precomputed["missing_terms"][:2]
        reasoning = (
            f"{candidate_profile['name']} matches {len(precomputed['matched_terms'])} structured requirements for this project, "
            f"including {', '.join(strengths[:2]) if strengths else 'core stack overlap'}."
        )
        if concerns:
            reasoning += f" Main gaps are {', '.join(concerns[:2])}."
        return reasoning, strengths, concerns
