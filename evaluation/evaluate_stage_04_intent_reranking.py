"""
Stage 4 Intent-Aware Reranking Evaluation Script.

Evaluates paired rankings on 102 benchmark queries:
- Architecture B: domain_routed (Movie CE, Anime/Book RRF)
- Architecture A: all_cross_encoder baseline
- Metrics: Hit@10, MRR, nDCG@10, Candidate Recall@50, Constraint Violations, Latency
- Intent breakdowns: reference_similarity, genre_discovery, mood_tone_discovery, metadata_constraints, mixed_intent
"""

import json
import math
import sys
import time
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from project_black_knight.query_schema import BlackKnightQuery
from project_black_knight.retrieval import RetrievalRepository, search_black_knight
from project_black_knight.intent_reranker import detect_query_intent


def compute_ndcg_at_k(ranked_ids: list[str], relevant_ids: set[str], k: int = 10) -> float:
    if not relevant_ids:
        return 0.0
    dcg = sum((1.0 / math.log2(i + 1.0)) for i, cid in enumerate(ranked_ids[:k], start=1) if cid in relevant_ids)
    idcg = sum((1.0 / math.log2(i + 1.0)) for i in range(1, min(len(relevant_ids), k) + 1))
    return (dcg / idcg) if idcg > 0 else 0.0


def compute_mrr(ranked_ids: list[str], relevant_ids: set[str], k: int = 10) -> float:
    for i, cid in enumerate(ranked_ids[:k], start=1):
        if cid in relevant_ids:
            return 1.0 / i
    return 0.0


def evaluate_stage_04():
    repo = RetrievalRepository()
    benchmark_path = Path("evaluation/black_knight_eval_queries_113_audited.csv")
    df_bench = pd.read_csv(benchmark_path)

    queries = []
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

            queries.append({
                "query_id": row["query_id"],
                "domain": row["domain"],
                "query_text": row["query_text"],
                "relevant_ids": set(rel_ids),
                "query_obj": query_obj,
            })

    print(f"Loaded {len(queries)} evaluation queries.")

    architectures = ["domain_routed", "all_cross_encoder"]
    metrics_by_arch = {
        arch: {
            "overall": {"hit10": [], "mrr": [], "ndcg10": [], "latencies": [], "violations": 0},
            "by_domain": defaultdict(lambda: {"hit10": [], "mrr": [], "ndcg10": [], "latencies": [], "violations": 0}),
            "by_intent": defaultdict(lambda: {"hit10": [], "mrr": [], "ndcg10": [], "latencies": [], "violations": 0}),
        }
        for arch in architectures
    }

    rankings_sample = []

    for item in queries:
        q_obj = item["query_obj"]
        rel_ids = item["relevant_ids"]
        domain = item["domain"]
        intent = detect_query_intent(q_obj)

        for arch in architectures:
            t0 = time.perf_counter()
            res = search_black_knight(parsed_query=q_obj, architecture=arch, top_k=10, repo=repo)
            lat_ms = (time.perf_counter() - t0) * 1000

            ranked_ids = [r["id"] for r in res["results"]]
            hits_10 = sum(1 for cid in ranked_ids[:10] if cid in rel_ids)
            h10 = 1.0 if hits_10 > 0 else 0.0
            mrr_val = compute_mrr(ranked_ids, rel_ids, k=10)
            ndcg_val = compute_ndcg_at_k(ranked_ids, rel_ids, k=10)

            # Check constraint violations
            df_meta = repo.get_metadata_df(domain)
            violations = 0
            for r in res["results"]:
                if r["id"] in repo._id_to_index[domain]:
                    row = df_meta.iloc[repo._id_to_index[domain][r["id"]]]
                    if q_obj.common.release_year_min and int(row["release_year"]) < q_obj.common.release_year_min:
                        violations += 1
                    if q_obj.common.release_year_max and int(row["release_year"]) > q_obj.common.release_year_max:
                        violations += 1

            store = metrics_by_arch[arch]
            store["overall"]["hit10"].append(h10)
            store["overall"]["mrr"].append(mrr_val)
            store["overall"]["ndcg10"].append(ndcg_val)
            store["overall"]["latencies"].append(lat_ms)
            store["overall"]["violations"] += violations

            d_store = store["by_domain"][domain]
            d_store["hit10"].append(h10)
            d_store["mrr"].append(mrr_val)
            d_store["ndcg10"].append(ndcg_val)
            d_store["latencies"].append(lat_ms)
            d_store["violations"] += violations

            i_store = store["by_intent"][intent]
            i_store["hit10"].append(h10)
            i_store["mrr"].append(mrr_val)
            i_store["ndcg10"].append(ndcg_val)
            i_store["latencies"].append(lat_ms)
            i_store["violations"] += violations

            if arch == "domain_routed" and len(rankings_sample) < 8:
                rankings_sample.append({
                    "query_id": item["query_id"],
                    "domain": domain,
                    "intent": intent,
                    "query_text": item["query_text"],
                    "top_3_results": [r["title"] for r in res["results"][:3]],
                    "hit@10": h10,
                    "mrr": round(mrr_val, 4),
                    "ndcg@10": round(ndcg_val, 4),
                })

    summary = {}
    for arch in architectures:
        summary[arch] = {
            "overall": {
                "query_count": len(queries),
                "hit@10": round(float(np.mean(metrics_by_arch[arch]["overall"]["hit10"])), 4),
                "mrr": round(float(np.mean(metrics_by_arch[arch]["overall"]["mrr"])), 4),
                "ndcg@10": round(float(np.mean(metrics_by_arch[arch]["overall"]["ndcg10"])), 4),
                "mean_latency_ms": round(float(np.mean(metrics_by_arch[arch]["overall"]["latencies"])), 2),
                "median_latency_ms": round(float(np.median(metrics_by_arch[arch]["overall"]["latencies"])), 2),
                "violations_count": metrics_by_arch[arch]["overall"]["violations"],
            },
            "by_domain": {
                d: {
                    "count": len(vals["hit10"]),
                    "hit@10": round(float(np.mean(vals["hit10"])), 4),
                    "mrr": round(float(np.mean(vals["mrr"])), 4),
                    "ndcg@10": round(float(np.mean(vals["ndcg10"])), 4),
                    "mean_latency_ms": round(float(np.mean(vals["latencies"])), 2),
                    "median_latency_ms": round(float(np.median(vals["latencies"])), 2),
                    "violations": vals["violations"],
                }
                for d, vals in metrics_by_arch[arch]["by_domain"].items()
            },
            "by_intent": {
                i: {
                    "count": len(vals["hit10"]),
                    "hit@10": round(float(np.mean(vals["hit10"])), 4),
                    "mrr": round(float(np.mean(vals["mrr"])), 4),
                    "ndcg@10": round(float(np.mean(vals["ndcg10"])), 4),
                }
                for i, vals in metrics_by_arch[arch]["by_intent"].items()
            },
        }

    # Save artifacts
    artifacts_dir = Path("reports/recommendation_quality/artifacts/stage_04")
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    metrics_path = artifacts_dir / "stage_04_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    rankings_path = artifacts_dir / "stage_04_rankings.json"
    with open(rankings_path, "w", encoding="utf-8") as f:
        json.dump(rankings_sample, f, indent=2)

    print("Stage 4 Evaluation Completed Successfully.")
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    evaluate_stage_04()
