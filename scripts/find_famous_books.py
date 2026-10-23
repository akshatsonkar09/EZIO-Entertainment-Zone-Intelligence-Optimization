import pandas as pd
from project_black_knight.retrieval import RetrievalRepository

repo = RetrievalRepository()
books_df = repo.get_metadata_df('book')

authors = ['Stephen King', 'Brandon Sanderson', 'Neil Gaiman', 'Agatha Christie', 'Suzanne Collins', 'Arthur Conan Doyle']

for a in authors:
    sub = books_df[books_df['author'].str.contains(a, case=False, na=False)]
    print(f"\n=== Books by {a} ({len(sub)}) ===")
    for idx, r in sub.head(5).iterrows():
        print(f"  book_{idx}: '{r['title']}' | Rating: {r['rating']} | Pages: {r.get('pages')}")

print("\n=== Check specific famous books ===")
for t in ['Brave New World', 'Hunger Games', 'Frankenstein', 'Dracula', 'Way of Kings', 'Final Empire', 'Sherlock', 'Murder on the Orient Express', 'Da Vinci Code']:
    m = books_df[books_df['title'].str.contains(t, case=False, na=False)]
    print(f"'{t}': {len(m)} matches -> {[(f'book_{i}', row_['title']) for i, row_ in m.head(3).iterrows()]}")
