import json
import pandas as pd
from project_black_knight.query_schema import BlackKnightQuery
from project_black_knight.retrieval import RetrievalRepository, search_black_knight

bench = pd.read_csv('evaluation/black_knight_eval_queries_113_audited.csv')
repo = RetrievalRepository()

for qid in ['MD_002', 'MD_004', 'MD_005', 'MD_006']:
    row = bench[bench['query_id'] == qid].iloc[0]
    p = json.loads(row['expected_parse'])
    q = BlackKnightQuery.model_validate(p)
    rel = json.loads(row['relevant_ids'])
    print(f"\n=== {qid}: '{row['query_text']}' ===")
    print('  benchmark domain column:', row['domain'])
    print('  parsed media_types:', q.media_types)
    print('  parsed semantic_query:', repr(q.semantic_query))
    print('  parsed common:', q.common.model_dump(exclude_none=True))
    print('  relevant_ids:', rel)
    
    res = search_black_knight(parsed_query=q, top_k=10, repo=repo, architecture='domain_routed')
    print('  Top 5 returned:')
    for i, r in enumerate(res['results'][:5]):
        is_hit = " *** HIT ***" if r['id'] in rel else ""
        print(f"    {i+1}. [{r['id']}] ({r.get('media_type')}) {r['title']} (score: {r['score']}){is_hit}")
