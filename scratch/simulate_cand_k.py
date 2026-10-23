import json
import math
import sys
import time
from pathlib import Path
import pandas as pd
import numpy as np

from project_black_knight.query_schema import BlackKnightQuery
from project_black_knight.retrieval import RetrievalRepository, search_black_knight, hybrid_retrieve

repo = RetrievalRepository()
df_eval = pd.read_csv("evaluation/black_knight_eval_queries_113_audited.csv")
pos_cases = [r for _, r in df_eval.iterrows() if json.loads(r["relevant_ids"]) != []]

def evaluate_cand_k(cand_k):
    mrr_list = []
    hr5_list = []
    hr10_list = []
    
    for case in pos_cases:
        rel_ids = set(json.loads(case["relevant_ids"]))
        parsed = json.loads(case["expected_parse"])
        q_obj = BlackKnightQuery.model_validate(parsed)
        
        # Test domain_routed architecture with cand_k
        all_res = []
        is_mixed = len(q_obj.media_types) > 1
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
            
            should_rerank = True if (is_mixed or dom == "movie") else False
            
            d_res, _ = hybrid_retrieve(
                query=q_obj.semantic_query,
                media_type=dom,
                filters=filters,
                similar_to=q_obj.similar_to,
                top_k=10,
                candidate_k=cand_k,
                rerank=should_rerank,
                repo=repo,
            )
            all_res.extend(d_res)
            
        all_res.sort(key=lambda x: (-x["score"], str(x["id"])))
        ranked_ids = [r["id"] for r in all_res[:10]]
        
        # Metrics
        hits10 = sum(1 for x in ranked_ids if x in rel_ids)
        hits5 = sum(1 for x in ranked_ids[:5] if x in rel_ids)
        hr10 = 1.0 if hits10 > 0 else 0.0
        hr5 = 1.0 if hits5 > 0 else 0.0
        mrr = 0.0
        for rank, item in enumerate(ranked_ids, 1):
            if item in rel_ids:
                mrr = 1.0 / rank
                break
        mrr_list.append(mrr)
        hr5_list.append(hr5)
        hr10_list.append(hr10)
        
    print(f"cand_k={cand_k}: MRR={np.mean(mrr_list):.4f}, Hit@5={np.mean(hr5_list):.4f}, Hit@10={np.mean(hr10_list):.4f}")

for k in [60, 80, 100]:
    t0 = time.perf_counter()
    evaluate_cand_k(k)
    print(f"  elapsed: {time.perf_counter() - t0:.2f}s")
