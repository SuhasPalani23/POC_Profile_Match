"""
matching_service.py — uses Pinecone VectorService instead of FAISS
"""
from services.vector_service import VectorService
from services.gemini_service import GeminiService
from models.user import User


class MatchingService:
    def __init__(self):
        self.vector_service = VectorService()
        self.gemini_service = GeminiService()

    def find_matches(self, project: dict, founder_id: str, top_k: int = 10) -> list:
        """Find and rank top matches for a project using Pinecone + Gemini."""

        # Step 1: Gemini analyses the project to surface required skills/roles
        project_analysis = self.gemini_service.analyze_project_needs(project["description"])

        skills_text = ", ".join(project_analysis.get("required_skills", []))
        roles_text = ", ".join(project_analysis.get("required_roles", []))
        search_query = f"{project['description']} Required skills: {skills_text}. Roles: {roles_text}"

        # Step 2: Pinecone semantic search — exclude the founder
        vector_results = self.vector_service.search(
            query_text=search_query,
            k=top_k,
            exclude_ids=[founder_id],
        )

        if not vector_results:
            return []

        # Step 3: Hydrate full user documents from MongoDB
        candidates = []
        for result in vector_results:
            user = User.find_by_id(result["user_id"])
            if user:
                user["vector_similarity"] = result["similarity_score"]
                candidates.append(user)

        if not candidates:
            return []

        # Step 4: Gemini re-ranks the shortlist for quality
        rankings = self.gemini_service.rank_candidates(project, candidates[:10])

        # Step 5: Combine ranking metadata with user data
        matches = []
        for ranking in rankings[:5]:  # Top 5 final matches
            idx = ranking.get("candidate_index", 0)
            if idx < len(candidates):
                candidate = candidates[idx]
                matches.append(
                    {
                        "user_id": candidate["_id"],
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
                        "match_percentage": ranking.get("match_percentage", 0),
                        "reasoning": ranking.get("reasoning", ""),
                        "strengths": ranking.get("strengths", []),
                        "concerns": ranking.get("concerns", []),
                        "vector_similarity": candidate.get("vector_similarity", 0),
                    }
                )

        return matches