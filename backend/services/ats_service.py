import PyPDF2
import docx
import re
from typing import Dict, List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from services.gemini_service import GeminiService

class ATSService:
    """Advanced ATS for resume parsing, scoring, and matching"""
    
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.gemini_service = GeminiService()
        
        # Common tech skills database
        self.tech_skills = {
            'programming': [
                'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'Go', 
                'Rust', 'Ruby', 'PHP', 'Swift', 'Kotlin', 'Scala', 'R'
            ],
            'web': [
                'React', 'Angular', 'Vue.js', 'Node.js', 'Django', 'Flask', 
                'Spring Boot', 'Express.js', 'Next.js', 'HTML', 'CSS', 'Tailwind'
            ],
            'data': [
                'SQL', 'MongoDB', 'PostgreSQL', 'MySQL', 'Redis', 'Cassandra',
                'Elasticsearch', 'Neo4j', 'DynamoDB'
            ],
            'cloud': [
                'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Terraform',
                'CloudFormation', 'Serverless', 'Lambda'
            ],
            'ml_ai': [
                'Machine Learning', 'Deep Learning', 'TensorFlow', 'PyTorch',
                'Scikit-learn', 'Pandas', 'NumPy', 'NLP', 'Computer Vision'
            ],
            'devops': [
                'CI/CD', 'Jenkins', 'GitLab CI', 'GitHub Actions', 'Ansible',
                'Chef', 'Puppet', 'Monitoring', 'Linux'
            ],
            'security': [
                'Penetration Testing', 'Cryptography', 'SIEM', 'Firewall',
                'OAuth', 'JWT', 'SSL/TLS', 'Vulnerability Assessment'
            ]
        }
    
    def parse_resume_pdf(self, file_path: str) -> str:
        """Extract text from PDF resume"""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
            return text
        except Exception as e:
            print(f"Error parsing PDF: {e}")
            return ""
    
    def parse_resume_docx(self, file_path: str) -> str:
        """Extract text from DOCX resume"""
        try:
            doc = docx.Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            print(f"Error parsing DOCX: {e}")
            return ""
    
    def parse_resume(self, file_path: str) -> str:
        """Parse resume based on file extension"""
        if file_path.endswith('.pdf'):
            return self.parse_resume_pdf(file_path)
        elif file_path.endswith('.docx'):
            return self.parse_resume_docx(file_path)
        else:
            return ""
    
    def extract_email(self, text: str) -> Optional[str]:
        """Extract email from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return emails[0] if emails else None
    
    def extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number from text"""
        phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phones = re.findall(phone_pattern, text)
        return phones[0] if phones else None
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from resume text"""
        text_lower = text.lower()
        found_skills = []
        
        for category, skills in self.tech_skills.items():
            for skill in skills:
                if skill.lower() in text_lower:
                    found_skills.append(skill)
        
        return list(set(found_skills))
    
    def extract_experience_years(self, text: str) -> int:
        """Estimate years of experience from resume"""
        # Look for patterns like "5 years", "5+ years", "5-7 years"
        patterns = [
            r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?experience',
            r'experience[:\s]+(\d+)\+?\s*(?:years?|yrs?)',
            r'(\d+)\+?\s*(?:years?|yrs?)',
        ]
        
        years = []
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            years.extend([int(m) for m in matches])
        
        return max(years) if years else 0
    
    def analyze_resume_with_ai(self, resume_text: str) -> Dict:
        """Use Gemini AI to analyze resume in depth"""
        prompt = f"""
Analyze this resume and extract structured information.

Resume Text:
{resume_text}

