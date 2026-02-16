from flask_socketio import SocketIO, emit, join_room, leave_room
from functools import wraps
import jwt
from config import Config

socketio = SocketIO(cors_allowed_origins="*")

def token_required_ws(f):
    """Decorator for WebSocket authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = kwargs.get('token')
        if not token:
            return {'error': 'Authentication required'}, 401
        
        try:
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            kwargs['user_id'] = data['user_id']
            return f(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            return {'error': 'Token expired'}, 401
        except jwt.InvalidTokenError:
            return {'error': 'Invalid token'}, 401
    
    return decorated

class WebSocketService:
    """Service for managing WebSocket connections and events"""
    
    @staticmethod
    def init_app(app):
        """Initialize SocketIO with Flask app"""
        socketio.init_app(app, 
                         cors_allowed_origins="*",
                         async_mode='threading',
                         logger=True,
                         engineio_logger=True)
        
        # Register event handlers
        WebSocketService._register_handlers()
        
        return socketio
    
    @staticmethod
    def _register_handlers():
        """Register all WebSocket event handlers"""
        
        @socketio.on('connect')
        def handle_connect(auth):
            """Handle client connection"""
            try:
                token = auth.get('token') if auth else None
                if not token:
                    return False
                
                # Verify token
                data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
                user_id = data['user_id']
                
                # Join user's personal room
                join_room(f'user_{user_id}')
                
                emit('connected', {
                    'message': 'Connected successfully',
                    'user_id': user_id
                })
                
                print(f"User {user_id} connected")
                return True
                
            except Exception as e:
                print(f"Connection error: {e}")
                return False
        
        @socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            print("Client disconnected")
        
        @socketio.on('join_project')
        @token_required_ws
        def handle_join_project(data, user_id=None):
            """Join a project room for updates"""
            project_id = data.get('project_id')
            if project_id:
                join_room(f'project_{project_id}')
                emit('joined_project', {
                    'project_id': project_id,
                    'message': 'Joined project room'
                })
        
        @socketio.on('leave_project')
        @token_required_ws
        def handle_leave_project(data, user_id=None):
            """Leave a project room"""
            project_id = data.get('project_id')
            if project_id:
                leave_room(f'project_{project_id}')
                emit('left_project', {
                    'project_id': project_id,
                    'message': 'Left project room'
                })
    
    @staticmethod
    def emit_profile_update(user_id, update_data):
        """Emit profile update event to user"""
        socketio.emit('profile_updated', update_data, 
                     room=f'user_{user_id}')
    
    @staticmethod
    def emit_vector_update(user_id, status):
        """Emit vector update status to user"""
        socketio.emit('vector_update', {
            'status': status,
            'message': 'Profile vectors updated'
        }, room=f'user_{user_id}')
    
    @staticmethod
    def emit_project_status(project_id, status_data):
        """Emit project status update"""
        socketio.emit('project_status_update', status_data,
                     room=f'project_{project_id}')
    
    @staticmethod
    def emit_match_found(user_id, match_data):
        """Emit new match notification to user"""
        socketio.emit('new_match', match_data,
                     room=f'user_{user_id}')
    
    @staticmethod
    def emit_collaboration_request(user_id, request_data):
        """Emit collaboration request notification"""
        socketio.emit('collaboration_request', request_data,
                     room=f'user_{user_id}')
    
    @staticmethod
    def emit_ats_score_update(user_id, score_data):
        """Emit ATS score update to user"""
        socketio.emit('ats_score_updated', score_data,
                     room=f'user_{user_id}')
    
    @staticmethod
    def emit_request_accepted(user_id, data):
        """Emit when collaboration request is accepted"""
        socketio.emit('request_accepted', data,
                     room=f'user_{user_id}')
    
    @staticmethod
    def emit_request_rejected(user_id, data):
        """Emit when collaboration request is rejected"""
        socketio.emit('request_rejected', data,
                     room=f'user_{user_id}')
    
    @staticmethod
    def emit_new_message(project_id, message_data):
        """Emit new chat message to project room"""
        socketio.emit('new_message', message_data,
                     room=f'project_{project_id}')
    
    @staticmethod
    def emit_member_left(project_id, data):
        """Emit when a team member leaves the project"""
        socketio.emit('member_left', data,
                     room=f'project_{project_id}')

# Singleton instance
ws_service = WebSocketService()