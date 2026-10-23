"""
Test Reranker and RRF combination strategies
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

def evaluate_strategy(name, get_ranked_ids_fn, pos_cases):
    hr5_list, hr10_list, mrr_list, ndcg_list = [], [], [], []
    dom_metrics = {"movie": {"hr10": [], "mrr": []}, "anime": {"hr10": [], "mrr": []}, "book": {"hr10": [], "mrr": []}}
    
    for case in pos_cases:
        dom = case["domain"]
        rel_ids = set(json.loads(case["relevant_ids"]))
        ranked_ids = get_ranked_ids_fn(case)
        hr5, hr10, mrr, ndcg10 = compute_metrics(ranked_ids, rel_ids)
        hr5_list.append(hr5)
        hr10_list.append(hr10)
        mrr_list.append(mrr)
        ndcg_list.append(ndcg10)
        dom_metrics[dom]["hr10"].append(hr10)
        dom_metrics[dom]["mrr"].append(mrr)
        
    print(f"\n[{name}]")
    print(f"  Overall: HR@5={np.mean(hr5_list):.4f}, HR@10={np.mean(hr10_list):.4f}, MRR={np.mean(mrr_list):.4f}, nDCG@10={np.mean(ndcg_list):.4f}")
    for d in ["movie", "anime", "book"]:
        print(f"    {d.capitalize()}: HR@10={np.mean(dom_metrics[d]['hr10']):.4f}, MRR={np.mean(dom_metrics[d]['mrr']):.4f}")

def main():
    repo = RetrievalRepository()
    df_eval = pd.read_csv(PROJECT_ROOT / "evaluation" / "black_knight_eval_queries_113_audited.csv")
    pos_cases = [r for _, r in df_eval.iterrows() if json.loads(r["relevant_ids"]) != []]
    
    # 0. Baseline Current search_black_knight
    def strat_current(case):
        parsed_dict = json.loads(case["expected_parse"])
        q_obj = BlackKnightQuery.model_validate(parsed_dict)
        res = search_black_knight(parsed_query=q_obj, top_k=10, repo=repo)
        return [r["id"] for r in res["results"]]
        
    evaluate_strategy("Baseline: Current search_black_knight (Cross-Encoder)", strat_current, pos_cases)

if __name__ == "__main__":
    main()
