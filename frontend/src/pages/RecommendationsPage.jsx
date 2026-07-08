import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import EventCard from '../components/EventCard';
import { Sparkles } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { Navigate } from 'react-router-dom';

export default function RecommendationsPage() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) return;

    const fetchRecommendations = async () => {
      try {
        const response = await apiClient.get('/recommendations/me?top_k=10');
        setEvents(response.data || []);
      } catch (err) {
        setError('Failed to load personalized recommendations.');
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [isAuthenticated]);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="recommendations-page">
      <div className="hero-section" style={{ padding: '3rem 1rem', background: 'radial-gradient(circle at center, rgba(236, 72, 153, 0.1) 0%, transparent 70%)' }}>
        <h1 className="hero-title" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '1rem', background: 'linear-gradient(135deg, #fff, var(--secondary))', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          <Sparkles color="#ec4899" /> For You ✨
        </h1>
        <p className="hero-subtitle">
          Events picked specifically for you based on your interactions and AI-powered Collaborative & Content-Based Filtering.
        </p>
      </div>

      <div className="events-container">
        {loading && <div className="loading-spinner">Analyzing your preferences...</div>}
        
        {error && <div className="error-message">{error}</div>}
        
        {!loading && !error && events.length === 0 && (
          <div className="empty-state" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
            We need more data! Try viewing or registering for some events first.
          </div>
        )}
        
        {!loading && !error && events.length > 0 && (
          <div className="events-grid">
            {events.map(event => (
              <EventCard key={event.id} event={event} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
