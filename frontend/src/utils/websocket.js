import { useEffect, useRef, useState } from 'react';
import { io } from 'socket.io-client';
import { getToken } from './auth';

const SOCKET_URL = process.env.REACT_APP_API_URL?.replace('/api', '') || 'http://localhost:5001';

export const useWebSocket = () => {
  const socketRef = useRef(null);
  const [connected, setConnected] = useState(false);
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    const token = getToken();
    
    if (!token) {
      return;
    }

    // Initialize socket connection
    socketRef.current = io(SOCKET_URL, {
      auth: {
        token: token
      },
      transports: ['websocket', 'polling']
    });

    // Connection events
    socketRef.current.on('connect', () => {
      console.log('WebSocket connected');
      setConnected(true);
    });

    socketRef.current.on('connected', (data) => {
      console.log('Connected to server:', data);
    });

    socketRef.current.on('disconnect', () => {
      console.log('WebSocket disconnected');
      setConnected(false);
    });

    // Profile events
    socketRef.current.on('profile_updated', (data) => {
      console.log('Profile updated:', data);
      addNotification({
        type: 'success',
        message: 'Profile updated successfully',
        data: data
      });
    });

    socketRef.current.on('vector_update', (data) => {
      console.log('Vector update:', data);
      if (data.status === 'completed') {
        addNotification({
          type: 'success',
          message: 'Your profile has been re-indexed for better matching'
        });
      }
    });

    // Project events
    socketRef.current.on('project_status_update', (data) => {
      console.log('Project status update:', data);
      addNotification({
        type: 'info',
        message: `Project status: ${data.status}`,
        data: data
      });
    });

    // Match events
    socketRef.current.on('new_match', (data) => {
      console.log('New match found:', data);
      addNotification({
        type: 'success',
        message: 'New match found!',
        data: data
      });
    });

    socketRef.current.on('collaboration_request', (data) => {
      console.log('Collaboration request:', data);
      addNotification({
        type: 'info',
        message: 'New collaboration request received',
        data: data
      });
    });

    socketRef.current.on('ats_score_updated', (data) => {
      console.log('ATS score updated:', data);
      addNotification({
        type: 'info',
        message: 'ATS score calculated',
        data: data
      });
    });

    // Collaboration events
    socketRef.current.on('request_accepted', (data) => {
      console.log('Request accepted:', data);
      addNotification({
        type: 'success',
        message: data.status === 'accepted' 
          ? `${data.candidate_name || 'Candidate'} accepted your request for ${data.project_title}!`
          : `You joined ${data.project_title}!`,
        data: data
      });
    });

    socketRef.current.on('request_rejected', (data) => {
      console.log('Request rejected:', data);
      addNotification({
        type: 'info',
        message: `${data.candidate_name} declined your request for ${data.project_title}`,
        data: data
      });
    });

    socketRef.current.on('member_left', (data) => {
      console.log('Member left:', data);
      addNotification({
        type: 'info',
        message: `${data.member_name} left ${data.project_title}`,
        data: data
      });
    });

    // Chat events
    socketRef.current.on('new_message', (data) => {
      console.log('New message:', data);
      // Message is handled in LiveChat component
    });

    // Cleanup on unmount
    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, []);

  const addNotification = (notification) => {
    setNotifications(prev => [...prev, { ...notification, id: Date.now() }]);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== notification.id));
    }, 5000);
  };

  const joinProject = (projectId) => {
    if (socketRef.current && connected) {
      socketRef.current.emit('join_project', { project_id: projectId });
    }
  };

  const leaveProject = (projectId) => {
    if (socketRef.current && connected) {
      socketRef.current.emit('leave_project', { project_id: projectId });
    }
  };

  const clearNotifications = () => {
    setNotifications([]);
  };

  return {
    socket: socketRef.current,
    connected,
    notifications,
    joinProject,
    leaveProject,
    clearNotifications
  };
};