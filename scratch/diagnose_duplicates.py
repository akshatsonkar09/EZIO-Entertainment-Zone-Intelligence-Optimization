import pandas as pd
from project_black_knight.retrieval import _REPO, search_black_knight

df = _REPO.get_metadata_df('anime')
fma_rows = df[df['title'].str.contains('Fullmetal Alchemist', case=False, na=False)]
print(f'Matches in anime_metadata_clean.csv (total: {len(fma_rows)}):')
for idx, row in fma_rows.iterrows():
    print(f"index: {idx}, id: anime_{idx}, title: {row['title']}, release_year: {row.get('release_year')}, aired: {row.get('aired')}, episodes: {row.get('episodes')}, ranking: {row.get('ranking')}")

print('\nTesting search for alchemist:')
res = search_black_knight('alchemist', top_k=10)
for r in res['results']:
    print(r['id'], r['media_type'], r['title'], r['score'])
