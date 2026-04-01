import { authAPI } from '../services/api';

export const setToken = (token) => {
  localStorage.setItem('token', token);
};

export const getToken = () => {
  return localStorage.getItem('token');
};

export const removeToken = () => {
  localStorage.removeItem('token');
};

export const getCurrentUser = async () => {
  try {
    const response = await authAPI.getCurrentUser();
    return response.data.user;
  } catch (error) {
    // Only remove token on auth errors (401/403), NOT on network/transient errors.
    // This prevents logout during page reloads (e.g. LinkedIn OAuth redirect).
    const status = error?.response?.status;
    if (status === 401 || status === 403) {
      removeToken();
    }
    throw error;
  }
};

export const isAuthenticated = () => {
  return !!getToken();
};