#!/usr/bin/env python3
"""
Sync Pinecone with MongoDB — removes vectors for users that no longer exist in MongoDB,
and re-indexes users that exist in MongoDB but not in Pinecone.

Usage:
    python scripts/sync_pinecone.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.user import User
from services.vector_service import VectorService


def sync():
    print("=== Pinecone ↔ MongoDB Sync ===")

    vs = VectorService()
    stats = vs.get_index_stats()
    print(f"Pinecone: {stats.get('total_vector_count', 0)} vectors")

    users = User.get_all_users()
    mongo_ids = {u["_id"] for u in users}
    print(f"MongoDB: {len(mongo_ids)} users")

    # Get all vector IDs from Pinecone
    # Note: Pinecone doesn't have a "list all IDs" API for serverless.
    # We re-index all MongoDB users instead.
    print("\nRe-indexing all MongoDB users into Pinecone...")
    ok = vs.build_index(users)

    if ok:
        new_stats = vs.get_index_stats()
        print(f"\nSync complete. Pinecone now has {new_stats.get('total_vector_count', 0)} vectors.")
    else:
        print("\nSync failed.")


if __name__ == "__main__":
    sync()
