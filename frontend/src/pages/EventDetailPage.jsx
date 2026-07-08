import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { apiClient } from '../api/client';
import { useAuthStore } from '../store/authStore';
import EventCard from '../components/EventCard';
import ReviewList from '../components/ReviewList';
import { Calendar, MapPin, Users, DollarSign, Tag, ArrowLeft, CheckCircle } from 'lucide-react';

export default function EventDetailPage() {
  const { id } = useParams();
  const { isAuthenticated, user } = useAuthStore();
  
  const [event, setEvent] = useState(null);
  const [similarEvents, setSimilarEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [registered, setRegistered] = useState(false);

  useEffect(() => {
    const fetchEventData = async () => {
      setLoading(true);
      setError(null);
      setRegistered(false);
      
      try {
        // 1. Fetch event details
        const response = await apiClient.get(`/events/${id}`);
        setEvent(response.data);
        
        // 2. Track "view" interaction if user is logged in
        if (isAuthenticated) {
          try {
            await apiClient.post('/interactions', {
              event_id: parseInt(id),
              interaction_type: 'view'
            });
            
            // Check if already registered
            // For MVP, we just fetch user interactions and check locally
            const interactionsResp = await apiClient.get('/interactions');
            const hasRegistered = interactionsResp.data.some(
              i => i.event_id === parseInt(id) && i.interaction_type === 'register'
            );
            setRegistered(hasRegistered);
          } catch (interactionErr) {
            console.error('Failed to track interaction', interactionErr);
          }
        }
        
        // 3. Fetch similar events
        try {
          const similarResp = await apiClient.get(`/recommendations/events/${id}/similar`);
          setSimilarEvents(similarResp.data || []);
        } catch (simErr) {
          console.warn('Failed to load similar events', simErr);
        }
        
      } catch (err) {
        setError('Event not found or failed to load.');
      } finally {
        setLoading(false);
      }
    };

    fetchEventData();
  }, [id, isAuthenticated]);

  const handleRegister = async () => {
    if (!isAuthenticated) {
      alert("Please log in to register for this event.");
      return;
    }
    
    try {
      await apiClient.post('/interactions', {
        event_id: parseInt(id),
        interaction_type: 'register'
      });
      setRegistered(true);
      alert("Successfully registered for the event!");
    } catch (err) {
      alert("Failed to register. Please try again.");
    }
  };

  if (loading) return <div className="loading-spinner">Loading event details...</div>;
  if (error || !event) return <div className="error-message">{error}</div>;

  const startDate = new Date(event.start_date).toLocaleString('en-US', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
    hour: '2-digit', minute: '2-digit'
  });

  return (
    <div className="event-detail-page">
      <Link to="/" className="back-link">
        <ArrowLeft size={16} /> Back to Events
      </Link>
      
      <div className="event-detail-header">
        <div className="category-badge large">{event.category_id}</div>
        <h1 className="event-detail-title">{event.title}</h1>
        
        <div className="event-detail-meta">
          <div className="meta-item"><Calendar size={18} /> {startDate}</div>
          <div className="meta-item"><MapPin size={18} /> {event.venue}, {event.city || 'Online'}</div>
          <div className="meta-item"><DollarSign size={18} /> {event.price === 0 ? 'Free' : event.price}</div>
          {event.capacity && <div className="meta-item"><Users size={18} /> Capacity: {event.capacity}</div>}
        </div>
      </div>
      
      <div className="event-detail-content">
        <div className="event-main-col">
          <h3>About This Event</h3>
          <p className="event-description">{event.description || "No description provided."}</p>
          
          {event.tags && (
            <div className="event-tags-large">
              <h4>Tags</h4>
              <div className="tags-list">
                {event.tags.split(',').map((tag, idx) => (
                  <span key={idx} className="tag-pill large">{tag.trim()}</span>
                ))}
              </div>
            </div>
          )}
        </div>
        
        <div className="event-sidebar">
          <div className="registration-card">
            <h3>Tickets</h3>
            <div className="price-tag">{event.price === 0 ? 'Free' : `$${event.price}`}</div>
            
            {registered ? (
              <div className="registered-success">
                <CheckCircle size={20} /> You are registered!
              </div>
            ) : (
              <button onClick={handleRegister} className="btn btn-primary btn-block large">
                Register Now
              </button>
            )}
            
            {!isAuthenticated && (
              <p className="auth-prompt">Log in to register and save this event.</p>
            )}
          </div>
        </div>
      </div>
      
      {/* Reviews Section */}
      <ReviewList eventId={id} />
      
      {/* Similar Events Section */}
      {similarEvents.length > 0 && (
        <div className="similar-events-section">
          <h3>You Might Also Like</h3>
          <div className="events-grid">
            {similarEvents.map(simEvent => (
              <EventCard key={simEvent.id} event={simEvent} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
