import faiss
import numpy as np
import pickle
import os
from sentence_transformers import SentenceTransformer
from config import Config

class VectorService:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = None
        self.user_ids = []
        self.index_path = Config.FAISS_INDEX_PATH
        
    def create_embedding(self, text):
        """Create embedding for a single text"""
        return self.model.encode([text])[0]
    
    def create_embeddings_batch(self, texts):
        """Create embeddings for multiple texts"""
        return self.model.encode(texts)
    
    def build_index(self, users):
        """Build FAISS index from user profiles"""
        texts = []
        self.user_ids = []
        
        for user in users:
            # Combine bio and skills for richer embedding
            skills_text = ", ".join(user.get('skills', []))
            bio = user.get('bio', '')
            professional_title = user.get('professional_title', '')
            location = user.get('location', '')
            
            combined_text = f"{bio} Skills: {skills_text} Role: {professional_title} Location: {location}"
            texts.append(combined_text)
            self.user_ids.append(user['_id'])
        
        embeddings = self.create_embeddings_batch(texts)
        
        # Create FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(np.array(embeddings).astype('float32'))
        
        # Save index
        self.save_index()
        
    def save_index(self):
        """Save FAISS index and user IDs to disk"""
        os.makedirs(self.index_path, exist_ok=True)
        
        faiss.write_index(self.index, os.path.join(self.index_path, 'index.faiss'))
        
        with open(os.path.join(self.index_path, 'user_ids.pkl'), 'wb') as f:
            pickle.dump(self.user_ids, f)
    
    def load_index(self):
        """Load FAISS index and user IDs from disk"""
        index_file = os.path.join(self.index_path, 'index.faiss')
        ids_file = os.path.join(self.index_path, 'user_ids.pkl')
        
        if not os.path.exists(index_file) or not os.path.exists(ids_file):
            return False
        
        self.index = faiss.read_index(index_file)
        
        with open(ids_file, 'rb') as f:
            self.user_ids = pickle.load(f)
        
        return True
    
    def search(self, query_text, k=5):
        """Search for similar users based on query text"""
        if self.index is None:
            if not self.load_index():
                return []
        
        query_embedding = self.create_embedding(query_text)
        query_embedding = np.array([query_embedding]).astype('float32')
        
        distances, indices = self.index.search(query_embedding, k)
        
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.user_ids):
                results.append({
                    'user_id': self.user_ids[idx],
                    'distance': float(distance),
                    'similarity_score': float(1 / (1 + distance))  # Convert distance to similarity
                })
        
        return results
    
    def update_user_vectors(self, users):
        """Update vectors for specific users by rebuilding index"""
        # This is a simple implementation - rebuild entire index
        # For production, consider incremental updates
        from models.user import User
        
        all_users = User.get_all_users()
        self.build_index(all_users)
    
    def add_user_to_index(self, user):
        """Add a single user to the existing index"""
        if self.index is None:
            self.load_index()
        
        # Create embedding for new user
        skills_text = ", ".join(user.get('skills', []))
        bio = user.get('bio', '')
        professional_title = user.get('professional_title', '')
        location = user.get('location', '')
        
        combined_text = f"{bio} Skills: {skills_text} Role: {professional_title} Location: {location}"
        
        embedding = self.create_embedding(combined_text)
        embedding = np.array([embedding]).astype('float32')
        
        # Add to index
        self.index.add(embedding)
        self.user_ids.append(user['_id'])
        
        # Save updated index
        self.save_index()
    
    def remove_user_from_index(self, user_id):
        """Remove a user from the index - requires rebuild"""
        if user_id in self.user_ids:
            from models.user import User
            all_users = User.get_all_users()
            all_users = [u for u in all_users if u['_id'] != user_id]
            self.build_index(all_users)