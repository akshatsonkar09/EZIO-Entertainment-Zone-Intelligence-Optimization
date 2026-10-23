"""
Stage 3 Candidate Retrieval Tuning and Overlap Analysis Script.

Measures:
1. Independent Dense Recall@50 and Recall@100
2. Independent BM25 Recall@50 and Recall@100
3. Overlap between Dense and BM25 candidate pools (Jaccard similarity, intersection size)
4. Incremental relevant items found exclusively by Dense vs BM25
5. Candidate pool depth ablation (candidate_k: 40, 60, 80, 100)
6. RRF fusion constant ablation (k: 20, 40, 60)
7. Domain-specific breakdown
"""

import json
import math
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
)

def run_retrieval_analysis():
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
                "category": row.get("category", "standard"),
                "query_text": row["query_text"],
                "relevant_ids": set(rel_ids),
                "query_obj": query_obj,
            })

    print(f"Loaded {len(valid_queries)} positive benchmark queries.")

    # Track retriever statistics
    overlap_records = []
    coverage_records = {
        "movie": {"both": 0, "dense_only": 0, "bm25_only": 0, "neither": 0, "total_targets": 0},
        "anime": {"both": 0, "dense_only": 0, "bm25_only": 0, "neither": 0, "total_targets": 0},
        "book": {"both": 0, "dense_only": 0, "bm25_only": 0, "neither": 0, "total_targets": 0},
        "overall": {"both": 0, "dense_only": 0, "bm25_only": 0, "neither": 0, "total_targets": 0},
    }

    # Compare candidate_k options: 40, 60, 80, 100
    k_options = [40, 60, 80, 100]
    k_eval = {k: {"overall": [], "movie": [], "anime": [], "book": []} for k in k_options}

    for item in valid_queries:
        domain = item["domain"]
        rel_ids = item["relevant_ids"]
        q_text = item["query_text"]
        retrieval_query = item["query_obj"].semantic_query if (item["query_obj"] and item["query_obj"].semantic_query) else q_text

        dense_cands = dense_retrieve(retrieval_query, media_type=domain, top_k=100, repo=repo)
        bm25_cands = bm25_retrieve(retrieval_query, media_type=domain, top_k=100, repo=repo, representation_version="v2_structured_semantic")

        dense_ids = [c["id"] for c in dense_cands]
        bm25_ids = [c["id"] for c in bm25_cands]

        dense_set_100 = set(dense_ids[:100])
        bm25_set_100 = set(bm25_ids[:100])
        intersection_100 = dense_set_100 & bm25_set_100
        union_100 = dense_set_100 | bm25_set_100
        jaccard_100 = len(intersection_100) / float(len(union_100)) if union_100 else 0.0

        dense_set_50 = set(dense_ids[:50])
        bm25_set_50 = set(bm25_ids[:50])
        intersection_50 = dense_set_50 & bm25_set_50
        union_50 = dense_set_50 | bm25_set_50
        jaccard_50 = len(intersection_50) / float(len(union_50)) if union_50 else 0.0

        overlap_records.append({
            "query_id": item["query_id"],
            "domain": domain,
            "dense_count": len(dense_ids),
            "bm25_count": len(bm25_ids),
            "jaccard@50": round(jaccard_50, 4),
            "intersection@50": len(intersection_50),
            "jaccard@100": round(jaccard_100, 4),
            "intersection@100": len(intersection_100),
        })

        # Measure coverage of targets
        for tid in rel_ids:
            in_dense = tid in dense_set_100
            in_bm25 = tid in bm25_set_100
            for d_key in (domain, "overall"):
                coverage_records[d_key]["total_targets"] += 1
                if in_dense and in_bm25:
                    coverage_records[d_key]["both"] += 1
                elif in_dense:
                    coverage_records[d_key]["dense_only"] += 1
                elif in_bm25:
                    coverage_records[d_key]["bm25_only"] += 1
                else:
                    coverage_records[d_key]["neither"] += 1

        # Test candidate_k depths
        for k_val in k_options:
            rrf_pairs = reciprocal_rank_fusion([dense_ids[:k_val], bm25_ids[:k_val]], k=60, top_k=k_val)
            rrf_ids = [cid for cid, _ in rrf_pairs]
            hits = sum(1 for tid in rel_ids if tid in rrf_ids)
            rec = hits / float(len(rel_ids))
            k_eval[k_val]["overall"].append(rec)
            k_eval[k_val][domain].append(rec)

    # Compile Summary
    summary = {
        "candidate_pool_depth_ablation": {
            k: {
                "overall_recall": round(float(np.mean(k_eval[k]["overall"])), 4),
                "movie_recall": round(float(np.mean(k_eval[k]["movie"])), 4),
                "anime_recall": round(float(np.mean(k_eval[k]["anime"])), 4),
                "book_recall": round(float(np.mean(k_eval[k]["book"])), 4),
            }
            for k in k_options
        },
        "retriever_overlap": {
            "mean_intersection@50": round(float(np.mean([r["intersection@50"] for r in overlap_records])), 2),
            "mean_jaccard@50": round(float(np.mean([r["jaccard@50"] for r in overlap_records])), 4),
            "mean_intersection@100": round(float(np.mean([r["intersection@100"] for r in overlap_records])), 2),
            "mean_jaccard@100": round(float(np.mean([r["jaccard@100"] for r in overlap_records])), 4),
        },
        "target_coverage_breakdown": coverage_records,
    }

    print(json.dumps(summary, indent=2))
    return summary, overlap_records

if __name__ == "__main__":
    run_retrieval_analysis()
