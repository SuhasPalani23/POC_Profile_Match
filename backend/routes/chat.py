from flask import Blueprint, request, jsonify
from models.message import Message
from models.collaboration import Collaboration
from models.project import Project
from routes.auth import token_required
from services.websocket_service import ws_service

chat_bp = Blueprint('chat', __name__)

def _is_team_member(project, current_user):
    """Returns True if user is founder or accepted team member"""
    if project['founder_id'] == current_user['_id']:
        return True
    collab = Collaboration.check_existing(project['_id'], current_user['_id'])
    return collab and collab['status'] == 'accepted'

@chat_bp.route('/send', methods=['POST'])
@token_required
def send_message(current_user):
    """Send a group or DM message"""
    data = request.get_json()
    project_id = data.get('project_id')
    message_text = data.get('message')
    dm_recipient_id = data.get('dm_recipient_id')  # optional — if set, it's a DM
    
    if not project_id or not message_text:
        return jsonify({"error": "Project ID and message are required"}), 400
    
    project = Project.find_by_id(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    if not _is_team_member(project, current_user):
        return jsonify({"error": "You must be a team member to send messages"}), 403
    
    message = Message.create(
        project_id=project_id,
        sender_id=current_user['_id'],
        sender_name=current_user['name'],
        message_text=message_text,
        dm_recipient_id=dm_recipient_id
    )
    
    payload = {
        'message_id': message['_id'],
        'project_id': project_id,
        'sender_id': message['sender_id'],
        'sender_name': message['sender_name'],
        'message': message['message'],
        'dm_recipient_id': dm_recipient_id,
        'created_at': message['created_at'].isoformat()
    }
    
    if dm_recipient_id:
        # Emit only to sender and recipient rooms
        ws_service.emit_new_message(f"dm_{_dm_room_key(current_user['_id'], dm_recipient_id)}", payload)
        ws_service.emit_new_dm_notification(dm_recipient_id, payload)
    else:
        ws_service.emit_new_message(project_id, payload)
    
    return jsonify({
        "message": "Message sent successfully",
        "data": message
    }), 200

@chat_bp.route('/messages/<project_id>', methods=['GET'])
@token_required
def get_messages(current_user, project_id):
    """Get group messages"""
    project = Project.find_by_id(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    if not _is_team_member(project, current_user):
        return jsonify({"error": "You must be a team member to view messages"}), 403
    
    messages = Message.get_project_messages(project_id)
    return jsonify({"project_id": project_id, "messages": messages}), 200

@chat_bp.route('/dm/<project_id>/<other_user_id>', methods=['GET'])
@token_required
def get_dm_messages(current_user, project_id, other_user_id):
    """Get DM messages between current user and another user in project context"""
    project = Project.find_by_id(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    if not _is_team_member(project, current_user):
        return jsonify({"error": "Unauthorized"}), 403
    
    messages = Message.get_dm_messages(project_id, current_user['_id'], other_user_id)
    return jsonify({"messages": messages}), 200

@chat_bp.route('/mark-read/<message_id>', methods=['POST'])
@token_required
def mark_message_read(current_user, message_id):
    success = Message.mark_as_read(message_id, current_user['_id'])
    if not success:
        return jsonify({"error": "Failed to mark message as read"}), 500
    return jsonify({"message": "Message marked as read"}), 200

@chat_bp.route('/unread-count/<project_id>', methods=['GET'])
@token_required
def get_unread_count(current_user, project_id):
    count = Message.get_unread_count(project_id, current_user['_id'])
    return jsonify({"project_id": project_id, "unread_count": count}), 200

def _dm_room_key(user_a, user_b):
    """Deterministic room key for two users"""
    return '_'.join(sorted([str(user_a), str(user_b)]))