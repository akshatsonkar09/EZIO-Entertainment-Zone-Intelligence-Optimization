import json
import pandas as pd
from project_black_knight.retrieval import RetrievalRepository
from project_black_knight.text_normalizer import normalize_title_key

with open(r'evaluation/results/baseline_audit_report.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

per_query = data['per_query_results']
bench = pd.read_csv(r'evaluation/black_knight_eval_queries_113_audited.csv')

repo = RetrievalRepository()
dfs = {}
for d in ('movie', 'anime', 'book'):
    dfs[d] = repo.get_metadata_df(d)
    repo.get_documents_and_ids(d)

print("Simulating Exact Title Promotion across ALL 113 queries:")

for arch in ['architecture_a', 'architecture_b']:
    wins = 0
    losses = 0
    neutral = 0
    
    old_mrrs = []
    new_mrrs = []
    old_hit1s = []
    new_hit1s = []
    old_hit10s = []
    new_hit10s = []
    
    for q in per_query:
        if q['is_absence_query']:
            continue
        qid = q['query_id']
        dom = q['domain']
        df = dfs[dom]
        id_to_idx = repo._id_to_index[dom]
        
        base_ranked = q[arch]['ranked_ids']
        rel = set(q['relevant_ids'])
        
        row = bench[bench['query_id'] == qid].iloc[0]
        p = json.loads(row['expected_parse'])
        q_title = p.get('common', {}).get('title')
        norm_q_title = normalize_title_key(q_title) if q_title else None
        
        if norm_q_title:
            exact = []
            non_exact = []
            for cid in base_ranked:
                idx = id_to_idx[cid]
                cand_title = str(df.iloc[idx]['title'])
                if normalize_title_key(cand_title) == norm_q_title:
                    exact.append(cid)
                else:
                    non_exact.append(cid)
            new_ranked = exact + non_exact
        else:
            new_ranked = list(base_ranked)
            
        old_rank = next((i+1 for i, r in enumerate(base_ranked[:10]) if r in rel), None)
        new_rank = next((i+1 for i, r in enumerate(new_ranked[:10]) if r in rel), None)
        
        old_mrrs.append(1.0 / old_rank if old_rank else 0.0)
        new_mrrs.append(1.0 / new_rank if new_rank else 0.0)
        old_hit1s.append(1.0 if old_rank == 1 else 0.0)
        new_hit1s.append(1.0 if new_rank == 1 else 0.0)
        old_hit10s.append(1.0 if old_rank is not None else 0.0)
        new_hit10s.append(1.0 if new_rank is not None else 0.0)
        
        if old_rank != new_rank:
            if (old_rank is None and new_rank is not None) or (old_rank is not None and new_rank is not None and new_rank < old_rank):
                wins += 1
                print(f"[{arch}] WIN: {qid} ({dom}, {q['category']}): '{q['query_text']}' rank {old_rank} -> {new_rank}")
            elif (new_rank is None and old_rank is not None) or (old_rank is not None and new_rank is not None and new_rank > old_rank):
                losses += 1
                print(f"[{arch}] LOSS: {qid} ({dom}, {q['category']}): '{q['query_text']}' rank {old_rank} -> {new_rank}")
        else:
            neutral += 1
            
    print(f"\n--- {arch} Summary ---")
    print(f"Wins: {wins}, Losses: {losses}, Neutral: {neutral}")
    print(f"Hit@1:  {sum(old_hit1s)/len(old_hit1s):.4f} -> {sum(new_hit1s)/len(new_hit1s):.4f} (Delta: {sum(new_hit1s)/len(new_hit1s) - sum(old_hit1s)/len(old_hit1s):+.4f})")
    print(f"Hit@10: {sum(old_hit10s)/len(old_hit10s):.4f} -> {sum(new_hit10s)/len(new_hit10s):.4f} (Delta: {sum(new_hit10s)/len(new_hit10s) - sum(old_hit10s)/len(old_hit10s):+.4f})")
    print(f"MRR:    {sum(old_mrrs)/len(old_mrrs):.4f} -> {sum(new_mrrs)/len(new_mrrs):.4f} (Delta: {sum(new_mrrs)/len(new_mrrs) - sum(old_mrrs)/len(old_mrrs):+.4f})\n")
