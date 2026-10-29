import React from 'react';
import { User, Star, Hash, BookOpen, Building, Calendar, Users } from 'lucide-react';

interface BookDetailsProps {
  metadata: Record<string, any>;
}

export const BookDetails: React.FC<BookDetailsProps> = ({ metadata }) => {
  const author = metadata.author;
  const rating = metadata.rating;
  const isbn = metadata.isbn;
  const publisher = metadata.publisher;
  const publishDate = metadata.publish_date;
  const pages = metadata.pages;
  const characters = metadata.characters;

  const sections: Array<{ label: string; icon: React.ReactNode; value: React.ReactNode }> = [];

  if (author) {
    sections.push({
      label: 'Author',
      icon: <User size={16} />,
      value: String(author),
    });
  }

  if (rating && Number(rating) > 0) {
    sections.push({
      label: 'Catalog Rating',
      icon: <Star size={16} />,
      value: `★ ${Number(rating).toFixed(2)} / 5.0`,
    });
  }

  if (pages && Number(pages) > 0) {
    sections.push({
      label: 'Page Count',
      icon: <BookOpen size={16} />,
      value: `${Math.round(Number(pages))} pages`,
    });
  }

  if (publisher) {
    sections.push({
      label: 'Publisher',
      icon: <Building size={16} />,
      value: String(publisher),
    });
  }

  if (publishDate) {
    sections.push({
      label: 'Publication Date',
      icon: <Calendar size={16} />,
      value: String(publishDate),
    });
  }

  if (isbn && String(isbn).trim() !== '0') {
    sections.push({
      label: 'ISBN',
      icon: <Hash size={16} />,
      value: String(isbn),
    });
  }

  if (characters) {
    const charsList = String(characters)
      .split(',')
      .map((c) => c.trim())
      .filter(Boolean);

    if (charsList.length > 0) {
      sections.push({
        label: 'Notable Characters',
        icon: <Users size={16} />,
        value: (
          <div className="detail-tags-wrap">
            {charsList.map((char, idx) => (
              <span key={idx} className="detail-tag character-tag">
                {char}
              </span>
            ))}
          </div>
        ),
      });
    }
  }

  if (sections.length === 0) {
    return null;
  }

  return (
    <div className="domain-specific-section">
      <h3 className="section-heading">Book Details</h3>
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
