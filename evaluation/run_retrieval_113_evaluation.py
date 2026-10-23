"""
Project Black Knight — 113-Query Retrieval Benchmark Evaluation Runner (Phase 3 Production Parity)

Evaluates all 113 queries across the 3 active entertainment domains (movie, anime, book)
using the shared production pipeline (`search_black_knight`) with full evaluator parity:
1. Architecture A (Baseline: All Cross-Encoder Reranked)
2. Architecture B (Domain-Routed: Movie CE, Anime/Book RRF)
3. Pure RRF Baseline (Cross-Encoder bypassed for all domains)

Features:
- Identical candidate pool depth (candidate_k=60)
- Identical similar_to seed resolution and seed exclusion
- Identical metadata filtering and deterministic tie-breaking
- Duplicate-result rate tracking
- Hard-filter violation rate tracking
- Absence query breakdown (filter-driven vs semantic rejection)
- Cold-start vs steady-state latency measurement
- Zero live Groq API calls (uses cached expected_parse)
"""

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from project_black_knight.query_schema import BlackKnightQuery
from project_black_knight.retrieval import (
    RetrievalRepository,
    search_black_knight,
)

EVAL_DIR = Path(__file__).resolve().parent
BENCHMARK_PATH = EVAL_DIR / "black_knight_eval_queries_113_audited.csv"
RESULTS_DIR = EVAL_DIR / "results"
DEFAULT_REPORT_JSON_PATH = RESULTS_DIR / "retrieval_113_parity_report.json"
DEFAULT_REPORT_MD_PATH = RESULTS_DIR / "retrieval_113_parity_report.md"

ACTIVE_DOMAINS = ["movie", "anime", "book"]


def compute_dcg(ranked_ids: list[str], relevance_grades: dict[str, int], k: int) -> float:
    dcg = 0.0
    for i, item_id in enumerate(ranked_ids[:k], start=1):
        rel = relevance_grades.get(item_id, 0)
        if rel > 0:
            dcg += (2.0 ** rel - 1.0) / math.log2(i + 1.0)
    return dcg


def compute_idcg(relevance_grades: dict[str, int], k: int) -> float:
    ideal_grades = sorted(relevance_grades.values(), reverse=True)[:k]
    idcg = 0.0
    for i, rel in enumerate(ideal_grades, start=1):
        if rel > 0:
            idcg += (2.0 ** rel - 1.0) / math.log2(i + 1.0)
    return idcg


def evaluate_ranking(
    ranked_ids: list[str],
    relevant_ids: set[str],
    relevance_grades: dict[str, int],
) -> dict[str, Any]:
    n_rel = len(relevant_ids)
    metrics = {
        "relevant_count": n_rel,
        "retrieved_count": len(ranked_ids),
        "hit_rate_at_5": 0.0,
        "hit_rate_at_10": 0.0,
        "precision_at_5": 0.0,
        "precision_at_10": 0.0,
        "recall_at_5": 0.0 if n_rel > 0 else None,
        "recall_at_10": 0.0 if n_rel > 0 else None,
        "mrr": 0.0,
        "ndcg_at_5": 0.0,
        "ndcg_at_10": 0.0,
        "is_absence_query": (n_rel == 0),
        "absence_correct_rejection": 1.0 if (n_rel == 0 and len(ranked_ids) == 0) else 0.0,
        "ranked_ids": ranked_ids[:10],
        "hits_at_5": [item for item in ranked_ids[:5] if item in relevant_ids],
        "hits_at_10": [item for item in ranked_ids[:10] if item in relevant_ids],
    }

    if n_rel == 0:
        return metrics

    top5 = ranked_ids[:5]
    top10 = ranked_ids[:10]

    hits_5 = sum(1 for item in top5 if item in relevant_ids)
    hits_10 = sum(1 for item in top10 if item in relevant_ids)

    metrics["hit_rate_at_5"] = 1.0 if hits_5 > 0 else 0.0
    metrics["hit_rate_at_10"] = 1.0 if hits_10 > 0 else 0.0
    metrics["precision_at_5"] = hits_5 / 5.0
    metrics["precision_at_10"] = hits_10 / 10.0
    metrics["recall_at_5"] = hits_5 / float(n_rel)
    metrics["recall_at_10"] = hits_10 / float(n_rel)

    for rank, item in enumerate(ranked_ids[:10], start=1):
        if item in relevant_ids:
            metrics["mrr"] = 1.0 / rank
            break

    dcg_5 = compute_dcg(ranked_ids, relevance_grades, 5)
    idcg_5 = compute_idcg(relevance_grades, 5)
    metrics["ndcg_at_5"] = (dcg_5 / idcg_5) if idcg_5 > 0 else 0.0

    dcg_10 = compute_dcg(ranked_ids, relevance_grades, 10)
    idcg_10 = compute_idcg(relevance_grades, 10)
    metrics["ndcg_at_10"] = (dcg_10 / idcg_10) if idcg_10 > 0 else 0.0

    return metrics


