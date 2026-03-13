from flask import Blueprint, request

from models.collaboration import Collaboration
from models.project import Project
from models.user import User
from routes.auth import token_required
from services.websocket_service import ws_service
from utils.api_response import api_error, api_success, unauthorized_error
from utils.authz import has_project_access, require_founder
from utils.validation import validate_required_fields

collaboration_bp = Blueprint("collaboration", __name__)


def _enrich_request(req: dict):
    project = Project.find_by_id(req["project_id"])
    founder = User.find_by_id(req["founder_id"])
    if not project or not founder:
        return None
    return {
        **req,
        "project": project,
        "founder": {
            "id": founder["_id"],
            "name": founder["name"],
            "email": founder["email"],
            "bio": founder.get("bio", ""),
            "skills": founder.get("skills", []),
            "professional_title": founder.get("professional_title", ""),
        },
    }


def _send_collaboration_request_impl(current_user, data):
    validation = validate_required_fields(data, ["project_id", "candidate_id"])
    if not validation["is_valid"]:
        return api_error(
            "VALIDATION_ERROR",
            "Project ID and candidate ID are required",
            400,
            {"missing_fields": validation["missing_fields"]},
        )

    project_id = data.get("project_id")
    candidate_id = data.get("candidate_id")
    message = data.get("message", "")

    project = Project.find_by_id(project_id)
    if not project:
        return api_error("PROJECT_NOT_FOUND", "Project not found", 404)
    if not require_founder(project, current_user["_id"]):
        return unauthorized_error("You can only send requests for your own projects", {"project_id": project_id})

    candidate = User.find_by_id(candidate_id)
    if not candidate:
        return api_error("CANDIDATE_NOT_FOUND", "Candidate not found", 404)
    if candidate.get("role") == "founder":
        return api_error("INVALID_CANDIDATE", "This user is a founder and cannot be invited", 403)

    collaboration, created = Collaboration.create_or_get_request(
        project_id=project_id,
        founder_id=current_user["_id"],
        candidate_id=candidate_id,
        message=message,
    )

    if created:
        ws_service.emit_collaboration_request(
            candidate_id,
            {
                "collaboration_id": collaboration["_id"],
                "project_id": project_id,
                "project_title": project["title"],
                "founder_name": current_user["name"],
                "message": message,
                "status": "request_sent",
            },
        )
        return api_success(
            {"collaboration": collaboration, "already_exists": False},
            message="Collaboration request sent successfully",
        )

    return api_success(
        {"collaboration": collaboration, "already_exists": True},
        message="Request already exists",
        code="ALREADY_EXISTS",
        status=200,
    )


@collaboration_bp.route("/send-request", methods=["POST"])
@token_required
def send_collaboration_request(current_user):
    return _send_collaboration_request_impl(current_user, request.get_json(silent=True) or {})


@collaboration_bp.route("/my-requests", methods=["GET"])
@token_required
def get_my_requests(current_user):
    requests = Collaboration.find_by_candidate(current_user["_id"])
    enriched_requests = [item for item in (_enrich_request(req) for req in requests) if item]
    return api_success({"requests": enriched_requests}, message="Requests fetched")


@collaboration_bp.route("/sent-requests/<project_id>", methods=["GET"])
@token_required
def get_sent_requests_for_project(current_user, project_id):
    project = Project.find_by_id(project_id)
    if not project:
        return api_error("PROJECT_NOT_FOUND", "Project not found", 404)
    if not require_founder(project, current_user["_id"]):
        return unauthorized_error("Unauthorized", {"project_id": project_id})

    all_project_requests = Collaboration.find_by_project(project_id)
    founder_requests = [req for req in all_project_requests if req.get("founder_id") == current_user["_id"]]
    candidate_ids = [req.get("candidate_id") for req in founder_requests if req.get("candidate_id")]

    return api_success(
        {"project_id": project_id, "candidate_ids": candidate_ids, "requests": founder_requests},
        message="Sent requests fetched",
    )


@collaboration_bp.route("/history", methods=["GET"])
@token_required
def request_history(current_user):
    sent = Collaboration.find_by_founder(current_user["_id"])
    received = Collaboration.find_by_candidate(current_user["_id"])
    return api_success(
        {"sent": sent, "received": received},
        message="Request history fetched",
    )


