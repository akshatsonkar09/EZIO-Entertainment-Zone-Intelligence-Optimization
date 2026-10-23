import json
import pandas as pd
from project_black_knight.query_schema import BlackKnightQuery
from project_black_knight.retrieval import RetrievalRepository, bm25_retrieve, dense_retrieve, reciprocal_rank_fusion
from project_black_knight.metadata_filter import get_valid_ids

repo = RetrievalRepository()
df = repo.get_metadata_df('anime')
docs, ids = repo.get_documents_and_ids('anime')

valid_ids = get_valid_ids(df, ids, {"title": "Shingeki no Kyojin"}, "anime")
dense = dense_retrieve("Find Shingeki no Kyojin.", "anime", valid_ids, top_k=60, repo=repo)
bm25 = bm25_retrieve("Find Shingeki no Kyojin.", "anime", valid_ids, top_k=60, repo=repo)

dense_ids = [r['id'] for r in dense]
bm25_ids = [r['id'] for r in bm25]

print("anime_667 dense rank:", dense_ids.index('anime_667') if 'anime_667' in dense_ids else 'Miss')
print("anime_14939 dense rank:", dense_ids.index('anime_14939') if 'anime_14939' in dense_ids else 'Miss')
print("anime_667 bm25 rank:", bm25_ids.index('anime_667') if 'anime_667' in bm25_ids else 'Miss')
print("anime_14939 bm25 rank:", bm25_ids.index('anime_14939') if 'anime_14939' in bm25_ids else 'Miss')
