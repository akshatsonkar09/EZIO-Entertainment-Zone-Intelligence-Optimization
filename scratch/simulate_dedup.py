import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import pandas as pd
import numpy as np
from project_black_knight.text_normalizer import normalize_title, normalize_title_key

raw = pd.read_csv('data/raw/anime/animes.csv')
clean = pd.read_csv('data/processed/anime_metadata_clean.csv')
pkl = pd.read_pickle('data/processed/anime.pkl')
tag2 = pd.read_pickle('data/processed/anime_tag2.pkl')
embs = np.load('data/processed/embeddings/anime_embeddings.npy')

pkl = pkl.reset_index(drop=True)
tag2 = tag2.reset_index(drop=True)
clean = clean.reset_index(drop=True)

print(f"Original clean shape: {clean.shape}")
print(f"Original pkl shape: {pkl.shape}")
print(f"Original tag2 shape: {tag2.shape}")
print(f"Original embs shape: {embs.shape}")

# Identify duplicates by UID (first occurrence is canonical)
canonical_mask = ~pkl.duplicated(subset=['uid'], keep='first')
duplicate_mask = pkl.duplicated(subset=['uid'], keep='first')

num_canonical = canonical_mask.sum()
num_duplicates = duplicate_mask.sum()
num_groups = pkl[duplicate_mask]['uid'].nunique()

print(f"\nUnique canonical anime records: {num_canonical}")
print(f"Redundant duplicate records to remove: {num_duplicates}")
print(f"Number of duplicate groups: {num_groups}")

# Check key anime rows in canonical set
fma_2003 = pkl[canonical_mask & (pkl['title'] == 'Fullmetal Alchemist')]
print(f"\nCanonical Fullmetal Alchemist: index {fma_2003.index.tolist()}, UID {fma_2003['uid'].tolist()}")

fma_bro = pkl[canonical_mask & (pkl['title'] == 'Fullmetal Alchemist: Brotherhood')]
print(f"Canonical FMA Brotherhood: index {fma_bro.index.tolist()}, UID {fma_bro['uid'].tolist()}")

cowboy = pkl[canonical_mask & (pkl['title'] == 'Cowboy Bebop')]
print(f"Canonical Cowboy Bebop: index {cowboy.index.tolist()}, UID {cowboy['uid'].tolist()}")

snk = pkl[canonical_mask & (pkl['title'] == 'Shingeki no Kyojin')]
print(f"Canonical Shingeki no Kyojin: index {snk.index.tolist()}, UID {snk['uid'].tolist()}")

# Check if any non-UID duplicate exists that is identical in (norm_title, release_year, episodes)
clean_canonical = clean[canonical_mask].copy()
clean_canonical['norm_title'] = clean_canonical['title'].astype(str).apply(normalize_title)

# Group by (norm_title, release_year, episodes)
meta_dups = clean_canonical[clean_canonical.duplicated(subset=['norm_title', 'release_year', 'episodes'], keep=False)]
print(f"\nNon-UID duplicates with identical (norm_title, release_year, episodes): {len(meta_dups)}")
if len(meta_dups) > 0:
    for _, r in meta_dups.iterrows():
        print(f"  Title: {r['title']}, Year: {r['release_year']}, Eps: {r['episodes']}")
