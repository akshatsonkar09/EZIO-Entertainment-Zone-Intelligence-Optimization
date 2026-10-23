import json
import pandas as pd
from project_black_knight.query_schema import BlackKnightQuery
from project_black_knight.retrieval import RetrievalRepository, search_black_knight

bench = pd.read_csv('evaluation/black_knight_eval_queries_113_audited.csv')
repo = RetrievalRepository()

for qid in ['SI_001', 'SI_006', 'SI_012']:
    row = bench[bench['query_id'] == qid].iloc[0]
    expected_parse = json.loads(row['expected_parse'])
    q = BlackKnightQuery.model_validate(expected_parse)
    res = search_black_knight(parsed_query=q, top_k=10, repo=repo, architecture='domain_routed')
    print(f"=== {qid}: \"{row['query_text']}\" ===")
    print('  similar_to in parse:', q.similar_to)
    print('  semantic_query in parse:', repr(q.semantic_query))
    print('  relevant_ids:', json.loads(row['relevant_ids']))
    print('  Top 5 retrieved:')
    for i, r in enumerate(res['results'][:5]):
        print(f"    {i+1}. [{r['id']}] {r['title']}")
