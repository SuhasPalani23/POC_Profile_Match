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
    removeToken();
    throw error;
  }
};

export const isAuthenticated = () => {
  return !!getToken();
};