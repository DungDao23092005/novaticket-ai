import React, { useState } from 'react';
import { apiClient } from '../api/client';
import { Star } from 'lucide-react';

export default function ReviewForm({ eventId, onReviewSubmitted }) {
  const [rating, setRating] = useState(5);
  const [reviewText, setReviewText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!reviewText.trim()) return;

    if (reviewText.trim().length < 10) {
      setError('Review must be at least 10 characters long.');
      return;
    }

    setSubmitting(true);
    setError(null);
    
    try {
      const response = await apiClient.post('/reviews/', {
        event_id: parseInt(eventId),
        rating: rating,
        content: reviewText
      });
      
      setReviewText('');
      setRating(5);
      
      // Trigger refresh in parent component
      if (onReviewSubmitted) {
        onReviewSubmitted(response.data);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit review. You might have already reviewed this event.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="review-form-container">
      <h4>Write a Review</h4>
      
      {error && <div className="auth-error" style={{ padding: '0.5rem', marginBottom: '1rem' }}>{error}</div>}
      
      <form onSubmit={handleSubmit}>
        <div className="rating-selector">
          <span>Rating: </span>
          <div className="stars-input">
            {[1, 2, 3, 4, 5].map((star) => (
              <Star 
                key={star} 
                size={24} 
                onClick={() => setRating(star)}
                className={star <= rating ? 'star-filled' : 'star-empty'}
                style={{ cursor: 'pointer', transition: 'color 0.2s' }}
              />
            ))}
          </div>
        </div>
        
        <div className="form-group" style={{ marginTop: '1rem' }}>
          <textarea 
            rows="4" 
            placeholder="Share your experience (Our AI will analyze your sentiment!)"
            value={reviewText}
            onChange={(e) => setReviewText(e.target.value)}
            required
            style={{ 
              width: '100%', 
              padding: '1rem', 
              borderRadius: '8px',
              backgroundColor: 'rgba(15, 23, 42, 0.5)',
              border: '1px solid var(--border-color)',
              color: 'var(--text-main)',
              fontFamily: 'inherit',
              resize: 'vertical'
            }}
          />
        </div>
        
        <button 
          type="submit" 
          className="btn btn-primary" 
          disabled={submitting || !reviewText.trim()}
          style={{ marginTop: '1rem' }}
        >
          {submitting ? 'Analyzing & Submitting...' : 'Submit Review'}
        </button>
      </form>
    </div>
  );
}
