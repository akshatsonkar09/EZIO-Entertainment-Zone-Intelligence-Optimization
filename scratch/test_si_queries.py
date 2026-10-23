import json
import pandas as pd
from project_black_knight.retrieval import RetrievalRepository, bm25_retrieve, dense_retrieve, reciprocal_rank_fusion

repo = RetrievalRepository()
docs, ids = repo.get_documents_and_ids('anime')
id_map = dict(zip(ids, docs))

# Death note doc
dn_doc = id_map['anime_726']
print("Death Note doc length:", len(dn_doc))

# Test different query formulations for SI_006
queries = [
    ("current", "Recommend anime similar to Death Note. " + dn_doc),
    ("doc_only", dn_doc),
    ("doc_bounded_350", dn_doc[:350]),
    ("thematic_only", "mystery police psychological supernatural thriller shounen " + dn_doc[:250]),
]

targets = {'anime_726', 'anime_9', 'anime_732', 'anime_759'}

for qname, qtext in queries:
    dense_res = dense_retrieve(qtext, 'anime', top_k=60, repo=repo)
    bm25_res = bm25_retrieve(qtext, 'anime', top_k=60, repo=repo)
    fused = reciprocal_rank_fusion([[c['id'] for c in dense_res], [c['id'] for c in bm25_res]], top_k=30)
    
    # Exclude all Death Note seed variants (anime_726, anime_16811)
    fused_clean = [p for p in fused if p[0] not in {'anime_726', 'anime_16811'}]
    
    hits = [p for p in fused_clean[:10] if p[0] in targets]
    print(f"\nQuery '{qname}': Hits in Top 10 = {len(hits)}")
    for i, p in enumerate(fused_clean[:10]):
        df_meta = repo.get_metadata_df('anime')
        title = df_meta.iloc[int(p[0].split('_')[1])]['title']
        is_hit = " *** HIT ***" if p[0] in targets else ""
        print(f"  {i+1}. [{p[0]}] {title} (score: {p[1]:.4f}){is_hit}")
