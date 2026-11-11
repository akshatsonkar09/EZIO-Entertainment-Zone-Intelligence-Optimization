import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Search, ChevronRight, RefreshCw, AlertCircle, Sparkles, Calendar, FolderTree, Flame, Globe, Languages, Award } from 'lucide-react';
import type { SearchResultItem } from '../types';
import { browseMetadataAPI } from '../api';
import { ResultCard } from '../components/ResultCard';
import { NoResults } from '../components/NoResults';
import { ErrorState } from '../components/ErrorState';
import './BrowsePage.css';

interface BrowseCardDef {
  id: string;
  name: string;
  subtitle?: string;
  theme: string;
  params: {
    domain?: 'movie' | 'anime' | 'book';
    genre?: string;
    release_year_min?: number;
    release_year_max?: number;
  };
}

const FEATURED_GENRES: BrowseCardDef[] = [
  { id: 'Action', name: 'Action', subtitle: 'High adrenaline & adventures', theme: 'action-theme', params: { genre: 'Action' } },
  { id: 'Comedy', name: 'Comedy', subtitle: 'Laughter, parodies & wit', theme: 'comedy-theme', params: { genre: 'Comedy' } },
  { id: 'Horror', name: 'Horror', subtitle: 'Spine-chilling dread & tension', theme: 'horror-theme', params: { genre: 'Horror' } },
  { id: 'Informative', name: 'Informative', subtitle: 'Documentaries & true stories', theme: 'informative-theme', params: { genre: 'Informative' } },
  { id: 'Mystery', name: 'Mystery', subtitle: 'Whodunits & complex riddles', theme: 'mystery-theme', params: { genre: 'Mystery' } },
  { id: 'Romance', name: 'Romance', subtitle: 'Heartfelt drama & connections', theme: 'romance-theme', params: { genre: 'Romance' } },
  { id: 'Sci-Fi', name: 'Sci-Fi', subtitle: 'Space, technology & futures', theme: 'scifi-theme', params: { genre: 'Sci-Fi' } },
  { id: 'Sports', name: 'Sports', subtitle: 'Rivalries, grit & victory', theme: 'sports-theme', params: { genre: 'Sports' } },
  { id: 'Thriller', name: 'Thriller', subtitle: 'Psychological twists & stakes', theme: 'thriller-theme', params: { genre: 'Thriller' } },
];

const YEAR_CARDS: BrowseCardDef[] = [
  { id: '2020s', name: '2020s Releases', subtitle: '2020 – 2026', theme: 'scifi-theme', params: { release_year_min: 2020, release_year_max: 2026 } },
  { id: '2010s', name: '2010s Era', subtitle: '2010 – 2019', theme: 'mystery-theme', params: { release_year_min: 2010, release_year_max: 2019 } },
  { id: '2000s', name: '2000s Era', subtitle: '2000 – 2009', theme: 'action-theme', params: { release_year_min: 2000, release_year_max: 2009 } },
  { id: '1990s', name: '1990s Era', subtitle: '1990 – 1999', theme: 'sports-theme', params: { release_year_min: 1990, release_year_max: 1999 } },
  { id: '1980s', name: '1980s Era', subtitle: '1980 – 1989', theme: 'romance-theme', params: { release_year_min: 1980, release_year_max: 1989 } },
  { id: 'Classics', name: 'Golden Classics', subtitle: 'Prior to 1980', theme: 'comedy-theme', params: { release_year_min: 1900, release_year_max: 1979 } },
];

const CATEGORY_CARDS: BrowseCardDef[] = [
  { id: 'Movies', name: 'Movies', subtitle: '4,805 feature films & cinema', theme: 'action-theme', params: { domain: 'movie' } },
  { id: 'Anime', name: 'Anime', subtitle: '18,336 anime series & OVAs', theme: 'mystery-theme', params: { domain: 'anime' } },
  { id: 'Books', name: 'Books', subtitle: '11,230 literature & novels', theme: 'informative-theme', params: { domain: 'book' } },
];

const ANIME_CARDS: BrowseCardDef[] = [
  { id: 'Shounen', name: 'Shounen Anime', subtitle: 'Battle, ambition & journeys', theme: 'action-theme', params: { domain: 'anime', genre: 'Shounen' } },
  { id: 'Action Anime', name: 'Action Anime', subtitle: 'Combat, martial arts & sci-fi', theme: 'thriller-theme', params: { domain: 'anime', genre: 'Action' } },
  { id: 'Fantasy Anime', name: 'Fantasy Anime', subtitle: 'Magic, worlds & creatures', theme: 'mystery-theme', params: { domain: 'anime', genre: 'Fantasy' } },
  { id: 'Sci-Fi Anime', name: 'Sci-Fi Anime', subtitle: 'Mecha, cyberpunk & future', theme: 'scifi-theme', params: { domain: 'anime', genre: 'Sci-Fi' } },
  { id: 'Supernatural Anime', name: 'Supernatural Anime', subtitle: 'Demons, spirits & powers', theme: 'horror-theme', params: { domain: 'anime', genre: 'Supernatural' } },
  { id: 'Comedy Anime', name: 'Comedy Anime', subtitle: 'Gags, parody & school life', theme: 'comedy-theme', params: { domain: 'anime', genre: 'Comedy' } },
  { id: 'Historical Anime', name: 'Historical Anime', subtitle: 'Samurai, legends & eras', theme: 'informative-theme', params: { domain: 'anime', genre: 'Historical' } },
  { id: 'Romance Anime', name: 'Romance Anime', subtitle: 'Drama, emotions & youth', theme: 'romance-theme', params: { domain: 'anime', genre: 'Romance' } },
  { id: 'Slice of Life', name: 'Slice of Life', subtitle: 'Everyday warmth & friendship', theme: 'sports-theme', params: { domain: 'anime', genre: 'Slice of Life' } },
];

