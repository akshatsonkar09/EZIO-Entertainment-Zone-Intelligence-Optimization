"""
Stage 3 Full Evaluation & Artifact Generation Script.
"""

import json
import time
import sys
from pathlib import Path
import numpy as np
import pandas as pd

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from project_black_knight.query_schema import BlackKnightQuery
from project_black_knight.retrieval import (
    RetrievalRepository,
    bm25_retrieve,
    dense_retrieve,
    reciprocal_rank_fusion,
    hybrid_retrieve,
)


def run_stage_03_evaluation():
    repo = RetrievalRepository()
    benchmark_path = Path("evaluation/black_knight_eval_queries_113_audited.csv")
    df_bench = pd.read_csv(benchmark_path)

    valid_queries = []
    for _, row in df_bench.iterrows():
        try:
            rel_ids = json.loads(row["relevant_ids"]) if isinstance(row["relevant_ids"], str) else []
        except Exception:
            rel_ids = []
        if rel_ids:
            try:
                parse_dict = json.loads(row["expected_parse"]) if isinstance(row["expected_parse"], str) else None
                query_obj = BlackKnightQuery.model_validate(parse_dict) if parse_dict else None
            except Exception:
                query_obj = None

            valid_queries.append({
                "query_id": row["query_id"],
                "domain": row["domain"],
                "query_text": row["query_text"],
                "relevant_ids": set(rel_ids),
                "query_obj": query_obj,
            })

    print(f"Loaded {len(valid_queries)} positive benchmark queries.")

    metrics_by_domain = {
        d: {
            "query_count": 0,
            "dense_rec50": [], "dense_rec100": [],
            "bm25_rec50": [], "bm25_rec100": [],
            "old_rrf60_rec50": [], "old_rrf60_rec100": [],
            "new_rrf80_rec50": [], "new_rrf80_rec100": [],
            "jaccard50": [], "jaccard100": [],
            "dense_latencies": [], "bm25_latencies": [], "rrf_latencies": [],
        }
        for d in ("movie", "anime", "book", "overall")
    }

    coverage_totals = {
        d: {"both": 0, "dense_only": 0, "bm25_only": 0, "neither": 0, "total_targets": 0}
        for d in ("movie", "anime", "book", "overall")
    }

    sample_candidates = []

    for item in valid_queries:
        domain = item["domain"]
        rel_ids = item["relevant_ids"]
        q_text = item["query_text"]
        retrieval_query = item["query_obj"].semantic_query if (item["query_obj"] and item["query_obj"].semantic_query) else q_text

        # 1. Dense retrieval
        t0 = time.perf_counter()
        dense_cands = dense_retrieve(retrieval_query, media_type=domain, top_k=100, repo=repo)
        t_dense = (time.perf_counter() - t0) * 1000
        dense_ids = [c["id"] for c in dense_cands]

        # 2. BM25 retrieval
        t0 = time.perf_counter()
        bm25_cands = bm25_retrieve(retrieval_query, media_type=domain, top_k=100, repo=repo, representation_version="v2_structured_semantic")
        t_bm25 = (time.perf_counter() - t0) * 1000
        bm25_ids = [c["id"] for c in bm25_cands]

        # 3. Old RRF (k=60, candidate_k=60)
        t0 = time.perf_counter()
        old_rrf_pairs = reciprocal_rank_fusion([dense_ids[:60], bm25_ids[:60]], k=60, top_k=60)
        old_rrf_ids = [cid for cid, _ in old_rrf_pairs]

        # 4. New Improved RRF (k=60, candidate_k=80)
        new_rrf_pairs = reciprocal_rank_fusion([dense_ids[:80], bm25_ids[:80]], k=60, top_k=80)
        t_rrf = (time.perf_counter() - t0) * 1000
        new_rrf_ids = [cid for cid, _ in new_rrf_pairs]

        def rec_at_k(c_list, k):
            return sum(1 for cid in c_list[:k] if cid in rel_ids) / float(len(rel_ids))

        d_r50 = rec_at_k(dense_ids, 50)
        d_r100 = rec_at_k(dense_ids, 100)
        b_r50 = rec_at_k(bm25_ids, 50)
        b_r100 = rec_at_k(bm25_ids, 100)
        o_r50 = rec_at_k(old_rrf_ids, 50)
        o_r100 = rec_at_k(old_rrf_ids, 60)
        n_r50 = rec_at_k(new_rrf_ids, 50)
        n_r80 = rec_at_k(new_rrf_ids, 80)

        # Overlap
        s_d50 = set(dense_ids[:50])
        s_b50 = set(bm25_ids[:50])
        j50 = len(s_d50 & s_b50) / float(len(s_d50 | s_b50)) if (s_d50 | s_b50) else 0.0

        s_d100 = set(dense_ids[:100])
        s_b100 = set(bm25_ids[:100])
        j100 = len(s_d100 & s_b100) / float(len(s_d100 | s_b100)) if (s_d100 | s_b100) else 0.0

        for d_key in (domain, "overall"):
            metrics_by_domain[d_key]["query_count"] += 1
            metrics_by_domain[d_key]["dense_rec50"].append(d_r50)
            metrics_by_domain[d_key]["dense_rec100"].append(d_r100)
            metrics_by_domain[d_key]["bm25_rec50"].append(b_r50)
            metrics_by_domain[d_key]["bm25_rec100"].append(b_r100)
            metrics_by_domain[d_key]["old_rrf60_rec50"].append(o_r50)
            metrics_by_domain[d_key]["old_rrf60_rec100"].append(o_r100)
            metrics_by_domain[d_key]["new_rrf80_rec50"].append(n_r50)
            metrics_by_domain[d_key]["new_rrf80_rec100"].append(n_r80)
            metrics_by_domain[d_key]["jaccard50"].append(j50)
            metrics_by_domain[d_key]["jaccard100"].append(j100)
            metrics_by_domain[d_key]["dense_latencies"].append(t_dense)
            metrics_by_domain[d_key]["bm25_latencies"].append(t_bm25)
            metrics_by_domain[d_key]["rrf_latencies"].append(t_rrf)

            for tid in rel_ids:
                in_d = tid in s_d100
                in_b = tid in s_b100
                coverage_totals[d_key]["total_targets"] += 1
                if in_d and in_b:
                    coverage_totals[d_key]["both"] += 1
                elif in_d:
                    coverage_totals[d_key]["dense_only"] += 1
                elif in_b:
                    coverage_totals[d_key]["bm25_only"] += 1
                else:
                    coverage_totals[d_key]["neither"] += 1

        if len(sample_candidates) < 6:
            df_meta = repo.get_metadata_df(domain)
            t_col = "title" if "title" in df_meta.columns else df_meta.columns[0]
            top_dense_titles = [str(df_meta.iloc[repo._id_to_index[domain][cid]][t_col]) for cid in dense_ids[:3] if cid in repo._id_to_index[domain]]
            top_bm25_titles = [str(df_meta.iloc[repo._id_to_index[domain][cid]][t_col]) for cid in bm25_ids[:3] if cid in repo._id_to_index[domain]]
            top_rrf_titles = [str(df_meta.iloc[repo._id_to_index[domain][cid]][t_col]) for cid in new_rrf_ids[:3] if cid in repo._id_to_index[domain]]
            sample_candidates.append({
                "query_id": item["query_id"],
                "domain": domain,
                "query_text": q_text,
                "dense_top_3": top_dense_titles,
                "bm25_top_3": top_bm25_titles,
                "fused_top_3": top_rrf_titles,
                "dense_recall@100": round(d_r100, 4),
                "bm25_recall@100": round(b_r100, 4),
                "rrf_recall@80": round(n_r80, 4),
            })

    # Summary
    summary = {
        "candidate_retrieval_metrics": {},
        "target_coverage_breakdown": coverage_totals,
        "latencies_ms": {},
    }

    for dom, data in metrics_by_domain.items():
        summary["candidate_retrieval_metrics"][dom] = {
            "query_count": data["query_count"],
            "dense_recall@50": round(float(np.mean(data["dense_rec50"])), 4),
            "dense_recall@100": round(float(np.mean(data["dense_rec100"])), 4),
            "bm25_recall@50": round(float(np.mean(data["bm25_rec50"])), 4),
            "bm25_recall@100": round(float(np.mean(data["bm25_rec100"])), 4),
            "old_rrf60_recall@60": round(float(np.mean(data["old_rrf60_rec100"])), 4),
            "new_rrf80_recall@80": round(float(np.mean(data["new_rrf80_rec100"])), 4),
            "rrf_recall_delta": round(float(np.mean(data["new_rrf80_rec100"]) - np.mean(data["old_rrf60_rec100"])), 4),
            "jaccard_overlap@50": round(float(np.mean(data["jaccard50"])), 4),
            "jaccard_overlap@100": round(float(np.mean(data["jaccard100"])), 4),
        }
        summary["latencies_ms"][dom] = {
            "dense_mean_ms": round(float(np.mean(data["dense_latencies"])), 2),
            "bm25_mean_ms": round(float(np.mean(data["bm25_latencies"])), 2),
            "rrf_mean_ms": round(float(np.mean(data["rrf_latencies"])), 2),
        }

    # Save artifacts
    artifacts_dir = Path("reports/recommendation_quality/artifacts/stage_03")
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    metrics_path = artifacts_dir / "stage_03_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    candidates_path = artifacts_dir / "stage_03_candidates.json"
    with open(candidates_path, "w", encoding="utf-8") as f:
        json.dump(sample_candidates, f, indent=2)

    print("Stage 3 Artifacts Generated Successfully.")
    print(json.dumps(summary["candidate_retrieval_metrics"], indent=2))
    return summary


if __name__ == "__main__":
    run_stage_03_evaluation()
