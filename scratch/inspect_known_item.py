"""
Diagnostic 4: Deep dive into Known Item queries KI_016 and KI_018
"""

import json
import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from project_black_knight.query_schema import BlackKnightQuery
from project_black_knight.retrieval import RetrievalRepository, search_black_knight, dense_retrieve, bm25_retrieve, reciprocal_rank_fusion, rerank_candidates
from project_black_knight.metadata_filter import get_valid_ids

def inspect_query(qid):
    repo = RetrievalRepository()
    df_eval = pd.read_csv(PROJECT_ROOT / "evaluation" / "black_knight_eval_queries_113_audited.csv").set_index("query_id")
    row = df_eval.loc[qid]
    print(f"\n==================== {qid}: '{row['query_text']}' ====================")
    rel_ids = json.loads(row["relevant_ids"])
    parsed_dict = json.loads(row["expected_parse"])
    print(f"Relevant IDs: {rel_ids}")
    print(f"Parsed dict: {parsed_dict}")
    
    q_obj = BlackKnightQuery.model_validate(parsed_dict)
    dom = row["domain"]
    
    # 1. Check valid_ids
    df_meta = repo.get_metadata_df(dom)
    docs, ids = repo.get_documents_and_ids(dom)
    id_to_idx = repo._id_to_index[dom]
    
    # Check title filter in metadata_filter
    common = q_obj.common
    filters = {"title": common.title}
    valid_ids = get_valid_ids(df_meta, ids, filters, dom)
    print(f"valid_ids count with title filter '{common.title}': {len(valid_ids)}")
    print(f"Are relevant_ids in valid_ids? {[r in valid_ids for r in rel_ids]}")
    for r in valid_ids:
        print(f"  valid_id: {r} -> '{df_meta.iloc[id_to_idx[r]]['title']}'")
        
    # Check dense retrieval
    eff_q = q_obj.semantic_query or common.title
    d_res = dense_retrieve(eff_q, dom, valid_ids=valid_ids, top_k=30, repo=repo)
    print(f"\nDense retrieved count: {len(d_res)}")
    for r in d_res[:5]:
        print(f"  Dense: {r['id']} (rank {r['rank']}, score {r['score']:.4f}) - '{df_meta.iloc[id_to_idx[r['id']]]['title']}'")
        
    b_res = bm25_retrieve(eff_q, dom, valid_ids=valid_ids, top_k=30, repo=repo)
    print(f"\nBM25 retrieved count: {len(b_res)}")
    for r in b_res[:5]:
        print(f"  BM25: {r['id']} (rank {r['rank']}, score {r['score']:.4f}) - '{df_meta.iloc[id_to_idx[r['id']]]['title']}'")
        
    rrf_res = reciprocal_rank_fusion([[c["id"] for c in d_res], [c["id"] for c in b_res]], k=60, top_k=30)
    print(f"\nRRF fused count: {len(rrf_res)}")
    for rank, (cid, s) in enumerate(rrf_res[:5], 1):
        print(f"  RRF: {cid} (rank {rank}, score {s:.4f}) - '{df_meta.iloc[id_to_idx[cid]]['title']}'")
        
    rerank_res = rerank_candidates(eff_q, [cid for cid, _ in rrf_res], dom, top_k=10, repo=repo)
    print(f"\nReranked count: {len(rerank_res)}")
    for rank, (cid, s) in enumerate(rerank_res, 1):
        is_hit = "*" if cid in rel_ids else " "
        print(f"  {is_hit} Rerank rank {rank}: {cid} (score {s:.4f}) - '{df_meta.iloc[id_to_idx[cid]]['title']}'")
        
    # Now check search_black_knight
    full_res = search_black_knight(parsed_query=q_obj, top_k=10, repo=repo)
    print(f"\nsearch_black_knight top 10:")
    for rank, r in enumerate(full_res["results"], 1):
        is_hit = "*" if r["id"] in rel_ids else " "
        print(f"  {is_hit} Rank {rank}: {r['id']} (score {r['score']}) - '{r['title']}'")

if __name__ == "__main__":
    inspect_query("KI_016")
    inspect_query("KI_018")
