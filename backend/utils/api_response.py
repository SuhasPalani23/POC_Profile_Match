from typing import Any, Dict, Optional
from flask import jsonify

def api_success(data: Optional[Dict[str, Any]] = None, message: str = "ok", code: str = "OK", status: int = 200):
    payload = {
        "ok": True,
        "code": code,
        "message": message,
        "details": data or {}
    }
    return jsonify(payload), status


def api_error(code: str, message: str, status: int, details: Optional[Dict[str, Any]] = None):
    payload = {
        "ok": False,
        "code": code,
        "message": message,
        "details": details or {}
    }
    return jsonify(payload), status


def validation_error(message: str = "Validation failed", details: Optional[Dict[str, Any]] = None):
    return api_error("VALIDATION_ERROR", message, 400, details or {})


def unauthorized_error(message: str = "Unauthorized", details: Optional[Dict[str, Any]] = None):
    return api_error("UNAUTHORIZED", message, 403, details or {})


def not_found_error(resource: str, details: Optional[Dict[str, Any]] = None):
    return api_error("NOT_FOUND", f"{resource} not found", 404, details or {})
