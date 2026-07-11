import axios from 'axios';
import { getToken } from '../utils/tokenHelper';

// Create an Axios instance with base URL
// Use relative URL for Docker compatibility, or env variable for flexibility
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL, // Empty string = relative to current origin (works in Docker)
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT token
apiClient.interceptors.request.use(
  (config) => {
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle global errors (e.g., 401 Unauthorized)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Token might be expired or invalid
      // Let the auth store handle the state, but we can log it here
      console.warn('Unauthorized request. Token may be expired.');
    }
    return Promise.reject(error);
  }
);
