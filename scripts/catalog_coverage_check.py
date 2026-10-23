import pandas as pd
from project_black_knight.retrieval import RetrievalRepository

repo = RetrievalRepository()
movies_df = repo.get_metadata_df('movie')
animes_df = repo.get_metadata_df('anime')
books_df = repo.get_metadata_df('book')
music_df = repo.get_metadata_df('music')

print("=== CHECKING AUTHORS IN BOOKS ===")
for author in ['Stephen King', 'J.K. Rowling', 'George R.R. Martin', 'Neil Gaiman', 'Agatha Christie', 'Brandon Sanderson', 'Rick Riordan', 'Suzanne Collins', 'Arthur Conan Doyle', 'Jane Austen']:
    m = books_df[books_df['author'].str.contains(author, case=False, na=False)]
    print(f"Author '{author}': {len(m)} books. Sample titles: {m['title'].head(3).tolist()}")

print("\n=== CHECKING POPULAR BOOK TITLES ===")
for t in ['Game of Thrones', 'Lightning Thief', 'Shining', 'American Gods', 'And Then There Were None', 'Way of Kings', 'Hunger Games', 'Catching Fire', 'Mockingjay', 'Golden Compass', 'Ender', 'Dune', 'Fahrenheit', 'Brave New World']:
    m = books_df[books_df['title'].str.contains(t, case=False, na=False)]
    print(f"Book '{t}': {len(m)} matches. Sample: {m['title'].head(2).tolist()}")

print("\n=== CHECKING MUSIC ARTISTS ===")
for artist in ['The Beatles', 'Led Zeppelin', 'Queen', 'Taylor Swift', 'Ed Sheeran', 'Michael Jackson', 'Ariana Grande', 'Daft Punk', 'Billie Eilish', 'Adele', 'Eminem', 'Drake', 'Coldplay', 'The Weeknd']:
    m = music_df[music_df['artist'].str.contains(artist, case=False, na=False)]
    print(f"Artist '{artist}': {len(m)} tracks. Sample: {m['track_name'].head(2).tolist()}")