@collaboration_bp.route("/withdraw/<collaboration_id>", methods=["POST"])
@token_required
def withdraw_request(current_user, collaboration_id):
    collaboration = Collaboration.find_by_id(collaboration_id)
    if not collaboration:
        return api_error("COLLABORATION_NOT_FOUND", "Collaboration request not found", 404)
    if collaboration["founder_id"] != current_user["_id"]:
        return unauthorized_error("Only founder can withdraw request")
    if collaboration["status"] != "pending":
        return api_error("INVALID_STATUS", "Only pending requests can be withdrawn", 400, {"status": collaboration["status"]})

    success = Collaboration.cancel_request(collaboration_id)
    if not success:
        return api_error("WITHDRAW_FAILED", "Failed to withdraw request", 500)

    return api_success({"collaboration_id": collaboration_id, "status": "cancelled"}, message="Request withdrawn")


@collaboration_bp.route("/accept/<collaboration_id>", methods=["POST"])
@token_required
def accept_request(current_user, collaboration_id):
    collaboration = Collaboration.find_by_id(collaboration_id)
    if not collaboration:
        return api_error("COLLABORATION_NOT_FOUND", "Collaboration request not found", 404)
    if collaboration["candidate_id"] != current_user["_id"]:
        return unauthorized_error("Unauthorized")
    if collaboration["status"] != "pending":
        return api_error("INVALID_STATUS", "Request already processed", 400, {"status": collaboration["status"]})

    success = Collaboration.accept_request(collaboration_id)
    if not success:
        return api_error("ACCEPT_FAILED", "Failed to accept request", 500)

    project = Project.find_by_id(collaboration["project_id"])
    ws_service.emit_request_accepted(
        collaboration["founder_id"],
        {
            "collaboration_id": collaboration_id,
            "project_id": collaboration["project_id"],
            "project_title": project["title"],
            "candidate_name": current_user["name"],
            "candidate_id": current_user["_id"],
            "status": "accepted",
        },
    )
    ws_service.emit_request_accepted(
        current_user["_id"],
        {
            "collaboration_id": collaboration_id,
            "project_id": collaboration["project_id"],
            "project_title": project["title"],
            "status": "accepted",
        },
    )

    return api_success(
        {"collaboration_id": collaboration_id, "project": project},
        message="Request accepted successfully",
    )


@collaboration_bp.route("/reject/<collaboration_id>", methods=["POST"])
@token_required
def reject_request(current_user, collaboration_id):
    collaboration = Collaboration.find_by_id(collaboration_id)
    if not collaboration:
        return api_error("COLLABORATION_NOT_FOUND", "Collaboration request not found", 404)
    if collaboration["candidate_id"] != current_user["_id"]:
        return unauthorized_error("Unauthorized")
    if collaboration["status"] != "pending":
        return api_error("INVALID_STATUS", "Request already processed", 400, {"status": collaboration["status"]})

    success = Collaboration.reject_request(collaboration_id)
    if not success:
        return api_error("REJECT_FAILED", "Failed to reject request", 500)

    project = Project.find_by_id(collaboration["project_id"])
    ws_service.emit_request_rejected(
        collaboration["founder_id"],
        {
            "collaboration_id": collaboration_id,
            "project_id": collaboration["project_id"],
            "project_title": project["title"],
            "candidate_name": current_user["name"],
            "status": "rejected",
        },
    )
    return api_success({}, message="Request rejected successfully")


