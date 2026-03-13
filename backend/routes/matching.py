from flask import Blueprint, request

from models.project import Project
from routes.auth import token_required
from services.matching_service import MatchingService
from utils.api_response import api_error, api_success, unauthorized_error
from utils.authz import require_founder
from utils.validation import validate_required_fields
from routes.collaboration import _send_collaboration_request_impl

matching_bp = Blueprint("matching", __name__)
matching_service = None


def get_matching_service():
    global matching_service
    if matching_service is None:
        matching_service = MatchingService()
    return matching_service


@matching_bp.route("/<project_id>", methods=["GET"])
@token_required
def get_matches(current_user, project_id):
    project = Project.find_by_id(project_id)
    if not project:
        return api_error("PROJECT_NOT_FOUND", "Project not found", 404)

    if not require_founder(project, current_user["_id"]):
        return unauthorized_error("Unauthorized", {"project_id": project_id})

    if not project.get("live", False):
        return api_error("PROJECT_NOT_LIVE", "Project is not live yet", 400)

    if project.get("cached_matches"):
        return api_success(
            {"project_id": project_id, "matches": project["cached_matches"], "cached": True},
            message="Matches fetched from cache",
        )

    matches = get_matching_service().find_matches(project, current_user["_id"])
    Project.cache_matches(project_id, matches)
    return api_success(
        {"project_id": project_id, "matches": matches, "cached": False},
        message="Matches generated",
    )


@matching_bp.route("/send-request", methods=["POST"])
@token_required
def send_collaboration_request(current_user):
    # Backward-compatible endpoint. Delegates to collaboration implementation.
    return _send_collaboration_request_impl(current_user, request.get_json(silent=True) or {})


@matching_bp.route("/feedback", methods=["POST"])
@token_required
def save_matching_feedback(current_user):
    data = request.get_json(silent=True) or {}
    validation = validate_required_fields(data, ["project_id", "candidate_id", "feedback"])
    if not validation["is_valid"]:
        return api_error("VALIDATION_ERROR", "project_id, candidate_id and feedback are required", 400, {
            "missing_fields": validation["missing_fields"]
        })

    project = Project.find_by_id(data["project_id"])
    if not project:
        return api_error("PROJECT_NOT_FOUND", "Project not found", 404)
    if not require_founder(project, current_user["_id"]):
        return unauthorized_error("Unauthorized", {"project_id": data["project_id"]})

    feedback = get_matching_service().store_feedback(
        project_id=data["project_id"],
        founder_id=current_user["_id"],
        candidate_id=data["candidate_id"],
        feedback=data["feedback"],
    )
    return api_success({"feedback": feedback}, message="Feedback stored")
