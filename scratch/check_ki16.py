"""
Check all 23 valid IDs for KI_016
"""
import sys, json
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from project_black_knight.retrieval import RetrievalRepository, dense_retrieve, bm25_retrieve, reciprocal_rank_fusion, rerank_candidates
from project_black_knight.metadata_filter import get_valid_ids

def main():
    repo = RetrievalRepository()
    df_meta = repo.get_metadata_df("anime")
    docs, ids = repo.get_documents_and_ids("anime")
    id_to_idx = repo._id_to_index["anime"]
    
    q = "Code Geass: Hangyaku no Lelouch"
    valid_ids = get_valid_ids(df_meta, ids, {"title": q}, "anime")
    print(f"valid_ids count: {len(valid_ids)}")
    
    d_res = dense_retrieve(q, "anime", valid_ids=valid_ids, top_k=30, repo=repo)
    b_res = bm25_retrieve(q, "anime", valid_ids=valid_ids, top_k=30, repo=repo)
    r_res = reciprocal_rank_fusion([[c["id"] for c in d_res], [c["id"] for c in b_res]], k=60, top_k=30)
    
    ce_pairs = [[q, docs[id_to_idx[cid]]] for cid, _ in r_res]
    ce_scores = repo.get_reranker_model().predict(ce_pairs)
    
    print("\nAll items for KI_016 sorted by RRF:")
    for rank, ((cid, rrf_score), ce_score) in enumerate(zip(r_res, ce_scores), 1):
        t = df_meta.iloc[id_to_idx[cid]]["title"]
        target_mark = "*** TARGET ***" if cid in ["anime_732", "anime_9"] else ""
        d_rank = next((c["rank"] for c in d_res if c["id"] == cid), None)
        b_rank = next((c["rank"] for c in b_res if c["id"] == cid), None)
        print(f"RRF {rank:2d}: {cid} (Dense rank {d_rank}, BM25 rank {b_rank}, RRF {rrf_score:.4f}, CE {ce_score:.4f}) - '{t}' {target_mark}")

    print("\nSorted by Cross-Encoder:")
    sorted_ce = sorted(zip([cid for cid, _ in r_res], ce_scores), key=lambda x: x[1], reverse=True)
    for rank, (cid, score) in enumerate(sorted_ce, 1):
        t = df_meta.iloc[id_to_idx[cid]]["title"]
        target_mark = "*** TARGET ***" if cid in ["anime_732", "anime_9"] else ""
        print(f"CE {rank:2d}: {cid} (Score {score:.4f}) - '{t}' {target_mark}")

if __name__ == "__main__":
    main()
