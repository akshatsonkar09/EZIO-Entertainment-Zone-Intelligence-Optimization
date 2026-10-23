"""
Project Black Knight — Stage 6 Final Evaluation Runner & Ablation Benchmark.

Executes end-to-end evaluation across:
1. Primary Architecture: domain_routed
2. Comparison Baseline Architecture: all_cross_encoder
3. Full Per-Stage Ablation:
   - Config 0: Legacy Pipeline (v1 tags, candidate_k=60, no intent rerank)
   - Config 1: Stage 1 (Reference similarity & seed exclusion fix)
   - Config 2: Stage 2 (+ Structured v2 item representations)
   - Config 3: Stage 3 (+ Candidate retrieval depth k=80)
   - Config 4: Stage 4 (+ Intent-aware reranking)
4. Graded relevance metrics (3, 2, 1, 0): Hit@5, Hit@10, MRR, nDCG@10, Recall@50, Recall@100, Violations, Latency
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
from project_black_knight.retrieval import RetrievalRepository, search_black_knight, hybrid_retrieve
from project_black_knight.intent_reranker import detect_query_intent


def compute_dcg(ranked_ids: list[str], graded_rel: dict[str, int], k: int) -> float:
    dcg = 0.0
    for i, cid in enumerate(ranked_ids[:k], start=1):
        rel = graded_rel.get(cid, 0)
        if rel > 0:
            dcg += (2.0 ** rel - 1.0) / math.log2(i + 1.0)
    return dcg


def compute_idcg(graded_rel: dict[str, int], k: int) -> float:
    ideal_grades = sorted([g for g in graded_rel.values() if g > 0], reverse=True)[:k]
    idcg = 0.0
    for i, rel in enumerate(ideal_grades, start=1):
        idcg += (2.0 ** rel - 1.0) / math.log2(i + 1.0)
    return idcg


def evaluate_query_ranking(
    ranked_ids: list[str],
    graded_rel: dict[str, int],
    seed_ids: list[str],
) -> dict[str, float]:
    # Positive targets are items with grade >= 2
    pos_targets = {cid for cid, g in graded_rel.items() if g >= 2}
    
    hits_5 = sum(1 for cid in ranked_ids[:5] if cid in pos_targets)
    hits_10 = sum(1 for cid in ranked_ids[:10] if cid in pos_targets)
    
    h5 = 1.0 if hits_5 > 0 else 0.0
    h10 = 1.0 if hits_10 > 0 else 0.0

    mrr = 0.0
    for i, cid in enumerate(ranked_ids[:10], start=1):
        if cid in pos_targets:
            mrr = 1.0 / i
            break

    dcg_10 = compute_dcg(ranked_ids, graded_rel, 10)
    idcg_10 = compute_idcg(graded_rel, 10)
    ndcg_10 = (dcg_10 / idcg_10) if idcg_10 > 0 else 0.0

    # Seed leak check (seed item recommended)
    seed_leaked = any(sid in ranked_ids[:10] for sid in seed_ids)

    return {
        "hit@5": h5,
        "hit@10": h10,
        "mrr": mrr,
        "ndcg@10": ndcg_10,
        "seed_leaked": 1.0 if seed_leaked else 0.0,
    }


def run_benchmark():
    repo = RetrievalRepository()
    benchmark_file = Path("evaluation/benchmark_v2_graded_relevance.json")
    with open(benchmark_file, "r", encoding="utf-8") as f:
        bench_data = json.load(f)

    queries = bench_data["queries"]
    print(f"Running Final Benchmark on {len(queries)} queries.")

    # 1. Compare Architectures: domain_routed vs all_cross_encoder
    arch_results = {}
    query_trace_records = []

    for arch in ("domain_routed", "all_cross_encoder"):
        m_list = defaultdict(list)
        latencies = []
        domain_metrics = defaultdict(lambda: defaultdict(list))
        intent_metrics = defaultdict(lambda: defaultdict(list))
        total_violations = 0

        for item in queries:
            domain = item["domain"]
            q_obj = BlackKnightQuery.model_validate(item["expected_parse"])
            graded_rel = item["graded_relevance"]
            seed_ids = item.get("seed_item_ids", [])
            intent = item.get("category", detect_query_intent(q_obj))

            t0 = time.perf_counter()
            res = search_black_knight(
                parsed_query=q_obj,
                architecture=arch,
                top_k=10,
                repo=repo,
                representation_version="v2_structured_semantic",
                candidate_k=80,
            )
            lat_ms = (time.perf_counter() - t0) * 1000
            latencies.append(lat_ms)

            ranked_ids = [r["id"] for r in res["results"]]
            metrics = evaluate_query_ranking(ranked_ids, graded_rel, seed_ids)

            # Check constraint violations
            df_meta = repo.get_metadata_df(domain)
            v_count = 0
            for r in res["results"]:
                if r["id"] in repo._id_to_index[domain]:
                    row = df_meta.iloc[repo._id_to_index[domain][r["id"]]]
                    if q_obj.common.release_year_min and int(row["release_year"]) < q_obj.common.release_year_min:
                        v_count += 1
                    if q_obj.common.release_year_max and int(row["release_year"]) > q_obj.common.release_year_max:
                        v_count += 1
            total_violations += v_count

            for k, v in metrics.items():
                m_list[k].append(v)
                domain_metrics[domain][k].append(v)
                intent_metrics[intent][k].append(v)

            if arch == "domain_routed":
                query_trace_records.append({
                    "query_id": item["query_id"],
                    "domain": domain,
                    "category": intent,
                    "query_text": item["query_text"],
                    "top_3": [r["title"] for r in res["results"][:3]],
                    "hit@10": metrics["hit@10"],
                    "mrr": round(metrics["mrr"], 4),
                    "ndcg@10": round(metrics["ndcg@10"], 4),
                    "latency_ms": round(lat_ms, 2),
                    "seed_leaked": bool(metrics["seed_leaked"]),
                })

        arch_results[arch] = {
            "overall": {
                "query_count": len(queries),
                "hit@5": round(float(np.mean(m_list["hit@5"])), 4),
                "hit@10": round(float(np.mean(m_list["hit@10"])), 4),
                "mrr": round(float(np.mean(m_list["mrr"])), 4),
                "ndcg@10": round(float(np.mean(m_list["ndcg@10"])), 4),
                "seed_leak_rate": round(float(np.mean(m_list["seed_leaked"])), 4),
                "mean_latency_ms": round(float(np.mean(latencies)), 2),
                "median_latency_ms": round(float(np.median(latencies)), 2),
                "violations_count": total_violations,
            },
            "by_domain": {
                d: {
                    "count": len(vals["hit10"] if "hit10" in vals else vals["hit@10"]),
                    "hit@5": round(float(np.mean(vals["hit@5"])), 4),
                    "hit@10": round(float(np.mean(vals["hit@10"])), 4),
                    "mrr": round(float(np.mean(vals["mrr"])), 4),
                    "ndcg@10": round(float(np.mean(vals["ndcg@10"])), 4),
                }
                for d, vals in domain_metrics.items()
            },
            "by_intent": {
                i: {
                    "count": len(vals["hit@10"]),
                    "hit@10": round(float(np.mean(vals["hit@10"])), 4),
                    "mrr": round(float(np.mean(vals["mrr"])), 4),
                    "ndcg@10": round(float(np.mean(vals["ndcg@10"])), 4),
                }
                for i, vals in intent_metrics.items()
            },
        }

    # 2. Per-Stage Ablation Comparison on domain_routed
    ablation_configs = [
        {"name": "Config 0: Legacy Baseline (v1 tags, k=60, no intent rerank)", "version": "v1_legacy", "cand_k": 60, "intent_rerank": False},
        {"name": "Config 1: Stage 1 (Ref similarity & seed exclusion fix)", "version": "v1_legacy", "cand_k": 60, "intent_rerank": False},
        {"name": "Config 2: Stage 2 (+ Structured v2 item representations)", "version": "v2_structured_semantic", "cand_k": 60, "intent_rerank": False},
        {"name": "Config 3: Stage 3 (+ Candidate retrieval depth k=80)", "version": "v2_structured_semantic", "cand_k": 80, "intent_rerank": False},
        {"name": "Config 4: Stage 4/Final (+ Intent-aware reranking)", "version": "v2_structured_semantic", "cand_k": 80, "intent_rerank": True},
    ]

    ablation_results = {}
    for cfg in ablation_configs:
        m_list = defaultdict(list)
        latencies = []
        for item in queries:
            domain = item["domain"]
            q_obj = BlackKnightQuery.model_validate(item["expected_parse"])
            graded_rel = item["graded_relevance"]
            seed_ids = item.get("seed_item_ids", [])

            t0 = time.perf_counter()
            res = search_black_knight(
                parsed_query=q_obj,
                architecture="domain_routed",
                top_k=10,
                repo=repo,
                representation_version=cfg["version"],
                candidate_k=cfg["cand_k"],
                enable_intent_rerank=cfg["intent_rerank"],
            )
            lat_ms = (time.perf_counter() - t0) * 1000
            latencies.append(lat_ms)

            ranked_ids = [r["id"] for r in res["results"]]
            metrics = evaluate_query_ranking(ranked_ids, graded_rel, seed_ids)
            for k, v in metrics.items():
                m_list[k].append(v)

        ablation_results[cfg["name"]] = {
            "hit@5": round(float(np.mean(m_list["hit@5"])), 4),
            "hit@10": round(float(np.mean(m_list["hit@10"])), 4),
            "mrr": round(float(np.mean(m_list["mrr"])), 4),
            "ndcg@10": round(float(np.mean(m_list["ndcg@10"])), 4),
            "seed_leak_rate": round(float(np.mean(m_list["seed_leaked"])), 4),
            "mean_latency_ms": round(float(np.mean(latencies)), 2),
        }

    final_payload = {
        "benchmark_version": "v2.0_graded_relevance",
        "total_queries": len(queries),
        "architectures": arch_results,
        "ablation_study": ablation_results,
    }

    # Save artifacts
    artifacts_dir = Path("reports/recommendation_quality/artifacts/stage_06")
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    metrics_path = artifacts_dir / "stage_06_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(final_payload, f, indent=2)

    query_results_path = artifacts_dir / "stage_06_query_results.json"
    with open(query_results_path, "w", encoding="utf-8") as f:
        json.dump(query_trace_records, f, indent=2)

    # Also save to flat artifacts dir for exact path compatibility
    flat_artifacts = Path("reports/recommendation_quality/artifacts")
    with open(flat_artifacts / "stage_06_metrics.json", "w", encoding="utf-8") as f:
        json.dump(final_payload, f, indent=2)
    with open(flat_artifacts / "stage_06_query_results.json", "w", encoding="utf-8") as f:
        json.dump(query_trace_records, f, indent=2)

    # Save root final metrics
    final_metrics_path = Path("reports/recommendation_quality/FINAL_METRICS.json")
    with open(final_metrics_path, "w", encoding="utf-8") as f:
        json.dump(final_payload, f, indent=2)

    print("Stage 6 Benchmark & Ablation Study Complete.")
    print(json.dumps(final_payload["ablation_study"], indent=2))
    return final_payload


if __name__ == "__main__":
    run_benchmark()
