import json
import pandas as pd
from project_black_knight.retrieval import RetrievalRepository

repo = RetrievalRepository()
bench = pd.read_csv('evaluation/black_knight_eval_queries_113_audited.csv')

# 1. KI_016
row_ki16 = bench[bench['query_id'] == 'KI_016'].iloc[0]
df_anime = repo.get_metadata_df('anime')
rel_ki16 = json.loads(row_ki16['relevant_ids'])
print('=== KI_016 ===')
print('Query text:', row_ki16['query_text'])
print('Labeled relevant_ids:', rel_ki16)
for rid in rel_ki16:
    idx = int(rid.split('_')[1])
    print(f'  Labeled item {rid}: title = "{df_anime.iloc[idx]["title"]}"')

code_geass_matches = df_anime[df_anime['title'].str.contains('Code Geass: Hangyaku no Lelouch', case=False, na=False)]
for idx, r in code_geass_matches.iterrows():
    print(f'  Actual catalog match: anime_{idx} -> "{r["title"]}"')

# 2. KI_023
row_ki23 = bench[bench['query_id'] == 'KI_023'].iloc[0]
df_book = repo.get_metadata_df('book')
rel_ki23 = json.loads(row_ki23['relevant_ids'])
print('\n=== KI_023 ===')
print('Query text:', row_ki23['query_text'])
print('Labeled relevant_ids:', rel_ki23)
for rid in rel_ki23:
    idx = int(rid.split('_')[1])
    print(f'  Labeled item {rid}: title = "{df_book.iloc[idx]["title"]}" by {df_book.iloc[idx]["author"]}')

mansfield_matches = df_book[df_book['title'].str.contains('Mansfield Park', case=False, na=False)]
for idx, r in mansfield_matches.iterrows():
    print(f'  Actual catalog match: book_{idx} -> "{r["title"]}" by {r["author"]}')

# 3. MD_005
row_md5 = bench[bench['query_id'] == 'MD_005'].iloc[0]
df_movie = repo.get_metadata_df('movie')
rel_md5 = json.loads(row_md5['relevant_ids'])
print('\n=== MD_005 ===')
print('Query text:', row_md5['query_text'])
print('Labeled relevant_ids:', rel_md5)
for rid in rel_md5:
    dom, idx_str = rid.split('_')
    idx = int(idx_str)
    if dom == 'movie':
        print(f'  Labeled item {rid}: title = "{df_movie.iloc[idx]["title"]}", director = {df_movie.iloc[idx]["director"]}')
    elif dom == 'anime':
        print(f'  Labeled item {rid}: title = "{df_anime.iloc[idx]["title"]}"')

# Miyazaki movies in movie catalog:
miyazaki_movies = df_movie[df_movie['director'].str.contains('Hayao Miyazaki', case=False, na=False)]
print('\nHayao Miyazaki movies in movie catalog:')
for idx, r in miyazaki_movies.iterrows():
    print(f'  movie_{idx}: "{r["title"]}" directed by {r["director"]}')
