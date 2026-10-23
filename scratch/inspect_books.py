import pandas as pd

book_df = pd.read_csv("data/processed/book_metadata_clean.csv")
print("Top 25 books:")
for idx, r in book_df.head(25).iterrows():
    print(f"book_{idx}: '{r['title']}' by '{r['author']}' | Genres: {r.get('genres')} | Rating: {r.get('rating')} | Pages: {r.get('pages')}")
