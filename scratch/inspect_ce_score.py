"""
Inspect Cross-Encoder scores for anime_667 vs other Shingeki no Kyojin docs
"""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from project_black_knight.retrieval import RetrievalRepository

def main():
    repo = RetrievalRepository()
    docs, ids = repo.get_documents_and_ids("anime")
    id_to_idx = repo._id_to_index["anime"]
    ce = repo.get_reranker_model()
    
    q = "Shingeki no Kyojin"
    cands = [
        "anime_667",    # Shingeki no Kyojin (Target)
        "anime_14939",  # Shingeki no Kyojin (Target)
        "anime_9564",   # Picture Drama
        "anime_885",    # Lost Girls
        "anime_61",     # OVA
    ]
    
    print(f"Query: '{q}'\n")
    for cid in cands:
        idx = id_to_idx[cid]
        doc = docs[idx]
        score = ce.predict([[q, doc]])[0]
        print(f"[{cid}] (Score: {score:.4f})")
        print(f"Doc: {doc[:200]}...\n")

if __name__ == "__main__":
    main()
