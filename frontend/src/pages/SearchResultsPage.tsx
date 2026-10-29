import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Search, X, ChevronDown, RefreshCw } from 'lucide-react';
import type { SearchResponse, SearchResultItem } from '../types';
import { searchAPI } from '../api';
import { ResultCard } from '../components/ResultCard';
import { NoResults } from '../components/NoResults';
import { ErrorState } from '../components/ErrorState';
import './SearchResultsPage.css';

export const SearchResultsPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const queryParam = searchParams.get('q') || '';
  const domainParam = searchParams.get('domain') || undefined;

  const [searchInput, setSearchInput] = useState(queryParam);
  const [activeTab, setActiveTab] = useState<'all' | 'movie' | 'anime' | 'book'>('all');

  const [data, setData] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const executeSearch = async (q: string, dom?: string) => {
    if (!q.trim()) {
      navigate('/');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await searchAPI(q, dom, 20);
      setData(response);
    } catch (err: any) {
      setError(err?.message || 'An error occurred during search.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setSearchInput(queryParam);
    if (domainParam && (domainParam === 'movie' || domainParam === 'anime' || domainParam === 'book')) {
      setActiveTab(domainParam);
    } else {
      setActiveTab('all');
    }

    if (queryParam) {
      executeSearch(queryParam, domainParam);
    } else {
      navigate('/');
    }
  }, [queryParam, domainParam]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchInput.trim()) return;
    const params = new URLSearchParams();
    params.set('q', searchInput.trim());
    if (activeTab !== 'all') {
      params.set('domain', activeTab);
    }
    navigate(`/search?${params.toString()}`);
  };

  const handleClearSearch = () => {
    setSearchInput('');
  };

  // Filter items based on active domain tab
  const allResults = data?.results || [];
  const movieCount = allResults.filter((r) => String(r.media_type).toLowerCase() === 'movie').length;
  const animeCount = allResults.filter((r) => String(r.media_type).toLowerCase() === 'anime').length;
  const bookCount = allResults.filter((r) => String(r.media_type).toLowerCase() === 'book').length;

  const filteredResults = allResults.filter((item) => {
    if (activeTab === 'all') return true;
    return String(item.media_type).toLowerCase() === activeTab;
  });

  return (
    <div className="results-page-layout">
      {/* Search Header Bar with Pill Search Input */}
      <div className="results-top-search-strip">
        <div className="results-strip-inner">
          <form className="strip-search-form" onSubmit={handleSearchSubmit}>
            <div className="strip-search-pill">
              <Search size={16} className="strip-search-icon" />
              <input
                type="text"
                className="strip-search-input"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="Search..."
              />
              {searchInput && (
                <button
                  type="button"
                  className="strip-clear-btn"
                  onClick={handleClearSearch}
                  aria-label="Clear input"
                >
                  <X size={14} />
                </button>
              )}
            </div>
          </form>
        </div>
      </div>

      {/* Main Body */}
      <main className="results-page-body">
        {loading ? (
          <div className="results-loading-box" role="status">
            <RefreshCw size={36} className="spin-icon purple" />
            <h2>Retrieving Ranked Results...</h2>
            <p>Searching catalogs across movies, anime, and books.</p>
          </div>
        ) : error ? (
          <ErrorState
            message={error}
            onRetry={() => executeSearch(queryParam, domainParam)}
          />
        ) : !data || allResults.length === 0 ? (
          <NoResults
            query={queryParam}
            onResetSearch={() => navigate('/')}
          />
        ) : (
          <div className="results-content-group animate-fade-in">
            {/* Heading: Search Results for "time travel" */}
            <div className="results-title-row">
              <h1 className="results-query-title">
                Search Results for <span className="query-highlight">"{queryParam}"</span>
              </h1>
            </div>

            {/* Filter Tabs and Sort Dropdown */}
            <div className="results-controls-row">
              <div className="results-domain-pills" role="tablist">
                <button
                  type="button"
                  className={`domain-count-pill ${activeTab === 'all' ? 'active' : ''}`}
                  onClick={() => setActiveTab('all')}
                >
                  All ({allResults.length})
                </button>

                <button
                  type="button"
                  className={`domain-count-pill ${activeTab === 'movie' ? 'active' : ''}`}
                  onClick={() => setActiveTab('movie')}
                >
                  Movies ({movieCount})
                </button>

                <button
                  type="button"
                  className={`domain-count-pill ${activeTab === 'anime' ? 'active' : ''}`}
                  onClick={() => setActiveTab('anime')}
                >
                  Anime ({animeCount})
                </button>

                <button
                  type="button"
                  className={`domain-count-pill ${activeTab === 'book' ? 'active' : ''}`}
                  onClick={() => setActiveTab('book')}
                >
                  Books ({bookCount})
                </button>
              </div>

              {/* Sort Dropdown */}
              <div className="sort-dropdown-wrap">
                <button type="button" className="sort-dropdown-btn">
                  <span>Sort by: Relevance</span>
                  <ChevronDown size={14} />
                </button>
              </div>
            </div>

            {/* Vertically Stacked Numbered Results List */}
            <div className="ranked-results-stack" role="feed">
              {filteredResults.map((item: SearchResultItem, index: number) => (
                <ResultCard
                  key={item.id}
                  item={item}
                  rank={index + 1}
                />
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
};
