import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Dices,
  Film,
  Sparkles,
  BookOpen,
  ChevronDown,
  AlertCircle,
} from 'lucide-react';
import type { FilterDomainType } from '../types';
import './HomePage.css';

interface HomePageProps {
  onOpenRandom: () => void;
}

export const HomePage: React.FC<HomePageProps> = ({ onOpenRandom }) => {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [selectedDomain, setSelectedDomain] = useState<FilterDomainType>('movie');
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleSearch = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const clean = query.trim();
    if (!clean) {
      setValidationError('Please enter a search query before searching.');
      return;
    }
    setValidationError(null);

    const searchParams = new URLSearchParams();
    searchParams.set('q', clean);
    if (selectedDomain && selectedDomain !== 'all') {
      searchParams.set('domain', selectedDomain);
    }
    navigate(`/search?${searchParams.toString()}`);
  };

  const handleDomainSelect = (domain: FilterDomainType) => {
    setSelectedDomain((prev) => (prev === domain ? 'all' : domain));
    if (validationError) setValidationError(null);
  };

  return (
    <div className="home-screen-wrapper">
      {/* Background Anime Landscape with Atmospheric Lighting */}
      <div className="hero-artwork-bg" aria-hidden="true" />
      <div className="hero-dark-overlay" aria-hidden="true" />

      {/* Main Content Area */}
      <div className="home-hero-container">
        {/* Main Hero Headings */}
        <div className="hero-headline-group">
          <h1 className="hero-title-main">
            Discover Movies,<br />
            Anime & Books<br />
            <span className="hero-title-highlight">Beyond the Ordinary</span>
          </h1>

          <p className="hero-tagline">
            AI-powered search and recommendations to help you find your next favourite story.
          </p>
        </div>

        {/* Prominent Natural-Language Search Bar */}
        <form className="hero-search-wrapper" onSubmit={handleSearch} noValidate>
          <div className={`search-pill-box ${validationError ? 'has-error' : ''}`}>
            <Search size={20} className="search-pill-icon" aria-hidden="true" />
            <input
              type="text"
              className="search-pill-input"
              placeholder="Search for movies, anime, books..."
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                if (validationError) setValidationError(null);
              }}
              autoFocus
              aria-label="Search movies, anime, books"
            />
            <button
              type="submit"
              className="search-pill-action-btn"
              aria-label="Search"
            >
              <Search size={16} />
              <span>Search</span>
            </button>
          </div>

          {validationError && (
            <div className="search-validation-banner" role="alert">
              <AlertCircle size={15} />
              <span>{validationError}</span>
            </div>
          )}
        </form>

        {/* 3 Domain Cards: Movies, Anime, Books */}
        <div className="domain-cards-row" role="group" aria-label="Content domain filters">
          <button
            type="button"
            className={`domain-card-btn ${selectedDomain === 'movie' ? 'active-movie' : ''}`}
            onClick={() => handleDomainSelect('movie')}
            aria-pressed={selectedDomain === 'movie'}
          >
            <div className="domain-card-icon-wrap movie-wrap">
              <Film size={26} />
            </div>
            <span className="domain-card-label">Movies</span>
          </button>

          <button
            type="button"
            className={`domain-card-btn ${selectedDomain === 'anime' ? 'active-anime' : ''}`}
            onClick={() => handleDomainSelect('anime')}
            aria-pressed={selectedDomain === 'anime'}
          >
            <div className="domain-card-icon-wrap anime-wrap">
              <Sparkles size={26} />
            </div>
            <span className="domain-card-label">Anime</span>
          </button>

          <button
            type="button"
            className={`domain-card-btn ${selectedDomain === 'book' ? 'active-book' : ''}`}
            onClick={() => handleDomainSelect('book')}
            aria-pressed={selectedDomain === 'book'}
          >
            <div className="domain-card-icon-wrap book-wrap">
              <BookOpen size={26} />
            </div>
            <span className="domain-card-label">Books</span>
          </button>
        </div>

        {/* Centered Find Random Button */}
        <div className="find-random-row">
          <button
            type="button"
            className="find-random-pill-btn"
            onClick={onOpenRandom}
            aria-label="Find a random movie, anime, or book"
          >
            <Dices size={20} className="random-dice-icon" />
            <span>Find Random</span>
          </button>
        </div>

        {/* Bottom Scroll Indicator */}
        <div className="scroll-indicator" onClick={() => navigate('/browse')}>
          <span>Scroll to explore</span>
          <ChevronDown size={14} className="scroll-chevron" />
        </div>
      </div>
    </div>
  );
};
