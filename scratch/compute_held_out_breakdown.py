import pandas as pd
import numpy as np

df = pd.read_csv("final_test_results.csv")
run1 = df[df["run_id"] == 1]

for arch in ["domain_routed", "all_cross_encoder"]:
    arch_df = run1[run1["architecture"] == arch]
    pos_df = arch_df[~arch_df["is_absence"]]
    abs_df = arch_df[arch_df["is_absence"]]
    
    print(f"\n==================== ARCHITECTURE: {arch.upper()} ====================")
    print(f"Overall MRR:     {pos_df['mrr'].mean():.4f}")
    print(f"Overall Hit@1:   {pos_df['hit_1'].mean():.4f}")
    print(f"Overall Hit@5:   {pos_df['hit_5'].mean():.4f}")
    print(f"Overall Hit@10:  {pos_df['hit_10'].mean():.4f}")
    print(f"Overall nDCG@5:  {pos_df['ndcg_5'].mean():.4f}")
    print(f"Overall nDCG@10: {pos_df['ndcg_10'].mean():.4f}")
    print(f"Absence FA Rate: {abs_df['false_acceptance'].mean():.4f} ({int(abs_df['false_acceptance'].sum())}/{len(abs_df)})")
    print(f"Hard Violations: {arch_df['hard_violations'].sum()}")
    print(f"Median Latency:  {arch_df['latency_ms'].median():.2f} ms")
    print(f"P95 Latency:     {np.percentile(arch_df['latency_ms'], 95):.2f} ms")
    
    print("\n--- By Category ---")
    for cat in ["known_item", "descriptive", "constraint", "multi_domain"]:
        cat_df = pos_df[pos_df["category"] == cat]
        print(f"  {cat:15s} (N={len(cat_df):2d}) | MRR: {cat_df['mrr'].mean():.4f} | Hit@1: {cat_df['hit_1'].mean():.4f} | Hit@10: {cat_df['hit_10'].mean():.4f} | nDCG@10: {cat_df['ndcg_10'].mean():.4f}")
        
    print("\n--- By Domain ---")
    for dom in ["movie", "anime", "book", "mixed"]:
        dom_df = pos_df[pos_df["domain"] == dom]
        print(f"  {dom:15s} (N={len(dom_df):2d}) | MRR: {dom_df['mrr'].mean():.4f} | Hit@1: {dom_df['hit_1'].mean():.4f} | Hit@10: {dom_df['hit_10'].mean():.4f} | nDCG@10: {dom_df['ndcg_10'].mean():.4f}")
