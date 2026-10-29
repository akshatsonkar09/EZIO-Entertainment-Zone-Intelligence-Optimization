import React from 'react';
import { Film, Sparkles, BookOpen } from 'lucide-react';
import type { DomainType } from '../types';

interface DomainIconProps {
  domain: DomainType | string;
  size?: number;
}

export const DomainIcon: React.FC<DomainIconProps> = ({ domain, size = 16 }) => {
  const norm = String(domain).toLowerCase();
  switch (norm) {
    case 'movie':
      return <Film size={size} className="domain-icon-svg" aria-hidden="true" />;
    case 'anime':
      return <Sparkles size={size} className="domain-icon-svg" aria-hidden="true" />;
    case 'book':
      return <BookOpen size={size} className="domain-icon-svg" aria-hidden="true" />;
    default:
      return <Film size={size} className="domain-icon-svg" aria-hidden="true" />;
  }
};

export const DomainBadge: React.FC<{ domain: DomainType | string }> = ({ domain }) => {
  const norm = String(domain).toLowerCase();
  const label = norm === 'movie' ? 'Movie' : norm === 'anime' ? 'Anime' : 'Book';
  return (
    <span className={`domain-badge ${norm}`}>
      <DomainIcon domain={norm} size={12} />
      <span>{label}</span>
    </span>
  );
};
