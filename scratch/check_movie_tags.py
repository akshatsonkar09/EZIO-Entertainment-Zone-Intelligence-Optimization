"""
Check if movies1234.pkl tag contains the movie title
"""
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
df_pkl = pd.read_pickle(PROJECT_ROOT / "data" / "processed" / "movies1234.pkl")
df_meta = pd.read_csv(PROJECT_ROOT / "data" / "processed" / "movie_metadata_clean.csv")

for i in [0, 1, 2, 65, 95, 96]:
    title = df_meta.iloc[i]["title"]
    tag = df_pkl.iloc[i]["tag"]
    print(f"[{i}] Title: '{title}'")
    print(f"    In tag? {title.lower() in tag.lower()}")
    print(f"    Tag start: {tag[:120]}...\n")
