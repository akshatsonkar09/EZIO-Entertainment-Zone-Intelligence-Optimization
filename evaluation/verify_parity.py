"""
Parity verification script for Project Black Knight Phase 5.
Directly compares search_black_knight(..., trace=False) vs search_black_knight(..., trace=True)
across representative queries from all supported domains and all 3 architectures.
"""

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import pandas as pd
from project_black_knight.query_schema import BlackKnightQuery
from project_black_knight.retrieval import RetrievalRepository, search_black_knight

BENCHMARK_PATH = ROOT / "evaluation" / "black_knight_eval_queries_113_audited.csv"


def verify_parity():
    df = pd.read_csv(BENCHMARK_PATH)
    cases = df.to_dict("records")
    
    # Stratified selection: 5 movie, 5 anime, 5 book, 5 mixed/absence (20 total queries)
    movie_cases = [c for c in cases if c["domain"] == "movie"][:5]
    anime_cases = [c for c in cases if c["domain"] == "anime"][:5]
    book_cases = [c for c in cases if c["domain"] == "book"][:5]
    other_cases = [c for c in cases if c["domain"] not in ("movie", "anime", "book") or not json.loads(c["relevant_ids"])][:5]
    
    selected_cases = movie_cases + anime_cases + book_cases + other_cases
    print(f"Running parity audit on {len(selected_cases)} stratified queries across 3 architectures (60 total comparisons)...")
    
    repo = RetrievalRepository()
    # Pre-warm
    for d in ("movie", "anime", "book"):
        repo.get_metadata_df(d)
        repo.get_documents_and_ids(d)
        repo.get_bm25_index(d)
    repo.get_embedding_model()
    repo.get_reranker_model()

    architectures = ["all_cross_encoder", "domain_routed", "rrf_only"]
    total_comparisons = 0
    passed_comparisons = 0
    failures = []

    t0 = time.time()
    for case in selected_cases:
        qid = case["query_id"]
        qtext = case["query_text"]
        parsed_dict = json.loads(case["expected_parse"]) if isinstance(case["expected_parse"], str) else {}
        query_obj = BlackKnightQuery.model_validate(parsed_dict)
        relevant_ids = sorted(list(set(json.loads(case["relevant_ids"])))) if isinstance(case["relevant_ids"], str) else []

        for arch in architectures:
            total_comparisons += 1
            res_untraced = search_black_knight(
                parsed_query=query_obj,
                top_k=10,
                repo=repo,
                architecture=arch,
                trace=False,
            )
            res_traced = search_black_knight(
                parsed_query=query_obj,
                top_k=10,
                repo=repo,
                architecture=arch,
                trace=True,
                query_id=qid,
                target_ids=relevant_ids,
            )

            u_items = res_untraced["results"]
            t_items = res_traced["results"]

            u_ids = [x["id"] for x in u_items]
            t_ids = [x["id"] for x in t_items]
            u_scores = [x["score"] for x in u_items]
            t_scores = [x["score"] for x in t_items]

            if u_ids != t_ids or u_scores != t_scores:
                failures.append({
                    "query_id": qid,
                    "architecture": arch,
                    "untraced_ids": u_ids,
                    "traced_ids": t_ids,
                    "untraced_scores": u_scores,
                    "traced_scores": t_scores,
                })
            else:
                passed_comparisons += 1

    elapsed = time.time() - t0
    print(f"Parity audit completed in {elapsed:.2f}s:")
    print(f"Total comparisons: {total_comparisons}")
    print(f"Passed: {passed_comparisons}")
    print(f"Failed: {len(failures)}")
    
    if failures:
        print("FAILURES DETECTED:")
        for f in failures:
            print(f)
        sys.exit(1)
    else:
        print("ALL COMPARISONS PASSED EXACT PARITY (100% match on IDs, ordering, and scores)!")


if __name__ == "__main__":
    verify_parity()
