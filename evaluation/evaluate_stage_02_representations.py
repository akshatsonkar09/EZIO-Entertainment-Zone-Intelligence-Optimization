"""
Stage 2 Representation Quality Evaluation Script.

Compares retrieval candidate coverage between:
- v1_legacy (unstructured tag/tag2 representations)
- v2_structured_semantic (structured domain-aware catalog representations)

Measures:
- Candidate Recall@50
- Candidate Recall@100
- Domain breakdowns (movie, anime, book)
- BM25 alone (v1 vs v2)
- Dense ChromaDB retrieval
- Hybrid RRF (v1 vs v2)
- Latency and indexing overhead
- Ground truth: audited historical benchmark (black_knight_eval_queries_113_audited.csv)
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
    tokenize_for_bm25,
)
from project_black_knight.item_representations import (
    build_movie_representation,
    build_anime_representation,
    build_book_representation,
)


def run_representation_evaluation():
    repo = RetrievalRepository()
    benchmark_path = Path("evaluation/black_knight_eval_queries_113_audited.csv")
    df_bench = pd.read_csv(benchmark_path)

    # Filter out absence queries (relevant_ids is empty)
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

    print(f"Loaded {len(valid_queries)} evaluation queries with ground-truth targets.")

    # 1. Measure indexing latency for both versions
    indexing_times = {}
    for domain in ("movie", "anime", "book"):
        t0 = time.perf_counter()
        docs_v1, _ = repo.get_documents_and_ids(domain, version="v1_legacy")
        _ = repo.get_bm25_index(domain, version="v1_legacy")
        t_v1 = round((time.perf_counter() - t0) * 1000, 2)

        t0 = time.perf_counter()
        docs_v2, _ = repo.get_documents_and_ids(domain, version="v2_structured_semantic")
        _ = repo.get_bm25_index(domain, version="v2_structured_semantic")
        t_v2 = round((time.perf_counter() - t0) * 1000, 2)

        indexing_times[domain] = {
            "v1_legacy_ms": t_v1,
            "v2_structured_ms": t_v2,
            "catalog_size": len(docs_v1),
            "v1_avg_char_length": round(float(np.mean([len(d) for d in docs_v1])), 1),
            "v2_avg_char_length": round(float(np.mean([len(d) for d in docs_v2])), 1),
        }

    # 2. Evaluate candidate retrieval across queries
    results_by_query = []
    latencies = {
        "v1_bm25": [],
        "v2_bm25": [],
        "dense": [],
        "v1_rrf": [],
        "v2_rrf": [],
    }

    domain_stats = {
        d: {
            "count": 0,
            "v1_bm25_rec50": [], "v1_bm25_rec100": [],
            "v2_bm25_rec50": [], "v2_bm25_rec100": [],
            "dense_rec50": [], "dense_rec100": [],
            "v1_rrf_rec50": [], "v1_rrf_rec100": [],
            "v2_rrf_rec50": [], "v2_rrf_rec100": [],
        }
        for d in ("movie", "anime", "book", "overall")
    }

    for item in valid_queries:
        domain = item["domain"]
        rel_ids = item["relevant_ids"]
        q_text = item["query_text"]
        if item["query_obj"] and item["query_obj"].semantic_query:
            retrieval_query = item["query_obj"].semantic_query
        else:
            retrieval_query = q_text

        # Dense retrieval (Chroma embeddings)
        t0 = time.perf_counter()
        dense_cands = dense_retrieve(retrieval_query, media_type=domain, top_k=100, repo=repo)
        t_dense = (time.perf_counter() - t0) * 1000
        latencies["dense"].append(t_dense)
        dense_ids = [c["id"] for c in dense_cands]

        # BM25 v1_legacy
        t0 = time.perf_counter()
        v1_bm25_cands = bm25_retrieve(retrieval_query, media_type=domain, top_k=100, repo=repo, representation_version="v1_legacy")
        t_v1_bm25 = (time.perf_counter() - t0) * 1000
        latencies["v1_bm25"].append(t_v1_bm25)
        v1_bm25_ids = [c["id"] for c in v1_bm25_cands]

        # BM25 v2_structured
        t0 = time.perf_counter()
        v2_bm25_cands = bm25_retrieve(retrieval_query, media_type=domain, top_k=100, repo=repo, representation_version="v2_structured_semantic")
        t_v2_bm25 = (time.perf_counter() - t0) * 1000
        latencies["v2_bm25"].append(t_v2_bm25)
        v2_bm25_ids = [c["id"] for c in v2_bm25_cands]

        # RRF v1
        t0 = time.perf_counter()
        v1_rrf_pairs = reciprocal_rank_fusion([dense_ids[:60], v1_bm25_ids[:60]], k=60, top_k=100)
        latencies["v1_rrf"].append((time.perf_counter() - t0) * 1000)
        v1_rrf_ids = [cid for cid, _ in v1_rrf_pairs]

        # RRF v2
        t0 = time.perf_counter()
        v2_rrf_pairs = reciprocal_rank_fusion([dense_ids[:60], v2_bm25_ids[:60]], k=60, top_k=100)
        latencies["v2_rrf"].append((time.perf_counter() - t0) * 1000)
        v2_rrf_ids = [cid for cid, _ in v2_rrf_pairs]

        def recall_at_k(c_ids, k):
            return sum(1 for cid in c_ids[:k] if cid in rel_ids) / float(len(rel_ids))

        metrics = {
            "query_id": item["query_id"],
            "domain": domain,
            "dense_rec50": recall_at_k(dense_ids, 50),
            "dense_rec100": recall_at_k(dense_ids, 100),
            "v1_bm25_rec50": recall_at_k(v1_bm25_ids, 50),
            "v1_bm25_rec100": recall_at_k(v1_bm25_ids, 100),
            "v2_bm25_rec50": recall_at_k(v2_bm25_ids, 50),
            "v2_bm25_rec100": recall_at_k(v2_bm25_ids, 100),
            "v1_rrf_rec50": recall_at_k(v1_rrf_ids, 50),
            "v1_rrf_rec100": recall_at_k(v1_rrf_ids, 100),
            "v2_rrf_rec50": recall_at_k(v2_rrf_ids, 50),
            "v2_rrf_rec100": recall_at_k(v2_rrf_ids, 100),
        }
        results_by_query.append(metrics)

        for target_dict in (domain_stats[domain], domain_stats["overall"]):
            target_dict["count"] += 1
            for k in ("v1_bm25_rec50", "v1_bm25_rec100", "v2_bm25_rec50", "v2_bm25_rec100",
                      "dense_rec50", "dense_rec100", "v1_rrf_rec50", "v1_rrf_rec100", "v2_rrf_rec50", "v2_rrf_rec100"):
                target_dict[k].append(metrics[k])

    # Summarize metrics
    summary = {
        "indexing_and_representation": indexing_times,
        "latency_ms": {
            k: {
                "mean": round(float(np.mean(vals)), 2),
                "median": round(float(np.median(vals)), 2),
                "p95": round(float(np.percentile(vals, 95)), 2),
            }
            for k, vals in latencies.items()
        },
        "recall_by_domain": {},
    }

    for dom, d_data in domain_stats.items():
        summary["recall_by_domain"][dom] = {
            "query_count": d_data["count"],
            "v1_bm25_recall@50": round(float(np.mean(d_data["v1_bm25_rec50"])), 4),
            "v1_bm25_recall@100": round(float(np.mean(d_data["v1_bm25_rec100"])), 4),
            "v2_bm25_recall@50": round(float(np.mean(d_data["v2_bm25_rec50"])), 4),
            "v2_bm25_recall@100": round(float(np.mean(d_data["v2_bm25_rec100"])), 4),
            "dense_recall@50": round(float(np.mean(d_data["dense_rec50"])), 4),
            "dense_recall@100": round(float(np.mean(d_data["dense_rec100"])), 4),
            "v1_rrf_recall@50": round(float(np.mean(d_data["v1_rrf_rec50"])), 4),
            "v1_rrf_recall@100": round(float(np.mean(d_data["v1_rrf_rec100"])), 4),
            "v2_rrf_recall@50": round(float(np.mean(d_data["v2_rrf_rec50"])), 4),
            "v2_rrf_recall@100": round(float(np.mean(d_data["v2_rrf_rec100"])), 4),
            "bm25_rec100_delta": round(float(np.mean(d_data["v2_bm25_rec100"]) - np.mean(d_data["v1_bm25_rec100"])), 4),
            "rrf_rec100_delta": round(float(np.mean(d_data["v2_rrf_rec100"]) - np.mean(d_data["v1_rrf_rec100"])), 4),
        }

    # Save representative samples
    samples = {}
    for dom in ("movie", "anime", "book"):
        docs_v1, _ = repo.get_documents_and_ids(dom, version="v1_legacy")
        docs_v2, _ = repo.get_documents_and_ids(dom, version="v2_structured_semantic")
        df_meta = repo.get_metadata_df(dom)
        samples[dom] = [
            {
                "id": f"{dom}_{idx}",
                "title": str(df_meta.iloc[idx]["title"]),
                "v1_legacy": docs_v1[idx][:250] + "..." if len(docs_v1[idx]) > 250 else docs_v1[idx],
                "v2_structured": docs_v2[idx][:250] + "..." if len(docs_v2[idx]) > 250 else docs_v2[idx],
            }
            for idx in [0, 1, 2]
        ]

    # Save artifacts
    artifacts_dir = Path("reports/recommendation_quality/artifacts/stage_02")
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    metrics_path = artifacts_dir / "stage_02_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    samples_path = artifacts_dir / "stage_02_representation_samples.json"
    with open(samples_path, "w", encoding="utf-8") as f:
        json.dump(samples, f, indent=2)

    print("Stage 2 Evaluation Completed Successfully.")
    print(json.dumps(summary["recall_by_domain"], indent=2))
    return summary


if __name__ == "__main__":
    run_representation_evaluation()
