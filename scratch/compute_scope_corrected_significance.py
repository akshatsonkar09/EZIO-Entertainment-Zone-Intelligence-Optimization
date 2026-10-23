import json
import numpy as np
from scipy import stats

with open("evaluation/results/baseline_audit_report.json", "r", encoding="utf-8") as f:
    b_data = json.load(f)
with open("evaluation/results/experiment_1_report.json", "r", encoding="utf-8") as f:
    e_data = json.load(f)

# Map by query_id for positive in-scope queries
b_cases = {c["query_id"]: c for c in b_data["per_query_results"] if not c["query_id"].startswith("SI_") and not c.get("is_absence_query")}
e_cases = {c["query_id"]: c for c in e_data["per_query_results"] if not c["query_id"].startswith("SI_") and not c.get("is_absence_query")}

common_ids = sorted(list(set(b_cases.keys()) & set(e_cases.keys())))
print(f"Total evaluated in-scope positive queries: {len(common_ids)}")

for cfg in ["architecture_b", "architecture_a", "rrf_only"]:
    print(f"\n--- Significance for {cfg.upper()} ---")
    mrr_b = np.array([b_cases[qid][cfg]["mrr"] for qid in common_ids])
    mrr_e = np.array([e_cases[qid][cfg]["mrr"] for qid in common_ids])
    diffs = mrr_e - mrr_b

    wins = np.sum(diffs > 1e-6)
    losses = np.sum(diffs < -1e-6)
    ties = np.sum(np.abs(diffs) <= 1e-6)
    print(f"Wins: {wins}, Losses: {losses}, Ties: {ties}")
    print(f"Mean baseline MRR: {np.mean(mrr_b):.4f}, Mean exp1 MRR: {np.mean(mrr_e):.4f}, Mean diff: {np.mean(diffs):.4f}")

    # Paired t-test
    t_stat, p_t = stats.ttest_rel(mrr_e, mrr_b)
    print(f"Paired t-test: t = {t_stat:.4f}, p = {p_t:.6f}")

    # Wilcoxon signed rank test
    w_res = stats.wilcoxon(diffs, zero_method="wilcox", alternative="two-sided")
    print(f"Wilcoxon signed-rank test (zero_method='wilcox'): statistic = {w_res.statistic}, p = {w_res.pvalue:.6f}")

    # Bootstrap 95% CI on mean difference
    np.random.seed(42)
    n_bootstraps = 10000
    boot_diffs = []
    for _ in range(n_bootstraps):
        sample = np.random.choice(diffs, size=len(diffs), replace=True)
        boot_diffs.append(np.mean(sample))

    ci_lower = np.percentile(boot_diffs, 2.5)
    ci_upper = np.percentile(boot_diffs, 97.5)
    print(f"Bootstrap 95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")
