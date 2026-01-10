import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Header.css';

function Header() {
  const location = useLocation();

  return (
    <header className="header">
      <div className="container">
        <div className="header-content">
          <Link to="/" className="logo">
            <h1>Inkling</h1>
          </Link>
          <nav className="nav">
            <Link to="/" className={location.pathname === '/' ? 'active' : ''}>
              Topics
            </Link>
            <Link to="/create-topic" className={location.pathname === '/create-topic' ? 'active' : ''}>
              Create Topic
            </Link>
            <Link to="/history" className={location.pathname === '/history' ? 'active' : ''}>
              History
            </Link>
          </nav>
        </div>
      </div>
    </header>
  );
}

export default Header;

