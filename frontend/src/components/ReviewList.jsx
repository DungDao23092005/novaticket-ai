import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import { Star, MessageSquare } from 'lucide-react';
import ReviewForm from './ReviewForm';
import { useAuthStore } from '../store/authStore';

export default function ReviewList({ eventId }) {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const { isAuthenticated } = useAuthStore();

  const fetchReviews = async () => {
    try {
      const response = await apiClient.get(`/events/${eventId}/reviews`);
      setReviews(response.data || []);
    } catch (err) {
      console.error('Failed to load reviews', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReviews();
  }, [eventId]);

  const handleReviewAdded = (newReview) => {
    // Optimistically prepend the new review or re-fetch
    // Since backend might need a moment to run ML (though it's synchronous here),
    // re-fetching is safest to get the predicted_sentiment.
    fetchReviews();
  };

  const getSentimentBadge = (sentiment) => {
    if (!sentiment) return null;
    
    let colorClass = 'sentiment-neutral';
    let label = 'Neutral';
    
    if (sentiment.toLowerCase() === 'positive') {
      colorClass = 'sentiment-positive';
      label = 'Positive';
    } else if (sentiment.toLowerCase() === 'negative') {
      colorClass = 'sentiment-negative';
      label = 'Negative';
    }
    
    return (
      <span className={`sentiment-badge ${colorClass}`}>
        AI: {label}
      </span>
    );
  };

  if (loading) return <div>Loading reviews...</div>;

  return (
    <div className="reviews-section" style={{ marginTop: '3rem', paddingTop: '2rem', borderTop: '1px solid var(--border-color)' }}>
      <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <MessageSquare size={20} /> User Reviews
      </h3>
      
      {isAuthenticated ? (
        <ReviewForm eventId={eventId} onReviewSubmitted={handleReviewAdded} />
      ) : (
        <div className="auth-prompt" style={{ marginBottom: '2rem', padding: '1rem', background: 'rgba(30, 41, 59, 0.5)', borderRadius: '8px' }}>
          Please log in to leave a review.
        </div>
      )}
      
      <div className="reviews-list" style={{ marginTop: '2rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {reviews.length === 0 ? (
          <p style={{ color: 'var(--text-muted)' }}>No reviews yet. Be the first to review!</p>
        ) : (
          reviews.map(review => (
            <div key={review.id} className="review-card" style={{ padding: '1.5rem', background: 'var(--bg-card)', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
              <div className="review-header" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                <div className="review-user-info">
                  <div style={{ fontWeight: 'bold' }}>{review.user?.username || review.user?.full_name || `User #${review.user_id}`}</div>
                  <div className="stars-display" style={{ display: 'flex', marginTop: '0.25rem' }}>
                    {[1, 2, 3, 4, 5].map(star => (
                      <Star 
                        key={star} 
                        size={14} 
                        className={star <= review.rating ? 'star-filled' : 'star-empty'} 
                      />
                    ))}
                  </div>
                </div>
                <div>
                  {getSentimentBadge(review.sentiment_label)}
                </div>
              </div>
              <p className="review-text" style={{ color: 'var(--text-main)', lineHeight: '1.6' }}>
                {review.content}
              </p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
