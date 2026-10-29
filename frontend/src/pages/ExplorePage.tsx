import React, { useState, useEffect } from 'react';
import { Compass, Film, Flame, BookOpen, RefreshCw, Layers } from 'lucide-react';
import type { DomainType, SearchResultItem } from '../types';
import { browseMetadataAPI } from '../api';
import { ResultCard } from '../components/ResultCard';
import { ErrorState } from '../components/ErrorState';
import { NoResults } from '../components/NoResults';
import './ExplorePage.css';

interface EraFilter {
  id: string;
  label: string;
  minYear?: number;
  maxYear?: number;
}

const ERA_FILTERS: EraFilter[] = [
  { id: 'all', label: 'All Eras' },
  { id: '2020s', label: '2020s', minYear: 2020, maxYear: 2026 },
  { id: '2010s', label: '2010s', minYear: 2010, maxYear: 2019 },
  { id: '2000s', label: '2000s', minYear: 2000, maxYear: 2009 },
  { id: '1990s', label: '1990s', minYear: 1990, maxYear: 1999 },
  { id: 'classics', label: 'Classics (<1990)', minYear: 1900, maxYear: 1989 },
];

const GENRE_CHIPS = [
  'All Genres',
  'Action',
  'Sci-Fi',
  'Mystery',
  'Comedy',
  'Romance',
  'Horror',
  'Thriller',
  'Informative',
];

export const ExplorePage: React.FC = () => {
  const [selectedDomain, setSelectedDomain] = useState<DomainType | 'all'>('all');
  const [selectedEra, setSelectedEra] = useState<string>('all');
  const [selectedGenre, setSelectedGenre] = useState<string>('All Genres');

  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchExploreData = async () => {
    setLoading(true);
    setError(null);

    const eraObj = ERA_FILTERS.find((e) => e.id === selectedEra);

    try {
      const resp = await browseMetadataAPI({
        domain: selectedDomain === 'all' ? undefined : selectedDomain,
        genre: selectedGenre === 'All Genres' ? undefined : selectedGenre,
        release_year_min: eraObj?.minYear,
        release_year_max: eraObj?.maxYear,
        limit: 24,
      });
      setResults(resp.results);
    } catch (err: any) {
      setError(err?.message || 'Failed to load catalog records for exploration.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExploreData();
  }, [selectedDomain, selectedEra, selectedGenre]);

  return (
    <div className="explore-page-layout animate-fade-in">
      <div className="explore-container">
        {/* Header Hero */}
        <div className="explore-header-card">
          <div className="explore-header-glow" aria-hidden="true" />
          <div className="explore-title-row">
            <div className="explore-icon-bubble">
              <Compass size={24} />
            </div>
            <div>
              <h1 className="explore-title">Explore Catalog</h1>
              <p className="explore-subtitle">
                Discover verified records across movies, anime, and books through real metadata.
              </p>
            </div>
          </div>

          {/* Genuine Dataset Metrics Badges (Real Catalog Counts) */}
          <div className="catalog-stat-strip">
            <div className="stat-pill">
              <Film size={14} className="stat-icon purple" />
              <span>4,805 Movies</span>
            </div>
            <div className="stat-pill">
              <Flame size={14} className="stat-icon orange" />
              <span>18,336 Anime</span>
            </div>
            <div className="stat-pill">
              <BookOpen size={14} className="stat-icon cyan" />
              <span>11,230 Books</span>
            </div>
            <div className="stat-pill total">
              <Layers size={14} className="stat-icon" />
              <span>34,371 Verified Titles</span>
            </div>
          </div>
        </div>

        {/* Filter Controls Bar */}
        <div className="explore-controls-panel">
          {/* Domain Tabs */}
          <div className="control-group">
            <span className="control-label">Domain</span>
            <div className="domain-tabs-row" role="tablist">
              <button
                type="button"
                className={`domain-tab-btn ${selectedDomain === 'all' ? 'active' : ''}`}
                onClick={() => setSelectedDomain('all')}
              >
                All Media
              </button>
              <button
                type="button"
                className={`domain-tab-btn ${selectedDomain === 'movie' ? 'active' : ''}`}
                onClick={() => setSelectedDomain('movie')}
              >
                Movies
              </button>
              <button
                type="button"
                className={`domain-tab-btn ${selectedDomain === 'anime' ? 'active' : ''}`}
                onClick={() => setSelectedDomain('anime')}
              >
                Anime
              </button>
              <button
                type="button"
                className={`domain-tab-btn ${selectedDomain === 'book' ? 'active' : ''}`}
                onClick={() => setSelectedDomain('book')}
              >
                Books
              </button>
            </div>
          </div>

          {/* Release Era Filter */}
          <div className="control-group">
            <span className="control-label">Release Era</span>
            <div className="filter-chips-row">
              {ERA_FILTERS.map((era) => (
                <button
                  key={era.id}
                  type="button"
                  className={`filter-chip-btn ${selectedEra === era.id ? 'active' : ''}`}
                  onClick={() => setSelectedEra(era.id)}
                >
                  {era.label}
                </button>
              ))}
            </div>
          </div>

          {/* Genre Chips */}
          <div className="control-group">
            <span className="control-label">Genre</span>
            <div className="filter-chips-row">
              {GENRE_CHIPS.map((genre) => (
                <button
                  key={genre}
                  type="button"
                  className={`filter-chip-btn ${selectedGenre === genre ? 'active' : ''}`}
                  onClick={() => setSelectedGenre(genre)}
                >
                  {genre}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Catalog Results View */}
        <div className="explore-results-tray">
          <div className="results-tray-header">
            <h2 className="tray-heading">
              Catalog Records
              {selectedDomain !== 'all' && <span className="tray-domain-tag"> • {selectedDomain}</span>}
              {selectedGenre !== 'All Genres' && <span className="tray-genre-tag"> • {selectedGenre}</span>}
            </h2>
            <span className="tray-badge-count">{results.length} records shown</span>
          </div>

          {loading ? (
            <div className="tray-loading-state">
              <RefreshCw size={32} className="spin-icon purple" />
              <span>Retrieving matching records from catalog...</span>
            </div>
          ) : error ? (
            <ErrorState message={error} onRetry={fetchExploreData} />
          ) : results.length === 0 ? (
            <NoResults
              query={`${selectedDomain !== 'all' ? selectedDomain : ''} ${selectedGenre !== 'All Genres' ? selectedGenre : ''} ${selectedEra !== 'all' ? selectedEra : ''}`}
              onResetSearch={() => {
                setSelectedDomain('all');
                setSelectedEra('all');
                setSelectedGenre('All Genres');
              }}
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
      </div>
    </div>
  );
};
