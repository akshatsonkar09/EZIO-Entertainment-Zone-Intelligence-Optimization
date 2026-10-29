import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { BookmarkProvider } from './context/BookmarkContext';
import { Navbar } from './components/Navbar';
import { RandomModal } from './components/RandomModal';
import { HomePage } from './pages/HomePage';
import { SearchResultsPage } from './pages/SearchResultsPage';
import { DetailPage } from './pages/DetailPage';
import { BrowsePage } from './pages/BrowsePage';
import { ExplorePage } from './pages/ExplorePage';
import { BookmarksPage } from './pages/BookmarksPage';
import { RandomPage } from './pages/RandomPage';

export const App: React.FC = () => {
  const [randomModalOpen, setRandomModalOpen] = useState<boolean>(false);

  return (
    <BookmarkProvider>
      <BrowserRouter>
        <div className="app-container">
          <Navbar onOpenRandom={() => setRandomModalOpen(true)} />

          <div className="main-content">
            <Routes>
              <Route path="/" element={<HomePage onOpenRandom={() => setRandomModalOpen(true)} />} />
              <Route path="/search" element={<SearchResultsPage />} />
              <Route path="/item/:itemId" element={<DetailPage />} />
              <Route path="/browse" element={<BrowsePage />} />
              <Route path="/explore" element={<ExplorePage />} />
              <Route path="/bookmarks" element={<BookmarksPage />} />
              <Route path="/random" element={<RandomPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </div>

          <RandomModal
            isOpen={randomModalOpen}
            onClose={() => setRandomModalOpen(false)}
          />
        </div>
      </BrowserRouter>
    </BookmarkProvider>
  );
};

export default App;
