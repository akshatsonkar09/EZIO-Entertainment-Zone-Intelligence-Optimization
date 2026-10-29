import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { X, Sparkles, RefreshCw, ExternalLink, Calendar, Star } from 'lucide-react';
import type { ItemDetail } from '../types';
import { getRandomItemAPI } from '../api';
import { DomainBadge } from './DomainIcon';
import './RandomModal.css';

interface RandomModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialDomain?: string;
}

export const RandomModal: React.FC<RandomModalProps> = ({ isOpen, onClose, initialDomain = 'any' }) => {
  const navigate = useNavigate();
  const [selectedDomain, setSelectedDomain] = useState<string>(initialDomain);
  const [item, setItem] = useState<ItemDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchRandomItem = async (domainToFetch: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await getRandomItemAPI(domainToFetch === 'any' ? null : domainToFetch);
      setItem(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to select random item.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchRandomItem(selectedDomain);
    }
  }, [isOpen, selectedDomain]);

  if (!isOpen) return null;

  const handleDomainChange = (dom: string) => {
    setSelectedDomain(dom);
  };

  const handleViewDetail = () => {
    if (item) {
      onClose();
      navigate(`/item/${encodeURIComponent(item.id)}`);
    }
  };

  return (
    <div className="random-modal-overlay" role="dialog" aria-modal="true" aria-labelledby="random-modal-title">
      <div className="random-modal-backdrop" onClick={onClose} />
      
      <div className="random-modal-card animate-fade-in">
        <div className="random-modal-header">
          <div className="random-header-title">
            <Sparkles size={20} className="header-sparkle-icon" />
            <h2 id="random-modal-title">Find Something Random</h2>
          </div>
          <button type="button" className="close-btn" onClick={onClose} aria-label="Close dialog">
            <X size={20} />
          </button>
        </div>

        {/* Domain Selectors */}
        <div className="random-domain-selector">
          {(['any', 'movie', 'anime', 'book'] as const).map((d) => (
            <button
              key={d}
              type="button"
              className={`domain-tab-btn ${selectedDomain === d ? 'active' : ''}`}
              onClick={() => handleDomainChange(d)}
            >
              {d === 'any' && 'Any Domain'}
              {d === 'movie' && 'Movies'}
              {d === 'anime' && 'Anime'}
              {d === 'book' && 'Books'}
            </button>
          ))}
        </div>

        {/* Content Preview */}
        <div className="random-content-container">
          {loading ? (
            <div className="random-loading-state">
              <RefreshCw size={32} className="spin-icon" />
              <span>Selecting a random item from catalog...</span>
            </div>
          ) : error ? (
            <div className="random-error-state">
              <p>{error}</p>
              <button type="button" className="retry-btn" onClick={() => fetchRandomItem(selectedDomain)}>
                Try Again
              </button>
            </div>
          ) : item ? (
            <div className="random-item-preview">
              <div className="random-preview-top">
                <DomainBadge domain={item.media_type} />
                {item.release_year && (
                  <span className="preview-pill">
                    <Calendar size={12} />
                    <span>{Math.round(item.release_year)}</span>
                  </span>
                )}
                {item.metadata?.rating && (
                  <span className="preview-pill">
                    <Star size={12} />
                    <span>★ {Number(item.metadata.rating).toFixed(1)}</span>
                  </span>
                )}
              </div>

              <h3 className="random-item-title">{item.title}</h3>

              {item.overview && (
                <p className="random-item-overview">{item.overview}</p>
              )}

              {item.genres.length > 0 && (
                <div className="random-genres-wrap">
                  {item.genres.slice(0, 4).map((g, i) => (
                    <span key={i} className="genre-pill">
                      {g}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ) : null}
        </div>

        {/* Footer Actions */}
        <div className="random-modal-footer">
          <button
            type="button"
            className="action-btn secondary"
            onClick={() => fetchRandomItem(selectedDomain)}
            disabled={loading}
          >
            <RefreshCw size={16} className={loading ? 'spin-icon' : ''} />
            <span>Try Another</span>
          </button>

          {item && (
            <button
              type="button"
              className="action-btn primary"
              onClick={handleViewDetail}
            >
              <span>Full Details</span>
              <ExternalLink size={16} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
