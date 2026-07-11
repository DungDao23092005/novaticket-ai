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
import DashboardPage from './pages/DashboardPage';
import RecommendationsPage from './pages/RecommendationsPage';

// Placeholder Pages (will be implemented in later Parts)
const NotFoundPage = () => <div><h1>404 - Not Found</h1></div>;

function App() {
  const { initialize, isInitialized } = useAuthStore();

  // Initialize auth state on app mount
  useEffect(() => {
    initialize();
  }, [initialize]);

  // Show loading while initializing
  if (!isInitialized) {
    return <div className="loading-spinner">Loading...</div>;
  }

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
