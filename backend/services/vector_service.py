import os
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
from config import Config


class VectorService:
    # Embedding dimension for 'all-MiniLM-L6-v2'
    DIMENSION = 384

    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

        # --- Pinecone init ---
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise EnvironmentError("PINECONE_API_KEY is not set in environment variables.")

        self.pc = Pinecone(api_key=api_key)
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "talent-match")
        self._ensure_index()
        self.index = self.pc.Index(self.index_name)

    # ------------------------------------------------------------------
    # Index lifecycle
    # ------------------------------------------------------------------

    def _ensure_index(self):
        """Create the Pinecone index if it doesn't already exist."""
        existing = [idx.name for idx in self.pc.list_indexes()]
        if self.index_name not in existing:
            print(f"[VectorService] Creating Pinecone index '{self.index_name}' ...")
            self.pc.create_index(
                name=self.index_name,
                dimension=self.DIMENSION,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region=os.getenv("PINECONE_ENVIRONMENT", "us-east-1"),
                ),
            )
            print(f"[VectorService] Index '{self.index_name}' created.")
        else:
            print(f"[VectorService] Using existing Pinecone index '{self.index_name}'.")

    # ------------------------------------------------------------------
    # Embedding helpers
    # ------------------------------------------------------------------

    def _user_to_text(self, user: Dict) -> str:
        """
        Build a rich text representation of a user so the embedding captures
        everything meaningful: bio, skills, title, resume content, location.
        All uploaded content (resume text, etc.) is included here so Pinecone
        always has the latest full picture of each user.
        """
        parts = []

        if user.get("bio"):
            parts.append(f"Bio: {user['bio']}")

        skills = user.get("skills", [])
        if skills:
            parts.append(f"Skills: {', '.join(skills)}")

        if user.get("professional_title"):
            parts.append(f"Role: {user['professional_title']}")

        if user.get("location"):
            parts.append(f"Location: {user['location']}")

        exp = user.get("experience_years", 0)
        if exp:
            parts.append(f"Experience: {exp} years")

        # Include resume text if it has been parsed and stored on the user doc
        if user.get("resume_text"):
            # Truncate to avoid token limits — first 2000 chars is plenty for embedding
            parts.append(f"Resume: {user['resume_text'][:2000]}")

        return " | ".join(parts) if parts else user.get("name", "")

    def _embed(self, text: str) -> List[float]:
        return self.model.encode(text).tolist()

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts).tolist()

    # ------------------------------------------------------------------
    # Core CRUD operations
    # ------------------------------------------------------------------

    def upsert_user(self, user: Dict) -> bool:
        """
        Insert or update a single user vector in Pinecone.
        Called whenever:
          - A new user signs up
          - A user updates their profile
          - A user uploads / deletes a resume

        Because Pinecone is cloud-hosted, this change is instantly visible
        to every server and developer querying the same index.
        """
        try:
            user_id = str(user["_id"])
            text = self._user_to_text(user)
            vector = self._embed(text)

            metadata = {
                "name": user.get("name", ""),
                "email": user.get("email", ""),
                "professional_title": user.get("professional_title", ""),
                "skills": user.get("skills", []),
                "experience_years": user.get("experience_years", 0),
                "location": user.get("location", ""),
                "has_resume": bool(user.get("resume")),
            }

            self.index.upsert(vectors=[(user_id, vector, metadata)])
            print(f"[VectorService] Upserted user {user_id} ({user.get('name', '')})")
            return True
        except Exception as e:
            print(f"[VectorService] Error upserting user: {e}")
            return False

    def build_index(self, users: List[Dict]) -> bool:
        """
        Bulk upsert all users — used during initial data ingestion or a full
        reindex. Sends in batches of 100 (Pinecone's recommended batch size).
        """
        if not users:
            print("[VectorService] No users to index.")
            return False

        try:
            texts = [self._user_to_text(u) for u in users]
            vectors = self._embed_batch(texts)

            batch_size = 100
            for i in range(0, len(users), batch_size):
                batch_users = users[i : i + batch_size]
                batch_vectors = vectors[i : i + batch_size]

                upsert_data = []
                for user, vector in zip(batch_users, batch_vectors):
                    user_id = str(user["_id"])
                    metadata = {
                        "name": user.get("name", ""),
                        "email": user.get("email", ""),
                        "professional_title": user.get("professional_title", ""),
                        "skills": user.get("skills", []),
                        "experience_years": user.get("experience_years", 0),
                        "location": user.get("location", ""),
                        "has_resume": bool(user.get("resume")),
                    }
                    upsert_data.append((user_id, vector, metadata))

                self.index.upsert(vectors=upsert_data)
                print(
                    f"[VectorService] Upserted batch {i // batch_size + 1} "
                    f"({len(batch_users)} users)"
                )

            print(f"[VectorService] Total users indexed: {len(users)}")
            return True
        except Exception as e:
            print(f"[VectorService] Error building index: {e}")
            return False

    def remove_user(self, user_id: str) -> bool:
        """Delete a user vector from Pinecone (e.g. account deletion)."""
        try:
            self.index.delete(ids=[str(user_id)])
            print(f"[VectorService] Deleted user {user_id} from Pinecone.")
            return True
        except Exception as e:
            print(f"[VectorService] Error removing user: {e}")
            return False

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, query_text: str, k: int = 10, exclude_ids: Optional[List[str]] = None) -> List[Dict]:
        """
        Query Pinecone for the top-k most semantically similar users.

        Args:
            query_text: free-form description of what you're looking for
                        (project description + required skills + roles work great)
            k:          how many results to return
            exclude_ids: list of user_ids to exclude (e.g. the founder)

        Returns:
            List of dicts with keys: user_id, similarity_score, metadata
        """
        try:
            query_vector = self._embed(query_text)

            # Fetch slightly more than k so we can filter excludes client-side
            fetch_k = k + len(exclude_ids or []) + 5

            response = self.index.query(
                vector=query_vector,
                top_k=fetch_k,
                include_metadata=True,
            )

            exclude_set = set(str(uid) for uid in (exclude_ids or []))
            results = []
            for match in response.matches:
                if match.id in exclude_set:
                    continue
                results.append(
                    {
                        "user_id": match.id,
                        "similarity_score": float(match.score),
                        "metadata": match.metadata or {},
                    }
                )
                if len(results) >= k:
                    break

            return results
        except Exception as e:
            print(f"[VectorService] Error searching: {e}")
            return []

    # ------------------------------------------------------------------
    # Convenience wrappers (called from profile routes)
    # ------------------------------------------------------------------

    def update_user_vectors(self, users: List[Dict]) -> bool:
        """Re-upsert one or more users (called after profile/resume update)."""
        success = True
        for user in users:
            ok = self.upsert_user(user)
            success = success and ok
        return success

    def get_index_stats(self) -> Dict:
        """Return index statistics (useful for health checks / admin)."""
        try:
            stats = self.index.describe_index_stats()
            return {
                "total_vector_count": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_name": self.index_name,
            }
        except Exception as e:
            return {"error": str(e)}