from typing import Optional

from models.collaboration import Collaboration


def has_project_access(project: dict, user_id: str) -> bool:
    if not project:
        return False
    if project.get("founder_id") == user_id:
        return True
    collab = Collaboration.check_existing(project.get("_id"), user_id)
    return bool(collab and collab.get("status") == "accepted")


def require_founder(project: dict, user_id: str) -> bool:
    return bool(project and project.get("founder_id") == user_id)


def require_candidate(collaboration: Optional[dict], user_id: str) -> bool:
    return bool(collaboration and collaboration.get("candidate_id") == user_id)
