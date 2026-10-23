import json
import numpy as np
import pandas as pd

with open('evaluation/results/baseline_audit_report.json', 'r') as f:
    base = json.load(f)

with open('evaluation/results/experiment_1_report.json', 'r') as f:
    exp1 = json.load(f)

print("=== BASELINE AUDIT DATA ===")
print("Generated at:", base.get("generated_at"))
print("Total queries evaluated:", base.get("total_queries_evaluated"))
print("Scored queries:", base.get("scored_queries_count"))
print("Absence queries:", base.get("absence_queries_count"))

for cfg in ["architecture_a", "architecture_b", "rrf_only"]:
    pos_m = base["summary_by_configuration"][cfg]["positive_ranking_metrics"]
    print(f"\nConfiguration: {cfg}")
    print(f"  Overall MRR:       {pos_m['mrr']:.6f}")
    print(f"  Overall Hit@1:     {sum(1 for c in base['per_query_results'] if not c.get('is_absence_query') and c[cfg]['hit_rate_at_5'] > 0 and c[cfg]['mrr'] == 1.0) / 102:.6f}")
    print(f"  Overall Hit@5:     {pos_m['hit_rate_at_5']:.6f}")
    print(f"  Overall Hit@10:    {pos_m['hit_rate_at_10']:.6f}")
    print(f"  Overall nDCG@5:    {pos_m['ndcg_at_5']:.6f}")
    print(f"  Overall nDCG@10:   {pos_m['ndcg_at_10']:.6f}")

print("\n=== CATEGORY BREAKDOWN IN BASELINE (Architecture B) ===")
# Group per_query_results by category
categories = sorted(list(set(c['category'] for c in base['per_query_results'])))
for cat in categories:
    cat_cases = [c for c in base['per_query_results'] if c['category'] == cat and not c.get('is_absence_query')]
    if not cat_cases:
        continue
    n = len(cat_cases)
    mrr = np.mean([c['architecture_b']['mrr'] for c in cat_cases])
    h1 = np.mean([1.0 if c['architecture_b']['mrr'] == 1.0 else 0.0 for c in cat_cases])
    h5 = np.mean([c['architecture_b']['hit_rate_at_5'] for c in cat_cases])
    h10 = np.mean([c['architecture_b']['hit_rate_at_10'] for c in cat_cases])
    ndcg10 = np.mean([c['architecture_b']['ndcg_at_10'] for c in cat_cases])
    print(f"Category: {cat:16s} (N={n:2d}) | MRR={mrr:.4f} | Hit@1={h1:.4f} | Hit@5={h5:.4f} | Hit@10={h10:.4f} | nDCG@10={ndcg10:.4f}")

print("\n=== CATEGORY BREAKDOWN IN EXPERIMENT 1 (Architecture B) ===")
for cat in categories:
    cat_cases = [c for c in exp1['per_query_results'] if c['category'] == cat and not c.get('is_absence_query')]
    if not cat_cases:
        continue
    n = len(cat_cases)
    mrr = np.mean([c['architecture_b']['mrr'] for c in cat_cases])
    h1 = np.mean([1.0 if c['architecture_b']['mrr'] == 1.0 else 0.0 for c in cat_cases])
    h5 = np.mean([c['architecture_b']['hit_rate_at_5'] for c in cat_cases])
    h10 = np.mean([c['architecture_b']['hit_rate_at_10'] for c in cat_cases])
    ndcg10 = np.mean([c['architecture_b']['ndcg_at_10'] for c in cat_cases])
    print(f"Category: {cat:16s} (N={n:2d}) | MRR={mrr:.4f} | Hit@1={h1:.4f} | Hit@5={h5:.4f} | Hit@10={h10:.4f} | nDCG@10={ndcg10:.4f}")

print("\n=== DOMAIN BREAKDOWN (Architecture B) ===")
for dom in ["movie", "anime", "book"]:
    base_cases = [c for c in base['per_query_results'] if c['domain'] == dom and not c.get('is_absence_query')]
    exp1_cases = [c for c in exp1['per_query_results'] if c['domain'] == dom and not c.get('is_absence_query')]
    n = len(base_cases)
    b_mrr = np.mean([c['architecture_b']['mrr'] for c in base_cases])
    e_mrr = np.mean([c['architecture_b']['mrr'] for c in exp1_cases])
    b_h10 = np.mean([c['architecture_b']['hit_rate_at_10'] for c in base_cases])
    e_h10 = np.mean([c['architecture_b']['hit_rate_at_10'] for c in exp1_cases])
    print(f"Domain: {dom:6s} (N={n:2d}) | Baseline: MRR={b_mrr:.4f}, Hit@10={b_h10:.4f} -> Exp1: MRR={e_mrr:.4f}, Hit@10={e_h10:.4f} (diff MRR: {e_mrr-b_mrr:+.4f}, diff Hit@10: {e_h10-b_h10:+.4f})")