@collaboration_bp.route("/team/<project_id>", methods=["GET"])
@token_required
def get_team_members(current_user, project_id):
    project = Project.find_by_id(project_id)
    if not project:
        return api_error("PROJECT_NOT_FOUND", "Project not found", 404)
    if not has_project_access(project, current_user["_id"]):
        return unauthorized_error("Unauthorized")

    collaborations = Collaboration.get_team_members(project_id)
    team_members = []
    for collab in collaborations:
        member = User.find_by_id(collab["candidate_id"])
        if member:
            team_members.append(
                {
                    "collaboration_id": collab["_id"],
                    "user_id": member["_id"],
                    "name": member["name"],
                    "email": member["email"],
                    "bio": member.get("bio", ""),
                    "skills": member.get("skills", []),
                    "professional_title": member.get("professional_title", ""),
                    "joined_at": collab.get("accepted_at"),
                }
            )

    founder = User.find_by_id(project["founder_id"])
    founder_info = {
        "collaboration_id": None,
        "user_id": founder["_id"],
        "name": founder["name"],
        "email": founder["email"],
        "bio": founder.get("bio", ""),
        "skills": founder.get("skills", []),
        "professional_title": founder.get("professional_title", ""),
        "is_founder": True,
        "joined_at": project["created_at"],
    }

    return api_success({"project": project, "founder": founder_info, "team_members": team_members}, message="Team fetched")


@collaboration_bp.route("/leave/<collaboration_id>", methods=["POST"])
@token_required
def leave_project(current_user, collaboration_id):
    collaboration = Collaboration.find_by_id(collaboration_id)
    if not collaboration:
        return api_error("COLLABORATION_NOT_FOUND", "Collaboration not found", 404)
    if collaboration["candidate_id"] != current_user["_id"]:
        return unauthorized_error("Unauthorized")
    if collaboration["status"] != "accepted":
        return api_error("INVALID_STATUS", "You are not part of this project", 400)

    success = Collaboration.leave_project(collaboration_id)
    if not success:
        return api_error("LEAVE_FAILED", "Failed to leave project", 500)

    project = Project.find_by_id(collaboration["project_id"])
    ws_service.emit_member_left(
        collaboration["project_id"],
        {
            "project_id": collaboration["project_id"],
            "project_title": project["title"],
            "member_name": current_user["name"],
            "member_id": current_user["_id"],
        },
    )
    return api_success({}, message="Successfully left the project")


@collaboration_bp.route("/remove-member", methods=["POST"])
@token_required
def remove_member(current_user):
    data = request.get_json(silent=True) or {}
    validation = validate_required_fields(data, ["collaboration_id"])
    if not validation["is_valid"]:
        return api_error("VALIDATION_ERROR", "collaboration_id is required", 400)

    collaboration_id = data.get("collaboration_id")
    collaboration = Collaboration.find_by_id(collaboration_id)
    if not collaboration:
        return api_error("COLLABORATION_NOT_FOUND", "Collaboration not found", 404)

    project = Project.find_by_id(collaboration["project_id"])
    if not project:
        return api_error("PROJECT_NOT_FOUND", "Project not found", 404)
    if not require_founder(project, current_user["_id"]):
        return unauthorized_error("Only the founder can remove members")
    if collaboration["status"] != "accepted":
        return api_error("INVALID_STATUS", "Member is not active in this project", 400)

    success = Collaboration.leave_project(collaboration_id)
    if not success:
        return api_error("REMOVE_MEMBER_FAILED", "Failed to remove member", 500)

    removed_user = User.find_by_id(collaboration["candidate_id"])
    ws_service.emit_member_left(
        collaboration["project_id"],
        {
            "project_id": collaboration["project_id"],
            "project_title": project["title"],
            "member_name": removed_user["name"] if removed_user else "Member",
            "member_id": collaboration["candidate_id"],
            "removed_by_founder": True,
        },
    )

    if removed_user:
        ws_service.emit_collaboration_request(
            collaboration["candidate_id"],
            {
                "type": "removed_from_project",
                "project_id": collaboration["project_id"],
                "project_title": project["title"],
                "message": f"You have been removed from {project['title']} by the founder.",
            },
        )

    return api_success({}, message="Member removed successfully")


@collaboration_bp.route("/my-projects", methods=["GET"])
@token_required
def get_my_projects(current_user):
    collaborations = Collaboration.get_user_projects(current_user["_id"])
    projects = []
    for collab in collaborations:
        project = Project.find_by_id(collab["project_id"])
        if project:
            founder = User.find_by_id(project["founder_id"])
            projects.append(
                {
                    "collaboration_id": collab["_id"],
                    "project": project,
                    "founder": {"id": founder["_id"], "name": founder["name"], "email": founder["email"]},
                    "joined_at": collab.get("accepted_at"),
                }
            )

    return api_success({"projects": projects}, message="Member projects fetched")
