import os
from typing import List, Dict, Optional
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from config import Config
import json


class VectorService:
    # Embedding dimension for OpenAI text-embedding-3-small
    DIMENSION = 1536

    def __init__(self):
        self.openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.embedding_model = "text-embedding-3-small"

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
        everything meaningful: bio, skills, title, resume content, location,
        and new LinkedIn profile fields.
        """
        parts = []

        if user.get("name"):
            parts.append(f"Name: {user['name']}")
        elif user.get("firstName"):
            parts.append(f"Name: {user.get('firstName', '')} {user.get('lastName', '')}")

        if user.get("headline"):
            parts.append(f"Headline: {user['headline']}")

        if user.get("currentCompany"):
            parts.append(f"Current Company: {user['currentCompany']}")
            
        if user.get("professional_title"):
            parts.append(f"Role: {user['professional_title']}")
            
        if user.get("bio"):
            parts.append(f"Bio: {user['bio']}")

        if user.get("about"):
            parts.append(f"About: {user['about']}")

        if user.get("aboutMe"):
            parts.append(f"About Me: {user['aboutMe']}")

        skills = user.get("skills", [])
        if skills:
            parts.append(f"Skills: {', '.join(skills)}")

        loc_parts = [str(p).strip() for p in [user.get("city"), user.get("state"), user.get("country")] if p]
        if loc_parts:
            parts.append(f"Location: {', '.join(loc_parts)}")
        elif user.get("location"):
            parts.append(f"Location: {self._stringify_metadata_value(user['location'])}")

        exp = user.get("totalYearsExperience", user.get("experience_years", 0))
        if exp:
            parts.append(f"Experience: {exp} years")
            
        education = user.get("education", [])
        if education:
            edu_str = ", ".join([f"{e.get('degree', '')} at {e.get('institution', '')}" for e in education])
            parts.append(f"Education: {edu_str}")

        if user.get("resume_text"):
            parts.append(f"Resume: {user['resume_text'][:2000]}")

        # Include dynamic fields from chatbot/post analysis for richer matching
        extra = user.get("extraFields", {})
        if extra and isinstance(extra, dict):
            extra_parts = []
            for k, v in extra.items():
                if v and v not in [[], {}, ""]:
                    val = ", ".join(v) if isinstance(v, list) else str(v)
                    extra_parts.append(f"{k.replace('_', ' ')}: {val}")
            if extra_parts:
                parts.append(f"Insights: {' | '.join(extra_parts[:15])}")

        return " | ".join(parts) if parts else user.get("name", "Unknown Profile")

    def _stringify_metadata_value(self, value):
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, (int, float, bool)):
            return value
        if isinstance(value, list):
            return [str(item).strip() for item in value if isinstance(item, (str, int, float, bool)) and str(item).strip()]
        if isinstance(value, dict):
            ordered = [value.get("city"), value.get("state"), value.get("country")]
            parts = [str(part).strip() for part in ordered if part not in [None, ""] and str(part).strip()]
            if parts:
                return ", ".join(parts)
            return json.dumps(value, ensure_ascii=False, sort_keys=True)
        return str(value).strip()

    def _normalize_metadata(self, user: Dict) -> Dict:
        location_value = self._stringify_metadata_value(
            ", ".join(
                str(part).strip()
                for part in [user.get("city"), user.get("state"), user.get("country")]
                if part not in [None, ""] and str(part).strip()
            ) or user.get("location", "")
        )
        # Flatten extraFields into readable strings for metadata
        extra = user.get("extraFields", {})
        extra_flat = {}
        if extra and isinstance(extra, dict):
            for k, v in extra.items():
                if v and v not in [[], {}, ""]:
                    extra_flat[k] = ", ".join(v) if isinstance(v, list) else str(v)[:200]

        metadata = {
            "name": self._stringify_metadata_value(user.get("name", "")),
            "email": self._stringify_metadata_value(user.get("email", "")),
            "professional_title": self._stringify_metadata_value(user.get("professional_title", "")),
            "skills": self._stringify_metadata_value(user.get("skills", [])),
            "experience_years": int(user.get("experience_years", 0) or 0),
            "location": location_value,
            "has_resume": bool(user.get("resume")),
            "core_domains": self._stringify_metadata_value(user.get("coreDomains", [])),
            "interests": self._stringify_metadata_value(user.get("interests", [])),
            "work_style": self._stringify_metadata_value(user.get("workStyle", "")),
            "career_goals": self._stringify_metadata_value(user.get("careerGoals", ""))[:200],
            "strengths": self._stringify_metadata_value(user.get("strengths", ""))[:200],
            "linkedin_url": self._stringify_metadata_value(user.get("linkedinUrl", "")),
            "open_to_work": bool(user.get("openToWork")),
            "headline": self._stringify_metadata_value(user.get("headline", ""))[:200],
        }

        # Add extraFields (chatbot answers + scrape insights) as metadata
        # Pinecone metadata limit is 40KB — keep it reasonable
        for k, v in list(extra_flat.items())[:20]:
            metadata[f"extra_{k}"] = v

        return metadata

    def _embed(self, text: str) -> List[float]:
        response = self.openai_client.embeddings.create(
            model=self.embedding_model,
            input=text,
        )
        return response.data[0].embedding

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        response = self.openai_client.embeddings.create(
            model=self.embedding_model,
            input=texts,
        )
        return [item.embedding for item in response.data]

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
            metadata = self._normalize_metadata(user)

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
                    metadata = self._normalize_metadata(user)
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
