"""
Inspect DE_023
"""
import sys, json
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from project_black_knight.query_schema import BlackKnightQuery
from project_black_knight.retrieval import RetrievalRepository, dense_retrieve, bm25_retrieve, reciprocal_rank_fusion

def main():
    repo = RetrievalRepository()
    q = "A street thief with magical allomantic powers joins a rebellion against an immortal emperor."
    
    d_res = dense_retrieve(q, "book", top_k=30, repo=repo)
    b_res = bm25_retrieve(q, "book", top_k=30, repo=repo)
    
    d_rank = next((c["rank"] for c in d_res if c["id"] == "book_530"), None)
    b_rank = next((c["rank"] for c in b_res if c["id"] == "book_530"), None)
    print(f"book_530 in Dense(30)? rank={d_rank}")
    print(f"book_530 in BM25(30)? rank={b_rank}")
    
    # What if top_k is 60?
    d_res60 = dense_retrieve(q, "book", top_k=60, repo=repo)
    b_res60 = bm25_retrieve(q, "book", top_k=60, repo=repo)
    d_rank60 = next((c["rank"] for c in d_res60 if c["id"] == "book_530"), None)
    b_rank60 = next((c["rank"] for c in b_res60 if c["id"] == "book_530"), None)
    print(f"book_530 in Dense(60)? rank={d_rank60}")
    print(f"book_530 in BM25(60)? rank={b_rank60}")
    
    # Now check RRF
    r30 = reciprocal_rank_fusion([[c["id"] for c in d_res], [c["id"] for c in b_res]], k=60, top_k=30)
    print(f"book_530 in RRF(30)? rank={next((i+1 for i, (cid, _) in enumerate(r30) if cid == 'book_530'), None)}")
    
    r60 = reciprocal_rank_fusion([[c["id"] for c in d_res60], [c["id"] for c in b_res60]], k=60, top_k=60)
    print(f"book_530 in RRF(60)? rank={next((i+1 for i, (cid, _) in enumerate(r60) if cid == 'book_530'), None)}")

if __name__ == "__main__":
    main()
