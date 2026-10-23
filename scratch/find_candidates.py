import pandas as pd

movies_df = pd.read_csv("data/processed/movie_metadata_clean.csv")
anime_df = pd.read_csv("data/processed/anime_metadata_clean.csv")
book_df = pd.read_csv("data/processed/book_metadata_clean.csv")

def search_movies(q):
    sub = movies_df[movies_df["title"].str.contains(q, case=False, na=False)]
    for idx, r in sub.head(5).iterrows():
        print(f"movie_{idx}: '{r['title']}' | Dir: {r.get('director')} | Year: {r.get('release_date')} | Genres: {r.get('genres')} | Runtime: {r.get('runtime')}")

def search_anime(q):
    sub = anime_df[anime_df["title"].str.contains(q, case=False, na=False)]
    for idx, r in sub.head(5).iterrows():
        print(f"anime_{idx}: '{r['title']}' | Year: {r.get('release_year')} | Ep: {r.get('episodes')} | Rank: {r.get('ranking')} | Genres: {r.get('genres')}")

def search_books(q):
    sub = book_df[book_df["title"].str.contains(q, case=False, na=False)]
    for idx, r in sub.head(5).iterrows():
        print(f"book_{idx}: '{r['title']}' | Author: {r.get('author')} | Rating: {r.get('rating')} | Pages: {r.get('pages')} | Genres: {r.get('genres')}")

print("--- CANDIDATE MOVIES ---")
for t in ["Memento", "The Prestige", "Whiplash", "Blade Runner", "Alien", "The Matrix", "Pulp Fiction", "Fargo", "Fight Club", "The Truman Show", "Pan's Labyrinth", "Arrival"]:
    search_movies(t)

print("\n--- CANDIDATE ANIME ---")
for t in ["Psycho-Pass", "Mushishi", "Monster", "Steins;Gate", "Erased", "Ping Pong", "Samurai Champloo", "Mob Psycho", "Haikyuu", "Fate/Zero"]:
    search_anime(t)

print("\n--- CANDIDATE BOOKS ---")
for t in ["Neuromancer", "Fahrenheit 451", "Brave New World", "Frankenstein", "The Road", "Foundation", "Snow Crash", "1984", "Animal Farm", "The Hobbit"]:
    search_books(t)
