import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.vector_service import VectorService
from models.user import User


def generate_vectors():
    print("=== Pinecone Vector Generation ===")
    print("Fetching all users from MongoDB...")

    users = User.get_all_users()
    if not users:
        print("No users found. Run ingest_data.py first.")
        return

    print(f"Found {len(users)} users. Building Pinecone index...")

    vs = VectorService()
    ok = vs.build_index(users)

    if ok:
        stats = vs.get_index_stats()
        print(f"\n✓ Pinecone index updated successfully!")
        print(f"  Index name : {stats.get('index_name')}")
        print(f"  Total vectors: {stats.get('total_vector_count')}")
        print(f"  Dimension  : {stats.get('dimension')}")
        print("\nAll developers querying this index will now see the updated data.")
    else:
        print("✗ Indexing failed. Check logs above.")


if __name__ == "__main__":
    generate_vectors()