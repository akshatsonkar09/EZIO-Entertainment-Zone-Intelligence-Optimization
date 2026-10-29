import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Sparkles,
  Dices,
  Film,
  BookOpen,
  Star,
  RefreshCw,
} from 'lucide-react';
import type { ItemDetail } from '../types';
import { getRandomItemAPI } from '../api';
import { getPosterGradient } from '../utils/poster';
import './RandomPage.css';

export const RandomPage: React.FC = () => {
  const navigate = useNavigate();
  const [selectedDomain, setSelectedDomain] = useState<'movie' | 'anime' | 'book'>('movie');
  const [item, setItem] = useState<ItemDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchRandomItem = async (domainToFetch: 'movie' | 'anime' | 'book') => {
    setLoading(true);
    setError(null);
    try {
      const data = await getRandomItemAPI(domainToFetch);
      setItem(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to select random item.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRandomItem(selectedDomain);
  }, [selectedDomain]);

  const handleDomainChange = (dom: 'movie' | 'anime' | 'book') => {
    setSelectedDomain(dom);
  };

  const domain = item ? String(item.media_type).toLowerCase() : selectedDomain;
  const domainLabel = domain === 'movie' ? 'Movie' : domain === 'anime' ? 'Anime' : 'Book';

  // Construct meta line
  const metaParts: string[] = [];
  if (item?.release_year && Number(item.release_year) > 1800) {
    metaParts.push(`${Math.round(Number(item.release_year))}`);
  }
  metaParts.push(domainLabel);
  if (item?.metadata?.runtime) {
    metaParts.push(`${item.metadata.runtime}m`);
  } else if (item?.metadata?.episodes) {
    metaParts.push(`${item.metadata.episodes} eps`);
  } else if (item?.metadata?.pages) {
    metaParts.push(`${item.metadata.pages} pages`);
  }

  // Rating
  let ratingDisplay: string = '8.3';
  if (item?.metadata?.rating) {
    ratingDisplay = Number(item.metadata.rating).toFixed(1);
  }

  const posterTheme = item ? getPosterGradient(item.title, domain) : { bg: '#1e1b4b', icon: '🎬', accent: '#c084fc' };

  return (
    <div className="random-page-screen">
      <div className="random-page-container animate-fade-in">
        {/* Title: What are we discovering today? */}
        <div className="random-title-block">
          <h1 className="random-heading">
            <Sparkles size={22} className="sparkle-spark" />
            <span>What are we discovering today?</span>
            <Sparkles size={22} className="sparkle-spark" />
          </h1>
        </div>

        {/* 3 Domain Selector Cards */}
        <div className="random-selectors-cluster" role="group" aria-label="Select domain for random discovery">
          <button
            type="button"
            className={`random-domain-card ${selectedDomain === 'movie' ? 'active' : ''}`}
            onClick={() => handleDomainChange('movie')}
          >
            <Film size={22} className="selector-icon" />
            <span className="selector-label">Movie</span>
          </button>

          <button
            type="button"
            className={`random-domain-card ${selectedDomain === 'anime' ? 'active' : ''}`}
            onClick={() => handleDomainChange('anime')}
          >
            <Sparkles size={22} className="selector-icon" />
            <span className="selector-label">Anime</span>
          </button>

          <button
            type="button"
            className={`random-domain-card ${selectedDomain === 'book' ? 'active' : ''}`}
            onClick={() => handleDomainChange('book')}
          >
            <BookOpen size={22} className="selector-icon" />
            <span className="selector-label">Book</span>
          </button>
        </div>

        {/* Action Button: Find Random */}
        <div className="random-cta-wrap">
          <button
            type="button"
            className="find-random-submit-btn"
            onClick={() => fetchRandomItem(selectedDomain)}
            disabled={loading}
          >
            <Dices size={20} className={loading ? 'spin-icon' : ''} />
            <span>Find Random</span>
          </button>
        </div>

        {/* Selected Item Preview Card */}
        {loading ? (
          <div className="random-card-loading">
            <RefreshCw size={36} className="spin-icon purple" />
            <span>Selecting a random title from verified catalog...</span>
          </div>
        ) : error ? (
          <div className="random-card-error">
            <p>{error}</p>
            <button
              type="button"
              className="retry-pill-btn"
              onClick={() => fetchRandomItem(selectedDomain)}
            >
              Try Again
            </button>
          </div>
        ) : item ? (
          <div
            className="discovered-item-card"
            onClick={() => navigate(`/item/${encodeURIComponent(item.id)}`)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                navigate(`/item/${encodeURIComponent(item.id)}`);
              }
            }}
          >
            {/* Left: Poster */}
            <div
              className="discovered-poster"
              style={{ background: posterTheme.bg }}
            >
              <div className="discovered-poster-content">
                <span className="discovered-poster-icon">{posterTheme.icon}</span>
                <span className="discovered-poster-title">{item.title}</span>
              </div>
            </div>

            {/* Middle: Title, Meta line, Overview */}
            <div className="discovered-middle">
              <h2 className="discovered-title">{item.title}</h2>
              <div className="discovered-meta-line">{metaParts.join(' • ')}</div>

              <p className="discovered-overview">
                {item.overview ||
                  'Click to inspect full catalog details, author or director notes, cast lists, and metadata.'}
              </p>
            </div>

            {/* Right: Rating, Genres, Try Another */}
            <div className="discovered-right">
              <div className="discovered-top-right">
                <div className="discovered-rating">
                  <Star size={14} className="star-icon" fill="#eab308" />
                  <span>{ratingDisplay}</span>
                </div>

                <div className="discovered-genres">
                  {item.genres.slice(0, 3).map((g, i) => (
                    <span key={i} className="small-genre-pill">
                      {g}
                    </span>
                  ))}
                </div>
              </div>

              <button
                type="button"
                className="try-another-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  fetchRandomItem(selectedDomain);
                }}
              >
                <RefreshCw size={14} />
                <span>Try Another</span>
              </button>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
};
