"""
Compare Baseline vs Post-Fix Reports on the 113 Benchmark
"""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def main():
    base_file = PROJECT_ROOT / "evaluation" / "results" / "retrieval_113_baseline_report.json"
    post_file = PROJECT_ROOT / "evaluation" / "results" / "retrieval_113_post_fix_report.json"
    
    with open(base_file, "r", encoding="utf-8") as f:
        base = json.load(f)
    with open(post_file, "r", encoding="utf-8") as f:
        post = json.load(f)
        
    base_queries = {q["query_id"]: q for q in base["per_query_results"]}
    post_queries = {q["query_id"]: q for q in post["per_query_results"]}
    
    print("=== PER-QUERY CROSS-ENCODER RERANKED COMPARISON ===")
    improved_mrr = []
    regressed_mrr = []
    improved_hr10 = []
    regressed_hr10 = []
    
    for qid, b_res in base_queries.items():
        if b_res["is_absence_query"]:
            continue
        p_res = post_queries[qid]
        
        b_ce_mrr = b_res["reranked"]["mrr"]
        p_ce_mrr = p_res["reranked"]["mrr"]
        
        b_ce_hr10 = b_res["reranked"]["hit_rate_at_10"]
        p_ce_hr10 = p_res["reranked"]["hit_rate_at_10"]
        
        if p_ce_mrr > b_ce_mrr:
            improved_mrr.append((qid, b_res["domain"], b_res["query_text"], b_ce_mrr, p_ce_mrr))
        elif p_ce_mrr < b_ce_mrr:
            regressed_mrr.append((qid, b_res["domain"], b_res["query_text"], b_ce_mrr, p_ce_mrr))
            
        if p_ce_hr10 > b_ce_hr10:
            improved_hr10.append((qid, b_res["domain"], b_res["query_text"]))
        elif p_ce_hr10 < b_ce_hr10:
            regressed_hr10.append((qid, b_res["domain"], b_res["query_text"]))
            
    print(f"\nMRR Improvements (N={len(improved_mrr)}):")
    for qid, dom, text, bm, pm in improved_mrr:
        print(f"  + [{qid}] ({dom}) '{text}': MRR {bm:.4f} -> {pm:.4f} (+{pm-bm:.4f})")
        
    print(f"\nMRR Regressions (N={len(regressed_mrr)}):")
    for qid, dom, text, bm, pm in regressed_mrr:
        print(f"  - [{qid}] ({dom}) '{text}': MRR {bm:.4f} -> {pm:.4f} ({pm-bm:.4f})")
        
    print(f"\nHit Rate@10 Improvements (N={len(improved_hr10)}): {improved_hr10}")
    print(f"Hit Rate@10 Regressions (N={len(regressed_hr10)}): {regressed_hr10}")

if __name__ == "__main__":
    main()
