from flask import Blueprint, request, jsonify
from models.user import User
from routes.auth import token_required
from services.ats_service import ATSService
from services.vector_service import VectorService
from services.websocket_service import ws_service
from werkzeug.utils import secure_filename
import os
from config import Config
import threading

profile_bp = Blueprint('profile', __name__)
ats_service = ATSService()
vector_service = VectorService()

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}
UPLOAD_FOLDER = 'data/resumes'

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def update_user_vectors(user_id):
    """Background task to update user vectors"""
    try:
        # Get updated user data
        user = User.find_by_id(user_id)
        if not user:
            return
        
        # Update vectors
        users = [user]
        vector_service.update_user_vectors(users)
        
        # Notify user via WebSocket
        ws_service.emit_vector_update(user_id, 'completed')
        
    except Exception as e:
        print(f"Error updating vectors: {e}")
        ws_service.emit_vector_update(user_id, 'failed')

@profile_bp.route('/me', methods=['GET'])
@token_required
def get_profile(current_user):
    """Get current user profile"""
    if 'password' in current_user:
        del current_user['password']
    
    return jsonify({"user": current_user}), 200

@profile_bp.route('/update', methods=['PUT'])
@token_required
def update_profile(current_user):
    """Update user profile"""
    data = request.get_json()
    
    update_fields = {}
    
    # Allowed fields to update
    if 'name' in data:
        update_fields['name'] = data['name']
    if 'bio' in data:
        update_fields['bio'] = data['bio']
    if 'skills' in data:
        update_fields['skills'] = data['skills']
    if 'linkedin' in data:
        update_fields['linkedin'] = data['linkedin']
    if 'professional_title' in data:
        update_fields['professional_title'] = data['professional_title']
    if 'experience_years' in data:
        update_fields['experience_years'] = int(data['experience_years'])
    if 'location' in data:
        update_fields['location'] = data['location']
    
    if not update_fields:
        return jsonify({"error": "No valid fields to update"}), 400
    
    # Update user
    success = User.update_profile(current_user['_id'], update_fields)
    
    if not success:
        return jsonify({"error": "Failed to update profile"}), 500
    
    # Get updated user
    updated_user = User.find_by_id(current_user['_id'])
    if 'password' in updated_user:
        del updated_user['password']
    
    # Update vectors in background
    vector_thread = threading.Thread(
        target=update_user_vectors,
        args=(current_user['_id'],)
    )
    vector_thread.daemon = True
    vector_thread.start()
    
    # Notify via WebSocket
    ws_service.emit_profile_update(current_user['_id'], {
        'message': 'Profile updated successfully',
        'updated_fields': list(update_fields.keys())
    })
    
    return jsonify({
        "message": "Profile updated successfully",
        "user": updated_user,
        "vector_update_initiated": True
    }), 200

