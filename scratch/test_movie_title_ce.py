"""
Test title prefix for movie in Cross-Encoder
"""
from pathlib import Path
import json, sys
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from project_black_knight.query_schema import BlackKnightQuery
from project_black_knight.retrieval import RetrievalRepository, reciprocal_rank_fusion, dense_retrieve, bm25_retrieve

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
    return hr5, hr10, mrr

def main():
    repo = RetrievalRepository()
    df_eval = pd.read_csv(PROJECT_ROOT / "evaluation" / "black_knight_eval_queries_113_audited.csv")
    movie_cases = [r for _, r in df_eval.iterrows() if r["domain"] == "movie" and json.loads(r["relevant_ids"]) != []]
    
    docs, ids = repo.get_documents_and_ids("movie")
    df_meta = repo.get_metadata_df("movie")
    id_to_idx = repo._id_to_index["movie"]
    ce_model = repo.get_reranker_model()
    
    print(f"Total movie positive cases: {len(movie_cases)}")
    
    hr10_orig, mrr_orig = [], []
    hr10_with_title, mrr_with_title = [], []
    
    for case in movie_cases:
        rel_ids = set(json.loads(case["relevant_ids"]))
        parsed = json.loads(case["expected_parse"])
        q_obj = BlackKnightQuery.model_validate(parsed)
        eff_q = q_obj.semantic_query or q_obj.common.title or ""
        
        # Dense + BM25 (top 60)
        d = dense_retrieve(eff_q, "movie", top_k=60, repo=repo)
        b = bm25_retrieve(eff_q, "movie", top_k=60, repo=repo)
        rrf = reciprocal_rank_fusion([[c["id"] for c in d], [c["id"] for c in b]], k=60, top_k=60)
        cids = [cid for cid, _ in rrf]
        
        # 1. Orig doc text
        pairs_orig = [[eff_q, docs[id_to_idx[cid]]] for cid in cids]
        scores_orig = ce_model.predict(pairs_orig)
        ranked_orig = [cid for cid, _ in sorted(zip(cids, scores_orig), key=lambda x: x[1], reverse=True)]
        
        # 2. Doc text with title:
        pairs_title = [[eff_q, f"title: {df_meta.iloc[id_to_idx[cid]]['title']} {docs[id_to_idx[cid]]}"] for cid in cids]
        scores_title = ce_model.predict(pairs_title)
        ranked_title = [cid for cid, _ in sorted(zip(cids, scores_title), key=lambda x: x[1], reverse=True)]
        
        h_o5, h_o10, m_o = compute_metrics(ranked_orig, rel_ids)
        h_t5, h_t10, m_t = compute_metrics(ranked_title, rel_ids)
        hr10_orig.append(h_o10)
        mrr_orig.append(m_o)
        hr10_with_title.append(h_t10)
        mrr_with_title.append(m_t)
        
    print(f"Movie without title: HR@10={np.mean(hr10_orig):.4f}, MRR={np.mean(mrr_orig):.4f}")
    print(f"Movie with title:    HR@10={np.mean(hr10_with_title):.4f}, MRR={np.mean(mrr_with_title):.4f}")

if __name__ == "__main__":
    main()
