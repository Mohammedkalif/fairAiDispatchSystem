import React, { useState, useEffect } from 'react';
import './Navbar.css';

const Navbar = ({ currentView }) => {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <nav className={`navbar ${isScrolled ? 'scrolled' : ''}`}>
      <div className="navbar-container">
        <div className="navbar-brand">
          <span className="brand-icon">⚖️</span>
          <span className="brand-text">FairDispatch</span>
        </div>

        <div className="navbar-nav">
          <a href="#" className={`nav-link ${currentView === 'home' ? 'active' : ''}`}>
            Home
          </a>
          <a href="#datasets" className={`nav-link ${currentView === 'datasets' ? 'active' : ''}`}>
            Datasets
          </a>
          <a href="#process" className={`nav-link ${currentView === 'process' ? 'active' : ''}`}>
            Process
          </a>
        </div>

        <div className="navbar-actions">
          <button className="btn btn-secondary btn-sm">Docs</button>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
