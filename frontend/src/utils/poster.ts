/**
 * Helper to generate consistent, attractive gradient thumbnails for catalog items.
 */
export function getPosterGradient(title: string, domain: string): { bg: string; accent: string; icon: string } {
  const norm = String(domain).toLowerCase();
  let hash = 0;
  for (let i = 0; i < title.length; i++) {
    hash = title.charCodeAt(i) + ((hash << 5) - hash);
  }

  if (norm === 'anime') {
    const animePalettes = [
      { bg: 'linear-gradient(135deg, #4a154b 0%, #1e1b4b 60%, #0f172a 100%)', accent: '#f472b6', icon: '🎌' },
      { bg: 'linear-gradient(135deg, #831843 0%, #312e81 60%, #090d16 100%)', accent: '#fb7185', icon: '✨' },
      { bg: 'linear-gradient(135deg, #581c87 0%, #172554 60%, #030712 100%)', accent: '#c084fc', icon: '⚡' },
    ];
    return animePalettes[Math.abs(hash) % animePalettes.length];
  } else if (norm === 'book') {
    const bookPalettes = [
      { bg: 'linear-gradient(135deg, #713f12 0%, #1c1917 60%, #0c0a09 100%)', accent: '#fbbf24', icon: '📖' },
      { bg: 'linear-gradient(135deg, #14532d 0%, #1e293b 60%, #020617 100%)', accent: '#4ade80', icon: '📚' },
      { bg: 'linear-gradient(135deg, #7c2d12 0%, #312e81 60%, #090d16 100%)', accent: '#fb923c', icon: '📜' },
    ];
    return bookPalettes[Math.abs(hash) % bookPalettes.length];
  } else {
    // movie
    const moviePalettes = [
      { bg: 'linear-gradient(135deg, #1e3a8a 0%, #0f172a 60%, #020617 100%)', accent: '#38bdf8', icon: '🎬' },
      { bg: 'linear-gradient(135deg, #6b21a8 0%, #1e1b4b 60%, #030712 100%)', accent: '#a855f7', icon: '🌌' },
      { bg: 'linear-gradient(135deg, #3730a3 0%, #111827 60%, #000000 100%)', accent: '#818cf8', icon: '🚀' },
      { bg: 'linear-gradient(135deg, #0369a1 0%, #1f2937 60%, #030712 100%)', accent: '#22d3ee', icon: '🪐' },
    ];
    return moviePalettes[Math.abs(hash) % moviePalettes.length];
  }
}
