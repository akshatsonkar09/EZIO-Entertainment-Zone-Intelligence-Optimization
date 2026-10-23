import time
import json
import math
import numpy as np
import pandas as pd
from pathlib import Path
from project_black_knight.query_schema import BlackKnightQuery
from project_black_knight.retrieval import search_black_knight, RetrievalRepository, _REPO

QUERIES_FILE = "final_test_queries.csv"
LABELS_FILE = "final_test_labels.csv"
PARSES_FILE = "scratch/held_out_parses.json"

def compute_ndcg(retrieved_ids, relevant_ids, k=10):
    if not relevant_ids:
        return 0.0
    rel_set = set(relevant_ids)
    dcg = 0.0
    for idx, item_id in enumerate(retrieved_ids[:k]):
        if item_id in rel_set:
            dcg += 1.0 / math.log2(idx + 2)
    idcg = sum(1.0 / math.log2(i + 2) for i in range(min(len(rel_set), k)))
    return dcg / idcg if idcg > 0 else 0.0

def evaluate_run(run_id=1, top_k=10, repo=_REPO):
    queries_df = pd.read_csv(QUERIES_FILE)
    labels_df = pd.read_csv(LABELS_FILE)
    with open(PARSES_FILE, "r", encoding="utf-8") as f:
        parses_dict = json.load(f)
        
    df = pd.merge(queries_df, labels_df[["query_id", "relevant_ids", "justification"]], on="query_id")
    
    run_records = []
    
    # Pre-warm repository
    print(f"Pre-warming repository for Run {run_id}...")
    t_warm = time.perf_counter()
    for d in ["movie", "anime", "book"]:
        repo.get_metadata_df(d)
        repo.get_documents_and_ids(d)
        repo.get_bm25_index(d)
    repo.get_embedding_model()
    repo.get_reranker_model()
    print(f"Warm-up complete in {(time.perf_counter() - t_warm):.2f}s.")
    
    print(f"Executing Run {run_id} over {len(df)} queries...")
    for idx, row in df.iterrows():
        qid = row["query_id"]
        qtext = row["query_text"]
        cat = row["category"]
        dom = row["domain"]
        is_abs = bool(row["expected_absence"])
        
        rel_ids_raw = row["relevant_ids"]
        if pd.isna(rel_ids_raw) or str(rel_ids_raw).strip() in ("[]", "nan", ""):
            rel_ids = []
        elif str(rel_ids_raw).startswith("["):
            rel_ids = json.loads(str(rel_ids_raw))
        else:
            rel_ids = [s.strip() for s in str(rel_ids_raw).split(";") if s.strip()]
            
        hard_con = json.loads(row["hard_constraints"]) if pd.notna(row["hard_constraints"]) else {}
        query_obj = BlackKnightQuery.model_validate(parses_dict[qid])
        
        for arch in ["domain_routed", "all_cross_encoder"]:
            t0 = time.perf_counter()
            res = search_black_knight(
                user_query=qtext,
                parsed_query=query_obj,
                architecture=arch,
                top_k=top_k,
                repo=repo
            )
            lat_ms = (time.perf_counter() - t0) * 1000.0
            
            top_items = res.get("results", [])
            ret_ids = [item["id"] for item in top_items]
            
            if is_abs:
                mrr = 0.0
                h1 = 0.0
                h5 = 0.0
                h10 = 0.0
                ndcg5 = 0.0
                ndcg10 = 0.0
                false_acceptance = len(top_items) > 0
            else:
                false_acceptance = False
                rank = None
                for r_idx, item_id in enumerate(ret_ids, start=1):
                    if item_id in rel_ids:
                        rank = r_idx
                        break
                mrr = (1.0 / rank) if rank is not None else 0.0
                h1 = 1.0 if (rank is not None and rank == 1) else 0.0
                h5 = 1.0 if (rank is not None and rank <= 5) else 0.0
                h10 = 1.0 if (rank is not None and rank <= 10) else 0.0
                ndcg5 = compute_ndcg(ret_ids, rel_ids, k=5)
                ndcg10 = compute_ndcg(ret_ids, rel_ids, k=10)
                
            # Filter violation check
            hard_violations = 0
            if cat == "constraint" and hard_con:
                for item in top_items:
                    m_type = item["media_type"]
                    meta_df = repo.get_metadata_df(m_type)
                    i_idx = repo._id_to_index[m_type].get(item["id"])
                    if i_idx is not None:
                        meta_row = meta_df.iloc[i_idx]
                        if "release_year_min" in hard_con:
                            y_col = "release_year" if m_type == "anime" else "release_date"
                            v = meta_row.get(y_col)
                            if pd.notna(v) and float(str(v)[:4]) < hard_con["release_year_min"]:
                                hard_violations += 1
                        if "release_year_max" in hard_con:
                            y_col = "release_year" if m_type == "anime" else "release_date"
                            v = meta_row.get(y_col)
                            if pd.notna(v) and float(str(v)[:4]) > hard_con["release_year_max"]:
                                hard_violations += 1
                        if "director" in hard_con:
                            d_val = str(meta_row.get("director", "")).lower()
                            if not any(d.lower() in d_val for d in hard_con["director"]):
                                hard_violations += 1
                                
            run_records.append({
                "run_id": run_id,
                "architecture": arch,
                "query_id": qid,
                "query_text": qtext,
                "category": cat,
                "domain": dom,
                "is_absence": is_abs,
                "latency_ms": round(lat_ms, 2),
                "mrr": round(mrr, 4),
                "hit_1": h1,
                "hit_5": h5,
                "hit_10": h10,
                "ndcg_5": round(ndcg5, 4),
                "ndcg_10": round(ndcg10, 4),
                "false_acceptance": false_acceptance,
                "hard_violations": hard_violations,
                "top_10_ids": json.dumps(ret_ids)
            })
            
    print(f"Run {run_id} completed successfully.")
    return pd.DataFrame(run_records)

