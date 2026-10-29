import React from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, RotateCcw, Home } from 'lucide-react';
import './StatusStates.css';

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({ onRetry }) => {
  return (
    <div className="status-fullscreen-wrap animate-fade-in" role="alert">
      <div className="status-hero-bg" aria-hidden="true" />
      <div className="status-dark-scrim" aria-hidden="true" />

      <div className="status-center-card">
        {/* Neon Coral Triangle with Alert */}
        <div className="neon-triangle-icon-box coral-glow">
          <AlertTriangle size={34} className="neon-alert-icon" />
        </div>

        <h2 className="status-main-heading">Something went wrong</h2>

        <p className="status-body-text">
          We're having trouble connecting to the server.<br />
          Please try again later.
        </p>

        <div className="status-pill-actions">
          {onRetry && (
            <button type="button" className="status-btn-pill primary" onClick={onRetry}>
              <RotateCcw size={16} />
              <span>Retry</span>
            </button>
          )}

          <Link to="/" className="status-btn-pill secondary">
            <Home size={16} />
            <span>Go back to home</span>
          </Link>
        </div>
      </div>
    </div>
  );
};
