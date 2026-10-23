import pandas as pd
import json

movies_df = pd.read_csv("data/processed/movie_metadata_clean.csv")
anime_df = pd.read_csv("data/processed/anime_metadata_clean.csv")
book_df = pd.read_csv("data/processed/book_metadata_clean.csv")

with open("scratch/all_known_queries.json", "r", encoding="utf-8") as f:
    known_queries = json.load(f)

# Also collect all titles mentioned in known queries or existing benchmarks
known_titles = set()
for q in known_queries:
    known_titles.add(q.lower())

for df, domain in [(movies_df, "movie"), (anime_df, "anime"), (book_df, "book")]:
    print(f"Domain {domain}: {len(df)} items")

# Let's inspect some candidate titles and genres
print("Movie sample:")
print(movies_df[["title", "genres", "release_date", "director"]].head(10))

print("\nAnime sample:")
print(anime_df[["title", "genres", "release_year", "ranking"]].head(10))

print("\nBook sample:")
print(book_df[["title", "author", "genres", "rating"]].head(10))
