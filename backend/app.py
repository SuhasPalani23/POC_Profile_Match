from flask import Flask, request
from flask_cors import CORS
from pymongo import MongoClient
from pinecone import Pinecone
from werkzeug.exceptions import HTTPException

from config import Config
from routes.auth import auth_bp
from routes.projects import projects_bp
from routes.matching import matching_bp
from routes.profile import profile_bp
from routes.collaboration import collaboration_bp
from routes.chat import chat_bp
from services.websocket_service import WebSocketService
from utils.api_response import api_error, api_success
from utils.rate_limit import InMemoryRateLimiter


rate_limiter = InMemoryRateLimiter()


def _client_ip() -> str:
    return request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",")[0].strip()


def _check_mongo() -> tuple[bool, str]:
    try:
        client = MongoClient(Config.MONGODB_URI, serverSelectionTimeoutMS=2000)
        client.admin.command("ping")
        return True, "ok"
    except Exception as exc:
        return False, str(exc)


def _check_pinecone() -> tuple[bool, str]:
    try:
        if not Config.PINECONE_API_KEY:
            return False, "PINECONE_API_KEY missing"
        pc = Pinecone(api_key=Config.PINECONE_API_KEY)
        _ = pc.list_indexes()
        return True, "ok"
    except Exception as exc:
        return False, str(exc)


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": Config.FRONTEND_URLS,
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
            }
        },
    )

    @app.before_request
    def apply_limits():
        max_content = app.config.get("MAX_CONTENT_LENGTH", 10 * 1024 * 1024)
        request_max = request.content_length or 0
        if request_max > max_content:
            return api_error(
                "REQUEST_TOO_LARGE",
                "Request body exceeds allowed size",
                413,
                {"max_bytes": max_content, "received_bytes": request_max},
            )

        path = request.path or ""
        ip = _client_ip()
        if path.startswith("/api/auth/"):
            allowed = rate_limiter.is_allowed(
                key=f"auth:{ip}",
                max_requests=Config.RATE_LIMIT_AUTH_MAX_REQUESTS,
                window_seconds=Config.RATE_LIMIT_AUTH_WINDOW_SECONDS,
            )
            if not allowed:
                return api_error("RATE_LIMITED", "Too many auth requests", 429, {"scope": "auth"})
        elif path.startswith("/api/"):
            allowed = rate_limiter.is_allowed(
                key=f"api:{ip}",
                max_requests=Config.RATE_LIMIT_MAX_REQUESTS,
                window_seconds=Config.RATE_LIMIT_WINDOW_SECONDS,
            )
            if not allowed:
                return api_error("RATE_LIMITED", "Too many requests", 429, {"scope": "api"})

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(projects_bp, url_prefix="/api/projects")
    app.register_blueprint(matching_bp, url_prefix="/api/matching")
    app.register_blueprint(profile_bp, url_prefix="/api/profile")
    app.register_blueprint(collaboration_bp, url_prefix="/api/collaboration")
    app.register_blueprint(chat_bp, url_prefix="/api/chat")

    @app.route("/api/health", methods=["GET"])
    def health_check():
        mongo_ok, _ = _check_mongo()
        return api_success(
            {
                "status": "healthy" if mongo_ok else "degraded",
                "services": {"mongo": mongo_ok},
                "websocket_enabled": True,
            },
            message="Founding Mindset Portal API",
        )

    @app.route("/api/ready", methods=["GET"])
    def readiness_check():
        mongo_ok, mongo_details = _check_mongo()
        pinecone_ok, pinecone_details = _check_pinecone()

        status = 200 if mongo_ok and pinecone_ok else 503
        return api_success(
            {
                "ready": mongo_ok and pinecone_ok,
                "services": {
                    "mongo": {"ok": mongo_ok, "details": mongo_details if not mongo_ok else "ok"},
                    "pinecone": {"ok": pinecone_ok, "details": pinecone_details if not pinecone_ok else "ok"},
                },
            },
            message="Readiness check",
            code="READY" if status == 200 else "NOT_READY",
            status=status,
        )

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return api_error(
            "HTTP_ERROR",
            error.description or "HTTP error",
            error.code or 500,
            {"name": error.name},
        )

    @app.errorhandler(Exception)
    def handle_internal_error(error):
        return api_error("INTERNAL_ERROR", "Internal server error", 500, {"error": str(error)})

    return app


app = create_app()
socketio = WebSocketService.init_app(app)


if __name__ == "__main__":
    socketio.run(app, debug=not Config.IS_PRODUCTION, host=Config.HOST, port=Config.PORT)
