from services.vector_service import VectorService
from services.gemini_service import GeminiService
from models.user import User

class MatchingService:
    def __init__(self):
        self.vector_service = VectorService()
        self.gemini_service = GeminiService()
    
    def find_matches(self, project, founder_id, top_k=10):
        """Find and rank top matches for a project"""
        
        # Step 1: Analyze project needs with Gemini
        project_analysis = self.gemini_service.analyze_project_needs(project['description'])
        
        # Step 2: Create search query from project description and analysis
        skills_text = ", ".join(project_analysis.get('required_skills', []))
        roles_text = ", ".join(project_analysis.get('required_roles', []))
        search_query = f"{project['description']} Required: {skills_text} {roles_text}"
        
        # Step 3: Get initial candidates from FAISS
        vector_results = self.vector_service.search(search_query, k=top_k)
        
        # Step 4: Get full user details for candidates
        candidates = []
        for result in vector_results:
            user = User.find_by_id(result['user_id'])
            if user and user['_id'] != founder_id:  # Exclude the founder
                user['vector_similarity'] = result['similarity_score']
                candidates.append(user)
        
        if not candidates:
            return []
        
        # Step 5: Use Gemini to rank candidates intelligently
        rankings = self.gemini_service.rank_candidates(project, candidates[:10])
        
        # Step 6: Combine rankings with user data
        matches = []
        for ranking in rankings[:5]:  # Top 5
            candidate_idx = ranking.get('candidate_index', 0)
            if candidate_idx < len(candidates):
                candidate = candidates[candidate_idx]
                match = {
                    'user_id': candidate['_id'],
                    'name': candidate['name'],
                    'email': candidate['email'],
                    'role': candidate.get('role', 'user'),
                    'skills': candidate.get('skills', []),
                    'bio': candidate.get('bio', ''),
                    'linkedin': candidate.get('linkedin', ''),
                    'resume': candidate.get('resume', ''),
                    'match_percentage': ranking.get('match_percentage', 0),
                    'reasoning': ranking.get('reasoning', ''),
                    'strengths': ranking.get('strengths', []),
                    'concerns': ranking.get('concerns', []),
                    'vector_similarity': candidate.get('vector_similarity', 0)
                }
                matches.append(match)
        
        return matches