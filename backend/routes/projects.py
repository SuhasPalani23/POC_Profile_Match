from flask import Blueprint, request
import time

from models.project import Project
from models.user import User
from routes.auth import token_required
from services.background_tasks import enqueue
from utils.api_response import api_error, api_success, unauthorized_error, validation_error
from utils.authz import require_founder
from utils.validation import validate_required_fields

projects_bp = Blueprint("projects", __name__)


def simulate_review(project_id, user_id):
    time.sleep(10)
    Project.update_status(project_id, live=True, status="approved")
    User.update_role(user_id, "founder")


@projects_bp.route("", methods=["POST"])
@token_required
def create_project(current_user):
    data = request.get_json(silent=True) or {}
    validation = validate_required_fields(data, ["title", "description"])
    if not validation["is_valid"]:
        return validation_error(
            "Title and description are required",
            {"missing_fields": validation["missing_fields"]},
        )

    title = data.get("title")
    description = data.get("description")
    required_skills = data.get("required_skills", [])

    if len(description) < 500:
        return validation_error("Description must be at least 500 characters", {"min_length": 500})

    project = Project.create(
        founder_id=current_user["_id"],
        title=title,
        description=description,
        required_skills=required_skills,
    )

    enqueue(simulate_review, project["_id"], current_user["_id"])

    return api_success(
        {"project": project},
        message="Project submitted for review",
        code="PROJECT_CREATED",
        status=201,
    )


@projects_bp.route("/my-projects", methods=["GET"])
@token_required
def get_my_projects(current_user):
    projects = Project.find_by_founder(current_user["_id"])
    return api_success({"projects": projects}, message="Projects fetched")


@projects_bp.route("/<project_id>", methods=["GET"])
@token_required
def get_project(current_user, project_id):
    project = Project.find_by_id(project_id)
    if not project:
        return api_error("PROJECT_NOT_FOUND", "Project not found", 404)

    if not require_founder(project, current_user["_id"]):
        # Allow candidate members to access read-only in project-scoped contexts.
        # Existing flow relies on this endpoint from founder dashboard; keep strict founder only for now.
        return unauthorized_error("Unauthorized project access", {"project_id": project_id})

    return api_success({"project": project}, message="Project fetched")


@projects_bp.route("/<project_id>", methods=["PUT"])
@token_required
def update_project(current_user, project_id):
    project = Project.find_by_id(project_id)
    if not project:
        return api_error("PROJECT_NOT_FOUND", "Project not found", 404)

    if not require_founder(project, current_user["_id"]):
        return unauthorized_error("Only founder can update this project", {"project_id": project_id})

    data = request.get_json(silent=True) or {}
    allowed_fields = ["title", "description", "required_skills"]
    update_fields = {k: data[k] for k in allowed_fields if k in data}
    if not update_fields:
        return validation_error("No valid fields to update", {"allowed_fields": allowed_fields})

    if "description" in update_fields and len(update_fields["description"]) < 500:
        return validation_error("Description must be at least 500 characters", {"min_length": 500})

    Project.update_project(project_id, update_fields)
    updated = Project.find_by_id(project_id)
    return api_success(
        {"project": updated, "cache_invalidated": any(k in update_fields for k in ["description", "required_skills", "title"])},
        message="Project updated successfully",
    )


@projects_bp.route("/live", methods=["GET"])
@token_required
def get_live_projects(current_user):
    projects = Project.get_all_live_projects()
    return api_success({"projects": projects}, message="Live projects fetched")