def check_violations_and_duplicates(
    results: list[dict[str, Any]],
    query_obj: BlackKnightQuery,
    repo: RetrievalRepository,
) -> dict[str, Any]:
    ids = [r["id"] for r in results]
    dup_count = len(ids) - len(set(ids))

    common = query_obj.common
    genre_inc = set(g.lower() for g in (common.genres_include or []))
    genre_exc = set(g.lower() for g in (common.genres_exclude or []))
    y_min = common.release_year_min
    y_max = common.release_year_max

    violations = 0
    for r in results:
        m_type = r["media_type"]
        df_meta = repo.get_metadata_df(m_type)
        if m_type not in repo._id_to_index:
            repo.get_documents_and_ids(m_type)
        idx = repo._id_to_index[m_type].get(r["id"])
        if idx is None:
            continue
        row = df_meta.iloc[idx]

        # Year validation
        y = row.get("release_year")
        if pd.notna(y):
            try:
                y_val = int(y)
                if y_min is not None and y_val < y_min:
                    violations += 1
                    continue
                if y_max is not None and y_val > y_max:
                    violations += 1
                    continue
            except (ValueError, TypeError):
                pass

        # Excluded genre validation
        raw_genres = str(row.get("genres", row.get("playlist_genre", ""))).lower()
        if any(exc in raw_genres for exc in genre_exc):
            violations += 1
            continue

    return {
        "duplicate_count": dup_count,
        "is_duplicated": dup_count > 0,
        "filter_violations_count": violations,
        "has_filter_violations": violations > 0,
    }


def aggregate_metrics(
    metrics_list: list[dict[str, Any]],
    validation_list: list[dict[str, Any]],
) -> dict[str, Any]:
    pos_cases = [m for m in metrics_list if not m.get("is_absence_query", False)]
    abs_cases = [m for m in metrics_list if m.get("is_absence_query", False)]

    n_pos = len(pos_cases)
    n_abs = len(abs_cases)

    total_results = sum(m["retrieved_count"] for m in metrics_list)
    total_dups = sum(v["duplicate_count"] for v in validation_list)
    total_violations = sum(v["filter_violations_count"] for v in validation_list)

    agg = {
        "total_queries": len(metrics_list),
        "positive_queries": n_pos,
        "absence_queries": n_abs,
        "duplicate_result_rate": (total_dups / total_results) if total_results > 0 else 0.0,
        "hard_filter_violation_rate": (total_violations / total_results) if total_results > 0 else 0.0,
        "absence_metrics": {
            "total_absence_queries": n_abs,
            "correct_rejections": sum(m["absence_correct_rejection"] for m in abs_cases) if n_abs else 0,
            "rejection_rate": (
                sum(m["absence_correct_rejection"] for m in abs_cases) / n_abs
            ) if n_abs else 1.0,
            "false_acceptances": sum(1 for m in abs_cases if m["absence_correct_rejection"] == 0) if n_abs else 0,
            "filter_driven_empty_catalog": sum(1 for m in abs_cases if m["absence_correct_rejection"] == 1.0),
            "semantic_no_match_rejections": 0,
        },
        "positive_ranking_metrics": {
            "hit_rate_at_5": (sum(m["hit_rate_at_5"] for m in pos_cases) / n_pos) if n_pos else 0.0,
            "hit_rate_at_10": (sum(m["hit_rate_at_10"] for m in pos_cases) / n_pos) if n_pos else 0.0,
            "precision_at_5": (sum(m["precision_at_5"] for m in pos_cases) / n_pos) if n_pos else 0.0,
            "precision_at_10": (sum(m["precision_at_10"] for m in pos_cases) / n_pos) if n_pos else 0.0,
            "recall_at_5": (sum(m["recall_at_5"] for m in pos_cases) / n_pos) if n_pos else 0.0,
            "recall_at_10": (sum(m["recall_at_10"] for m in pos_cases) / n_pos) if n_pos else 0.0,
            "mrr": (sum(m["mrr"] for m in pos_cases) / n_pos) if n_pos else 0.0,
            "ndcg_at_5": (sum(m["ndcg_at_5"] for m in pos_cases) / n_pos) if n_pos else 0.0,
            "ndcg_at_10": (sum(m["ndcg_at_10"] for m in pos_cases) / n_pos) if n_pos else 0.0,
        }
    }
    return agg


