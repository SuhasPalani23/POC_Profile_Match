from flask_socketio import SocketIO, emit, join_room, leave_room
from functools import wraps
import jwt
from config import Config

socketio = SocketIO(cors_allowed_origins="*")

def token_required_ws(f):
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

def _dm_room_key(user_a, user_b):
    return '_'.join(sorted([str(user_a), str(user_b)]))

class WebSocketService:
    @staticmethod
    def init_app(app):
        socketio.init_app(app,
                         cors_allowed_origins="*",
                         async_mode='threading',
                         logger=True,
                         engineio_logger=True)
        WebSocketService._register_handlers()
        return socketio
    
    @staticmethod
    def _register_handlers():
        @socketio.on('connect')
        def handle_connect(auth):
            try:
                token = auth.get('token') if auth else None
                if not token:
                    return False
                data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
                user_id = data['user_id']
                join_room(f'user_{user_id}')
                emit('connected', {'message': 'Connected successfully', 'user_id': user_id})
                print(f"User {user_id} connected")
                return True
            except Exception as e:
                print(f"Connection error: {e}")
                return False
        
        @socketio.on('disconnect')
        def handle_disconnect():
            print("Client disconnected")
        
        @socketio.on('join_project')
        @token_required_ws
        def handle_join_project(data, user_id=None):
            project_id = data.get('project_id')
            if project_id:
                join_room(f'project_{project_id}')
                emit('joined_project', {'project_id': project_id, 'message': 'Joined project room'})
        
        @socketio.on('leave_project')
        @token_required_ws
        def handle_leave_project(data, user_id=None):
            project_id = data.get('project_id')
            if project_id:
                leave_room(f'project_{project_id}')
                emit('left_project', {'project_id': project_id, 'message': 'Left project room'})
        
        @socketio.on('join_dm')
        @token_required_ws
        def handle_join_dm(data, user_id=None):
            """Join a DM room with another user"""
            other_user_id = data.get('other_user_id')
            if other_user_id and user_id:
                room = f'dm_{_dm_room_key(user_id, other_user_id)}'
                join_room(room)
                emit('joined_dm', {'room': room})
        
        @socketio.on('leave_dm')
        @token_required_ws
        def handle_leave_dm(data, user_id=None):
            other_user_id = data.get('other_user_id')
            if other_user_id and user_id:
                room = f'dm_{_dm_room_key(user_id, other_user_id)}'
                leave_room(room)
    
    @staticmethod
    def emit_profile_update(user_id, update_data):
        socketio.emit('profile_updated', update_data, room=f'user_{user_id}')
    
    @staticmethod
    def emit_vector_update(user_id, status):
        socketio.emit('vector_update', {'status': status, 'message': 'Profile vectors updated'}, room=f'user_{user_id}')
    
    @staticmethod
    def emit_project_status(project_id, status_data):
        socketio.emit('project_status_update', status_data, room=f'project_{project_id}')
    
    @staticmethod
    def emit_match_found(user_id, match_data):
        socketio.emit('new_match', match_data, room=f'user_{user_id}')
    
    @staticmethod
    def emit_collaboration_request(user_id, request_data):
        socketio.emit('collaboration_request', request_data, room=f'user_{user_id}')
    
    @staticmethod
    def emit_ats_score_update(user_id, score_data):
        socketio.emit('ats_score_updated', score_data, room=f'user_{user_id}')
    
    @staticmethod
    def emit_request_accepted(user_id, data):
        socketio.emit('request_accepted', data, room=f'user_{user_id}')
    
    @staticmethod
    def emit_request_rejected(user_id, data):
        socketio.emit('request_rejected', data, room=f'user_{user_id}')
    
    @staticmethod
    def emit_new_message(project_id_or_room, message_data):
        """Emit to either a project room or a DM room"""
        if project_id_or_room.startswith('dm_'):
            socketio.emit('new_message', message_data, room=project_id_or_room)
        else:
            socketio.emit('new_message', message_data, room=f'project_{project_id_or_room}')
    
    @staticmethod
    def emit_new_dm_notification(user_id, message_data):
        """Notify recipient of a new DM (for badge/sound even if not in DM view)"""
        socketio.emit('new_dm', message_data, room=f'user_{user_id}')
    
    @staticmethod
    def emit_member_left(project_id, data):
        socketio.emit('member_left', data, room=f'project_{project_id}')

ws_service = WebSocketService()