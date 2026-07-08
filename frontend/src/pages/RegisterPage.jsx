import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

export default function RegisterPage() {
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  
  const { register, isAuthenticated, isLoading, error, clearError } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    // Clear errors
    clearError();
    
    // Redirect if already logged in
    if (isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate, clearError]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const success = await register(email, username, password, fullName);
    if (success) {
      // After successful registration, redirect to login page
      navigate('/login');
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Create an Account</h2>
        <p className="auth-subtitle">Join NovaTicket AI to get personalized event recommendations.</p>
        
        {error && <div className="auth-error">{error}</div>}
        
        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="email">Email address</label>
            <input 
              type="email" 
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required 
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input 
              type="text" 
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="johndoe"
              required 
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="fullName">Full Name</label>
            <input 
              type="text" 
              id="fullName"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="John Doe"
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input 
              type="password" 
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              minLength="8"
              required 
            />
          </div>
          
          <button type="submit" className="btn btn-primary btn-block" disabled={isLoading}>
            {isLoading ? 'Creating account...' : 'Sign Up'}
          </button>
        </form>
        
        <div className="auth-footer">
          Already have an account? <Link to="/login">Log in</Link>
        </div>
      </div>
    </div>
  );
}
