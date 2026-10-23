import pandas as pd
import json
import re

movies_df = pd.read_csv("data/processed/movie_metadata_clean.csv")
anime_df = pd.read_csv("data/processed/anime_metadata_clean.csv")
book_df = pd.read_csv("data/processed/book_metadata_clean.csv")

with open("scratch/all_known_queries.json", "r", encoding="utf-8") as f:
    known_queries = json.load(f)

# Helper to verify no leakage with any existing query
def check_overlap(query_text: str):
    q_low = query_text.lower().strip()
    for kq in known_queries:
        if q_low == kq or (len(q_low) > 15 and q_low in kq) or (len(kq) > 15 and kq in q_low):
            return kq
    return None

print("Catalogs loaded successfully.")
