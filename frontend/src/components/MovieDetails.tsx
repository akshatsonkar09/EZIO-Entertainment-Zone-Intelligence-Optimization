import React from 'react';
import { User, Users, Building, Calendar, Clock, DollarSign } from 'lucide-react';

interface MovieDetailsProps {
  metadata: Record<string, any>;
  releaseDate?: string | null;
}

export const MovieDetails: React.FC<MovieDetailsProps> = ({ metadata, releaseDate }) => {
  const director = metadata.director;
  const cast = metadata.cast;
  const companies = metadata.production_companies;
  const runtime = metadata.runtime;
  const revenue = metadata.revenue;
  const date = releaseDate || metadata.release_date;

  const sections: Array<{ label: string; icon: React.ReactNode; value: React.ReactNode }> = [];

  if (director) {
    sections.push({
      label: 'Director',
      icon: <User size={16} />,
      value: String(director),
    });
  }

  if (cast) {
    const castList = String(cast)
      .split(',')
      .map((c) => c.trim().replace(/['"\[\]]/g, ''))
      .filter(Boolean);

    sections.push({
      label: 'Cast',
      icon: <Users size={16} />,
      value: (
        <div className="detail-tags-wrap">
          {castList.map((actor, idx) => (
            <span key={idx} className="detail-tag">
              {actor}
            </span>
          ))}
        </div>
      ),
    });
  }

  if (date) {
    sections.push({
      label: 'Release Date',
      icon: <Calendar size={16} />,
      value: String(date),
    });
  }

  if (runtime && Number(runtime) > 0) {
    sections.push({
      label: 'Runtime',
      icon: <Clock size={16} />,
      value: `${Math.round(Number(runtime))} minutes`,
    });
  }

  if (revenue && Number(revenue) > 0) {
    sections.push({
      label: 'Box Office Revenue',
      icon: <DollarSign size={16} />,
      value: `$${Number(revenue).toLocaleString()}`,
    });
  }

  if (companies) {
    const companyList = String(companies)
      .split(',')
      .map((c) => c.trim().replace(/['"\[\]]/g, ''))
      .filter(Boolean);

    sections.push({
      label: 'Production Companies',
      icon: <Building size={16} />,
      value: (
        <div className="detail-tags-wrap">
          {companyList.map((comp, idx) => (
            <span key={idx} className="detail-tag company-tag">
              {comp}
            </span>
          ))}
        </div>
      ),
    });
  }

  if (sections.length === 0) {
    return null;
  }

  return (
    <div className="domain-specific-section">
      <h3 className="section-heading">Movie Details</h3>
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
