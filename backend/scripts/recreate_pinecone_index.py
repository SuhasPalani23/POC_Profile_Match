#!/usr/bin/env python3
"""
Recreate the Pinecone index with the correct dimension for OpenAI text-embedding-3-small (1536).
This deletes the existing index and creates a new one.

Usage:
    python scripts/recreate_pinecone_index.py
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from pinecone import Pinecone, ServerlessSpec

def main():
    api_key = Config.PINECONE_API_KEY
    index_name = Config.PINECONE_INDEX_NAME or "talent-match"
    region = Config.PINECONE_ENVIRONMENT or "us-east-1"

    if not api_key:
        print("ERROR: PINECONE_API_KEY not set")
        sys.exit(1)

    pc = Pinecone(api_key=api_key)
    existing = [idx.name for idx in pc.list_indexes()]

    if index_name in existing:
        print(f"Deleting existing index '{index_name}'...")
        pc.delete_index(index_name)
        print("Waiting for deletion...")
        time.sleep(5)

    print(f"Creating index '{index_name}' with dimension=1536 (text-embedding-3-small)...")
    pc.create_index(
        name=index_name,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region=region),
    )
    print(f"Index '{index_name}' created successfully.")
    print("Run 'python scripts/generate_vectors.py' to re-index existing users.")


if __name__ == "__main__":
    main()
