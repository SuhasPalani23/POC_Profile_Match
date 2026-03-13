import { useEffect, useRef, useState, useCallback } from 'react';
import { io } from 'socket.io-client';
import { getToken } from './auth';

const SOCKET_URL = process.env.REACT_APP_API_URL?.replace('/api', '') || 'http://localhost:5001';

export const useWebSocket = () => {
  const socketRef = useRef(null);
  const [connected, setConnected] = useState(false);
  const [notifications, setNotifications] = useState([]);

  // Stable ref so callbacks inside useEffect never capture stale state
  const notificationTimers = useRef({});

  const addNotification = useCallback((notification) => {
    // Generate id synchronously BEFORE the setTimeout so the closure captures it correctly
    const id = Date.now() + Math.random();
    const fullNotification = { ...notification, id };

    setNotifications(prev => [...prev, fullNotification]);

    // id is now captured correctly in this closure
    const timer = setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id));
      delete notificationTimers.current[id];
    }, 5000);

    notificationTimers.current[id] = timer;
  }, []);

  useEffect(() => {
    const token = getToken();
    if (!token) return;

    const socket = io(SOCKET_URL, {
      auth: { token },
      transports: ['websocket', 'polling'],
    });
    socketRef.current = socket;

    socket.on('connect', () => {
      console.log('WebSocket connected');
      setConnected(true);
    });

    socket.on('connected', (data) => {
      console.log('Connected to server:', data);
    });

    socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
      setConnected(false);
    });

    socket.on('profile_updated', (data) => {
      addNotification({ type: 'success', message: 'Profile updated successfully', data });
    });

    socket.on('vector_update', (data) => {
      if (data.status === 'completed') {
        addNotification({ type: 'success', message: 'Your profile has been re-indexed for better matching' });
      }
    });

    socket.on('project_status_update', (data) => {
      addNotification({ type: 'info', message: `Project status: ${data.status}`, data });
    });

    socket.on('new_match', (data) => {
      addNotification({ type: 'success', message: 'New match found!', data });
    });

    socket.on('collaboration_request', (data) => {
      addNotification({ type: 'info', message: 'New collaboration request received', data });
    });

    socket.on('ats_score_updated', (data) => {
      addNotification({ type: 'info', message: 'ATS score calculated', data });
    });

    socket.on('request_accepted', (data) => {
      addNotification({
        type: 'success',
        message: data.candidate_name
          ? `${data.candidate_name} accepted your request for ${data.project_title}!`
          : `You joined ${data.project_title}!`,
        data,
      });
    });

    socket.on('request_rejected', (data) => {
      addNotification({
        type: 'info',
        message: `${data.candidate_name} declined your request for ${data.project_title}`,
        data,
      });
    });

    socket.on('member_left', (data) => {
      addNotification({ type: 'info', message: `${data.member_name} left ${data.project_title}`, data });
    });

    // Chat messages are handled in LiveChat — no notification needed here
    socket.on('new_message', () => {});

    return () => {
      socket.disconnect();
      // Clear all pending notification timers on unmount
      Object.values(notificationTimers.current).forEach(clearTimeout);
      notificationTimers.current = {};
    };
  }, [addNotification]);

  // --- Project room helpers ---
  // These use the socket ref directly so they always have the live socket,
  // and we gate on socket.connected (the socket's own property) rather than
  // the React `connected` state, which can be stale.
  const joinProject = useCallback((projectId) => {
    const socket = socketRef.current;
    if (socket?.connected) {
      socket.emit('join_project', { project_id: projectId, token: getToken() });
    } else if (socket) {
      // Socket exists but not yet connected — wait for the connect event
      socket.once('connect', () => {
        socket.emit('join_project', { project_id: projectId, token: getToken() });
      });
    }
  }, []);

  const leaveProject = useCallback((projectId) => {
    const socket = socketRef.current;
    if (socket?.connected) {
      socket.emit('leave_project', { project_id: projectId, token: getToken() });
    }
  }, []);

  const clearNotifications = useCallback(() => {
    setNotifications([]);
    Object.values(notificationTimers.current).forEach(clearTimeout);
    notificationTimers.current = {};
  }, []);

  return {
    socket: socketRef.current,
    connected,
    notifications,
    joinProject,
    leaveProject,
    clearNotifications,
  };
};