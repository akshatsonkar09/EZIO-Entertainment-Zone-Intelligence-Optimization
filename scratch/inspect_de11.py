import json
import pandas as pd
from project_black_knight.query_schema import BlackKnightQuery
from project_black_knight.retrieval import RetrievalRepository, search_black_knight

repo = RetrievalRepository()
bench = pd.read_csv('evaluation/black_knight_eval_queries_113_audited.csv')
row_11 = bench[bench['query_id'] == 'DE_011'].iloc[0]
print(row_11)

p11 = json.loads(row_11['expected_parse'])
q11 = BlackKnightQuery.model_validate(p11)

res = search_black_knight(parsed_query=q11, top_k=15, repo=repo, architecture='domain_routed')
print("\nDE_011 results:")
for i, r in enumerate(res['results']):
    print(f"  {i+1}. [{r['id']}] {r['title']} (score: {r['score']})")

rel_ids = json.loads(row_11['relevant_ids'])
print("\nTarget relevant_ids:", rel_ids)
for tid in rel_ids:
    df_meta = repo.get_metadata_df('anime')
    print("  Target title:", df_meta.iloc[int(tid.split('_')[1])]['title'])
