import json
import numpy as np
from scipy import stats

with open('evaluation/results/baseline_audit_report.json', 'r') as f:
    b = json.load(f)

with open('evaluation/results/experiment_1_report.json', 'r') as f:
    e = json.load(f)

b_cases = {c['query_id']: c for c in b['per_query_results'] if not c.get('is_absence_query')}
e_cases = {c['query_id']: c for c in e['per_query_results'] if not c.get('is_absence_query')}

qids = sorted(list(b_cases.keys()))
n = len(qids)

for cfg in ['architecture_a', 'architecture_b', 'rrf_only']:
    print(f"\n==================== STATISTICAL SIGNIFICANCE: {cfg.upper()} ====================")
    b_rr = np.array([b_cases[qid][cfg]['mrr'] for qid in qids])
    e_rr = np.array([e_cases[qid][cfg]['mrr'] for qid in qids])
    diffs = e_rr - b_rr
    
    mean_diff = np.mean(diffs)
    std_diff = np.std(diffs, ddof=1)
    se_diff = std_diff / np.sqrt(n)
    
    # 1. Paired Student's t-test
    t_stat, t_pval = stats.ttest_rel(e_rr, b_rr)
    
    # 2. Paired Wilcoxon Signed-Rank Test (non-parametric)
    # Filter non-zero differences
    nonzero_diffs = diffs[diffs != 0]
    n_wins = np.sum(diffs > 0)
    n_losses = np.sum(diffs < 0)
    n_ties = np.sum(diffs == 0)
    
    if len(nonzero_diffs) > 0:
        w_stat, w_pval = stats.wilcoxon(diffs, alternative='two-sided')
    else:
        w_stat, w_pval = 0.0, 1.0
        
    # 3. Paired Bootstrap Confidence Interval (10,000 resamples)
    np.random.seed(42)
    boot_means = []
    for _ in range(10000):
        idx = np.random.randint(0, n, size=n)
        boot_means.append(np.mean(diffs[idx]))
    boot_ci_low = np.percentile(boot_means, 2.5)
    boot_ci_high = np.percentile(boot_means, 97.5)
    
    print(f"Sample Size (N): {n} positive queries")
    print(f"Baseline Mean MRR: {np.mean(b_rr):.4f}")
    print(f"Final Mean MRR:    {np.mean(e_rr):.4f}")
    print(f"Observed Delta:    {mean_diff:+.4f}")
    print(f"Query Outcomes:    {n_wins} Wins, {n_losses} Losses, {n_ties} Ties (Net Gain: {n_wins - n_losses})")
    print(f"Paired t-test:     t = {t_stat:.4f}, p-value = {t_pval:.6e}")
    print(f"Wilcoxon signed:   W = {w_stat:.1f}, p-value = {w_pval:.6e}")
    print(f"Bootstrap 95% CI:  [{boot_ci_low:+.4f}, {boot_ci_high:+.4f}] (excludes zero: {boot_ci_low > 0})")
    
    # Significance conclusion
    is_sig = (boot_ci_low > 0) and (w_pval < 0.05)
    print(f"Conclusion:        Statistically Significant at alpha=0.05? {'YES' if is_sig else 'NO'}")
