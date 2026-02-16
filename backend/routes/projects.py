from flask import Blueprint, request, jsonify
from models.project import Project
from models.user import User
from routes.auth import token_required
import time
import threading

projects_bp = Blueprint('projects', __name__)

def simulate_review(project_id, user_id):
    """Simulate 10-second review process"""
    time.sleep(10)
    # Update project to live
    Project.update_status(project_id, live=True, status="approved")
    # Update user role to founder
    User.update_role(user_id, "founder")

@projects_bp.route('', methods=['POST'])
@token_required
def create_project(current_user):
    data = request.get_json()
    
    title = data.get('title')
    description = data.get('description')
    required_skills = data.get('required_skills', [])
    
    if not title or not description:
        return jsonify({"error": "Title and description are required"}), 400
    
    if len(description) < 500:
        return jsonify({"error": "Description must be at least 500 characters"}), 400
    
    project = Project.create(
        founder_id=current_user['_id'],
        title=title,
        description=description,
        required_skills=required_skills
    )
    
    # Start background thread for review simulation
    review_thread = threading.Thread(
        target=simulate_review,
        args=(project['_id'], current_user['_id'])
    )
    review_thread.daemon = True
    review_thread.start()
    
    return jsonify({
        "message": "Project submitted for review",
        "project": project
    }), 201

@projects_bp.route('/my-projects', methods=['GET'])
@token_required
def get_my_projects(current_user):
    projects = Project.find_by_founder(current_user['_id'])
    return jsonify({"projects": projects}), 200

@projects_bp.route('/<project_id>', methods=['GET'])
@token_required
def get_project(current_user, project_id):
    project = Project.find_by_id(project_id)
    
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    return jsonify({"project": project}), 200

@projects_bp.route('/live', methods=['GET'])
@token_required
def get_live_projects(current_user):
    projects = Project.get_all_live_projects()
    return jsonify({"projects": projects}), 200