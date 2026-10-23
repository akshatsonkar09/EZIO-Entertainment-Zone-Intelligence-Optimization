import json
import pandas as pd
from project_black_knight.query_schema import BlackKnightQuery
from project_black_knight.retrieval import RetrievalRepository, search_black_knight

repo = RetrievalRepository()
bench = pd.read_csv('evaluation/black_knight_eval_queries_113_audited.csv')
row_1 = bench[bench['query_id'] == 'SI_001'].iloc[0]
parse_1 = json.loads(row_1['expected_parse'])
q1 = BlackKnightQuery.model_validate(parse_1)

res = search_black_knight(parsed_query=q1, top_k=60, repo=repo, architecture='all_cross_encoder')
target_ids = {'movie_96', 'movie_95', 'movie_634', 'movie_2660'}

print("SI_001 ranks in all_cross_encoder:")
for i, r in enumerate(res['results']):
    if r['id'] in target_ids:
        print(f"  Rank {i+1}: {r['id']} - {r['title']} (score: {r['score']})")

res_b = search_black_knight(parsed_query=q1, top_k=60, repo=repo, architecture='domain_routed')
print("\nSI_001 ranks in domain_routed:")
for i, r in enumerate(res_b['results']):
    if r['id'] in target_ids:
        print(f"  Rank {i+1}: {r['id']} - {r['title']} (score: {r['score']})")
