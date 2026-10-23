"""
Experimentation script to test isolated retrieval fixes on the 102 positive queries.
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
from project_black_knight.metadata_filter import get_valid_ids

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

def main():
    repo = RetrievalRepository()
    df_eval = pd.read_csv(PROJECT_ROOT / "evaluation" / "black_knight_eval_queries_113_audited.csv")
    pos_cases = [r for _, r in df_eval.iterrows() if json.loads(r["relevant_ids"]) != []]
    
    print(f"Total positive benchmark queries: {len(pos_cases)}")
    
    # Baseline checks:
    # Test candidate recall at different candidate_k (30, 50, 60, 100)
    print("\n--- 1. CANDIDATE POOL SIZE (candidate_k) IMPACT ON RRF ---")
    for cand_k in [30, 50, 60]:
        hr5_list, hr10_list, mrr_list, ndcg_list = [], [], [], []
        # also track per-domain HR@10
        dom_hr10 = {"movie": [], "anime": [], "book": []}
        
        for case in pos_cases:
            dom = case["domain"]
            rel_ids = set(json.loads(case["relevant_ids"]))
            parsed_dict = json.loads(case["expected_parse"])
            q_obj = BlackKnightQuery.model_validate(parsed_dict)
            
            # Simulate per-domain search
            common = q_obj.common
            domain_queries_obj = q_obj.domain_queries
            dom_q = getattr(domain_queries_obj, dom, None)
            filters = {
                "title": common.title,
                "genres_include": common.genres_include,
                "genres_exclude": common.genres_exclude,
                "release_year_min": common.release_year_min,
                "release_year_max": common.release_year_max,
            }
            if dom_q is not None:
                filters.update(dom_q.model_dump(exclude_none=True))
                
            df_meta = repo.get_metadata_df(dom)
            _, item_ids = repo.get_documents_and_ids(dom)
            valid_ids = get_valid_ids(df_meta, item_ids, filters, dom)
            
            eff_q = q_obj.semantic_query or common.title or "popular recommended entertainment"
            
            # Dense & BM25 with cand_k
            d_res = dense_retrieve(eff_q, dom, valid_ids=valid_ids, top_k=cand_k, repo=repo)
            b_res = bm25_retrieve(eff_q, dom, valid_ids=valid_ids, top_k=cand_k, repo=repo)
            
            # RRF
            r_res = reciprocal_rank_fusion(
                [[c["id"] for c in d_res], [c["id"] for c in b_res]],
                k=60,
                top_k=cand_k,
            )
            rrf_ids = [cid for cid, s in r_res]
            
            hr5, hr10, mrr, ndcg10 = compute_metrics(rrf_ids, rel_ids)
            hr5_list.append(hr5)
            hr10_list.append(hr10)
            mrr_list.append(mrr)
            ndcg_list.append(ndcg10)
            dom_hr10[dom].append(hr10)
            
        print(f"RRF (cand_k={cand_k}): Overall HR@5={np.mean(hr5_list):.4f}, HR@10={np.mean(hr10_list):.4f}, MRR={np.mean(mrr_list):.4f}, nDCG@10={np.mean(ndcg_list):.4f}")
        for d in ["movie", "anime", "book"]:
            print(f"   Domain {d}: HR@10={np.mean(dom_hr10[d]):.4f}")

if __name__ == "__main__":
    main()
