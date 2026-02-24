from flask import Blueprint, request, jsonify
from models.project import Project
from models.user import User
from models.collaboration import Collaboration
from routes.auth import token_required
from services.matching_service import MatchingService
from services.websocket_service import ws_service

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

    # Return cached matches if available
    if project.get('cached_matches'):
        return jsonify({
            "project_id": project_id,
            "matches": project['cached_matches'],
            "cached": True
        }), 200

    # Generate fresh matches
    matches = matching_service.find_matches(project, current_user['_id'])

    # Cache matches in MongoDB so results are consistent on refresh
    Project.cache_matches(project_id, matches)

    return jsonify({
        "project_id": project_id,
        "matches": matches,
        "cached": False
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

    # Block invite if candidate is a founder
    candidate = User.find_by_id(candidate_id)
    if not candidate:
        return jsonify({"error": "Candidate not found"}), 404
    if candidate.get("role") == "founder":
        return jsonify({"error": "This user is a founder and cannot be invited"}), 403

    # Check for duplicate request
    existing = Collaboration.check_existing(project_id, candidate_id)
    if existing:
        return jsonify({"error": "Request already sent to this candidate"}), 400

    # Store in Collaboration collection so candidate can see it
    collaboration = Collaboration.create_request(
        project_id=project_id,
        founder_id=current_user['_id'],
        candidate_id=candidate_id,
        message=message
    )

    # Also update project embedded array for consistency
    Project.add_collaboration_request(project_id, candidate_id, message)

    # Emit WebSocket notification to candidate
    ws_service.emit_collaboration_request(candidate_id, {
        'collaboration_id': collaboration['_id'],
        'project_id': project_id,
        'project_title': project['title'],
        'founder_name': current_user.get('name', ''),
        'message': message,
        'status': 'request_sent'
    })

    return jsonify({
        "message": "Collaboration request sent successfully",
        "collaboration": collaboration
    }), 200