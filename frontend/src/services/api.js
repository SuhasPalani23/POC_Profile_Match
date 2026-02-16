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

export default api;