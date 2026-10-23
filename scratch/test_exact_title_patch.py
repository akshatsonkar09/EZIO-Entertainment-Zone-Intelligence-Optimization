import json
import pandas as pd
from project_black_knight.query_schema import BlackKnightQuery
from project_black_knight.retrieval import RetrievalRepository, search_black_knight

bench = pd.read_csv('evaluation/black_knight_eval_queries_113_audited.csv')
repo = RetrievalRepository()

# Test KI_018
row_18 = bench[bench['query_id'] == 'KI_018'].iloc[0]
parse_18 = json.loads(row_18['expected_parse'])
q_18 = BlackKnightQuery.model_validate(parse_18)

res_18 = search_black_knight(parsed_query=q_18, top_k=10, repo=repo, architecture="domain_routed")
print("KI_018 current results:")
for i, r in enumerate(res_18['results']):
    print(f" {i+1}. {r['id']}: {r['title']}")
