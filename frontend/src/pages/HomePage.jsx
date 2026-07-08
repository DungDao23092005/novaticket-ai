import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import EventCard from '../components/EventCard';
import { Search } from 'lucide-react';

export default function HomePage() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        // Fetch up to 50 events for now
        const response = await apiClient.get('/events?page=1&page_size=50');
        setEvents(response.data.items || []);
      } catch (err) {
        setError('Failed to load events. Please ensure backend is running.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchEvents();
  }, []);

  // Simple client-side filtering for search
  const filteredEvents = events.filter(e => 
    e.title.toLowerCase().includes(searchTerm.toLowerCase()) || 
    (e.tags && e.tags.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="home-page">
      <div className="hero-section">
        <h1 className="hero-title">Discover Amazing Events</h1>
        <p className="hero-subtitle">Book tickets for the best concerts, tech conferences, and workshops in town.</p>
        
        <div className="search-bar">
          <Search className="search-icon" size={20} />
          <input 
            type="text" 
            placeholder="Search events by title or tags..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      <div className="events-container">
        <h2>Upcoming Events</h2>
        
        {loading && <div className="loading-spinner">Loading amazing experiences...</div>}
        
        {error && <div className="error-message">{error}</div>}
        
        {!loading && !error && filteredEvents.length === 0 && (
          <div className="empty-state">No events found matching your search.</div>
        )}
        
        {!loading && !error && filteredEvents.length > 0 && (
          <div className="events-grid">
            {filteredEvents.map(event => (
              <EventCard key={event.id} event={event} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