@profile_bp.route('/upload-resume', methods=['POST'])
@token_required
def upload_resume(current_user):
    """Upload and parse resume"""
    if 'resume' not in request.files:
        return jsonify({"error": "No resume file provided"}), 400
    
    file = request.files['resume']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type. Only PDF and DOCX allowed"}), 400
    
    # Save file
    filename = secure_filename(f"{current_user['_id']}_{file.filename}")
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)
    
    # Parse resume
    try:
        # Comprehensive analysis
        analysis = ats_service.comprehensive_profile_analysis(
            current_user,
            file_path
        )
        
        # Update user with resume info
        update_data = {
            'resume': file_path,
            'resume_parsed': True
        }
        
        # Optionally merge extracted skills
        if analysis.get('merged_skills'):
            update_data['skills'] = analysis['merged_skills']
        
        # Update experience if found in resume
        if analysis.get('resume_analysis', {}).get('estimated_experience', 0) > 0:
            extracted_exp = analysis['resume_analysis']['estimated_experience']
            if extracted_exp > current_user.get('experience_years', 0):
                update_data['experience_years'] = extracted_exp
        
        User.update_profile(current_user['_id'], update_data)
        
        # Update vectors in background
        vector_thread = threading.Thread(
            target=update_user_vectors,
            args=(current_user['_id'],)
        )
        vector_thread.daemon = True
        vector_thread.start()
        
        # Get updated user
        updated_user = User.find_by_id(current_user['_id'])
        if 'password' in updated_user:
            del updated_user['password']
        
        return jsonify({
            "message": "Resume uploaded and analyzed successfully",
            "analysis": analysis,
            "user": updated_user,
            "vector_update_initiated": True
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to parse resume: {str(e)}"}), 500

@profile_bp.route('/ats-score/<project_id>', methods=['GET'])
@token_required
def calculate_ats_score(current_user, project_id):
    """Calculate ATS score for user against a project"""
    from models.project import Project
    
    project = Project.find_by_id(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    # Build user profile text
    user_text = f"""
    Name: {current_user.get('name', '')}
    Bio: {current_user.get('bio', '')}
    Skills: {', '.join(current_user.get('skills', []))}
    Experience: {current_user.get('experience_years', 0)} years
    """
    
    # Add resume text if available
    if current_user.get('resume'):
        resume_text = ats_service.parse_resume(current_user['resume'])
        if resume_text:
            user_text += f"\n\nResume:\n{resume_text}"
    
    # Calculate score
    score_data = ats_service.calculate_ats_score(
        user_text,
        project['description']
    )
    
    # Get optimization tips
    tips = ats_service.generate_profile_optimization_tips(
        user_text,
        project['description']
    )
    
    result = {
        'project_id': project_id,
        'project_title': project['title'],
        'ats_score': score_data,
        'optimization_tips': tips
    }
    
    # Emit to user via WebSocket
    ws_service.emit_ats_score_update(current_user['_id'], result)
    
    return jsonify(result), 200

@profile_bp.route('/analyze-resume', methods=['POST'])
@token_required
def analyze_current_resume(current_user):
    """Analyze current user's resume"""
    if not current_user.get('resume'):
        return jsonify({"error": "No resume uploaded"}), 404
    
    analysis = ats_service.comprehensive_profile_analysis(
        current_user,
        current_user['resume']
    )
    
    return jsonify({
        "message": "Resume analyzed successfully",
        "analysis": analysis
    }), 200

@profile_bp.route('/skills-suggestions', methods=['POST'])
@token_required
def get_skills_suggestions(current_user):
    """Get AI-powered skills suggestions based on profile"""
    data = request.get_json()
    target_role = data.get('target_role', current_user.get('professional_title', ''))
    
    prompt = f"""
Based on this profile, suggest relevant skills to add:

Current Profile:
- Name: {current_user.get('name', '')}
- Bio: {current_user.get('bio', '')}
- Current Skills: {', '.join(current_user.get('skills', []))}
- Experience: {current_user.get('experience_years', 0)} years
- Target Role: {target_role}

Suggest 10-15 relevant skills they should consider adding to improve their profile.
Consider trending technologies and industry demands.

Respond in JSON format:
{{
    "suggested_skills": ["skill1", "skill2", ...],
    "reasoning": "brief explanation"
}}
"""
    
    try:
        response = ats_service.gemini_service.client.models.generate_content(
            model=ats_service.gemini_service.model,
            contents=prompt
        )
        
        result = ats_service.gemini_service._extract_json(response.text)
        return jsonify(result if result else {"suggested_skills": []}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@profile_bp.route('/delete-resume', methods=['DELETE'])
@token_required
def delete_resume(current_user):
    """Delete uploaded resume"""
    if not current_user.get('resume'):
        return jsonify({"error": "No resume to delete"}), 404
    
    # Delete file
    try:
        if os.path.exists(current_user['resume']):
            os.remove(current_user['resume'])
    except Exception as e:
        print(f"Error deleting resume file: {e}")
    
    # Update user
    User.update_profile(current_user['_id'], {
        'resume': '',
        'resume_parsed': False
    })
    
    # Update vectors
    vector_thread = threading.Thread(
        target=update_user_vectors,
        args=(current_user['_id'],)
    )
    vector_thread.daemon = True
    vector_thread.start()
    
    return jsonify({
        "message": "Resume deleted successfully",
        "vector_update_initiated": True
    }), 200