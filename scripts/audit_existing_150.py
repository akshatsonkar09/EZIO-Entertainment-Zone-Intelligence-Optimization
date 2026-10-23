import pandas as pd
from project_black_knight.retrieval import RetrievalRepository

repo = RetrievalRepository()
df_eval = pd.read_csv('evaluation/black_knight_eval_queries_150.csv')

movies_df = repo.get_metadata_df('movie')
animes_df = repo.get_metadata_df('anime')
books_df = repo.get_metadata_df('book')
music_df = repo.get_metadata_df('music')

print("\n--- AUDITING SIMILAR_TO QUERIES (20) ---")
si_df = df_eval[df_eval['category'] == 'similar_to']
for _, r in si_df.iterrows():
    q = r['query_text']
    dom = r['domain']
    qid = r['query_id']
    # extract seed title
    seed = q.replace('Recommend movies similar to ', '').replace('Recommend anime similar to ', '')
    seed = seed.replace('Recommend books similar to ', '').replace('Recommend songs similar to ', '').rstrip('.')
    seed_title = seed.split(' by ')[0].strip()
    
    found = []
    if dom == 'movie':
        m = movies_df[movies_df['title'].str.contains('^' + seed_title + '$', case=False, na=False)]
        found = [(f'movie_{idx}', row_['title']) for idx, row_ in m.iterrows()]
    elif dom == 'anime':
        m = animes_df[animes_df['title'].str.contains('^' + seed_title + '$', case=False, na=False)]
        found = [(f'anime_{idx}', row_['title']) for idx, row_ in m.iterrows()]
    elif dom == 'book':
        m = books_df[books_df['title'].str.contains('^' + seed_title + '$', case=False, na=False)]
        found = [(f'book_{idx}', row_['title']) for idx, row_ in m.iterrows()]
    elif dom == 'music':
        m = music_df[music_df['track_name'].str.contains('^' + seed_title + '$', case=False, na=False)]
        found = [(f'music_{idx}', row_['track_name']) for idx, row_ in m.iterrows()]
    
    print(f"{qid} [{dom}] Seed: '{seed_title}' -> Seed found in catalog: {len(found)} {found[:1]}")

print("\n--- AUDITING CONSTRAINT QUERIES (30) ---")
co_df = df_eval[df_eval['category'] == 'constraint']
for _, r in co_df.iterrows():
    q = r['query_text']
    dom = r['domain']
    qid = r['query_id']
    print(f"{qid} [{dom}]: {q}")

print("\n--- AUDITING DESCRIPTIVE QUERIES (30) ---")
de_df = df_eval[df_eval['category'] == 'descriptive']
for _, r in de_df.iterrows():
    q = r['query_text']
    dom = r['domain']
    qid = r['query_id']
    print(f"{qid} [{dom}]: {q}")

print("\n--- AUDITING MULTI-DOMAIN QUERIES (15) ---")
md_df = df_eval[df_eval['category'] == 'multi_domain']
for _, r in md_df.iterrows():
    q = r['query_text']
    dom = r['domain']
    qid = r['query_id']
    print(f"{qid} [{dom}]: {q}")
