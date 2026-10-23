import json

with open('evaluation/results/baseline_audit_report.json', 'r') as f:
    b = json.load(f)
with open('evaluation/results/experiment_1_report.json', 'r') as f:
    e = json.load(f)

for cfg in b['summary_by_configuration'].keys():
    print(f"\n==================== {cfg.upper()} ====================")
    b_agg = b['summary_by_configuration'][cfg]['positive_ranking_metrics']
    e_agg = e['summary_by_configuration'][cfg]['positive_ranking_metrics']
    for k in ['hit_rate_at_5', 'hit_rate_at_10', 'precision_at_5', 'precision_at_10', 'recall_at_5', 'recall_at_10', 'mrr', 'ndcg_at_5', 'ndcg_at_10']:
        diff = e_agg[k] - b_agg[k]
        print(f"  {k:18s}: baseline={b_agg[k]:.4f} -> exp1={e_agg[k]:.4f} (diff={diff:+.4f})")
    
    print("\n  Validation & Correctness:")
    b_all = b['summary_by_configuration'][cfg]
    e_all = e['summary_by_configuration'][cfg]
    print(f"    Duplicate Rate: baseline={b_all['duplicate_result_rate']:.4f} -> exp1={e_all['duplicate_result_rate']:.4f}")
    print(f"    Hard Filter Violations: baseline={b_all['hard_filter_violation_rate']:.4f} -> exp1={e_all['hard_filter_violation_rate']:.4f}")
    print(f"    Absence Rejection Rate: baseline={b_all['absence_metrics']['rejection_rate']:.4f} -> exp1={e_all['absence_metrics']['rejection_rate']:.4f}")

    print("\n  Domain breakdowns (MRR & Hit@10):")
    for d in ['movie', 'anime', 'book']:
        b_d = b['per_domain_summary'][d]['configs'][cfg]['positive_ranking_metrics']
        e_d = e['per_domain_summary'][d]['configs'][cfg]['positive_ranking_metrics']
        mrr_diff = e_d['mrr'] - b_d['mrr']
        h10_diff = e_d['hit_rate_at_10'] - b_d['hit_rate_at_10']
        print(f"    {d:6s} | MRR: {b_d['mrr']:.4f} -> {e_d['mrr']:.4f} ({mrr_diff:+.4f}) | Hit@10: {b_d['hit_rate_at_10']:.4f} -> {e_d['hit_rate_at_10']:.4f} ({h10_diff:+.4f})")

    # Wins and losses analysis on query level
    b_cases = {c['query_id']: c for c in b['per_query_results']}
    e_cases = {c['query_id']: c for c in e['per_query_results']}
    wins = []
    losses = []
    for qid, bc in b_cases.items():
        ec = e_cases[qid]
        if bc.get('is_absence_query'):
            continue
        bc_cfg = bc[cfg]
        ec_cfg = ec[cfg]
        b_mrr = bc_cfg['mrr']
        e_mrr = ec_cfg['mrr']
        b_rank = round(1.0 / b_mrr) if b_mrr > 0 else "Miss"
        e_rank = round(1.0 / e_mrr) if e_mrr > 0 else "Miss"
        if e_mrr > b_mrr:
            wins.append((qid, bc['query_text'], b_mrr, e_mrr, b_rank, e_rank))
        elif e_mrr < b_mrr:
            losses.append((qid, bc['query_text'], b_mrr, e_mrr, b_rank, e_rank))
    
    print(f"\n  Query-level Wins: {len(wins)}, Losses: {len(losses)}, Net Gain: {len(wins)-len(losses)}")
    for w in wins:
        print(f"    WIN:  [{w[0]}] \"{w[1]}\": rank {w[4]} -> {w[5]} (MRR {w[2]:.3f} -> {w[3]:.3f})")
    for l in losses:
        print(f"    LOSS: [{l[0]}] \"{l[1]}\": rank {l[4]} -> {l[5]} (MRR {l[2]:.3f} -> {l[3]:.3f})")

# Latencies
print("\n==================== LATENCY ====================")
for cfg in b['latency_summary']:
    b_lat = b['latency_summary'][cfg]
    e_lat = e['latency_summary'][cfg]
    print(f"{cfg}:")
    print(f"  P50:  {b_lat['p50_ms']:.1f}ms -> {e_lat['p50_ms']:.1f}ms ({(e_lat['p50_ms']-b_lat['p50_ms'])/b_lat['p50_ms']*100:+.1f}%)")
    print(f"  P95:  {b_lat['p95_ms']:.1f}ms -> {e_lat['p95_ms']:.1f}ms ({(e_lat['p95_ms']-b_lat['p95_ms'])/b_lat['p95_ms']*100:+.1f}%)")
    print(f"  Mean: {b_lat['mean_ms']:.1f}ms -> {e_lat['mean_ms']:.1f}ms ({(e_lat['mean_ms']-b_lat['mean_ms'])/b_lat['mean_ms']*100:+.1f}%)")
