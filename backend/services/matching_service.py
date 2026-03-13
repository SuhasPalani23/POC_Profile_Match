from datetime import datetime
from pymongo import MongoClient

from config import Config
from models.user import User
from services.gemini_service import GeminiService
from services.vector_service import VectorService


client = MongoClient(Config.MONGODB_URI)
db = client[Config.DB_NAME]
feedback_collection = db["matching_feedback"]


class MatchingService:
    def __init__(self):
        self.vector_service = VectorService()
        self.gemini_service = GeminiService()
        self.default_weights = {
            "vector_similarity": 0.35,
            "skills_overlap": 0.30,
            "experience_fit": 0.20,
            "role_fit": 0.15,
        }

    def store_feedback(self, project_id: str, founder_id: str, candidate_id: str, feedback: str):
        doc = {
            "project_id": project_id,
            "founder_id": founder_id,
            "candidate_id": candidate_id,
            "feedback": feedback,
            "created_at": datetime.utcnow(),
        }
        result = feedback_collection.insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        return doc

    def _normalize_vector_score(self, value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    def _skills_overlap_score(self, required_skills: list, candidate_skills: list) -> float:
        req = {s.strip().lower() for s in required_skills if s}
        cand = {s.strip().lower() for s in candidate_skills if s}
        if not req:
            return 1.0
        return len(req.intersection(cand)) / len(req)

    def _experience_fit_score(self, project_desc: str, candidate_experience: int) -> float:
        desc = (project_desc or "").lower()
        target_years = 0
        for token in desc.replace("+", " ").split():
            if token.isdigit():
                target_years = int(token)
                break
        if target_years <= 0:
            return 0.8 if candidate_experience > 0 else 0.5
        ratio = min(1.0, max(0.0, candidate_experience / target_years))
        return ratio

    def _role_fit_score(self, required_roles: list, candidate_title: str) -> float:
        roles = [r.lower() for r in (required_roles or []) if r]
        if not roles:
            return 0.7
        title = (candidate_title or "").lower()
        return 1.0 if any(role in title for role in roles) else 0.4

    def _weighted_score(self, subscores: dict) -> float:
        return sum(self.default_weights[key] * subscores[key] for key in self.default_weights)

    def find_matches(self, project: dict, founder_id: str, top_k: int = 10) -> list:
        project_analysis = self.gemini_service.analyze_project_needs(project["description"])
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

        rankings = self.gemini_service.rank_candidates(
            project=project,
            candidates=candidates[:10],
            project_analysis=project_analysis,
        )
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
            }
            weighted = self._weighted_score(subscores)
            llm_percentage = max(0, min(100, int(ranking.get("match_percentage", round(weighted * 100)))))
            final_percentage = int(round((weighted * 100 * 0.7) + (llm_percentage * 0.3)))

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
                    "explanation": {
                        "subscores": {
                            "vector_similarity": round(subscores["vector_similarity"] * 100, 2),
                            "skills_overlap": round(subscores["skills_overlap"] * 100, 2),
                            "experience_fit": round(subscores["experience_fit"] * 100, 2),
                            "role_fit": round(subscores["role_fit"] * 100, 2),
                        },
                        "weights": self.default_weights,
                        "llm_match_percentage": llm_percentage,
                        "final_match_percentage": final_percentage,
                    },
                }
            )

        matches.sort(key=lambda m: m["match_percentage"], reverse=True)
        return matches[:5]
