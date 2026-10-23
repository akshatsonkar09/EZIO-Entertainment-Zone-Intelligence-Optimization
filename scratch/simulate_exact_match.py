import json
import pandas as pd
from project_black_knight.retrieval import RetrievalRepository
from project_black_knight.text_normalizer import normalize_title_key

with open(r'evaluation/results/baseline_audit_report.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

per_query = data['per_query_results']
ki_queries = [q for q in per_query if q['category'] == 'known_item']

bench = pd.read_csv(r'evaluation/black_knight_eval_queries_113_audited.csv')

repo = RetrievalRepository()
dfs = {}
for d in ('movie', 'anime', 'book'):
    dfs[d] = repo.get_metadata_df(d)
    repo.get_documents_and_ids(d)

print("Simulating Exact Title Priority on baseline rankings:")
wins = 0
losses = 0

old_mrrs = []
new_mrrs = []
old_hit1 = []
new_hit1 = []

for q in ki_queries:
    qid = q['query_id']
    dom = q['domain']
    df = dfs[dom]
    id_to_idx = repo._id_to_index[dom]
    
    base_ranked = q['architecture_b']['ranked_ids']
    rel = set(q['relevant_ids'])
    
    row = bench[bench['query_id'] == qid].iloc[0]
    p = json.loads(row['expected_parse'])
    q_title = p.get('common', {}).get('title')
    norm_q_title = normalize_title_key(q_title) if q_title else None
    
    exact_matches = []
    others = []
    for cid in base_ranked:
        idx = id_to_idx[cid]
        cand_title = str(df.iloc[idx]['title'])
        if norm_q_title and normalize_title_key(cand_title) == norm_q_title:
            exact_matches.append(cid)
        else:
            others.append(cid)
    new_ranked = exact_matches + others
    
    old_rank = next((i+1 for i, r in enumerate(base_ranked) if r in rel), None)
    new_rank = next((i+1 for i, r in enumerate(new_ranked) if r in rel), None)
    
    old_mrr = 1.0 / old_rank if old_rank else 0.0
    new_mrr = 1.0 / new_rank if new_rank else 0.0
    old_mrrs.append(old_mrr)
    new_mrrs.append(new_mrr)
    old_hit1.append(1.0 if old_rank == 1 else 0.0)
    new_hit1.append(1.0 if new_rank == 1 else 0.0)
    
    if new_rank != old_rank:
        if (old_rank is None and new_rank is not None) or (old_rank is not None and new_rank < old_rank):
            wins += 1
            print(f" WIN: {qid} ({dom}): '{q_title}' rank {old_rank} -> {new_rank}")
        else:
            losses += 1
            print(f" LOSS: {qid} ({dom}): '{q_title}' rank {old_rank} -> {new_rank}")

print(f"\nTotal Known-Item Wins: {wins}, Losses: {losses}")
print(f"Known-Item MRR: {sum(old_mrrs)/len(old_mrrs):.4f} -> {sum(new_mrrs)/len(new_mrrs):.4f}")
print(f"Known-Item Hit@1: {sum(old_hit1)/len(old_hit1):.4f} -> {sum(new_hit1)/len(new_hit1):.4f}")