def main():
    print("=== PROJECT BLACK KNIGHT HELD-OUT EVALUATION (3 REPEATED RUNS) ===")
    
    # Run 1
    df1 = evaluate_run(run_id=1)
    
    # Run 2
    df2 = evaluate_run(run_id=2)
    
    # Run 3
    df3 = evaluate_run(run_id=3)
    
    all_runs_df = pd.concat([df1, df2, df3], ignore_index=True)
    
    # Save combined results
    all_runs_df.to_csv("final_test_results.csv", index=False)
    print("\nSaved final_test_results.csv successfully!")
    
    # Reproducibility verification
    print("\n=== VERIFYING REPRODUCIBILITY ACROSS RUNS 1, 2, AND 3 ===")
    run1_b = df1[df1["architecture"] == "domain_routed"].sort_values("query_id").reset_index(drop=True)
    run2_b = df2[df2["architecture"] == "domain_routed"].sort_values("query_id").reset_index(drop=True)
    run3_b = df3[df3["architecture"] == "domain_routed"].sort_values("query_id").reset_index(drop=True)
    
    # Check top_10_ids match exactly
    match_1_2 = (run1_b["top_10_ids"] == run2_b["top_10_ids"]).all()
    match_1_3 = (run1_b["top_10_ids"] == run3_b["top_10_ids"]).all()
    print(f"Domain-Routed top_10_ids identical (Run 1 vs Run 2): {match_1_2}")
    print(f"Domain-Routed top_10_ids identical (Run 1 vs Run 3): {match_1_3}")
    
    run1_a = df1[df1["architecture"] == "all_cross_encoder"].sort_values("query_id").reset_index(drop=True)
    run2_a = df2[df2["architecture"] == "all_cross_encoder"].sort_values("query_id").reset_index(drop=True)
    run3_a = df3[df3["architecture"] == "all_cross_encoder"].sort_values("query_id").reset_index(drop=True)
    
    match_a_1_2 = (run1_a["top_10_ids"] == run2_a["top_10_ids"]).all()
    match_a_1_3 = (run1_a["top_10_ids"] == run3_a["top_10_ids"]).all()
    print(f"All-Cross-Encoder top_10_ids identical (Run 1 vs Run 2): {match_a_1_2}")
    print(f"All-Cross-Encoder top_10_ids identical (Run 1 vs Run 3): {match_a_1_3}")
    
    # Print summary metrics for domain_routed
    pos_df1 = df1[(df1["architecture"] == "domain_routed") & (~df1["is_absence"])]
    print("\n=== DOMAIN-ROUTED SUMMARY METRICS (Run 1, N=85 Positive Queries) ===")
    print(f"MRR:     {pos_df1['mrr'].mean():.4f}")
    print(f"Hit@1:   {pos_df1['hit_1'].mean():.4f} ({int(pos_df1['hit_1'].sum())} / {len(pos_df1)})")
    print(f"Hit@5:   {pos_df1['hit_5'].mean():.4f} ({int(pos_df1['hit_5'].sum())} / {len(pos_df1)})")
    print(f"Hit@10:  {pos_df1['hit_10'].mean():.4f} ({int(pos_df1['hit_10'].sum())} / {len(pos_df1)})")
    print(f"nDCG@5:  {pos_df1['ndcg_5'].mean():.4f}")
    print(f"nDCG@10: {pos_df1['ndcg_10'].mean():.4f}")
    
    abs_df1 = df1[(df1["architecture"] == "domain_routed") & (df1["is_absence"])]
    print(f"Absence False Acceptance Rate: {abs_df1['false_acceptance'].mean():.4f} ({int(abs_df1['false_acceptance'].sum())} / {len(abs_df1)})")
    print(f"Hard-filter violations: {df1['hard_violations'].sum()}")
    print(f"Median Latency: {df1[df1['architecture'] == 'domain_routed']['latency_ms'].median():.2f} ms")
    print(f"P95 Latency:    {np.percentile(df1[df1['architecture'] == 'domain_routed']['latency_ms'], 95):.2f} ms")

if __name__ == "__main__":
    main()
