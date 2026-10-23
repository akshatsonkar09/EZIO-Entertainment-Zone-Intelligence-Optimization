"""
Comprehensive audit and ground truth generator for Project Black Knight 150-query retrieval benchmark.
"""
import json
import re
import pandas as pd
from project_black_knight.retrieval import RetrievalRepository
from project_black_knight.metadata_filter import get_valid_ids, row_matches_filters

repo = RetrievalRepository()
movies_df = repo.get_metadata_df('movie')
animes_df = repo.get_metadata_df('anime')
books_df = repo.get_metadata_df('book')
music_df = repo.get_metadata_df('music')

_, movie_ids = repo.get_documents_and_ids('movie')
_, anime_ids = repo.get_documents_and_ids('anime')
_, book_ids = repo.get_documents_and_ids('book')
_, music_ids = repo.get_documents_and_ids('music')

print(f"Catalog sizes: Movies={len(movie_ids)}, Anime={len(anime_ids)}, Books={len(book_ids)}, Music={len(music_ids)}")
