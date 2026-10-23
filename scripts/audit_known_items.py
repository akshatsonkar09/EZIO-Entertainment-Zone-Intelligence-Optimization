import pandas as pd
from project_black_knight.retrieval import RetrievalRepository

repo = RetrievalRepository()
df = pd.read_csv('evaluation/black_knight_eval_queries_150.csv')

movies_df = repo.get_metadata_df('movie')
animes_df = repo.get_metadata_df('anime')
books_df = repo.get_metadata_df('book')
music_df = repo.get_metadata_df('music')

ki_df = df[df['category'] == 'known_item']

for _, r in ki_df.iterrows():
    qid = r['query_id']
    dom = r['domain']
    q = r['query_text']
    
    # check in catalog
    found = []
    if dom == 'movie':
        # common titles in queries:
        t = q.replace('Find the movie ', '').replace('Find the film ', '').replace('Show me the movie ', '').replace('Find ', '').rstrip('.')
        t_clean = t.split(' directed by ')[0].strip()
        m = movies_df[movies_df['title'].str.contains('^' + t_clean + '$', case=False, na=False, regex=True)]
        if len(m) == 0:
            m = movies_df[movies_df['title'].str.contains(t_clean, case=False, na=False, regex=False)]
        found = [(f"movie_{idx}", row_['title']) for idx, row_ in m.iterrows()]
    elif dom == 'anime':
        t_clean = q.replace('Find the anime ', '').replace('Find ', '').rstrip('.')
        m = animes_df[animes_df['title'].str.contains('^' + t_clean + '$', case=False, na=False, regex=True)]
        if len(m) == 0:
            m = animes_df[animes_df['title'].str.contains(t_clean, case=False, na=False, regex=False)]
        found = [(f"anime_{idx}", row_['title']) for idx, row_ in m.iterrows()]
    elif dom == 'book':
        t = q.replace('Find ', '').split(' by ')[0].strip().rstrip('.')
        m = books_df[books_df['title'].str.contains('^' + t + '$', case=False, na=False, regex=True)]
        if len(m) == 0:
            m = books_df[books_df['title'].str.contains(t, case=False, na=False, regex=False)]
        found = [(f"book_{idx}", row_['title']) for idx, row_ in m.iterrows()]
    elif dom == 'music':
        t = q.replace('Find the song ', '').replace('Find tracks from the album ', '').replace('Find ', '').split(' by ')[0].strip().rstrip('.')
        m = music_df[music_df['track_name'].str.contains('^' + t + '$', case=False, na=False, regex=True)]
        if len(m) == 0:
            m = music_df[music_df['track_name'].str.contains(t, case=False, na=False, regex=False)]
        found = [(f"music_{idx}", row_['track_name'], row_['artist']) for idx, row_ in m.iterrows()]
        
    print(f"{qid} [{dom}] '{q}' -> Found: {len(found)} {found[:2]}")
