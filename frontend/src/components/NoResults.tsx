import React from 'react';
import { Link } from 'react-router-dom';
import { X, RotateCcw, Compass } from 'lucide-react';
import './StatusStates.css';

interface NoResultsProps {
  query?: string;
  onResetSearch?: () => void;
}

export const NoResults: React.FC<NoResultsProps> = ({ onResetSearch }) => {
  return (
    <div className="status-fullscreen-wrap animate-fade-in" role="status">
      <div className="status-hero-bg" aria-hidden="true" />
      <div className="status-dark-scrim" aria-hidden="true" />

      <div className="status-center-card">
        {/* Neon Purple Circle with X */}
        <div className="neon-circle-icon-box purple-glow">
          <X size={32} className="neon-cross-icon" />
        </div>

        <h2 className="status-main-heading">No results found</h2>

        <p className="status-body-text">
          We couldn't find any matches for your search.<br />
          Try different keywords or remove some filters.
        </p>

        <div className="status-pill-actions">
          {onResetSearch ? (
            <button type="button" className="status-btn-pill primary" onClick={onResetSearch}>
              <RotateCcw size={16} />
              <span>Try another search</span>
            </button>
          ) : (
            <Link to="/" className="status-btn-pill primary">
              <RotateCcw size={16} />
              <span>Try another search</span>
            </Link>
          )}

          <Link to="/browse" className="status-btn-pill secondary">
            <Compass size={16} />
            <span>Browse by metadata</span>
          </Link>
        </div>
      </div>
    </div>
  );
};
