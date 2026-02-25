from flask import Blueprint, request, jsonify
from models.collaboration import Collaboration
from models.project import Project
from models.user import User
from routes.auth import token_required
from services.websocket_service import ws_service

collaboration_bp = Blueprint('collaboration', __name__)

@collaboration_bp.route('/send-request', methods=['POST'])
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
        return jsonify({"error": "You can only send requests for your own projects"}), 403
    
    existing = Collaboration.check_existing(project_id, candidate_id)
    if existing:
        return jsonify({"error": "Request already sent to this candidate"}), 400
    
    collaboration = Collaboration.create_request(
        project_id=project_id,
        founder_id=current_user['_id'],
        candidate_id=candidate_id,
        message=message
    )
    
    ws_service.emit_collaboration_request(candidate_id, {
        'collaboration_id': collaboration['_id'],
        'project_id': project_id,
        'project_title': project['title'],
        'founder_name': current_user['name'],
        'message': message,
        'status': 'request_sent'
    })
    
    return jsonify({
        "message": "Collaboration request sent successfully",
        "collaboration": collaboration
    }), 200

@collaboration_bp.route('/my-requests', methods=['GET'])
@token_required
def get_my_requests(current_user):
    requests = Collaboration.find_by_candidate(current_user['_id'])
    
    enriched_requests = []
    for req in requests:
        project = Project.find_by_id(req['project_id'])
        founder = User.find_by_id(req['founder_id'])
        
        if project and founder:
            enriched_requests.append({
                **req,
                'project': project,
                'founder': {
                    'id': founder['_id'],
                    'name': founder['name'],
                    'email': founder['email'],
                    'bio': founder.get('bio', ''),
                    'skills': founder.get('skills', []),
                    'professional_title': founder.get('professional_title', '')
                }
            })
    
    return jsonify({"requests": enriched_requests}), 200

