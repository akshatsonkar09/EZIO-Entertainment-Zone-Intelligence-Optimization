import pandas as pd
from project_black_knight.retrieval import RetrievalRepository

repo = RetrievalRepository()
df = pd.read_csv('evaluation/black_knight_eval_queries_150.csv')

movies_df = repo.get_metadata_df('movie')
animes_df = repo.get_metadata_df('anime')
books_df = repo.get_metadata_df('book')
music_df = repo.get_metadata_df('music')

print('=== AUDITING ALL 15 ABSENCE QUERIES ===')
for _, r in df[df['category'] == 'absence'].iterrows():
    qid = r['query_id']
    dom = r['domain']
    q = r['query_text']
    
    matches = []
    if dom == 'movie':
        t = q.replace('Find the movie ', '').rstrip('.')
        m = movies_df[movies_df['title'].str.contains(t, case=False, na=False, regex=False)]
        matches = list(m['title'])
    elif dom == 'anime':
        t = q.replace('Find the anime ', '').rstrip('.')
        m = animes_df[animes_df['title'].str.contains(t, case=False, na=False, regex=False)]
        matches = list(m['title'])
    elif dom == 'book':
        t = q.replace('Find ', '').split(' by ')[0].strip().rstrip('.')
        m = books_df[books_df['title'].str.contains(t, case=False, na=False, regex=False)]
        matches = list(m['title'])
    elif dom == 'music':
        t = q.replace('Find the song ', '').split(' by ')[0].strip().rstrip('.')
        m = music_df[music_df['track_name'].str.contains(t, case=False, na=False, regex=False)]
        matches = list(m['track_name'])
        
    print(f"{qid} [{dom}] '{q}' -> Matches found: {len(matches)} {matches[:2]}")

print('\n=== AUDITING ALL 40 KNOWN ITEM QUERIES ===')
for _, r in df[df['category'] == 'known_item'].iterrows():
    qid = r['query_id']
    dom = r['domain']
    q = r['query_text']
    print(f"{qid} [{dom}] '{q}'")
