import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import { useAuthStore } from '../store/authStore';
import { Navigate, Link } from 'react-router-dom';
import { Clock, Eye, CheckCircle } from 'lucide-react';

export default function DashboardPage() {
  const [interactions, setInteractions] = useState([]);
  const [eventsMap, setEventsMap] = useState({});
  const [loading, setLoading] = useState(true);
  
  const { isAuthenticated, user } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) return;

    const fetchDashboardData = async () => {
      try {
        // 1. Fetch user's interactions
        const intResp = await apiClient.get('/interactions/me');
        const userInteractions = intResp.data || [];
        setInteractions(userInteractions);
        
        // 2. Fetch event details for these interactions
        // Extract unique event IDs
        const uniqueEventIds = [...new Set(userInteractions.map(i => i.event_id))];
        
        // In a real app we'd have a batch endpoint, but for MVP we do concurrent gets
        const eventPromises = uniqueEventIds.map(id => apiClient.get(`/events/${id}`).catch(() => null));
        const eventResponses = await Promise.all(eventPromises);
        
        const eMap = {};
        eventResponses.forEach(resp => {
          if (resp && resp.data) {
            eMap[resp.data.id] = resp.data;
          }
        });
        
        setEventsMap(eMap);
      } catch (err) {
        console.error('Failed to load dashboard data', err);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, [isAuthenticated]);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Group interactions by type
  const registrations = interactions.filter(i => i.interaction_type === 'register');
  const views = interactions.filter(i => i.interaction_type === 'view');

  return (
    <div className="dashboard-page" style={{ padding: '2rem 0' }}>
      <div style={{ marginBottom: '3rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '2rem' }}>
        <h1 style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>Dashboard</h1>
        <p style={{ color: 'var(--text-muted)' }}>Welcome back, {user?.full_name || user?.username}!</p>
      </div>

      {loading ? (
        <div className="loading-spinner">Loading your activity...</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '3rem' }}>
          
          {/* Registrations Section */}
          <section>
            <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem', color: 'var(--success)' }}>
              <CheckCircle /> My Tickets ({registrations.length})
            </h2>
            
            {registrations.length === 0 ? (
              <div style={{ padding: '2rem', background: 'var(--bg-card)', borderRadius: '12px', color: 'var(--text-muted)' }}>
                You haven't registered for any events yet. <Link to="/">Browse events</Link>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {registrations.map(interaction => {
                  const event = eventsMap[interaction.event_id];
                  if (!event) return null;
                  
                  return (
                    <div key={interaction.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1.5rem', background: 'var(--bg-card)', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
                      <div>
                        <h4 style={{ fontSize: '1.2rem', marginBottom: '0.25rem' }}>{event.title}</h4>
                        <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                          Registered on: {new Date(interaction.timestamp).toLocaleDateString()}
                        </div>
                      </div>
                      <Link to={`/events/${event.id}`} className="btn btn-outline">View Event</Link>
                    </div>
                  );
                })}
              </div>
            )}
          </section>

          {/* Recently Viewed Section */}
          <section>
            <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem' }}>
              <Clock /> Recently Viewed
            </h2>
            
            {views.length === 0 ? (
              <div style={{ color: 'var(--text-muted)' }}>No viewing history.</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {views.slice(0, 5).map(interaction => {
                  const event = eventsMap[interaction.event_id];
                  if (!event) return null;
                  
                  return (
                    <div key={interaction.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem', background: 'rgba(30, 41, 59, 0.5)', borderRadius: '8px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                        <Eye size={16} color="var(--text-muted)" />
                        <Link to={`/events/${event.id}`} style={{ color: 'var(--text-main)' }}>
                          {event.title}
                        </Link>
                      </div>
                      <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                        {new Date(interaction.timestamp).toLocaleDateString()}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </section>
          
        </div>
      )}
    </div>
  );
}
