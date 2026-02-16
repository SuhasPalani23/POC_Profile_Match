from flask import Blueprint, request, jsonify
from models.message import Message
from models.collaboration import Collaboration
from models.project import Project
from routes.auth import token_required
from services.websocket_service import ws_service

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/send', methods=['POST'])
@token_required
def send_message(current_user):
    """Send a message in project chat"""
    data = request.get_json()
    
    project_id = data.get('project_id')
    message_text = data.get('message')
    
    if not project_id or not message_text:
        return jsonify({"error": "Project ID and message are required"}), 400
    
    # Verify user is part of the project
    project = Project.find_by_id(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    is_founder = project['founder_id'] == current_user['_id']
    
    if not is_founder:
        # Check if user is a team member
        collab = Collaboration.check_existing(project_id, current_user['_id'])
        if not collab or collab['status'] != 'accepted':
            return jsonify({"error": "You must be a team member to send messages"}), 403
    
    # Create message
    message = Message.create(
        project_id=project_id,
        sender_id=current_user['_id'],
        sender_name=current_user['name'],
        message_text=message_text
    )
    
    # Emit WebSocket message to project room
    ws_service.emit_new_message(project_id, {
        'message_id': message['_id'],
        'project_id': project_id,
        'sender_id': message['sender_id'],
        'sender_name': message['sender_name'],
        'message': message['message'],
        'created_at': message['created_at'].isoformat()
    })
    
    return jsonify({
        "message": "Message sent successfully",
        "data": message
    }), 200

@chat_bp.route('/messages/<project_id>', methods=['GET'])
@token_required
def get_messages(current_user, project_id):
    """Get chat messages for a project"""
    # Verify user is part of the project
    project = Project.find_by_id(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    is_founder = project['founder_id'] == current_user['_id']
    
    if not is_founder:
        # Check if user is a team member
        collab = Collaboration.check_existing(project_id, current_user['_id'])
        if not collab or collab['status'] != 'accepted':
            return jsonify({"error": "You must be a team member to view messages"}), 403
    
    # Get messages
    messages = Message.get_project_messages(project_id)
    
    return jsonify({
        "project_id": project_id,
        "messages": messages
    }), 200

@chat_bp.route('/mark-read/<message_id>', methods=['POST'])
@token_required
def mark_message_read(current_user, message_id):
    """Mark a message as read"""
    success = Message.mark_as_read(message_id, current_user['_id'])
    
    if not success:
        return jsonify({"error": "Failed to mark message as read"}), 500
    
    return jsonify({"message": "Message marked as read"}), 200

@chat_bp.route('/unread-count/<project_id>', methods=['GET'])
@token_required
def get_unread_count(current_user, project_id):
    """Get unread message count for a project"""
    count = Message.get_unread_count(project_id, current_user['_id'])
    
    return jsonify({
        "project_id": project_id,
        "unread_count": count
    }), 200