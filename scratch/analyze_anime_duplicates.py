import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import pandas as pd
from project_black_knight.text_normalizer import normalize_title, normalize_title_key

raw = pd.read_csv('data/raw/anime/animes.csv')
clean = pd.read_csv('data/processed/anime_metadata_clean.csv')

print(f"Total rows in raw: {len(raw)}")
print(f"Unique UIDs in raw: {raw['uid'].nunique()}")

# Drop duplicate UIDs
raw_unique_uid = raw.drop_duplicates(subset=['uid']).copy()
raw_unique_uid['norm_title'] = raw_unique_uid['title'].astype(str).apply(normalize_title)

title_counts = raw_unique_uid['norm_title'].value_counts()
dup_titles = title_counts[title_counts > 1]
print(f"Number of normalized titles with >1 distinct UID: {len(dup_titles)}")

with open('scratch/dup_titles.txt', 'w', encoding='utf-8') as out:
    out.write(f"Total rows in raw: {len(raw)}\n")
    out.write(f"Unique UIDs in raw: {raw['uid'].nunique()}\n")
    out.write(f"Number of normalized titles with >1 distinct UID: {len(dup_titles)}\n")
    for t in dup_titles.index:
        subset = raw_unique_uid[raw_unique_uid['norm_title'] == t]
        out.write(f"\n=== Title: '{t}' ({len(subset)} entries with different UIDs) ===\n")
        for _, r in subset.iterrows():
            out.write(f"  UID: {r['uid']}, Title: '{r['title']}', Aired: {r['aired']}, Episodes: {r['episodes']}, Link: {r['link']}\n")
