import React, { createContext, useContext, useState, useEffect } from 'react';
import type { SearchResultItem, ItemDetail } from '../types';

interface BookmarkContextType {
  bookmarks: SearchResultItem[];
  bookmarksCount: number;
  isBookmarked: (id: string) => boolean;
  toggleBookmark: (item: SearchResultItem | ItemDetail) => void;
  removeBookmark: (id: string) => void;
  clearBookmarks: () => void;
}

const STORAGE_KEY = 'pbk_bookmarks_v1';

const BookmarkContext = createContext<BookmarkContextType | undefined>(undefined);

// Helper to normalize either SearchResultItem or ItemDetail into SearchResultItem
function normalizeToSearchResultItem(item: SearchResultItem | ItemDetail): SearchResultItem {
  if ('score' in item) {
    return item;
  }

  // ItemDetail structure
  const detail = item as ItemDetail;
  const genresStr = Array.isArray(detail.genres) ? detail.genres.join(', ') : '';

  return {
    id: detail.id,
    title: detail.title,
    media_type: detail.media_type,
    score: 1.0,
    release_year: detail.release_year,
    genres: genresStr,
    overview: detail.overview,
    extra: detail.metadata || {},
  };
}

export const BookmarkProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [bookmarks, setBookmarks] = useState<SearchResultItem[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed)) {
          return parsed;
        }
      }
    } catch (e) {
      console.warn('Failed to parse bookmarks from localStorage:', e);
    }
    return [];
  });

  // Sync to localStorage whenever bookmarks changes
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(bookmarks));
    } catch (e) {
      console.warn('Failed to save bookmarks to localStorage:', e);
    }
  }, [bookmarks]);

  const isBookmarked = (id: string): boolean => {
    return bookmarks.some((b) => b.id === id);
  };

  const toggleBookmark = (item: SearchResultItem | ItemDetail) => {
    const normalized = normalizeToSearchResultItem(item);
    setBookmarks((prev) => {
      const exists = prev.some((b) => b.id === normalized.id);
      if (exists) {
        return prev.filter((b) => b.id !== normalized.id);
      } else {
        // Prepend newest bookmark
        return [normalized, ...prev];
      }
    });
  };

  const removeBookmark = (id: string) => {
    setBookmarks((prev) => prev.filter((b) => b.id !== id));
  };

  const clearBookmarks = () => {
    setBookmarks([]);
  };

  return (
    <BookmarkContext.Provider
      value={{
        bookmarks,
        bookmarksCount: bookmarks.length,
        isBookmarked,
        toggleBookmark,
        removeBookmark,
        clearBookmarks,
      }}
    >
      {children}
    </BookmarkContext.Provider>
  );
};

export const useBookmarks = (): BookmarkContextType => {
  const context = useContext(BookmarkContext);
  if (!context) {
    throw new Error('useBookmarks must be used within a BookmarkProvider');
  }
  return context;
};
