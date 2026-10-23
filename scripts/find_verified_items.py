import pandas as pd
from project_black_knight.retrieval import RetrievalRepository

repo = RetrievalRepository()
books_df = repo.get_metadata_df('book')
music_df = repo.get_metadata_df('music')
animes_df = repo.get_metadata_df('anime')

print("=== CHECKING TAYLOR SWIFT IN MUSIC ===")
ts = music_df[music_df['artist'].str.contains('Taylor Swift', case=False, na=False)]
print("Taylor Swift albums:", ts['album'].value_counts().head(10))
print("Taylor Swift tracks:", ts['track_name'].head(5).tolist())

print("\n=== CHECKING EMINEM IN MUSIC ===")
em = music_df[music_df['artist'].str.contains('Eminem', case=False, na=False)]
print("Eminem tracks:", em['track_name'].head(10).tolist())

print("\n=== CHECKING ANIME ABSENCES ===")
for cand in ['Solo Leveling', 'Kaiju No. 8', 'Chainsaw Man', 'Jujutsu Kaisen', 'Spy x Family']:
    m = animes_df[animes_df['title'].str.contains(cand, case=False, na=False)]
    print(f"'{cand}': {len(m)} matches")

print("\n=== CHECKING MUSIC ABSENCES ===")
for cand in ['Espresso', 'Vampire', 'Cruel Summer', 'Paint The Town Red']:
    m = music_df[music_df['track_name'].str.contains(cand, case=False, na=False)]
    print(f"'{cand}': {len(m)} matches")

print("\n=== CHECKING POPULAR BOOKS IN CATALOG ===")
# Top rated books with high ratings and known titles
top_books = books_df[books_df['rating'] > 4.2].sort_values(by='rating', ascending=False)
print("Top books sample:")
for idx, r in top_books.head(15).iterrows():
    print(f"book_{idx}: '{r['title']}' by {r['author']} | Rating: {r['rating']} | Pages: {r.get('pages')} | Publisher: {r.get('publisher')}")
