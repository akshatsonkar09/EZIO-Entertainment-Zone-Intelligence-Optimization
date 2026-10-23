import json
import pandas as pd
from project_black_knight.query_schema import BlackKnightQuery
from project_black_knight.retrieval import RetrievalRepository, dense_retrieve, bm25_retrieve, resolve_similar_seed

repo = RetrievalRepository()
bench = pd.read_csv('evaluation/black_knight_eval_queries_113_audited.csv')
row_1 = bench[bench['query_id'] == 'SI_001'].iloc[0]
parse_1 = json.loads(row_1['expected_parse'])
q1 = BlackKnightQuery.model_validate(parse_1)

resolved = resolve_similar_seed('Inception', target_domain='movie', repo=repo)
print("Resolved seed doc text:")
print(resolved['doc_text'])

effective_query = f"{q1.semantic_query} {resolved['doc_text']}"
print("\nCurrent effective_query:")
print(repr(effective_query[:200]))

dense_res = dense_retrieve(effective_query, 'movie', top_k=200, repo=repo)
dense_ranks = {c['id']: (i+1, c['score']) for i, c in enumerate(dense_res)}

bm25_res = bm25_retrieve(effective_query, 'movie', top_k=200, repo=repo)
bm25_ranks = {c['id']: (i+1, c['score']) for i, c in enumerate(bm25_res)}

for tid in ['movie_96', 'movie_95', 'movie_634', 'movie_2660']:
    print(f"{tid}: dense_rank={dense_ranks.get(tid)} | bm25_rank={bm25_ranks.get(tid)}")