export const BrowsePage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const activeType = searchParams.get('type') || 'genre';

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCardId, setSelectedCardId] = useState<string | null>(null);
  const [selectedTitle, setSelectedTitle] = useState<string>('');

  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const resultsTrayRef = useRef<HTMLDivElement>(null);
  const shouldScrollRef = useRef<boolean>(false);

  // Clear selections when tab changes
  useEffect(() => {
    setSelectedCardId(null);
    setResults([]);
    setError(null);
    setSearchQuery('');
    shouldScrollRef.current = false;
  }, [activeType]);

  // Smooth scroll to results once rendering finishes
  useEffect(() => {
    if (!loading && selectedCardId && shouldScrollRef.current && resultsTrayRef.current) {
      const animationFrameId = requestAnimationFrame(() => {
        if (!resultsTrayRef.current) return;

        const prefersReducedMotion =
          typeof window !== 'undefined' &&
          window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        const behavior: ScrollBehavior = prefersReducedMotion ? 'auto' : 'smooth';

        const NAVBAR_HEIGHT = 64;
        const BUFFER_SPACING = 20;
        const topOffset = NAVBAR_HEIGHT + BUFFER_SPACING;

        const rect = resultsTrayRef.current.getBoundingClientRect();
        const targetY = rect.top + window.scrollY - topOffset;

        window.scrollTo({
          top: Math.max(0, targetY),
          behavior,
        });

        shouldScrollRef.current = false;
      });

      return () => cancelAnimationFrame(animationFrameId);
    }
  }, [loading, selectedCardId]);

  const handleSelectTab = (type: string) => {
    setSearchParams({ type });
  };

  const handleCardClick = async (card: BrowseCardDef) => {
    if (selectedCardId === card.id) {
      setSelectedCardId(null);
      setResults([]);
      shouldScrollRef.current = false;
      return;
    }

    setSelectedCardId(card.id);
    setSelectedTitle(card.name);
    setLoading(true);
    setError(null);
    shouldScrollRef.current = true;

    try {
      const response = await browseMetadataAPI({
        ...card.params,
        limit: 15,
      });
      setResults(response.results);
    } catch (err: any) {
      setError(err?.message || 'Failed to retrieve catalog records.');
    } finally {
      setLoading(false);
    }
  };

  let activeCardList: BrowseCardDef[] = [];
  let isAuditedField = false;

  if (activeType === 'year') {
    activeCardList = YEAR_CARDS;
  } else if (activeType === 'category') {
    activeCardList = CATEGORY_CARDS;
  } else if (activeType === 'anime') {
    activeCardList = ANIME_CARDS;
  } else if (activeType === 'genre') {
    activeCardList = FEATURED_GENRES;
  } else if (activeType === 'country' || activeType === 'language' || activeType === 'award_winners') {
    isAuditedField = true;
  } else {
    activeCardList = FEATURED_GENRES;
  }

  const visibleCards = activeCardList.filter((c) =>
    c.name.toLowerCase().includes(searchQuery.toLowerCase().trim())
  );

  return (
    <div className="browse-screen-layout">
      <div className="browse-container">
        {/* Top Header Row with Title & Search Input */}
        <div className="browse-top-header">
          <div className="browse-title-cluster">
            <h1 className="browse-main-heading">Browse by Metadata</h1>
            <p className="browse-subtitle">
              Explore movies, anime, and books through verified catalog metadata tags.
            </p>
          </div>

          {!isAuditedField && (
            <div className="browse-search-box">
              <Search size={16} className="browse-search-icon" />
              <input
                type="text"
                className="browse-search-input"
                placeholder="Filter categories..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          )}
        </div>

        {/* Metadata Filter Type Selector Strip */}
        <div className="browse-type-nav-strip" role="tablist">
          <button
            type="button"
            className={`browse-type-pill ${activeType === 'genre' ? 'active' : ''}`}
            onClick={() => handleSelectTab('genre')}
          >
            <Sparkles size={14} />
            <span>Genre</span>
          </button>

          <button
            type="button"
            className={`browse-type-pill ${activeType === 'year' ? 'active' : ''}`}
            onClick={() => handleSelectTab('year')}
          >
            <Calendar size={14} />
            <span>Year</span>
          </button>

          <button
            type="button"
            className={`browse-type-pill ${activeType === 'category' ? 'active' : ''}`}
            onClick={() => handleSelectTab('category')}
          >
            <FolderTree size={14} />
            <span>Category</span>
          </button>

          <button
            type="button"
            className={`browse-type-pill ${activeType === 'anime' ? 'active' : ''}`}
            onClick={() => handleSelectTab('anime')}
          >
            <Flame size={14} />
            <span>Anime</span>
          </button>

          <button
            type="button"
            className={`browse-type-pill ${activeType === 'country' ? 'active' : ''}`}
            onClick={() => handleSelectTab('country')}
          >
            <Globe size={14} />
            <span>Country</span>
          </button>

          <button
            type="button"
            className={`browse-type-pill ${activeType === 'language' ? 'active' : ''}`}
            onClick={() => handleSelectTab('language')}
          >
            <Languages size={14} />
            <span>Language</span>
          </button>

          <button
            type="button"
            className={`browse-type-pill ${activeType === 'award_winners' ? 'active' : ''}`}
            onClick={() => handleSelectTab('award_winners')}
          >
            <Award size={14} />
            <span>Award Winners</span>
          </button>
        </div>

        {/* Audit Status Panel for Unsupported Fields */}
        {isAuditedField && (
          <div className="audit-notice-card animate-fade-in">
            <div className="audit-notice-icon-wrap">
              <AlertCircle size={28} className="audit-icon" />
            </div>
            <div className="audit-notice-content">
              <h3 className="audit-notice-title">
                Catalog Metadata Audit Notice: {activeType === 'country' ? 'Country' : activeType === 'language' ? 'Language' : 'Award Winners'}
              </h3>
              <p className="audit-notice-desc">
                In the current verified local datasets (<code>movie_metadata_clean.csv</code>, <code>anime_metadata_clean.csv</code>, and <code>book_metadata_clean.csv</code>), {activeType === 'country' ? 'country origin' : activeType === 'language' ? 'original spoken/written language' : 'awards and honors'} is not indexed as a clean structured attribute.
              </p>
              <p className="audit-notice-sub">
                To prevent returning ungrounded or synthetic records, EZIO filters exclusively on verified attributes. You can browse through our indexed categories below:
              </p>
              <div className="audit-suggested-actions">
                <button
                  type="button"
                  className="audit-switch-btn"
                  onClick={() => handleSelectTab('genre')}
                >
                  <Sparkles size={15} />
                  <span>Browse by Genre</span>
                </button>
                <button
                  type="button"
                  className="audit-switch-btn"
                  onClick={() => handleSelectTab('year')}
                >
                  <Calendar size={15} />
                  <span>Browse by Year</span>
                </button>
                <button
                  type="button"
                  className="audit-switch-btn"
                  onClick={() => handleSelectTab('category')}
                >
                  <FolderTree size={15} />
                  <span>Browse by Category</span>
                </button>
                <button
                  type="button"
                  className="audit-switch-btn"
                  onClick={() => handleSelectTab('anime')}
                >
                  <Flame size={15} />
                  <span>Browse Anime</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Visual Category Cards Grid */}
        {!isAuditedField && (
          <div className="genre-cards-grid" role="group" aria-label="Metadata categories">
            {visibleCards.map((card) => {
              const isSelected = selectedCardId === card.id;
              return (
                <div
                  key={card.id}
                  className={`genre-art-card ${card.theme} ${isSelected ? 'selected' : ''}`}
                  onClick={() => handleCardClick(card)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      handleCardClick(card);
                    }
                  }}
                >
                  <div className="card-silhouette-layer" />
                  <div className="card-gradient-sheen" />

                  <div className="card-footer-info">
                    <div>
                      <span className="genre-name-text">{card.name}</span>
                      {card.subtitle && (
                        <span className="genre-card-subtext">{card.subtitle}</span>
                      )}
                    </div>
                    <div className="genre-arrow-indicator">
                      <ChevronRight size={18} />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Filtered Results View */}
        {selectedCardId && (
          <div
            key={selectedCardId}
            ref={resultsTrayRef}
            className="browse-results-tray animate-fade-in"
          >
            <div className="tray-header">
              <h2 className="tray-title">
                Showing top records for <span className="tray-highlight">"{selectedTitle}"</span>
              </h2>
              <span className="tray-count">{results.length} results</span>
            </div>

            {loading ? (
              <div className="tray-loading-state">
                <RefreshCw size={32} className="spin-icon purple" />
                <span>Retrieving catalog records...</span>
              </div>
            ) : error ? (
              <ErrorState
                message={error}
                onRetry={() => {
                  const card = activeCardList.find((c) => c.id === selectedCardId);
                  if (card) handleCardClick(card);
                }}
              />
            ) : results.length === 0 ? (
              <NoResults
                query={selectedTitle}
                onResetSearch={() => setSelectedCardId(null)}
              />
            ) : (
              <div className="ranked-results-stack">
                {results.map((item, index) => (
                  <ResultCard
                    key={item.id}
                    item={item}
                    rank={index + 1}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
