import json
import numpy as np
import pandas as pd

with open('evaluation/results/baseline_audit_report.json', 'r') as f:
    base = json.load(f)

with open('evaluation/results/experiment_1_report.json', 'r') as f:
    exp1 = json.load(f)

# Filter out SI_* queries
b_cases = [c for c in base['per_query_results'] if not c['query_id'].startswith('SI_')]
e_cases = [c for c in exp1['per_query_results'] if not c['query_id'].startswith('SI_')]

print(f"Total in-scope queries: {len(b_cases)}")
pos_b = [c for c in b_cases if not c.get('is_absence_query')]
abs_b = [c for c in b_cases if c.get('is_absence_query')]
pos_e = [c for c in e_cases if not c.get('is_absence_query')]
abs_e = [c for c in e_cases if c.get('is_absence_query')]
print(f"In-scope positive queries: {len(pos_b)}")
print(f"In-scope absence queries:  {len(abs_b)}")

for cfg in ['architecture_a', 'architecture_b', 'rrf_only']:
    print(f"\n==================== CONFIGURATION: {cfg.upper()} ====================")
    b_mrr = np.mean([c[cfg]['mrr'] for c in pos_b])
    e_mrr = np.mean([c[cfg]['mrr'] for c in pos_e])
    
    b_h1 = np.mean([1.0 if c[cfg]['mrr'] == 1.0 else 0.0 for c in pos_b])
    e_h1 = np.mean([1.0 if c[cfg]['mrr'] == 1.0 else 0.0 for c in pos_e])
    
    b_h5 = np.mean([c[cfg]['hit_rate_at_5'] for c in pos_b])
    e_h5 = np.mean([c[cfg]['hit_rate_at_5'] for c in pos_e])
    
    b_h10 = np.mean([c[cfg]['hit_rate_at_10'] for c in pos_b])
    e_h10 = np.mean([c[cfg]['hit_rate_at_10'] for c in pos_e])
    
    b_ndcg5 = np.mean([c[cfg]['ndcg_at_5'] for c in pos_b])
    e_ndcg5 = np.mean([c[cfg]['ndcg_at_5'] for c in pos_e])
    
    b_ndcg10 = np.mean([c[cfg]['ndcg_at_10'] for c in pos_b])
    e_ndcg10 = np.mean([c[cfg]['ndcg_at_10'] for c in pos_e])
    
    print(f"MRR:     baseline={b_mrr:.4f} -> exp1={e_mrr:.4f} (diff: {e_mrr - b_mrr:+.4f})")
    print(f"Hit@1:   baseline={b_h1:.4f} -> exp1={e_h1:.4f} (diff: {e_h1 - b_h1:+.4f})")
    print(f"Hit@5:   baseline={b_h5:.4f} -> exp1={e_h5:.4f} (diff: {e_h5 - b_h5:+.4f})")
    print(f"Hit@10:  baseline={b_h10:.4f} -> exp1={e_h10:.4f} (diff: {e_h10 - b_h10:+.4f})")
    print(f"nDCG@5:  baseline={b_ndcg5:.4f} -> exp1={e_ndcg5:.4f} (diff: {e_ndcg5 - b_ndcg5:+.4f})")
    print(f"nDCG@10: baseline={b_ndcg10:.4f} -> exp1={e_ndcg10:.4f} (diff: {e_ndcg10 - b_ndcg10:+.4f})")

print("\n==================== IN-SCOPE CATEGORY BREAKDOWN (Architecture B) ====================")
categories = sorted(list(set(c['category'] for c in pos_b)))
for cat in categories:
    cat_b = [c for c in pos_b if c['category'] == cat]
    cat_e = [c for c in e_cases if c['category'] == cat and not c.get('is_absence_query')]
    n_cat = len(cat_b)
    bm = np.mean([c['architecture_b']['mrr'] for c in cat_b])
    em = np.mean([c['architecture_b']['mrr'] for c in cat_e])
    bh1 = np.mean([1.0 if c['architecture_b']['mrr'] == 1.0 else 0.0 for c in cat_b])
    eh1 = np.mean([1.0 if c['architecture_b']['mrr'] == 1.0 else 0.0 for c in cat_e])
    bh10 = np.mean([c['architecture_b']['hit_rate_at_10'] for c in cat_b])
    eh10 = np.mean([c['architecture_b']['hit_rate_at_10'] for c in cat_e])
    endcg10 = np.mean([c['architecture_b']['ndcg_at_10'] for c in cat_e])
    print(f"Category: {cat:16s} (N={n_cat:2d}) | MRR: {bm:.4f} -> {em:.4f} ({em-bm:+.4f}) | Hit@1: {bh1:.4f} -> {eh1:.4f} ({eh1-bh1:+.4f}) | Hit@10: {bh10:.4f} -> {eh10:.4f} ({eh10-bh10:+.4f}) | nDCG@10: {endcg10:.4f}")

print("\n==================== IN-SCOPE DOMAIN BREAKDOWN (Architecture B) ====================")
for dom in ["movie", "anime", "book"]:
    dom_b = [c for c in pos_b if c['domain'] == dom]
    dom_e = [c for c in e_cases if c['domain'] == dom and not c.get('is_absence_query')]
    n_dom = len(dom_b)
    bm = np.mean([c['architecture_b']['mrr'] for c in dom_b])
    em = np.mean([c['architecture_b']['mrr'] for c in dom_e])
    bh10 = np.mean([c['architecture_b']['hit_rate_at_10'] for c in dom_b])
    eh10 = np.mean([c['architecture_b']['hit_rate_at_10'] for c in dom_e])
    print(f"Domain: {dom:6s} (N={n_dom:2d}) | MRR: {bm:.4f} -> {em:.4f} ({em-bm:+.4f}) | Hit@10: {bh10:.4f} -> {eh10:.4f} ({eh10-bh10:+.4f})")
