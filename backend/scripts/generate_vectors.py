import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.vector_service import VectorService
from models.user import User

def generate_vectors():
    """Generate FAISS index from all users"""
    
    print("Fetching all users from database...")
    users = User.get_all_users()
    
    if not users:
        print("No users found in database. Please run ingest_data.py first.")
        return
    
    print(f"Found {len(users)} users")
    print("Generating embeddings and building FAISS index...")
    
    vector_service = VectorService()
    vector_service.build_index(users)
    
    print(f"✓ FAISS index created and saved successfully!")
    print(f"  - Index file: data/faiss_index/index.faiss")
    print(f"  - User IDs file: data/faiss_index/user_ids.pkl")
    print(f"  - Total users indexed: {len(users)}")

if __name__ == "__main__":
    print("=== Vector Generation Script ===")
    generate_vectors()