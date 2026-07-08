import React from 'react';
import { Link } from 'react-router-dom';
import { Calendar, MapPin, Tag } from 'lucide-react';

export default function EventCard({ event }) {
  // Format the date nicely
  const startDate = new Date(event.start_date).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });

  return (
    <Link to={`/events/${event.id}`} className="event-card-link">
      <div className="event-card">
        <div className="event-card-header">
          <span className="category-badge">{event.category_id}</span>
          <h3 className="event-title">{event.title}</h3>
        </div>
        
        <div className="event-card-body">
          <div className="event-meta">
            <Calendar size={16} />
            <span>{startDate}</span>
          </div>
          
          <div className="event-meta">
            <MapPin size={16} />
            <span>{event.city || 'Online'}</span>
          </div>
          
          {event.tags && (
            <div className="event-tags">
              <Tag size={14} />
              <div className="tags-list">
                {event.tags.split(',').slice(0, 3).map((tag, idx) => (
                  <span key={idx} className="tag-pill">{tag.trim()}</span>
                ))}
              </div>
            </div>
          )}
        </div>
        
        <div className="event-card-footer">
          <div className="event-price">
            {event.price === 0 ? 'Free' : `$${event.price}`}
          </div>
          <div className="view-details">View Details →</div>
        </div>
      </div>
    </Link>
  );
}
