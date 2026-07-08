import React, { useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import { useAuthStore } from './store/authStore';

// Layout
import MainLayout from './layouts/MainLayout';

// Pages
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import HomePage from './pages/HomePage';
import EventDetailPage from './pages/EventDetailPage';

// Placeholder Pages (will be implemented in later Parts)
const DashboardPage = () => <div><h1>Dashboard</h1></div>;
const RecommendationsPage = () => <div><h1>For You ✨</h1></div>;
const NotFoundPage = () => <div><h1>404 - Not Found</h1></div>;

function App() {
  const { fetchUser, isAuthenticated } = useAuthStore();

  // Try to load user profile if token exists on app mount
  useEffect(() => {
    if (isAuthenticated) {
      fetchUser();
    }
  }, [isAuthenticated, fetchUser]);

  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        <Route index element={<HomePage />} />
        <Route path="login" element={<LoginPage />} />
        <Route path="register" element={<RegisterPage />} />
        <Route path="events/:id" element={<EventDetailPage />} />
        
        {/* Protected Routes (we will add guards later) */}
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="recommendations" element={<RecommendationsPage />} />
        
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}

export default App;