@collaboration_bp.route('/sent-requests/<project_id>', methods=['GET'])
@token_required
def get_sent_requests_for_project(current_user, project_id):
    project = Project.find_by_id(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    if project['founder_id'] != current_user['_id']:
        return jsonify({"error": "Unauthorized"}), 403

    all_project_requests = Collaboration.find_by_project(project_id)
    founder_requests = [
        req for req in all_project_requests if req.get('founder_id') == current_user['_id']
    ]
    candidate_ids = [req.get('candidate_id') for req in founder_requests if req.get('candidate_id')]

    return jsonify({
        "project_id": project_id,
        "candidate_ids": candidate_ids,
        "requests": founder_requests
    }), 200

@collaboration_bp.route('/accept/<collaboration_id>', methods=['POST'])
@token_required
def accept_request(current_user, collaboration_id):
    collaboration = Collaboration.find_by_id(collaboration_id)
    if not collaboration:
        return jsonify({"error": "Collaboration request not found"}), 404
    if collaboration['candidate_id'] != current_user['_id']:
        return jsonify({"error": "Unauthorized"}), 403
    if collaboration['status'] != 'pending':
        return jsonify({"error": "Request already processed"}), 400
    
    success = Collaboration.accept_request(collaboration_id)
    if not success:
        return jsonify({"error": "Failed to accept request"}), 500
    
    project = Project.find_by_id(collaboration['project_id'])
    
    ws_service.emit_request_accepted(collaboration['founder_id'], {
        'collaboration_id': collaboration_id,
        'project_id': collaboration['project_id'],
        'project_title': project['title'],
        'candidate_name': current_user['name'],
        'candidate_id': current_user['_id'],
        'status': 'accepted'
    })
    ws_service.emit_request_accepted(current_user['_id'], {
        'collaboration_id': collaboration_id,
        'project_id': collaboration['project_id'],
        'project_title': project['title'],
        'status': 'accepted'
    })
    
    return jsonify({
        "message": "Request accepted successfully",
        "collaboration_id": collaboration_id,
        "project": project
    }), 200

@collaboration_bp.route('/reject/<collaboration_id>', methods=['POST'])
@token_required
def reject_request(current_user, collaboration_id):
    collaboration = Collaboration.find_by_id(collaboration_id)
    if not collaboration:
        return jsonify({"error": "Collaboration request not found"}), 404
    if collaboration['candidate_id'] != current_user['_id']:
        return jsonify({"error": "Unauthorized"}), 403
    if collaboration['status'] != 'pending':
        return jsonify({"error": "Request already processed"}), 400
    
    success = Collaboration.reject_request(collaboration_id)
    if not success:
        return jsonify({"error": "Failed to reject request"}), 500
    
    project = Project.find_by_id(collaboration['project_id'])
    ws_service.emit_request_rejected(collaboration['founder_id'], {
        'collaboration_id': collaboration_id,
        'project_id': collaboration['project_id'],
        'project_title': project['title'],
        'candidate_name': current_user['name'],
        'status': 'rejected'
    })
    
    return jsonify({"message": "Request rejected successfully"}), 200

@collaboration_bp.route('/team/<project_id>', methods=['GET'])
@token_required
def get_team_members(current_user, project_id):
    project = Project.find_by_id(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    is_founder = project['founder_id'] == current_user['_id']
    
    if not is_founder:
        user_collab = Collaboration.check_existing(project_id, current_user['_id'])
        if not user_collab or user_collab['status'] != 'accepted':
            return jsonify({"error": "Unauthorized"}), 403
    
    collaborations = Collaboration.get_team_members(project_id)
    
    team_members = []
    for collab in collaborations:
        member = User.find_by_id(collab['candidate_id'])
        if member:
            team_members.append({
                'collaboration_id': collab['_id'],
                'user_id': member['_id'],
                'name': member['name'],
                'email': member['email'],
                'bio': member.get('bio', ''),
                'skills': member.get('skills', []),
                'professional_title': member.get('professional_title', ''),
                'joined_at': collab.get('accepted_at')
            })
    
    founder = User.find_by_id(project['founder_id'])
    founder_info = {
        'collaboration_id': None,
        'user_id': founder['_id'],
        'name': founder['name'],
        'email': founder['email'],
        'bio': founder.get('bio', ''),
        'skills': founder.get('skills', []),
        'professional_title': founder.get('professional_title', ''),
        'is_founder': True,
        'joined_at': project['created_at']
    }
    
    return jsonify({
        "project": project,
        "founder": founder_info,
        "team_members": team_members
    }), 200

@collaboration_bp.route('/leave/<collaboration_id>', methods=['POST'])
@token_required
def leave_project(current_user, collaboration_id):
    collaboration = Collaboration.find_by_id(collaboration_id)
    if not collaboration:
        return jsonify({"error": "Collaboration not found"}), 404
    if collaboration['candidate_id'] != current_user['_id']:
        return jsonify({"error": "Unauthorized"}), 403
    if collaboration['status'] != 'accepted':
        return jsonify({"error": "You are not part of this project"}), 400
    
    success = Collaboration.leave_project(collaboration_id)
    if not success:
        return jsonify({"error": "Failed to leave project"}), 500
    
    project = Project.find_by_id(collaboration['project_id'])
    ws_service.emit_member_left(collaboration['project_id'], {
        'project_id': collaboration['project_id'],
        'project_title': project['title'],
        'member_name': current_user['name'],
        'member_id': current_user['_id']
    })
    
    return jsonify({"message": "Successfully left the project"}), 200

@collaboration_bp.route('/remove-member', methods=['POST'])
@token_required
def remove_member(current_user):
    """Founder removes a team member"""
    data = request.get_json()
    collaboration_id = data.get('collaboration_id')
    
    if not collaboration_id:
        return jsonify({"error": "collaboration_id is required"}), 400
    
    collaboration = Collaboration.find_by_id(collaboration_id)
    if not collaboration:
        return jsonify({"error": "Collaboration not found"}), 404
    
    project = Project.find_by_id(collaboration['project_id'])
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    if project['founder_id'] != current_user['_id']:
        return jsonify({"error": "Only the founder can remove members"}), 403
    
    if collaboration['status'] != 'accepted':
        return jsonify({"error": "Member is not active in this project"}), 400
    
    success = Collaboration.leave_project(collaboration_id)
    if not success:
        return jsonify({"error": "Failed to remove member"}), 500
    
    removed_user = User.find_by_id(collaboration['candidate_id'])
    
    ws_service.emit_member_left(collaboration['project_id'], {
        'project_id': collaboration['project_id'],
        'project_title': project['title'],
        'member_name': removed_user['name'] if removed_user else 'Member',
        'member_id': collaboration['candidate_id'],
        'removed_by_founder': True
    })
    
    # Notify the removed user
    if removed_user:
        ws_service.emit_collaboration_request(collaboration['candidate_id'], {
            'type': 'removed_from_project',
            'project_id': collaboration['project_id'],
            'project_title': project['title'],
            'message': f'You have been removed from {project["title"]} by the founder.'
        })
    
    return jsonify({"message": "Member removed successfully"}), 200

@collaboration_bp.route('/my-projects', methods=['GET'])
@token_required
def get_my_projects(current_user):
    """Get all projects where user is an accepted team member"""
    collaborations = Collaboration.get_user_projects(current_user['_id'])
    
    projects = []
    for collab in collaborations:
        project = Project.find_by_id(collab['project_id'])
        if project:
            founder = User.find_by_id(project['founder_id'])
            projects.append({
                'collaboration_id': collab['_id'],
                'project': project,
                'founder': {
                    'id': founder['_id'],
                    'name': founder['name'],
                    'email': founder['email']
                },
                'joined_at': collab.get('accepted_at')
            })
    
    return jsonify({"projects": projects}), 200