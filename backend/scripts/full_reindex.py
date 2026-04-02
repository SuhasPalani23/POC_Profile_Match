#!/usr/bin/env python3
"""
Full reindex: Delete and recreate the Pinecone index, then index all MongoDB users.

Usage:
    python scripts/full_reindex.py
    python scripts/full_reindex.py --skip-recreate   # Just re-index without deleting
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from models.user import User
from services.vector_service import VectorService
from pinecone import Pinecone, ServerlessSpec


def recreate_index():
    api_key = Config.PINECONE_API_KEY
    index_name = Config.PINECONE_INDEX_NAME or "talent-match"
    region = Config.PINECONE_ENVIRONMENT or "us-east-1"

    pc = Pinecone(api_key=api_key)
    existing = [idx.name for idx in pc.list_indexes()]

    if index_name in existing:
        print(f"  Deleting index '{index_name}'...")
        pc.delete_index(index_name)
        time.sleep(5)

    print(f"  Creating index '{index_name}' (dim=1536, cosine)...")
    pc.create_index(
        name=index_name,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region=region),
    )
    print(f"  Index ready.")


def reindex_users():
    users = User.get_all_users()
    if not users:
        print("  No users in MongoDB.")
        return

    print(f"  Found {len(users)} users. Generating embeddings...")
    vs = VectorService()
    ok = vs.build_index(users)

    if ok:
        stats = vs.get_index_stats()
        print(f"  Indexed: {stats.get('total_vector_count')} vectors")
    else:
        print("  Indexing failed.")


def main():
    skip_recreate = "--skip-recreate" in sys.argv

    print("=== Full Pinecone Reindex ===\n")

    if not skip_recreate:
        print("[1/2] Recreating index...")
        recreate_index()
    else:
        print("[1/2] Skipping index recreation (--skip-recreate)")

    print("\n[2/2] Indexing all users from MongoDB...")
    reindex_users()

    print("\nDone.")


if __name__ == "__main__":
    main()
