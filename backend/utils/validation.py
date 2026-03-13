from typing import Any, Dict, Iterable, Optional


def validate_required_fields(data: Optional[Dict[str, Any]], required_fields: Iterable[str]) -> Dict[str, Any]:
    payload = data or {}
    missing = [field for field in required_fields if payload.get(field) in (None, "", [])]
    return {
        "is_valid": len(missing) == 0,
        "missing_fields": missing,
        "payload": payload,
    }

