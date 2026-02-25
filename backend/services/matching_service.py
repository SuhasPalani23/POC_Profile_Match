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
        """Find and rank top matches for a project using Pinecone + Gemini ATS scoring."""

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
        # Include resume_text and experience_years so Gemini ATS scoring is accurate
        candidates = []
        for result in vector_results:
            user = User.find_by_id(result["user_id"])
            if user:
                user["vector_similarity"] = result["similarity_score"]
                candidates.append(user)

        if not candidates:
            return []

        # Build a lookup map: candidate_index (as sent to Gemini) -> candidate dict.
        # This is keyed by the positional index we pass in the prompt so that even if
        # Gemini returns indices out of order, skips some, or repeats one, we never
        # silently fall back to candidate 0.
        candidate_map = {i: candidate for i, candidate in enumerate(candidates[:10])}

        # Step 4: Gemini ATS-style re-ranking
        # Pass project_analysis so Gemini uses the pre-extracted required skills/roles
        # rather than re-deriving them, keeping scoring consistent with the search query
        rankings = self.gemini_service.rank_candidates(
            project=project,
            candidates=candidates[:10],
            project_analysis=project_analysis,
        )

        # Step 5: Combine ranking metadata with user data.
        # Use the candidate_map for safe lookups — skip any ranking whose index is
        # out of range rather than silently returning the wrong candidate.
        matches = []
        seen_user_ids = set()  # Guard against duplicate entries if Gemini repeats an index

        for ranking in rankings:
            idx = ranking.get("candidate_index")

            # Validate index: must be an integer and present in our map
            if not isinstance(idx, int) or idx not in candidate_map:
                print(
                    f"[MatchingService] Skipping ranking with invalid candidate_index: {idx!r} "
                    f"(valid range: 0–{len(candidate_map) - 1})"
                )
                continue

            candidate = candidate_map[idx]
            user_id = candidate["_id"]

            # Skip duplicates
            if user_id in seen_user_ids:
                print(f"[MatchingService] Skipping duplicate candidate_index {idx} (user_id: {user_id})")
                continue

            seen_user_ids.add(user_id)

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
                    "match_percentage": ranking.get("match_percentage", 0),
                    "reasoning": ranking.get("reasoning", ""),
                    "strengths": ranking.get("strengths", []),
                    "concerns": ranking.get("concerns", []),
                    "vector_similarity": candidate.get("vector_similarity", 0),
                }
            )

            if len(matches) >= 5:  # Top 5 final matches
                break

        return matches