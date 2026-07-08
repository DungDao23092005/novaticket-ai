import axios from 'axios';
import { getToken } from '../utils/tokenHelper';

// Create an Axios instance with base URL
export const apiClient = axios.create({
  baseURL: 'http://localhost:8000', // Our FastAPI backend
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
