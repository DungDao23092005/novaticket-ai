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
      const response = await apiClient.get('/users/me');
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
      // FastAPI OAuth2PasswordRequestForm expects x-www-form-urlencoded
      const formData = new URLSearchParams();
      formData.append('username', email); // OAuth2 expects 'username'
      formData.append('password', password);

      const response = await apiClient.post('/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
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
        full_name: fullName,
      });
      set({ isLoading: false });
      return true;
    } catch (error) {
      set({ 
        error: error.response?.data?.detail || 'Registration failed', 
        isLoading: false 
      });
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
