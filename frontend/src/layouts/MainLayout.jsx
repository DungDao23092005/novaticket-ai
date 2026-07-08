import React from 'react';
import { Outlet, Link } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

export default function MainLayout() {
  const { user, isAuthenticated, logout } = useAuthStore();

  return (
    <div className="app-container">
      <nav className="navbar">
        <div className="navbar-brand">
          <Link to="/">NovaTicket AI</Link>
        </div>
        <div className="navbar-menu">
          <Link to="/">Events</Link>
          {isAuthenticated ? (
            <>
              <Link to="/recommendations">For You ✨</Link>
              <Link to="/dashboard">Dashboard</Link>
              <span className="user-greeting">Hi, {user?.full_name || user?.username}</span>
              <button onClick={logout} className="btn btn-outline">Logout</button>
            </>
          ) : (
            <>
              <Link to="/login" className="btn btn-outline">Login</Link>
              <Link to="/register" className="btn btn-primary">Sign Up</Link>
            </>
          )}
        </div>
      </nav>

      <main className="main-content">
        {/* Render child routes here */}
        <Outlet />
      </main>

      <footer className="footer">
        <p>© 2026 NovaTicket AI. All rights reserved.</p>
      </footer>
    </div>
  );
}
