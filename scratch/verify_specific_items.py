import pandas as pd
import json

movies_df = pd.read_csv("data/processed/movie_metadata_clean.csv")
anime_df = pd.read_csv("data/processed/anime_metadata_clean.csv")
book_df = pd.read_csv("data/processed/book_metadata_clean.csv")

def check_movie(title_exact=None, dir_exact=None):
    df = movies_df
    if title_exact:
        df = df[df["title"].str.lower() == title_exact.lower()]
    for idx, r in df.iterrows():
        print(f"movie_{idx}: '{r['title']}' | Dir: {r.get('director')} | Year: {r.get('release_date')} | Genres: {r.get('genres')} | Runtime: {r.get('runtime')} | Rev: {r.get('revenue')}")

def check_anime(title_exact=None):
    df = anime_df
    if title_exact:
        df = df[df["title"].str.lower() == title_exact.lower()]
    for idx, r in df.iterrows():
        print(f"anime_{idx}: '{r['title']}' | Year: {r.get('release_year')} | Ep: {r.get('episodes')} | Rank: {r.get('ranking')} | Pop: {r.get('popularity')} | Genres: {r.get('genres')}")

def check_book(title_exact=None, author_exact=None):
    df = book_df
    if title_exact:
        df = df[df["title"].str.lower() == title_exact.lower()]
    if author_exact:
        df = df[df["author"].str.contains(author_exact, case=False, na=False)]
    for idx, r in df.iterrows():
        print(f"book_{idx}: '{r['title']}' | Author: {r.get('author')} | Pages: {r.get('pages')} | Rating: {r.get('rating')} | Genres: {r.get('genres')} | Pub: {r.get('publisher')}")

print("=== BOOKS ===")
for b in ["Neuromancer", "Fahrenheit 451", "The Road", "Foundation", "Snow Crash", "The Da Vinci Code", "Gone Girl", "The Book Thief", "Life of Pi", "Divergent", "The Alchemist"]:
    print(f"\nSearch for book '{b}':")
    check_book(title_exact=b)

print("\n=== ANIME ===")
for a in ["Mushishi", "Monster", "Fate/Zero", "Steins;Gate 0", "Hyouka", "Toradora!", "Baccano!", "Noragami"]:
    print(f"\nSearch for anime '{a}':")
    check_anime(title_exact=a)
