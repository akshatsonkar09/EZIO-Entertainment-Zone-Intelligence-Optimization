import pandas as pd
import json
import re

movies_df = pd.read_csv("data/processed/movie_metadata_clean.csv")
anime_df = pd.read_csv("data/processed/anime_metadata_clean.csv")
book_df = pd.read_csv("data/processed/book_metadata_clean.csv")

with open("scratch/all_known_queries.json", "r", encoding="utf-8") as f:
    known_queries = json.load(f)

# Helper to check if string or title overlaps with known queries
def has_leakage(text: str) -> bool:
    t_clean = text.lower().strip()
    for kq in known_queries:
        if t_clean in kq or kq in t_clean:
            return True
    return False

# Search helper for movies
def find_movie(title_substr=None, director=None, genre=None):
    df = movies_df
    if title_substr:
        df = df[df["title"].str.contains(title_substr, case=False, na=False)]
    if director:
        df = df[df["director"].str.contains(director, case=False, na=False)]
    if genre:
        df = df[df["genres"].str.contains(genre, case=False, na=False)]
    res = []
    for idx, r in df.head(10).iterrows():
        res.append({
            "id": f"movie_{idx}",
            "title": r["title"],
            "director": r.get("director"),
            "release_date": r.get("release_date"),
            "genres": r.get("genres"),
            "runtime": r.get("runtime"),
            "revenue": r.get("revenue")
        })
    return res

# Search helper for anime
def find_anime(title_substr=None, genre=None, min_rank=None, max_rank=None):
    df = anime_df
    if title_substr:
        df = df[df["title"].str.contains(title_substr, case=False, na=False)]
    if genre:
        df = df[df["genres"].str.contains(genre, case=False, na=False)]
    if max_rank is not None:
        df = df[df["ranking"] <= max_rank]
    res = []
    for idx, r in df.head(10).iterrows():
        res.append({
            "id": f"anime_{idx}",
            "title": r["title"],
            "genres": r.get("genres"),
            "release_year": r.get("release_year"),
            "episodes": r.get("episodes"),
            "ranking": r.get("ranking"),
            "popularity": r.get("popularity")
        })
    return res

# Search helper for books
def find_book(title_substr=None, author=None, genre=None):
    df = book_df
    if title_substr:
        df = df[df["title"].str.contains(title_substr, case=False, na=False)]
    if author:
        df = df[df["author"].str.contains(author, case=False, na=False)]
    if genre:
        df = df[df["genres"].str.contains(genre, case=False, na=False)]
    res = []
    for idx, r in df.head(10).iterrows():
        res.append({
            "id": f"book_{idx}",
            "title": r["title"],
            "author": r.get("author"),
            "genres": r.get("genres"),
            "rating": r.get("rating"),
            "pages": r.get("pages")
        })
    return res

print("Find Gattaca:", find_movie("Gattaca"))
print("Find Vinland Saga:", find_anime("Vinland Saga"))
print("Find Dune:", find_book(title_substr="^Dune$"))
