import json
with open('evaluation/results/experiment_1_report.json', 'r') as f:
    rep = json.load(f)

de_cases = [q for q in rep['per_query_results'] if q['category'] == 'descriptive']
print(f"Total Descriptive queries: {len(de_cases)}")
for cfg in ['architecture_a', 'architecture_b', 'rrf_only']:
    h10 = sum(1 for c in de_cases if c[cfg]['hit_rate_at_10'] > 0) / len(de_cases)
    ndcg10 = sum(c[cfg]['ndcg_at_10'] for c in de_cases) / len(de_cases)
    mrr = sum(c[cfg]['mrr'] for c in de_cases) / len(de_cases)
    print(f"{cfg:16s}: Hit@10={h10:.4f}, nDCG@10={ndcg10:.4f}, MRR={mrr:.4f}")

print("\nZero-hit descriptive queries in Architecture B:")
for c in de_cases:
    h10_b = c['architecture_b']['hit_rate_at_10']
    if h10_b == 0:
        print(f"  {c['query_id']} ({c['domain']}): '{c['query_text']}' | rel={c['relevant_ids']}")
