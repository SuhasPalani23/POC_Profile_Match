from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from routes.auth import auth_bp
from routes.projects import projects_bp
from routes.matching import matching_bp
from routes.profile import profile_bp
from routes.collaboration import collaboration_bp
from routes.chat import chat_bp
from services.websocket_service import WebSocketService

app = Flask(__name__)
app.config.from_object(Config)

# Configure CORS
CORS(app, resources={
    r"/api/*": {
        "origins": [Config.FRONTEND_URL],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Initialize WebSocket
socketio = WebSocketService.init_app(app)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(projects_bp, url_prefix='/api/projects')
app.register_blueprint(matching_bp, url_prefix='/api/matching')
app.register_blueprint(profile_bp, url_prefix='/api/profile')
app.register_blueprint(collaboration_bp, url_prefix='/api/collaboration')
app.register_blueprint(chat_bp, url_prefix='/api/chat')

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy", 
        "message": "Founding Mindset Portal API",
        "websocket_enabled": True
    }), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Use socketio.run instead of app.run for WebSocket support
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)