"""
One-off script: trigger About Me enrichment for a user whose chatbot
interview finished but enrichment never ran (due to the conversation_complete
bug that has since been fixed).

Usage:
    python trigger_enrichment.py <user_email>

Example:
    python trigger_enrichment.py sumukha@example.com
"""
import sys
import os

# Ensure the backend package is on the path
sys.path.insert(0, os.path.dirname(__file__))

# Increase MongoDB timeout before importing db (Atlas needs more than 2s)
from config import Config
from pymongo import MongoClient

_client = MongoClient(
    Config.MONGODB_URI,
    serverSelectionTimeoutMS=30000,
    connectTimeoutMS=10000,
    socketTimeoutMS=10000,
)

import db as _db_mod
_db_mod._client = _client
_db_mod._db = _client[Config.DB_NAME]

from db import get_collection
from models.user import User
from services.openai_service import enrich_profile_from_chat


def main():
    if len(sys.argv) < 2:
        print("Usage: python trigger_enrichment.py <user_email>")
        sys.exit(1)

    email = sys.argv[1]
    users = get_collection("users")
    user = users.find_one({"email": email})
    if not user:
        print(f"No user found with email: {email}")
        sys.exit(1)

    user["_id"] = str(user["_id"])
    print(f"Found user: {user.get('firstName', '')} {user.get('lastName', '')} ({email})")
    print(f"  Confidence: {user.get('profileConfidenceScore', 'N/A')}%")
    print(f"  Current About Me: {(user.get('about') or user.get('aboutMe') or '(empty)')[:80]}")

    # Build the same inputs the route would pass to enrich_profile_from_chat
    profile_data = {k: v for k, v in user.items() if k != "password"}
    extra_fields = user.get("extraFields", {}) or {}
    discovered_fields = user.get("postInsights", {}) or {}
    resume_text = user.get("resume_text") or ""

    # Surface raw LinkedIn about if available
    raw_about = user.get("linkedin_about_raw")
    if raw_about:
        profile_data["linkedin_about_raw"] = raw_about

    print("\nRunning enrichment...")
    enriched = enrich_profile_from_chat(
        profile_data=profile_data,
        extra_fields=extra_fields,
        discovered_fields=discovered_fields,
        resume_text=resume_text,
    )

    if not enriched:
        print("Enrichment returned nothing. Check OpenAI API key / logs.")
        sys.exit(1)

    print(f"\nEnriched fields: {list(enriched.keys())}")
    if enriched.get("aboutMe"):
        print(f"\nGenerated About Me:\n  {enriched['aboutMe'][:300]}")

    # Persist to MongoDB
    User.update_profile(user["_id"], enriched)
    print("\nSaved to MongoDB. Refresh the browser to see the updated About Me.")


if __name__ == "__main__":
    main()
