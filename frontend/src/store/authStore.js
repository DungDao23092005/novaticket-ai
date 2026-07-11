import { create } from 'zustand';
import { apiClient } from '../api/client';
import { setToken, removeToken, getToken } from '../utils/tokenHelper';

export const useAuthStore = create((set, get) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  isInitialized: false,

  // Initialize auth state on app startup
  initialize: async () => {
    const token = getToken();
    if (!token) {
      set({ isInitialized: true });
      return;
    }

    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.get('/auth/me');
      set({ user: response.data, isAuthenticated: true, isLoading: false, isInitialized: true });
    } catch (error) {
      // If 401, clear token
      if (error.response?.status === 401) {
        removeToken();
        set({ user: null, isAuthenticated: false, isLoading: false, isInitialized: true });
      } else {
        set({ error: error.message, isLoading: false, isInitialized: true });
      }
    }
  },

  // Action to fetch current user profile
  fetchUser: async () => {
    const token = getToken();
    if (!token) return;
    
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.get('/auth/me');
      set({ user: response.data, isAuthenticated: true, isLoading: false });
    } catch (error) {
      // If 401, clear token
      if (error.response?.status === 401) {
        removeToken();
        set({ user: null, isAuthenticated: false });
      }
      set({ error: error.message, isLoading: false });
    }
  },

  // Action to log in
  login: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.post('/auth/login', {
        email,
        password
      });
      
      const { access_token } = response.data;
      setToken(access_token);
      
      set({ isAuthenticated: true, isLoading: false });
      
      // Fetch user profile immediately after login
      await get().fetchUser();
      return true;
    } catch (error) {
      set({ 
        error: error.response?.data?.detail || 'Login failed', 
        isLoading: false 
      });
      return false;
    }
  },

  // Action to register
  register: async (email, username, password, fullName) => {
    set({ isLoading: true, error: null });
    try {
      await apiClient.post('/auth/register', {
        email,
        username,
        password,
        full_name: fullName || null,
      });
      set({ isLoading: false });
      return true;
    } catch (error) {
      let errorMsg = 'Registration failed';
      if (error.response?.data?.detail) {
        if (Array.isArray(error.response.data.detail)) {
          // FastAPI 422 Validation Error
          errorMsg = error.response.data.detail.map(err => `${err.loc[err.loc.length - 1]}: ${err.msg}`).join(', ');
        } else {
          errorMsg = error.response.data.detail;
        }
      }
      set({ error: errorMsg, isLoading: false });
      return false;
    }
  },

  // Action to logout
  logout: () => {
    removeToken();
    set({ user: null, isAuthenticated: false });
  },
  
  // Clear error
  clearError: () => set({ error: null })
}));
