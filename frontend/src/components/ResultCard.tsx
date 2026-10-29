import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Star, Bookmark, ChevronRight } from 'lucide-react';
import { useBookmarks } from '../context/BookmarkContext';
import type { SearchResultItem } from '../types';
import { getPosterGradient } from '../utils/poster';
import './ResultCard.css';

interface ResultCardProps {
  item: SearchResultItem;
  rank: number;
}

export const ResultCard: React.FC<ResultCardProps> = ({ item, rank }) => {
  const navigate = useNavigate();
  const domain = String(item.media_type).toLowerCase();
  const domainLabel = domain === 'movie' ? 'Movie' : domain === 'anime' ? 'Anime' : 'Book';

  // Construct meta line: "Year • Domain • Duration/Episodes/Pages"
  const metaParts: string[] = [];
  if (item.release_year && Number(item.release_year) > 1800) {
    metaParts.push(`${Math.round(Number(item.release_year))}`);
  }
  metaParts.push(domainLabel);

  const extra = item.extra || {};
  if (domain === 'movie' && extra.runtime) {
    metaParts.push(extra.runtime);
  } else if (domain === 'anime' && extra.episodes) {
    metaParts.push(extra.episodes);
  } else if (domain === 'book' && extra.pages) {
    metaParts.push(extra.pages);
  }

  // Parse rating (if available in extra.rating or compute normalized score)
  let ratingDisplay: string | null = null;
  if (extra.rating) {
    const rawNum = String(extra.rating).replace(/[^0-9.]/g, '');
    if (rawNum) {
      ratingDisplay = Number(rawNum).toFixed(1);
    }
  }
  if (!ratingDisplay && item.score) {
    // Normalize retrieval score to a 7.0 - 9.5 visual score for display
    const mapped = (item.score > 0.1 ? 7.0 + (item.score * 2.5) : 8.2);
    ratingDisplay = Math.min(9.8, Math.max(6.5, mapped)).toFixed(1);
  }

  // Clean genres pills (up to 3)
  const genresList = item.genres
    ? item.genres
        .split(/[,/]\s*|\s{2,}/)
        .map((g) => g.trim().replace(/['"\[\]]/g, ''))
        .filter((g) => g.length > 1 && isNaN(Number(g)))
        .slice(0, 3)
    : [];

  const posterTheme = getPosterGradient(item.title, domain);

  const { isBookmarked, toggleBookmark } = useBookmarks();
  const bookmarked = isBookmarked(item.id);

  const handleCardClick = () => {
    navigate(`/item/${encodeURIComponent(item.id)}`);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleCardClick();
    }
  };

  return (
    <div
      className="ranked-item-row"
      onClick={handleCardClick}
      onKeyDown={handleKeyDown}
      role="button"
      tabIndex={0}
      aria-label={`Rank ${rank}: ${item.title}`}
    >
      {/* 1. Large 3D stylized embossed rank number */}
      <div className="rank-large-number" aria-hidden="true">
        <span>{rank}</span>
      </div>

      {/* 2. Main Card Container */}
      <div className="card-inner-box">
        {/* Left: Poster thumbnail */}
        <div
          className="poster-thumbnail"
          style={{ background: posterTheme.bg }}
          aria-hidden="true"
        >
          <div className="poster-inner-content">
            <span className="poster-domain-icon">{posterTheme.icon}</span>
            <span className="poster-title-abbr">{item.title}</span>
          </div>
          <div className="poster-sheen-overlay" />
        </div>

        {/* Center: Title, Meta row, Overview snippet */}
        <div className="card-middle-content">
          <div className="card-title-row">
            <h3 className="card-main-title">{item.title}</h3>
          </div>

          <div className="card-meta-line">
            {metaParts.join(' • ')}
          </div>

          {item.overview ? (
            <p className="card-description-text">{item.overview}</p>
          ) : (
            <p className="card-description-text muted">
              Discover full catalog metadata, production credits, and tags in full details.
            </p>
          )}
        </div>

        {/* Right: Genre pills, Rating, Bookmark, Chevron */}
        <div className="card-right-content">
          {/* Top Genre Pills */}
          <div className="card-genres-pills">
            {genresList.map((g, i) => (
              <span key={i} className="small-genre-pill">
                {g}
              </span>
            ))}
          </div>

          {/* Bottom Actions Row */}
          <div className="card-actions-cluster">
            {ratingDisplay && (
              <div className="rating-pill">
                <Star size={14} className="star-icon" fill="#eab308" />
                <span className="rating-value">{ratingDisplay}</span>
              </div>
            )}

            <button
              type="button"
              className={`card-bookmark-btn ${bookmarked ? 'active' : ''}`}
              onClick={(e) => {
                e.stopPropagation();
                toggleBookmark(item);
              }}
              aria-label={bookmarked ? 'Remove bookmark' : 'Bookmark item'}
              title={bookmarked ? 'Remove bookmark' : 'Bookmark item'}
            >
              <Bookmark
                size={16}
                fill={bookmarked ? '#c084fc' : 'none'}
                color={bookmarked ? '#c084fc' : 'currentColor'}
              />
            </button>

            <div className="card-arrow-wrap">
              <ChevronRight size={18} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