Provide analysis in JSON format:
{{
    "skills": ["skill1", "skill2", ...],
    "experience_years": <number>,
    "strengths": ["strength1", "strength2", ...],
    "roles": ["role1", "role2", ...],
    "education": ["degree1", "degree2", ...],
    "certifications": ["cert1", "cert2", ...],
    "key_achievements": ["achievement1", "achievement2", ...],
    "recommended_roles": ["role1", "role2", ...],
    "summary": "brief professional summary"
}}
"""
        
        try:
            response = self.gemini_service.client.models.generate_content(
                model=self.gemini_service.model,
                contents=prompt
            )
            
            result = self.gemini_service._extract_json(response.text)
            return result if result else {}
        except Exception as e:
            print(f"Error in AI resume analysis: {e}")
            return {}
    
    def calculate_ats_score(self, resume_text: str, job_description: str) -> Dict:
        """Calculate ATS compatibility score"""
        # Create embeddings
        resume_embedding = self.model.encode(resume_text)
        job_embedding = self.model.encode(job_description)
        
        # Calculate cosine similarity
        similarity = np.dot(resume_embedding, job_embedding) / (
            np.linalg.norm(resume_embedding) * np.linalg.norm(job_embedding)
        )
        
        # Convert to percentage
        base_score = float(similarity * 100)
        
        # Extract skills from both
        resume_skills = set([s.lower() for s in self.extract_skills(resume_text)])
        job_skills = set([s.lower() for s in self.extract_skills(job_description)])
        
        # Calculate skill match
        if job_skills:
            skill_match = len(resume_skills & job_skills) / len(job_skills)
        else:
            skill_match = 0
        
        # Combined score with weights
        final_score = (base_score * 0.7) + (skill_match * 100 * 0.3)
        
        return {
            'overall_score': round(final_score, 2),
            'semantic_similarity': round(base_score, 2),
            'skill_match_score': round(skill_match * 100, 2),
            'matched_skills': list(resume_skills & job_skills),
            'missing_skills': list(job_skills - resume_skills),
            'additional_skills': list(resume_skills - job_skills)
        }
    
    def generate_profile_optimization_tips(self, resume_text: str, 
                                          job_description: str) -> List[str]:
        """Generate tips to optimize profile for better ATS score"""
        prompt = f"""
You are an expert career advisor and ATS optimization specialist.

Candidate's Resume:
{resume_text}

Target Job Description:
{job_description}

Provide 5-7 actionable tips to optimize the candidate's profile for this job.
Focus on:
1. Skills to highlight or add
2. Keywords to include
3. Experience to emphasize
4. Certifications that would help
5. Profile improvements

Respond in JSON format:
{{
    "optimization_tips": [
        "tip1",
        "tip2",
        ...
    ]
}}
"""
        
        try:
            response = self.gemini_service.client.models.generate_content(
                model=self.gemini_service.model,
                contents=prompt
            )
            
            result = self.gemini_service._extract_json(response.text)
            return result.get('optimization_tips', []) if result else []
        except Exception as e:
            print(f"Error generating optimization tips: {e}")
            return []
    
    def comprehensive_profile_analysis(self, user_data: Dict, 
                                      resume_path: Optional[str] = None) -> Dict:
        """Comprehensive analysis combining user data and resume"""
        analysis = {
            'basic_info': {
                'name': user_data.get('name', ''),
                'email': user_data.get('email', ''),
                'bio': user_data.get('bio', ''),
                'skills': user_data.get('skills', []),
                'experience_years': user_data.get('experience_years', 0)
            },
            'resume_analysis': {},
            'ai_insights': {},
            'recommendations': []
        }
        
        # Parse resume if provided
        if resume_path:
            resume_text = self.parse_resume(resume_path)
            if resume_text:
                # Basic extraction
                extracted_email = self.extract_email(resume_text)
                extracted_phone = self.extract_phone(resume_text)
                extracted_skills = self.extract_skills(resume_text)
                extracted_experience = self.extract_experience_years(resume_text)
                
                analysis['resume_analysis'] = {
                    'text': resume_text[:500] + '...',  # Preview
                    'email': extracted_email,
                    'phone': extracted_phone,
                    'extracted_skills': extracted_skills,
                    'estimated_experience': extracted_experience
                }
                
                # AI-powered analysis
                ai_analysis = self.analyze_resume_with_ai(resume_text)
                analysis['ai_insights'] = ai_analysis
                
                # Merge skills
                all_skills = list(set(user_data.get('skills', []) + extracted_skills))
                analysis['merged_skills'] = all_skills
        
        return analysis