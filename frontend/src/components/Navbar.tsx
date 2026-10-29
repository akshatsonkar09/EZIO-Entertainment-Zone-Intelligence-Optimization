import React, { useState, useRef, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  Sparkles,
  ChevronDown,
  Search,
  Bookmark,
  Bell,
  Globe,
  Languages,
  Calendar,
  FolderTree,
  Flame,
  Award,
  Star,
  User,
  X,
  Compass,
  Shuffle,
  ShieldAlert,
} from 'lucide-react';
import { useBookmarks } from '../context/BookmarkContext';
import './Navbar.css';

interface NavbarProps {
  onOpenRandom?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onOpenRandom }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { bookmarksCount } = useBookmarks();

  const [browseDropdownOpen, setBrowseDropdownOpen] = useState(false);
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);
  const [searchOverlayOpen, setSearchOverlayOpen] = useState(false);

  const [searchQuery, setSearchQuery] = useState('');
  const [searchDomain, setSearchDomain] = useState<'all' | 'movie' | 'anime' | 'book'>('all');

  const dropdownRef = useRef<HTMLDivElement>(null);
  const profileRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;
      if (dropdownRef.current && !dropdownRef.current.contains(target)) {
        setBrowseDropdownOpen(false);
      }
      if (profileRef.current && !profileRef.current.contains(target)) {
        setProfileMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Autofocus input when search overlay opens
  useEffect(() => {
    if (searchOverlayOpen) {
      setTimeout(() => {
        searchInputRef.current?.focus();
      }, 50);
    }
  }, [searchOverlayOpen]);

  // Handle escape key to close overlays
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setSearchOverlayOpen(false);
        setBrowseDropdownOpen(false);
        setProfileMenuOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleDropdownSelect = (type: string) => {
    setBrowseDropdownOpen(false);
    navigate(`/browse?type=${encodeURIComponent(type)}`);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const q = searchQuery.trim();
    if (!q) return;

    setSearchOverlayOpen(false);
    const params = new URLSearchParams();
    params.set('q', q);
    if (searchDomain !== 'all') {
      params.set('domain', searchDomain);
    }
    navigate(`/search?${params.toString()}`);
  };

  const isHome = location.pathname === '/';
  const isBrowse = location.pathname.startsWith('/browse');
  const isExplore = location.pathname.startsWith('/explore');
  const isBookmarks = location.pathname.startsWith('/bookmarks');
  const isRandom = location.pathname.startsWith('/random');

  return (
    <header className="site-header" role="banner">
      <div className="header-inner">
        {/* Left: Brand Logo */}
        <Link to="/" className="brand-link" aria-label="Project Black Knight">
          <div className="brand-logo-icon">
            <Star size={16} fill="#ffffff" color="#ffffff" />
          </div>
          <span className="brand-text">PROJECT BLACK KNIGHT</span>
        </Link>

        {/* Center: Main Navigation */}
        <nav className="center-nav">
          <Link to="/" className={`center-nav-item ${isHome ? 'active' : ''}`}>
            <span>Home</span>
            {isHome && <div className="nav-active-pill" />}
          </Link>

          {/* Browse dropdown button */}
          <div className="browse-dropdown-wrapper" ref={dropdownRef}>
            <button
              type="button"
              className={`center-nav-item ${isBrowse ? 'active' : ''}`}
              onClick={() => setBrowseDropdownOpen(!browseDropdownOpen)}
              aria-expanded={browseDropdownOpen}
            >
              <span>Browse</span>
              <ChevronDown
                size={14}
                className={`dropdown-chevron ${browseDropdownOpen ? 'open' : ''}`}
              />
              {isBrowse && <div className="nav-active-pill" />}
            </button>

            {/* Dropdown Menu Modal/Panel */}
            {browseDropdownOpen && (
              <div className="browse-dropdown-menu animate-fade-in">
                <div className="browse-dropdown-grid">
                  <button
                    type="button"
                    className="dropdown-menu-item active"
                    onClick={() => handleDropdownSelect('genre')}
                  >
                    <Sparkles size={16} className="item-icon purple" />
                    <span>Genre</span>
                  </button>

                  <button
                    type="button"
                    className="dropdown-menu-item"
                    onClick={() => handleDropdownSelect('country')}
                  >
                    <Globe size={16} className="item-icon" />
                    <span>Country</span>
                  </button>

                  <button
                    type="button"
                    className="dropdown-menu-item"
                    onClick={() => handleDropdownSelect('language')}
                  >
                    <Languages size={16} className="item-icon" />
                    <span>Language</span>
                  </button>

                  <button
                    type="button"
                    className="dropdown-menu-item"
                    onClick={() => handleDropdownSelect('year')}
                  >
                    <Calendar size={16} className="item-icon" />
                    <span>Year</span>
                  </button>

                  <button
                    type="button"
                    className="dropdown-menu-item"
                    onClick={() => handleDropdownSelect('category')}
                  >
                    <FolderTree size={16} className="item-icon" />
                    <span>Category</span>
                  </button>

                  <button
                    type="button"
                    className="dropdown-menu-item"
                    onClick={() => handleDropdownSelect('anime')}
                  >
                    <Flame size={16} className="item-icon" />
                    <span>Anime</span>
                  </button>

                  <button
                    type="button"
                    className="dropdown-menu-item"
                    onClick={() => handleDropdownSelect('award_winners')}
                  >
                    <Award size={16} className="item-icon" />
                    <span>Award Winners</span>
                  </button>
                </div>
              </div>
            )}
          </div>

          <Link to="/explore" className={`center-nav-item ${isExplore ? 'active' : ''}`}>
            <span>Explore</span>
            {isExplore && <div className="nav-active-pill" />}
          </Link>

          <Link
            to="/random"
            className={`center-nav-item ${isRandom ? 'active' : ''}`}
            onClick={(e) => {
              if (onOpenRandom && isHome) {
                e.preventDefault();
                onOpenRandom();
              }
            }}
          >
            <span>Random</span>
            {isRandom && <div className="nav-active-pill" />}
          </Link>
        </nav>

        {/* Right: Actions */}
        <div className="header-right-actions">
          {/* Header Search Trigger */}
          <button
            type="button"
            className={`action-icon-btn ${searchOverlayOpen ? 'active' : ''}`}
            onClick={() => setSearchOverlayOpen(!searchOverlayOpen)}
            aria-label="Open search"
            title="Search catalog"
          >
            <Search size={18} />
          </button>

          {/* Bookmarks Navigation Trigger with real count badge */}
          <button
            type="button"
            className={`action-icon-btn ${isBookmarks ? 'active' : ''}`}
            onClick={() => navigate('/bookmarks')}
            aria-label={`Bookmarks (${bookmarksCount} saved)`}
            title="Saved bookmarks"
          >
            <Bookmark size={18} />
            {bookmarksCount > 0 && (
              <span className="navbar-badge-count">{bookmarksCount}</span>
            )}
          </button>

          {/* Notifications */}
          <button
            type="button"
            className="action-icon-btn relative"
            aria-label="Notifications"
            title="Notifications"
          >
            <Bell size={18} />
            <span className="notification-dot" />
          </button>

          {/* User Profile Avatar with Menu Dropdown */}
          <div className="profile-wrapper" ref={profileRef}>
            <div
              className={`user-avatar-pill ${profileMenuOpen ? 'active' : ''}`}
              onClick={() => setProfileMenuOpen(!profileMenuOpen)}
              title="Demo Profile"
              role="button"
              tabIndex={0}
              aria-expanded={profileMenuOpen}
              aria-label="User profile menu"
            >
              <User size={16} />
            </div>

            {profileMenuOpen && (
              <div className="profile-dropdown-menu animate-fade-in">
                {/* Profile Header */}
                <div className="profile-menu-header">
                  <div className="profile-avatar-large">
                    <span>DU</span>
                  </div>
                  <div className="profile-info-block">
                    <span className="profile-user-name">Demo User</span>
                    <span className="profile-badge-role">Demo Account (Single User)</span>
                  </div>
                </div>

                {/* Profile Links */}
                <div className="profile-menu-links">
                  <button
                    type="button"
                    className="profile-link-item"
                    onClick={() => {
                      setProfileMenuOpen(false);
                      navigate('/bookmarks');
                    }}
                  >
                    <Bookmark size={16} className="profile-item-icon purple" />
                    <span>Saved Bookmarks</span>
                    <span className="profile-item-count">{bookmarksCount}</span>
                  </button>

                  <button
                    type="button"
                    className="profile-link-item"
                    onClick={() => {
                      setProfileMenuOpen(false);
                      navigate('/explore');
                    }}
                  >
                    <Compass size={16} className="profile-item-icon" />
                    <span>Explore Catalog</span>
                  </button>

                  <button
                    type="button"
                    className="profile-link-item"
                    onClick={() => {
                      setProfileMenuOpen(false);
                      navigate('/random');
                    }}
                  >
                    <Shuffle size={16} className="profile-item-icon" />
                    <span>Random Picker</span>
                  </button>
                </div>

                {/* Disclaimer / Authentication notice */}
                <div className="profile-menu-footer">
                  <ShieldAlert size={14} className="profile-alert-icon" />
                  <p className="profile-auth-notice">
                    Authentication and multi-user registration are planned for a later phase. Bookmarks are stored in local storage for this session.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Expandable Header Search Overlay */}
      {searchOverlayOpen && (
        <div className="header-search-overlay animate-fade-in">
          <form className="header-search-form" onSubmit={handleSearchSubmit}>
            <div className="header-search-input-wrap">
              <Search size={18} className="search-wrap-icon" />
              <input
                ref={searchInputRef}
                type="text"
                className="header-search-input-field"
                placeholder="Search movies, anime, and books by title, genre, or premise..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              {searchQuery && (
                <button
                  type="button"
                  className="clear-search-btn"
                  onClick={() => setSearchQuery('')}
                  aria-label="Clear text"
                >
                  <X size={16} />
                </button>
              )}
            </div>

            {/* Quick Domain Filters */}
            <div className="header-search-domains">
              <button
                type="button"
                className={`search-domain-pill ${searchDomain === 'all' ? 'active' : ''}`}
                onClick={() => setSearchDomain('all')}
              >
                All
              </button>
              <button
                type="button"
                className={`search-domain-pill ${searchDomain === 'movie' ? 'active' : ''}`}
                onClick={() => setSearchDomain('movie')}
              >
                Movies
              </button>
              <button
                type="button"
                className={`search-domain-pill ${searchDomain === 'anime' ? 'active' : ''}`}
                onClick={() => setSearchDomain('anime')}
              >
                Anime
              </button>
              <button
                type="button"
                className={`search-domain-pill ${searchDomain === 'book' ? 'active' : ''}`}
                onClick={() => setSearchDomain('book')}
              >
                Books
              </button>
            </div>

            <div className="header-search-actions">
              <button
                type="submit"
                className="search-submit-btn"
                disabled={!searchQuery.trim()}
              >
                Search
              </button>
              <button
                type="button"
                className="search-close-btn"
                onClick={() => setSearchOverlayOpen(false)}
                aria-label="Close search"
              >
                <X size={18} />
              </button>
            </div>
          </form>
        </div>
      )}
    </header>
  );
};
