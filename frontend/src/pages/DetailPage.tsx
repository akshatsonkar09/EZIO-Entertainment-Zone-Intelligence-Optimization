import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, RefreshCw, Calendar, Tag, Info, Bookmark } from 'lucide-react';
import type { ItemDetail } from '../types';
import { getItemAPI } from '../api';
import { useBookmarks } from '../context/BookmarkContext';
import { DomainBadge } from '../components/DomainIcon';
import { MovieDetails } from '../components/MovieDetails';
import { AnimeDetails } from '../components/AnimeDetails';
import { BookDetails } from '../components/BookDetails';
import { ErrorState } from '../components/ErrorState';
import './DetailPage.css';

export const DetailPage: React.FC = () => {
  const { itemId } = useParams<{ itemId: string }>();
  const navigate = useNavigate();
  const { isBookmarked, toggleBookmark } = useBookmarks();

  const [item, setItem] = useState<ItemDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchItem = async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await getItemAPI(id);
      setItem(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to load item metadata.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (itemId) {
      fetchItem(itemId);
    }
  }, [itemId]);

  if (loading) {
    return (
      <div className="detail-loading-state" role="status">
        <RefreshCw size={36} className="spin-icon" />
        <h2>Loading Item Details...</h2>
      </div>
    );
  }

  if (error || !item) {
    return (
      <div className="detail-error-wrapper">
        <ErrorState
          message={error || 'Item was not found.'}
          onRetry={() => itemId && fetchItem(itemId)}
        />
      </div>
    );
  }

  const domain = String(item.media_type).toLowerCase();
  const bookmarked = isBookmarked(item.id);

  return (
    <div className="detail-page-container animate-fade-in">
      {/* Top Navigation Bar with Back and Bookmark Buttons */}
      <div className="detail-top-bar">
        <button
          type="button"
          className="detail-back-button"
          onClick={() => navigate(-1)}
          aria-label="Return to previous page"
        >
          <ArrowLeft size={18} />
          <span>Back</span>
        </button>

        <button
          type="button"
          className={`detail-bookmark-action-btn ${bookmarked ? 'active' : ''}`}
          onClick={() => toggleBookmark(item)}
          aria-label={bookmarked ? 'Remove from bookmarks' : 'Save to bookmarks'}
          title={bookmarked ? 'Remove from bookmarks' : 'Save to bookmarks'}
        >
          <Bookmark
            size={17}
            fill={bookmarked ? '#c084fc' : 'none'}
            color={bookmarked ? '#c084fc' : 'currentColor'}
          />
          <span>{bookmarked ? 'Saved to Bookmarks' : 'Bookmark Item'}</span>
        </button>
      </div>

      <main className="detail-main-layout">
        {/* Header Hero Section */}
        <section className="detail-hero-card">
          <div className="detail-hero-glow" aria-hidden="true" />

          <div className="detail-hero-content">
            {/* Domain & Quick Meta */}
            <div className="detail-header-meta">
              <DomainBadge domain={domain} />
              {item.release_year && (
                <span className="detail-header-pill">
                  <Calendar size={13} />
                  <span>{Math.round(item.release_year)}</span>
                </span>
              )}
              <span className="canonical-id-pill">ID: {item.id}</span>
            </div>

            {/* Large Item Title */}
            <h1 className="detail-title">{item.title}</h1>

            {/* Genres Tag List */}
            {item.genres && item.genres.length > 0 && (
              <div className="detail-genres-container">
                <Tag size={14} className="genre-lead-icon" />
                <div className="detail-genres-list">
                  {item.genres.map((g, idx) => (
                    <span key={idx} className="genre-pill">
                      {g}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </section>

        {/* Overview / Synopsis / Description Section (Omitted if empty) */}
        {item.overview && (
          <section className="detail-section overview-section">
            <h2 className="section-title">
              <Info size={18} className="section-icon" />
              <span>Overview</span>
            </h2>
            <p className="overview-text">{item.overview}</p>
          </section>
        )}

        {/* Domain-Specific Metadata Sections */}
        <section className="detail-section metadata-section">
          {domain === 'movie' && (
            <MovieDetails metadata={item.metadata} />
          )}
          {domain === 'anime' && (
            <AnimeDetails metadata={item.metadata} />
          )}
          {domain === 'book' && (
            <BookDetails metadata={item.metadata} />
          )}
        </section>
      </main>
    </div>
  );
};
