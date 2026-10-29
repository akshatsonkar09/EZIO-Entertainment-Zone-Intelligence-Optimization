import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Bookmark, Trash2, Compass, ArrowLeft } from 'lucide-react';
import { useBookmarks } from '../context/BookmarkContext';
import { ResultCard } from '../components/ResultCard';
import './BookmarksPage.css';

export const BookmarksPage: React.FC = () => {
  const navigate = useNavigate();
  const { bookmarks, bookmarksCount, clearBookmarks } = useBookmarks();

  return (
    <div className="bookmarks-screen-layout animate-fade-in">
      <div className="bookmarks-container">
        {/* Top Header Bar */}
        <div className="bookmarks-header-row">
          <div className="bookmarks-title-group">
            <button
              type="button"
              className="bookmarks-back-btn"
              onClick={() => navigate(-1)}
              aria-label="Back"
            >
              <ArrowLeft size={18} />
              <span>Back</span>
            </button>
            <div className="bookmarks-heading-cluster">
              <h1 className="bookmarks-main-title">Saved Bookmarks</h1>
              <span className="bookmarks-count-badge">
                {bookmarksCount} {bookmarksCount === 1 ? 'item' : 'items'}
              </span>
            </div>
          </div>

          {bookmarksCount > 0 && (
            <button
              type="button"
              className="clear-all-bookmarks-btn"
              onClick={() => {
                if (window.confirm('Are you sure you want to remove all saved bookmarks?')) {
                  clearBookmarks();
                }
              }}
              title="Remove all bookmarks"
            >
              <Trash2 size={16} />
              <span>Clear All</span>
            </button>
          )}
        </div>

        {/* Content Area */}
        {bookmarksCount === 0 ? (
          <div className="bookmarks-empty-card">
            <div className="empty-bookmark-glow" />
            <div className="empty-bookmark-icon-wrap">
              <Bookmark size={44} className="empty-bookmark-icon" />
            </div>
            <h2 className="empty-bookmark-title">No Bookmarks Saved Yet</h2>
            <p className="empty-bookmark-desc">
              Your personal library is currently empty. Bookmark movies, anime, or books while searching and browsing to save them for quick access across sessions.
            </p>
            <div className="empty-bookmark-actions">
              <button
                type="button"
                className="explore-btn-primary"
                onClick={() => navigate('/explore')}
              >
                <Compass size={18} />
                <span>Explore Catalog</span>
              </button>
              <button
                type="button"
                className="explore-btn-secondary"
                onClick={() => navigate('/browse')}
              >
                <span>Browse by Metadata</span>
              </button>
            </div>
          </div>
        ) : (
          <div className="bookmarks-list-tray">
            <div className="ranked-results-stack">
              {bookmarks.map((item, index) => (
                <ResultCard
                  key={item.id}
                  item={item}
                  rank={index + 1}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
