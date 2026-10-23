import json

with open('evaluation/results/experiment_1_report.json', 'r') as f:
    e = json.load(f)

for cfg in ['architecture_a', 'architecture_b', 'rrf_only']:
    agg = e['summary_by_configuration'][cfg]
    pos = agg['positive_ranking_metrics']
    abs_m = agg['absence_metrics']
    h1 = sum(1 for c in e['per_query_results'] if not c.get('is_absence_query') and c[cfg]['mrr'] == 1.0) / 102
    print(f"=== {cfg.upper()} ===")
    print(f"  MRR:        {pos['mrr']:.4f}")
    print(f"  Hit@1:      {h1:.4f}")
    print(f"  Hit@5:      {pos['hit_rate_at_5']:.4f}")
    print(f"  Hit@10:     {pos['hit_rate_at_10']:.4f}")
    print(f"  nDCG@5:     {pos['ndcg_at_5']:.4f}")
    print(f"  nDCG@10:    {pos['ndcg_at_10']:.4f}")
    print(f"  Duplicates: {agg['duplicate_result_rate']:.4f}")
    print(f"  HardFilter: {agg['hard_filter_violation_rate']:.4f}")
    print(f"  AbsenceRej: {abs_m['rejection_rate']:.4f} (False Acc: {abs_m['false_acceptances']})")
