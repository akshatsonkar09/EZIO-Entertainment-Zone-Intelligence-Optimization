import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import pandas as pd
import chromadb

raw = pd.read_csv('data/raw/anime/animes.csv')
clean = pd.read_csv('data/processed/anime_metadata_clean.csv')
meta = pd.read_csv('data/processed/anime_metadata.csv')
pkl = pd.read_pickle('data/processed/anime.pkl')
tag2 = pd.read_pickle('data/processed/anime_tag2.pkl')

print("=== RAW (animes.csv) ===")
print("Total rows:", len(raw))
print("Unique uids:", raw['uid'].nunique())
print("Duplicate uids count:", raw.duplicated(subset=['uid']).sum())
print("Exact duplicate rows:", raw.duplicated().sum())

print("\n=== PROCESSED (anime.pkl) ===")
print("Total rows:", len(pkl))
print("Unique uids:", pkl['uid'].nunique())
print("Duplicate uids count:", pkl.duplicated(subset=['uid']).sum())
print("Exact duplicate rows:", pkl.duplicated().sum())

print("\n=== PROCESSED (anime_tag2.pkl) ===")
print("Total rows:", len(tag2))
print("Unique uids:", tag2['uid'].nunique())
print("Duplicate uids count:", tag2.duplicated(subset=['uid']).sum())

print("\n=== METADATA (anime_metadata_clean.csv) ===")
print("Total rows:", len(clean))
print("Exact duplicate rows:", clean.duplicated().sum())

# Let's check the alignment between pkl, clean, tag2
print("\nIs pkl['title'] equal to clean['title']?:", (pkl['title'].fillna('') == clean['title'].fillna('')).all())
print("Is pkl['title'] equal to tag2['title']?:", (pkl['title'].fillna('') == tag2['title'].fillna('')).all())
print("Is pkl['uid'] equal to tag2['uid']?:", (pkl['uid'] == tag2['uid']).all())