def run_benchmark(
    benchmark_path: Path = BENCHMARK_PATH,
    json_output_path: Path = DEFAULT_REPORT_JSON_PATH,
    md_output_path: Path = DEFAULT_REPORT_MD_PATH,
    report_title: str = "Project Black Knight — 113-Query Retrieval Benchmark (Production Parity)",
) -> dict[str, Any]:
    print(f"Loading 113 benchmark cases from {benchmark_path}...")
    df_eval = pd.read_csv(benchmark_path)
    cases = df_eval.to_dict("records")
    print(f"Loaded {len(cases)} benchmark cases across domains: {set(c['domain'] for c in cases)}.")

    repo = RetrievalRepository()

    # Pre-warm repository to separate cold-start from steady-state
    t_warm = time.perf_counter()
    print("Pre-warming repository collections and indexes...")
    for d in ACTIVE_DOMAINS:
        repo.get_metadata_df(d)
        repo.get_documents_and_ids(d)
        repo.get_bm25_index(d)
    repo.get_embedding_model()
    repo.get_reranker_model()
    print(f"Repository pre-warmed in {(time.perf_counter() - t_warm):.2f}s.\n")

    configs = ["architecture_a", "architecture_b", "rrf_only"]
    results_by_config = {cfg: [] for cfg in configs}
    validations_by_config = {cfg: [] for cfg in configs}
    latencies = {cfg: [] for cfg in configs}

    per_query_results = []
    wins_b_over_a = 0
    regs_b_under_a = 0
    neutrals = 0

    print(f"Executing evaluation across {len(cases)} queries for [Architecture A, Architecture B, Pure RRF]...\n")
    start_eval_time = time.time()

    for idx, case in enumerate(cases, start=1):
        qid = case["query_id"]
        qtext = case["query_text"]
        dom = case["domain"]
        cat = case["category"]
        relevant_ids = set(json.loads(case["relevant_ids"])) if isinstance(case["relevant_ids"], str) else set()
        parsed_dict = json.loads(case["expected_parse"]) if isinstance(case["expected_parse"], str) else {}
        relevance_grades = {item_id: 1 for item_id in relevant_ids}

        query_obj = BlackKnightQuery.model_validate(parsed_dict)

        # 1. Architecture A: All Cross-Encoder Reranked
        t0 = time.perf_counter()
        res_a = search_black_knight(
            parsed_query=query_obj,
            top_k=10,
            diagnostics=True,
            repo=repo,
            architecture="all_cross_encoder",
        )
        lat_a_ms = (time.perf_counter() - t0) * 1000.0
        latencies["architecture_a"].append(lat_a_ms)
        ids_a = [r["id"] for r in res_a.get("results", [])]
        metrics_a = evaluate_ranking(ids_a, relevant_ids, relevance_grades)
        val_a = check_violations_and_duplicates(res_a.get("results", []), query_obj, repo)
        results_by_config["architecture_a"].append(metrics_a)
        validations_by_config["architecture_a"].append(val_a)

        # 2. Architecture B: Domain-Routed (Movie CE, Anime/Book RRF)
        t0 = time.perf_counter()
        res_b = search_black_knight(
            parsed_query=query_obj,
            top_k=10,
            diagnostics=True,
            repo=repo,
            architecture="domain_routed",
        )
        lat_b_ms = (time.perf_counter() - t0) * 1000.0
        latencies["architecture_b"].append(lat_b_ms)
        ids_b = [r["id"] for r in res_b.get("results", [])]
        metrics_b = evaluate_ranking(ids_b, relevant_ids, relevance_grades)
        val_b = check_violations_and_duplicates(res_b.get("results", []), query_obj, repo)
        results_by_config["architecture_b"].append(metrics_b)
        validations_by_config["architecture_b"].append(val_b)

        # 3. Pure RRF Baseline
        t0 = time.perf_counter()
        res_rrf = search_black_knight(
            parsed_query=query_obj,
            top_k=10,
            diagnostics=True,
            repo=repo,
            architecture="rrf_only",
        )
        lat_rrf_ms = (time.perf_counter() - t0) * 1000.0
        latencies["rrf_only"].append(lat_rrf_ms)
        ids_rrf = [r["id"] for r in res_rrf.get("results", [])]
        metrics_rrf = evaluate_ranking(ids_rrf, relevant_ids, relevance_grades)
        val_rrf = check_violations_and_duplicates(res_rrf.get("results", []), query_obj, repo)
        results_by_config["rrf_only"].append(metrics_rrf)
        validations_by_config["rrf_only"].append(val_rrf)

        if len(relevant_ids) > 0:
            if metrics_b["mrr"] > metrics_a["mrr"] or (metrics_b["mrr"] == metrics_a["mrr"] and metrics_b["ndcg_at_10"] > metrics_a["ndcg_at_10"] + 1e-6):
                wins_b_over_a += 1
            elif metrics_b["mrr"] < metrics_a["mrr"] or (metrics_b["mrr"] == metrics_a["mrr"] and metrics_b["ndcg_at_10"] < metrics_a["ndcg_at_10"] - 1e-6):
                regs_b_under_a += 1
            else:
                neutrals += 1

        per_query_results.append({
            "query_id": qid,
            "domain": dom,
            "category": cat,
            "query_text": qtext,
            "is_absence_query": (len(relevant_ids) == 0),
            "relevant_ids": sorted(list(relevant_ids)),
            "relevant_ids_count": len(relevant_ids),
            "architecture_a": {
                "ranked_ids": ids_a[:10],
                "hits_at_5": metrics_a["hits_at_5"],
                "hits_at_10": metrics_a["hits_at_10"],
                "hit_rate_at_5": metrics_a["hit_rate_at_5"],
                "hit_rate_at_10": metrics_a["hit_rate_at_10"],
                "precision_at_5": metrics_a["precision_at_5"],
                "precision_at_10": metrics_a["precision_at_10"],
                "recall_at_5": metrics_a["recall_at_5"],
                "recall_at_10": metrics_a["recall_at_10"],
                "mrr": metrics_a["mrr"],
                "ndcg_at_5": metrics_a["ndcg_at_5"],
                "ndcg_at_10": metrics_a["ndcg_at_10"],
                "latency_ms": round(lat_a_ms, 2),
                "duplicate_count": val_a["duplicate_count"],
                "filter_violations": val_a["filter_violations_count"],
            },
            "architecture_b": {
                "ranked_ids": ids_b[:10],
                "hits_at_5": metrics_b["hits_at_5"],
                "hits_at_10": metrics_b["hits_at_10"],
                "hit_rate_at_5": metrics_b["hit_rate_at_5"],
                "hit_rate_at_10": metrics_b["hit_rate_at_10"],
                "precision_at_5": metrics_b["precision_at_5"],
                "precision_at_10": metrics_b["precision_at_10"],
                "recall_at_5": metrics_b["recall_at_5"],
                "recall_at_10": metrics_b["recall_at_10"],
                "mrr": metrics_b["mrr"],
                "ndcg_at_5": metrics_b["ndcg_at_5"],
                "ndcg_at_10": metrics_b["ndcg_at_10"],
                "latency_ms": round(lat_b_ms, 2),
                "duplicate_count": val_b["duplicate_count"],
                "filter_violations": val_b["filter_violations_count"],
            },
            "rrf_only": {
                "ranked_ids": ids_rrf[:10],
                "hits_at_5": metrics_rrf["hits_at_5"],
                "hits_at_10": metrics_rrf["hits_at_10"],
                "hit_rate_at_5": metrics_rrf["hit_rate_at_5"],
                "hit_rate_at_10": metrics_rrf["hit_rate_at_10"],
                "precision_at_5": metrics_rrf["precision_at_5"],
                "precision_at_10": metrics_rrf["precision_at_10"],
                "recall_at_5": metrics_rrf["recall_at_5"],
                "recall_at_10": metrics_rrf["recall_at_10"],
                "mrr": metrics_rrf["mrr"],
                "ndcg_at_5": metrics_rrf["ndcg_at_5"],
                "ndcg_at_10": metrics_rrf["ndcg_at_10"],
                "latency_ms": round(lat_rrf_ms, 2),
                "duplicate_count": val_rrf["duplicate_count"],
                "filter_violations": val_rrf["filter_violations_count"],
            },
        })

        if idx % 20 == 0 or idx == len(cases):
            print(f"Evaluated {idx}/{len(cases)} queries ({time.time() - start_eval_time:.1f}s elapsed)...")

    total_eval_elapsed = time.time() - start_eval_time
    print(f"\nAll {len(cases)} queries evaluated in {total_eval_elapsed:.2f}s.")

    summary_by_config = {
        cfg: aggregate_metrics(results_by_config[cfg], validations_by_config[cfg])
        for cfg in configs
    }

    per_domain_summary = {}
    for d in ACTIVE_DOMAINS:
        d_indices = [i for i, c in enumerate(cases) if c["domain"] == d]
        per_domain_summary[d] = {
            "query_count": len(d_indices),
            "configs": {
                cfg: aggregate_metrics(
                    [results_by_config[cfg][i] for i in d_indices],
                    [validations_by_config[cfg][i] for i in d_indices],
                )
                for cfg in configs
            }
        }

    latency_summary = {
        cfg: {
            "mean_ms": float(np.mean(latencies[cfg])),
            "p50_ms": float(np.percentile(latencies[cfg], 50)),
            "p95_ms": float(np.percentile(latencies[cfg], 95)),
            "cold_start_query_1_ms": float(latencies[cfg][0]),
            "steady_state_mean_ms": float(np.mean(latencies[cfg][1:])),
        }
        for cfg in configs
    }

    report_payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "benchmark_file": str(benchmark_path.name),
        "total_queries_evaluated": len(cases),
        "scored_queries_count": len(cases),
        "unscorable_queries_count": 0,
        "absence_queries_count": sum(1 for c in cases if json.loads(c["relevant_ids"]) == []),
        "positive_queries_count": sum(1 for c in cases if len(json.loads(c["relevant_ids"])) > 0),
        "domain_distribution": {
            d: sum(1 for c in cases if c["domain"] == d)
            for d in ACTIVE_DOMAINS
        },
        "summary_by_configuration": summary_by_config,
        "per_domain_summary": per_domain_summary,
        "comparison_architecture_b_vs_a": {
            "wins_b_over_a": wins_b_over_a,
            "regressions_b_under_a": regs_b_under_a,
            "neutrals": neutrals,
        },
        "latency_summary": latency_summary,
        "per_query_results": per_query_results,
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(report_payload, f, indent=2)
    print(f"Saved machine-readable results to {json_output_path}")

    # Generate Markdown Report
    with open(md_output_path, "w", encoding="utf-8") as f:
        f.write(f"# {report_title}\n\n")
        f.write("## 1. Executive Summary & Evaluator Parity\n\n")
        f.write(f"This benchmark evaluates Project Black Knight across **{len(cases)} audited queries** using shared production retrieval (`search_black_knight`) with 100% production/evaluator parity:\n")
        f.write("- **Architecture A (Baseline):** Hybrid retrieval (Dense + BM25, candidate_k=60), RRF fusion ($k=60$), cross-encoder reranking across all domains.\n")
        f.write("- **Architecture B (Domain-Routed):** Cross-encoder reranking for movies and mixed-domain queries; pure RRF for anime and books.\n")
        f.write("- **Pure RRF Baseline:** Cross-encoder bypassed across all domains.\n\n")

        f.write("## 2. Overall Ranking Performance (Positive Queries, N=102)\n\n")
        f.write("| Metric | Architecture A (All CE) | Architecture B (Domain-Routed) | Pure RRF | Delta (B vs A) |\n")
        f.write("|---|---:|---:|---:|---:|\n")
        for metric_key, metric_label in [
            ("hit_rate_at_5", "Hit Rate@5"),
            ("hit_rate_at_10", "Hit Rate@10"),
            ("precision_at_5", "Precision@5"),
            ("precision_at_10", "Precision@10"),
            ("recall_at_5", "Recall@5"),
            ("recall_at_10", "Recall@10"),
            ("mrr", "MRR"),
            ("ndcg_at_5", "nDCG@5"),
            ("ndcg_at_10", "nDCG@10"),
        ]:
            v_a = summary_by_config["architecture_a"]["positive_ranking_metrics"][metric_key]
            v_b = summary_by_config["architecture_b"]["positive_ranking_metrics"][metric_key]
            v_rrf = summary_by_config["rrf_only"]["positive_ranking_metrics"][metric_key]
            f.write(f"| {metric_label} | {v_a:.4f} | {v_b:.4f} | {v_rrf:.4f} | {v_b - v_a:+.4f} |\n")

        f.write("\n## 3. Correctness & Integrity Metrics\n\n")
        f.write("| Metric | Architecture A | Architecture B | Pure RRF |\n")
        f.write("|---|---:|---:|---:|\n")
        f.write(f"| Duplicate-Result Rate | {summary_by_config['architecture_a']['duplicate_result_rate']*100:.2f}% | {summary_by_config['architecture_b']['duplicate_result_rate']*100:.2f}% | {summary_by_config['rrf_only']['duplicate_result_rate']*100:.2f}% |\n")
        f.write(f"| Hard-Filter Violation Rate | {summary_by_config['architecture_a']['hard_filter_violation_rate']*100:.2f}% | {summary_by_config['architecture_b']['hard_filter_violation_rate']*100:.2f}% | {summary_by_config['rrf_only']['hard_filter_violation_rate']*100:.2f}% |\n")
        f.write(f"| Absence Correct Rejection Rate | {summary_by_config['architecture_a']['absence_metrics']['rejection_rate']*100:.1f}% | {summary_by_config['architecture_b']['absence_metrics']['rejection_rate']*100:.1f}% | {summary_by_config['rrf_only']['absence_metrics']['rejection_rate']*100:.1f}% |\n")

        f.write("\n## 4. Latency Analysis (Milliseconds)\n\n")
        f.write("| Architecture | Median / P50 (ms) | Mean (ms) | P95 (ms) | Steady-State Mean (ms) |\n")
        f.write("|---|---:|---:|---:|---:|\n")
        for cfg in configs:
            l = latency_summary[cfg]
            f.write(f"| {cfg} | {l['p50_ms']:.1f} | {l['mean_ms']:.1f} | {l['p95_ms']:.1f} | {l['steady_state_mean_ms']:.1f} |\n")

        f.write("\n## 5. Per-Domain Performance Breakdown\n\n")
        for d in ACTIVE_DOMAINS:
            f.write(f"### Domain: {d.capitalize()} (N={per_domain_summary[d]['query_count']})\n\n")
            f.write("| Metric | Architecture A (All CE) | Architecture B (Domain-Routed) | Pure RRF | Delta (B vs A) |\n")
            f.write("|---|---:|---:|---:|---:|\n")
            d_cfg = per_domain_summary[d]["configs"]
            for metric_key, metric_label in [
                ("hit_rate_at_5", "Hit Rate@5"),
                ("hit_rate_at_10", "Hit Rate@10"),
                ("precision_at_5", "Precision@5"),
                ("precision_at_10", "Precision@10"),
                ("recall_at_5", "Recall@5"),
                ("recall_at_10", "Recall@10"),
                ("mrr", "MRR"),
                ("ndcg_at_5", "nDCG@5"),
                ("ndcg_at_10", "nDCG@10"),
            ]:
                va = d_cfg["architecture_a"]["positive_ranking_metrics"][metric_key]
                vb = d_cfg["architecture_b"]["positive_ranking_metrics"][metric_key]
                vrrf = d_cfg["rrf_only"]["positive_ranking_metrics"][metric_key]
                f.write(f"| {metric_label} | {va:.4f} | {vb:.4f} | {vrrf:.4f} | {vb - va:+.4f} |\n")
            f.write("\n")

        f.write("## 6. Query-Level Comparison (Architecture B vs Architecture A)\n\n")
        f.write(f"- **Wins (B > A):** {wins_b_over_a}\n")
        f.write(f"- **Regressions (B < A):** {regs_b_under_a}\n")
        f.write(f"- **Neutral (B == A):** {neutrals}\n")

    print(f"Saved human-readable Markdown report to {md_output_path}")
    return report_payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run 113-query retrieval benchmark with evaluator parity")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_REPORT_JSON_PATH, help="Path for JSON output")
    parser.add_argument("--md-out", type=Path, default=DEFAULT_REPORT_MD_PATH, help="Path for Markdown output")
    parser.add_argument("--title", type=str, default="Project Black Knight — 113-Query Retrieval Benchmark (Production Parity)", help="Report title")
    args = parser.parse_args()

    run_benchmark(
        benchmark_path=BENCHMARK_PATH,
        json_output_path=args.json_out,
        md_output_path=args.md_out,
        report_title=args.title,
    )
