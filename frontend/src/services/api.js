import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Auth APIs
export const authAPI = {
  signup: (data) => api.post('/auth/signup', data),
  login: (data) => api.post('/auth/login', data),
  getCurrentUser: () => api.get('/auth/me'),
};

// Project APIs
export const projectAPI = {
  create: (data) => api.post('/projects', data),
  getMyProjects: () => api.get('/projects/my-projects'),
  getProject: (id) => api.get(`/projects/${id}`),
  getLiveProjects: () => api.get('/projects/live'),
};

// Matching APIs
export const matchingAPI = {
  getMatches: (projectId) => api.get(`/matching/${projectId}`),
  sendRequest: (data) => api.post('/matching/send-request', data),
};

// Profile APIs
export const profileAPI = {
  getProfile: () => api.get('/profile/me'),
  updateProfile: (data) => api.put('/profile/update', data),
  uploadResume: (formData) => {
    const uploadApi = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    uploadApi.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );
    
    return uploadApi.post('/profile/upload-resume', formData);
  },
  deleteResume: () => api.delete('/profile/delete-resume'),
  analyzeResume: () => api.post('/profile/analyze-resume'),
  getATSScore: (projectId) => api.get(`/profile/ats-score/${projectId}`),
  getSkillsSuggestions: (data) => api.post('/profile/skills-suggestions', data),
};

// Collaboration APIs
export const collaborationAPI = {
  sendRequest: (data) => api.post('/collaboration/send-request', data),
  getMyRequests: () => api.get('/collaboration/my-requests'),
  acceptRequest: (collaborationId) => api.post(`/collaboration/accept/${collaborationId}`),
  rejectRequest: (collaborationId) => api.post(`/collaboration/reject/${collaborationId}`),
  getTeamMembers: (projectId) => api.get(`/collaboration/team/${projectId}`),
  leaveProject: (collaborationId) => api.post(`/collaboration/leave/${collaborationId}`),
  getMyProjects: () => api.get('/collaboration/my-projects'),
};

// Chat APIs
export const chatAPI = {
  sendMessage: (data) => api.post('/chat/send', data),
  getMessages: (projectId) => api.get(`/chat/messages/${projectId}`),
  markAsRead: (messageId) => api.post(`/chat/mark-read/${messageId}`),
  getUnreadCount: (projectId) => api.get(`/chat/unread-count/${projectId}`),
};

export default api;