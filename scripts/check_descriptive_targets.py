import pandas as pd
from project_black_knight.retrieval import RetrievalRepository

repo = RetrievalRepository()
df = pd.read_csv('evaluation/black_knight_eval_queries_150.csv')

movies_df = repo.get_metadata_df('movie')
animes_df = repo.get_metadata_df('anime')
books_df = repo.get_metadata_df('book')
music_df = repo.get_metadata_df('music')

print("=== CHECKING DESCRIPTIVE TARGETS ===")
# DE_001 to DE_030
# E.g. DE_001 Groundhog Day, DE_002 Inception, DE_003 Toy Story, DE_004 Jaws, DE_005 The Hangover, DE_006 John Wick, DE_007 Finding Nemo, DE_008 Jurassic Park
for title, dom in [
    ('Groundhog Day', 'movie'), ('Inception', 'movie'), ('Toy Story', 'movie'), ('Jaws', 'movie'),
    ('The Hangover', 'movie'), ('John Wick', 'movie'), ('Finding Nemo', 'movie'), ('Jurassic Park', 'movie'),
    ('One Piece', 'anime'), ('Death Note', 'anime'), ('Neon Genesis Evangelion', 'anime'), ('Kimi no Na wa', 'anime'),
    ('Tensei shitara Slime Datta Ken', 'anime'), ('Haikyuu', 'anime'), ('Cowboy Bebop', 'anime'), ('Shingeki no Kyojin', 'anime'),
    ('The Hunger Games', 'book'), ('Murder on the Orient Express', 'book'), ('The Way of Kings', 'book'), ('Brave New World', 'book')
]:
    df_ = {'movie': movies_df, 'anime': animes_df, 'book': books_df, 'music': music_df}[dom]
    col = 'track_name' if dom == 'music' else 'title'
    m = df_[df_[col].str.contains(title, case=False, na=False)]
    print(f"[{dom}] '{title}': {len(m)} matches -> {[(f'{dom}_{i}', row_[col]) for i, row_ in m.head(2).iterrows()]}")
