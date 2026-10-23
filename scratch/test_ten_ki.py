import json
import pandas as pd
from project_black_knight.query_schema import BlackKnightQuery
from project_black_knight.retrieval import RetrievalRepository, search_black_knight
from project_black_knight.text_normalizer import normalize_title_key

repo = RetrievalRepository()
bench = pd.read_csv('evaluation/black_knight_eval_queries_113_audited.csv')

# Let's inspect KI_018 and KI_001 specifically
for qid in ['KI_001', 'KI_005', 'KI_012', 'KI_013', 'KI_014', 'KI_015', 'KI_017', 'KI_018', 'KI_020', 'KI_025']:
    row = bench[bench['query_id'] == qid].iloc[0]
    p = json.loads(row['expected_parse'])
    q = BlackKnightQuery.model_validate(p)
    rel = set(json.loads(row['relevant_ids']))
    
    res = search_black_knight(parsed_query=q, top_k=10, repo=repo, architecture="domain_routed")
    ranked = [r['id'] for r in res['results']]
    rank = next((i+1 for i, r in enumerate(ranked) if r in rel), 'Miss')
    print(f"{qid} ({row['domain']}): target at rank {rank}. Top result: {res['results'][0]['title']} ({res['results'][0]['id']})")
