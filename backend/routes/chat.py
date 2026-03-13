from datetime import datetime

from flask import Blueprint, request

from models.message import Message
from models.project import Project
from routes.auth import token_required
from services.websocket_service import ws_service
from utils.api_response import api_error, api_success, unauthorized_error
from utils.authz import has_project_access
from utils.validation import validate_required_fields

chat_bp = Blueprint("chat", __name__)


def _parse_pagination():
    before_raw = request.args.get("before")
    limit_raw = request.args.get("limit", "50")

    try:
        limit = max(1, min(200, int(limit_raw)))
    except ValueError:
        limit = 50

    before = None
    if before_raw:
        try:
            before = datetime.fromisoformat(before_raw.replace("Z", "+00:00"))
        except ValueError:
            before = None
    return before, limit


def _dm_room_key(user_a, user_b):
    return "_".join(sorted([str(user_a), str(user_b)]))


@chat_bp.route("/send", methods=["POST"])
@token_required
def send_message(current_user):
    data = request.get_json(silent=True) or {}
    validation = validate_required_fields(data, ["project_id", "message"])
    if not validation["is_valid"]:
        return api_error(
            "VALIDATION_ERROR",
            "Project ID and message are required",
            400,
            {"missing_fields": validation["missing_fields"]},
        )

    project_id = data.get("project_id")
    message_text = data.get("message")
    dm_recipient_id = data.get("dm_recipient_id")
    client_message_id = data.get("client_message_id")

    project = Project.find_by_id(project_id)
    if not project:
        return api_error("PROJECT_NOT_FOUND", "Project not found", 404)
    if not has_project_access(project, current_user["_id"]):
        return unauthorized_error("You must be a team member to send messages")

    message = Message.create(
        project_id=project_id,
        sender_id=current_user["_id"],
        sender_name=current_user["name"],
        message_text=message_text,
        dm_recipient_id=dm_recipient_id,
    )

    payload = {
        "message_id": message["_id"],
        "client_message_id": client_message_id,
        "project_id": project_id,
        "sender_id": message["sender_id"],
        "sender_name": message["sender_name"],
        "message": message["message"],
        "dm_recipient_id": dm_recipient_id,
        "created_at": message["created_at"].isoformat(),
    }

    if dm_recipient_id:
        room = f"dm_{_dm_room_key(current_user['_id'], dm_recipient_id)}"
        ws_service.emit_new_message(room, payload)
        ws_service.emit_new_dm_notification(dm_recipient_id, payload)
    else:
        ws_service.emit_new_message(project_id, payload)

    return api_success({"message": message, "client_message_id": client_message_id}, message="Message sent successfully")


@chat_bp.route("/messages/<project_id>", methods=["GET"])
@token_required
def get_messages(current_user, project_id):
    project = Project.find_by_id(project_id)
    if not project:
        return api_error("PROJECT_NOT_FOUND", "Project not found", 404)
    if not has_project_access(project, current_user["_id"]):
        return unauthorized_error("You must be a team member to view messages")

    before, limit = _parse_pagination()
    messages = Message.get_project_messages(project_id, limit=limit, before=before)
    next_before = messages[0]["created_at"].isoformat() if messages else None
    return api_success(
        {"project_id": project_id, "messages": messages, "paging": {"limit": limit, "next_before": next_before}},
        message="Messages fetched",
    )


@chat_bp.route("/dm/<project_id>/<other_user_id>", methods=["GET"])
@token_required
def get_dm_messages(current_user, project_id, other_user_id):
    project = Project.find_by_id(project_id)
    if not project:
        return api_error("PROJECT_NOT_FOUND", "Project not found", 404)
    if not has_project_access(project, current_user["_id"]):
        return unauthorized_error("Unauthorized")

    before, limit = _parse_pagination()
    messages = Message.get_dm_messages(project_id, current_user["_id"], other_user_id, limit=limit, before=before)
    next_before = messages[0]["created_at"].isoformat() if messages else None
    return api_success({"messages": messages, "paging": {"limit": limit, "next_before": next_before}}, message="DM messages fetched")


@chat_bp.route("/mark-read/<message_id>", methods=["POST"])
@token_required
def mark_message_read(current_user, message_id):
    success = Message.mark_as_read(message_id, current_user["_id"])
    if not success:
        return api_error("MARK_READ_FAILED", "Failed to mark message as read", 500)
    return api_success({}, message="Message marked as read")


@chat_bp.route("/unread-count/<project_id>", methods=["GET"])
@token_required
def get_unread_count(current_user, project_id):
    breakdown = Message.get_unread_breakdown(project_id, current_user["_id"])
    total = breakdown["group"] + sum(breakdown["dms"].values())
    return api_success(
        {"project_id": project_id, "unread_count": total, "threads": breakdown},
        message="Unread counts fetched",
    )
