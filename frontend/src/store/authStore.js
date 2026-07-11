import { create } from 'zustand';
import { apiClient } from '../api/client';
import { setToken, removeToken, isAuthenticated } from '../utils/tokenHelper';

export const useAuthStore = create((set, get) => ({
  user: null,
  isAuthenticated: isAuthenticated(),
  isLoading: false,
  error: null,

  // Action to fetch current user profile
  fetchUser: async () => {
    if (!get().isAuthenticated) return;
    
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
