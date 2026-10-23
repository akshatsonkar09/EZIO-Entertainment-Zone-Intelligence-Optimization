import pandas as pd
from project_black_knight.retrieval import RetrievalRepository
from project_black_knight.metadata_filter import get_valid_ids

repo = RetrievalRepository()

movies_df = repo.get_metadata_df('movie')
animes_df = repo.get_metadata_df('anime')
books_df = repo.get_metadata_df('book')
music_df = repo.get_metadata_df('music')

_, movie_ids = repo.get_documents_and_ids('movie')
_, anime_ids = repo.get_documents_and_ids('anime')
_, book_ids = repo.get_documents_and_ids('book')
_, music_ids = repo.get_documents_and_ids('music')

test_constraints = [
    ('CO_001', 'movie', {'director': ['Christopher Nolan']}),
    ('CO_002', 'movie', {'genres_include': ['Science Fiction'], 'release_year_min': 2011, 'runtime_max': 149}),
    ('CO_003', 'movie', {'genres_include': ['Comedy'], 'runtime_max': 99}),
    ('CO_004', 'movie', {'genres_include': ['Action'], 'cast': ['Tom Cruise']}),
    ('CO_005', 'movie', {'genres_include': ['Horror'], 'release_year_min': 1980, 'release_year_max': 1989}),
    ('CO_006', 'movie', {'revenue_min': 500}),
    ('CO_007', 'movie', {'genres_include': ['Drama'], 'cast': ['Meryl Streep'], 'release_year_max': 1999}),
    ('CO_008', 'movie', {'genres_include': ['Thriller'], 'genres_exclude': ['Horror'], 'runtime_min': 151}),
    ('CO_009', 'anime', {'genres_include': ['Romance'], 'episodes_max': 14}),
    ('CO_010', 'anime', {'ranking_max': 50}),
    ('CO_011', 'anime', {'genres_include': ['Comedy'], 'release_year_min': 2016, 'episodes_min': 25}),
    ('CO_012', 'anime', {'genres_include': ['Mecha'], 'release_year_min': 1990, 'release_year_max': 1999}),
    ('CO_013', 'anime', {'genres_include': ['Fantasy'], 'genres_exclude': ['Ecchi']}),
    ('CO_014', 'anime', {'genres_include': ['Sports'], 'ranking_max': 300}),
    ('CO_015', 'anime', {'genres_include': ['Drama'], 'episodes_min': 1, 'episodes_max': 1}),
    ('CO_016', 'anime', {'genres_include': ['Horror'], 'release_year_min': 2000, 'release_year_max': 2010}),
    ('CO_017', 'book', {'author': ['Stephen King'], 'rating_min': 4.0}),
    ('CO_018', 'book', {'genres_include': ['Fantasy'], 'pages_min': 801}),
    ('CO_019', 'book', {'author': ['Agatha Christie'], 'rating_min': 4.0}),
    ('CO_020', 'book', {'genres_include': ['Science Fiction'], 'pages_max': 250}),
    ('CO_021', 'book', {'author': ['Neil Gaiman'], 'pages_min': 300}),
    ('CO_022', 'book', {'genres_include': ['Non-fiction'], 'rating_min': 4.2}),
    ('CO_023', 'book', {'author': ['Arthur Conan Doyle'], 'genres_include': ['Mystery']}),
    ('CO_024', 'music', {'artist': 'Taylor Swift'}),
    ('CO_025', 'music', {'artist': 'Queen', 'duration_max': 3.0}),
    ('CO_026', 'music', {'artist': 'The Beatles'}),
    ('CO_027', 'music', {'artist': 'Ed Sheeran', 'duration_min': 4.0}),
    ('CO_028', 'music', {'artist': 'Michael Jackson', 'album': 'Thriller'}),
    ('CO_029', 'music', {'artist': 'Led Zeppelin', 'duration_min': 5.0, 'playlist_genre': 'rock'}),
    ('CO_030', 'music', {'artist': 'Ariana Grande', 'duration_max': 3.5, 'playlist_genre': 'pop'}),
]

for qid, dom, filt in test_constraints:
    df_ = {'movie': movies_df, 'anime': animes_df, 'book': books_df, 'music': music_df}[dom]
    c_ids = {'movie': movie_ids, 'anime': anime_ids, 'book': book_ids, 'music': music_ids}[dom]
    v_ids = get_valid_ids(df_, c_ids, filt, dom)
    print(f"{qid} [{dom}] Valid items: {len(v_ids)} | Filter: {filt}")
