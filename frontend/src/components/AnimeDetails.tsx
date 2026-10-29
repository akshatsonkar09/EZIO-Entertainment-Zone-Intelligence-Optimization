import React from 'react';
import { Calendar, Layers, TrendingUp, Award } from 'lucide-react';

interface AnimeDetailsProps {
  metadata: Record<string, any>;
}

export const AnimeDetails: React.FC<AnimeDetailsProps> = ({ metadata }) => {
  const episodes = metadata.episodes;
  const aired = metadata.aired;
  const popularity = metadata.popularity;
  const ranking = metadata.ranking;

  const sections: Array<{ label: string; icon: React.ReactNode; value: React.ReactNode }> = [];

  if (episodes && Number(episodes) > 0) {
    sections.push({
      label: 'Episodes',
      icon: <Layers size={16} />,
      value: `${Math.round(Number(episodes))} Episodes`,
    });
  }

  if (aired) {
    sections.push({
      label: 'Aired Period',
      icon: <Calendar size={16} />,
      value: String(aired),
    });
  }

  if (ranking && Number(ranking) > 0) {
    sections.push({
      label: 'Rank',
      icon: <Award size={16} />,
      value: `#${Math.round(Number(ranking))}`,
    });
  }

  if (popularity && Number(popularity) > 0) {
    sections.push({
      label: 'Popularity',
      icon: <TrendingUp size={16} />,
      value: `#${Math.round(Number(popularity))}`,
    });
  }

  if (sections.length === 0) {
    return null;
  }

  return (
    <div className="domain-specific-section">
      <h3 className="section-heading">Anime Details</h3>
      <div className="details-grid">
        {sections.map((sec, idx) => (
          <div key={idx} className="detail-item">
            <span className="detail-label">
              {sec.icon}
              <span>{sec.label}</span>
            </span>
            <div className="detail-value">{sec.value}</div>
          </div>
        ))}
      </div>
    </div>
  );
};
