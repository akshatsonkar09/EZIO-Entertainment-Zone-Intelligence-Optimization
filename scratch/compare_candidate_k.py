"""
Evaluate Pipeline Configurations across all 102 positive benchmark queries
"""

import json
import math
import sys
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from project_black_knight.query_schema import BlackKnightQuery
from project_black_knight.retrieval import (
    RetrievalRepository,
    dense_retrieve,
    bm25_retrieve,
    reciprocal_rank_fusion,
    rerank_candidates,
    search_black_knight,
)
from project_black_knight.metadata_filter import get_valid_ids, normalize_token_str

def compute_metrics(ranked_ids, relevant_ids):
    n_rel = len(relevant_ids)
    if n_rel == 0:
        return 0.0, 0.0, 0.0, 0.0
    hits_5 = sum(1 for x in ranked_ids[:5] if x in relevant_ids)
    hits_10 = sum(1 for x in ranked_ids[:10] if x in relevant_ids)
    hr5 = 1.0 if hits_5 > 0 else 0.0
    hr10 = 1.0 if hits_10 > 0 else 0.0
    mrr = 0.0
    for r, item in enumerate(ranked_ids[:10], 1):
        if item in relevant_ids:
            mrr = 1.0 / r
            break
    dcg_10 = sum((1.0 / math.log2(i + 1.0)) for i, item in enumerate(ranked_ids[:10], 1) if item in relevant_ids)
    idcg_10 = sum((1.0 / math.log2(i + 1.0)) for i in range(1, min(n_rel, 10) + 1))
    ndcg10 = (dcg_10 / idcg_10) if idcg_10 > 0 else 0.0
    return hr5, hr10, mrr, ndcg10

def evaluate_pipeline(name, run_fn, cases):
    hr5_list, hr10_list, mrr_list, ndcg_list = [], [], [], []
    dom_hr10 = {"movie": [], "anime": [], "book": []}
    dom_mrr = {"movie": [], "anime": [], "book": []}
    
    for case in cases:
        dom = case["domain"]
        rel_ids = set(json.loads(case["relevant_ids"]))
        ranked_ids = run_fn(case)
        hr5, hr10, mrr, ndcg10 = compute_metrics(ranked_ids, rel_ids)
        hr5_list.append(hr5)
        hr10_list.append(hr10)
        mrr_list.append(mrr)
        ndcg_list.append(ndcg10)
        dom_hr10[dom].append(hr10)
        dom_mrr[dom].append(mrr)
        
    print(f"\n==================== {name} ====================")
    print(f"Overall (N={len(cases)}): HR@5={np.mean(hr5_list):.4f}, HR@10={np.mean(hr10_list):.4f}, MRR={np.mean(mrr_list):.4f}, nDCG@10={np.mean(ndcg_list):.4f}")
    for d in ["movie", "anime", "book"]:
        print(f"  {d.capitalize()}: HR@10={np.mean(dom_hr10[d]):.4f}, MRR={np.mean(dom_mrr[d]):.4f}")
    return np.mean(hr10_list), np.mean(mrr_list)

def main():
    repo = RetrievalRepository()
    df_eval = pd.read_csv(PROJECT_ROOT / "evaluation" / "black_knight_eval_queries_113_audited.csv")
    pos_cases = [r for _, r in df_eval.iterrows() if json.loads(r["relevant_ids"]) != []]
    
    # Baseline Current search_black_knight
    def run_baseline(case):
        parsed = json.loads(case["expected_parse"])
        q_obj = BlackKnightQuery.model_validate(parsed)
        res = search_black_knight(parsed_query=q_obj, top_k=10, repo=repo)
        return [r["id"] for r in res["results"]]
    evaluate_pipeline("1. Baseline Current (candidate_k=30, pure CE rerank)", run_baseline, pos_cases)
    
    # Test 2: candidate_k = 60
    # Let's test custom hybrid retrieve with candidate_k = 60
    def run_candk60(case):
        parsed = json.loads(case["expected_parse"])
        q_obj = BlackKnightQuery.model_validate(parsed)
        
        all_res = []
        for dom in q_obj.media_types:
            common = q_obj.common
            dom_q = getattr(q_obj.domain_queries, dom, None)
            filters = {
                "title": common.title,
                "genres_include": common.genres_include,
                "genres_exclude": common.genres_exclude,
                "release_year_min": common.release_year_min,
                "release_year_max": common.release_year_max,
            }
            if dom_q:
                filters.update(dom_q.model_dump(exclude_none=True))
                
            from project_black_knight.retrieval import hybrid_retrieve
            d_res, _ = hybrid_retrieve(
                query=q_obj.semantic_query,
                media_type=dom,
                filters=filters,
                similar_to=q_obj.similar_to,
                top_k=10,
                candidate_k=60,
                repo=repo,
            )
            all_res.extend(d_res)
        all_res.sort(key=lambda x: x["score"], reverse=True)
        return [r["id"] for r in all_res[:10]]
    evaluate_pipeline("2. candidate_k=60 (Dense/BM25/RRF pool 60)", run_candk60, pos_cases)

if __name__ == "__main__":
    main()
