from flask import Blueprint, request, jsonify
from models.project import Project
from models.user import User
from routes.auth import token_required
from services.matching_service import MatchingService

matching_bp = Blueprint('matching', __name__)
matching_service = MatchingService()

@matching_bp.route('/<project_id>', methods=['GET'])
@token_required
def get_matches(current_user, project_id):
    project = Project.find_by_id(project_id)
    
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    if project['founder_id'] != current_user['_id']:
        return jsonify({"error": "Unauthorized"}), 403
    
    if not project.get('live', False):
        return jsonify({"error": "Project is not live yet"}), 400
    
    # Get AI-powered matches
    matches = matching_service.find_matches(project, current_user['_id'])
    
    return jsonify({
        "project_id": project_id,
        "matches": matches
    }), 200

@matching_bp.route('/send-request', methods=['POST'])
@token_required
def send_collaboration_request(current_user):
    data = request.get_json()
    
    project_id = data.get('project_id')
    candidate_id = data.get('candidate_id')
    message = data.get('message', '')
    
    if not project_id or not candidate_id:
        return jsonify({"error": "Project ID and candidate ID are required"}), 400
    
    project = Project.find_by_id(project_id)
    
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    if project['founder_id'] != current_user['_id']:
        return jsonify({"error": "Unauthorized"}), 403
    
    success = Project.add_collaboration_request(project_id, candidate_id, message)
    
    if success:
        return jsonify({"message": "Collaboration request sent successfully"}), 200
    else:
        return jsonify({"error": "Failed to send request"}), 500