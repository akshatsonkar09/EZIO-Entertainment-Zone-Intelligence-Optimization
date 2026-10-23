"""
Test Fusion of RRF and Cross-Encoder on Positive Queries
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
    hybrid_retrieve,
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

def evaluate_method(name, method_fn, cases):
    hr5_list, hr10_list, mrr_list, ndcg_list = [], [], [], []
    dom_hr10 = {"movie": [], "anime": [], "book": []}
    dom_mrr = {"movie": [], "anime": [], "book": []}
    
    for case_idx, case in enumerate(cases):
        dom = case["domain"]
        rel_ids = set(json.loads(case["relevant_ids"]))
        ranked_ids = method_fn(case_idx)
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

def main():
    repo = RetrievalRepository()
    df_eval = pd.read_csv(PROJECT_ROOT / "evaluation" / "black_knight_eval_queries_113_audited.csv")
    pos_cases = [r for _, r in df_eval.iterrows() if json.loads(r["relevant_ids"]) != []]
    
    # Precompute per case: RRF candidates (cand_k=60) and CE scores
    print("Precomputing candidate pools and CE scores for 102 cases...")
    precomputed = []
    for case in pos_cases:
        dom = case["domain"]
        parsed = json.loads(case["expected_parse"])
        q_obj = BlackKnightQuery.model_validate(parsed)
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
            
        df_meta = repo.get_metadata_df(dom)
        docs, item_ids = repo.get_documents_and_ids(dom)
        id_to_idx = repo._id_to_index[dom]
        valid_ids = get_valid_ids(df_meta, item_ids, filters, dom)
        
        eff_q = q_obj.semantic_query or common.title or "popular recommended entertainment"
        
        d_res = dense_retrieve(eff_q, dom, valid_ids=valid_ids, top_k=60, repo=repo)
        b_res = bm25_retrieve(eff_q, dom, valid_ids=valid_ids, top_k=60, repo=repo)
        
        # RRF with alphabetical tie-breaking
        r_res = reciprocal_rank_fusion([[c["id"] for c in d_res], [c["id"] for c in b_res]], k=60, top_k=60)
        cids = [cid for cid, s in r_res]
        
        pairs = [[eff_q, docs[id_to_idx[cid]]] for cid in cids]
        ce_model = repo.get_reranker_model()
        ce_scores = ce_model.predict(pairs) if pairs else []
        
        precomputed.append({
            "case": case,
            "dom": dom,
            "r_res": r_res,
            "cids": cids,
            "ce_scores": [float(s) for s in ce_scores],
            "title_filter": common.title,
        })
        
    print("Precomputation complete. Running evaluations...\n")
    
    # Method 1: Pure RRF (cand_k=60)
    def m_rrf_pure(case_idx):
        return [cid for cid, _ in precomputed[case_idx]["r_res"][:10]]
    evaluate_method("Method 1: Pure RRF (cand_k=60)", m_rrf_pure, pos_cases)
    
    # Method 2: Pure Cross-Encoder (cand_k=60)
    def m_ce_pure(case_idx):
        p = precomputed[case_idx]
        ranked = sorted(zip(p["cids"], p["ce_scores"]), key=lambda x: (x[1], x[0]), reverse=True)
        return [cid for cid, s in ranked[:10]]
    evaluate_method("Method 2: Pure CE (cand_k=60)", m_ce_pure, pos_cases)
    
    # Method 3: Second-stage RRF (combining RRF rank and CE rank)
    for k_val in [20, 40, 60]:
        def make_second_rrf(k):
            def m_second_rrf(case_idx):
                p = precomputed[case_idx]
                ce_ranked = [cid for cid, _ in sorted(zip(p["cids"], p["ce_scores"]), key=lambda x: (x[1], x[0]), reverse=True)]
                fused = reciprocal_rank_fusion([p["cids"], ce_ranked], k=k, top_k=10)
                return [cid for cid, _ in fused]
            return m_second_rrf
        evaluate_method(f"Method 3: Second-stage RRF (RRF rank + CE rank, k={k_val})", make_second_rrf(k_val), pos_cases)

    # Method 4: Linear combination of normalized CE score + normalized RRF score
    for alpha in [0.3, 0.5, 0.7]:
        def make_score_combo(a):
            def m_score_combo(case_idx):
                p = precomputed[case_idx]
                if not p["cids"]:
                    return []
                rrf_dict = dict(p["r_res"])
                ce_dict = dict(zip(p["cids"], p["ce_scores"]))
                
                min_ce = min(p["ce_scores"])
                max_ce = max(p["ce_scores"])
                ce_range = (max_ce - min_ce) if max_ce > min_ce else 1.0
                
                rrf_vals = list(rrf_dict.values())
                min_r = min(rrf_vals)
                max_r = max(rrf_vals)
                r_range = (max_r - min_r) if max_r > min_r else 1.0
                
                combined = []
                for cid in p["cids"]:
                    norm_ce = (ce_dict[cid] - min_ce) / ce_range
                    norm_r = (rrf_dict[cid] - min_r) / r_range
                    final_score = a * norm_ce + (1.0 - a) * norm_r
                    combined.append((cid, final_score))
                    
                combined.sort(key=lambda x: (-x[1], x[0]))
                return [cid for cid, _ in combined[:10]]
            return m_score_combo
        evaluate_method(f"Method 4: Score Combination (alpha_ce={alpha}, 1-alpha_rrf={1-alpha:.1f})", make_score_combo(alpha), pos_cases)

if __name__ == "__main__":
    main()
