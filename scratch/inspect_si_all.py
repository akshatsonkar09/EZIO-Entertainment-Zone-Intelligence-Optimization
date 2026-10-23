import json
import pandas as pd
df = pd.read_csv('evaluation/black_knight_eval_queries_113_audited.csv')
si = df[df['query_id'].str.startswith('SI_')]
for idx, r in si.iterrows():
    p = json.loads(r['expected_parse'])
    rel = json.loads(r['relevant_ids'])
    print(f"{r['query_id']} ({r['domain']}): text='{r['query_text']}' | similar_to={p.get('similar_to')} | rel={rel}")
