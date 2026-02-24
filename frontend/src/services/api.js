import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT to every request
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ----------------------------------------------------------------
// Auth
// ----------------------------------------------------------------
export const authAPI = {
  signup: (data) => api.post('/auth/signup', data),
  login: (data) => api.post('/auth/login', data),
  getCurrentUser: () => api.get('/auth/me'),
};

// ----------------------------------------------------------------
// Projects
// ----------------------------------------------------------------
export const projectAPI = {
  create: (data) => api.post('/projects', data),
  getMyProjects: () => api.get('/projects/my-projects'),
  getProject: (id) => api.get(`/projects/${id}`),
  getLiveProjects: () => api.get('/projects/live'),
};

// ----------------------------------------------------------------
// Matching
// ----------------------------------------------------------------
export const matchingAPI = {
  getMatches: (projectId) => api.get(`/matching/${projectId}`),
  sendRequest: (data) => api.post('/matching/send-request', data),
};

// ----------------------------------------------------------------
// Profile
// ----------------------------------------------------------------
export const profileAPI = {
  getProfile: () => api.get('/profile/me'),

  updateProfile: (data) => api.put('/profile/update', data),

  // Resume upload — multipart form, file stored in MongoDB GridFS
  uploadResume: (formData) => {
    const token = localStorage.getItem('token');
    return axios.post(`${API_BASE_URL}/profile/upload-resume`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        Authorization: `Bearer ${token}`,
      },
    });
  },

  /**
   * Download a user's resume directly from GridFS via the backend.
   * Works for any developer — the file lives in MongoDB, not on local disk.
   *
   * @param {string} userId - the user whose resume to download
   */
  getResume: (userId) =>
    api.get(`/profile/resume/${userId}`, { responseType: 'blob' }),

  deleteResume: () => api.delete('/profile/delete-resume'),

  analyzeResume: () => api.post('/profile/analyze-resume'),

  getATSScore: (projectId) => api.get(`/profile/ats-score/${projectId}`),

  getSkillsSuggestions: (data) => api.post('/profile/skills-suggestions', data),
};

// ----------------------------------------------------------------
// Collaboration
// ----------------------------------------------------------------
export const collaborationAPI = {
  sendRequest: (data) => api.post('/collaboration/send-request', data),
  getMyRequests: () => api.get('/collaboration/my-requests'),
  getSentRequestsForProject: (projectId) =>
    api.get(`/collaboration/sent-requests/${projectId}`),
  acceptRequest: (collaborationId) =>
    api.post(`/collaboration/accept/${collaborationId}`),
  rejectRequest: (collaborationId) =>
    api.post(`/collaboration/reject/${collaborationId}`),
  getTeamMembers: (projectId) => api.get(`/collaboration/team/${projectId}`),
  leaveProject: (collaborationId) =>
    api.post(`/collaboration/leave/${collaborationId}`),
  getMyProjects: () => api.get('/collaboration/my-projects'),
};

// ----------------------------------------------------------------
// Chat
// ----------------------------------------------------------------
export const chatAPI = {
  sendMessage: (data) => api.post('/chat/send', data),
  getMessages: (projectId) => api.get(`/chat/messages/${projectId}`),
  markAsRead: (messageId) => api.post(`/chat/mark-read/${messageId}`),
  getUnreadCount: (projectId) => api.get(`/chat/unread-count/${projectId}`),
};

export default api;
