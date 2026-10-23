import json
from project_black_knight.retrieval import RetrievalRepository, bm25_retrieve, dense_retrieve
from project_black_knight.metadata_filter import get_valid_ids
from project_black_knight.text_normalizer import normalize_title_key

repo = RetrievalRepository()
df = repo.get_metadata_df('anime')
docs, ids = repo.get_documents_and_ids('anime')

# KI_018 query
q = "Find Shingeki no Kyojin."
title = "Shingeki no Kyojin"
valid = get_valid_ids(df, ids, {"title": title}, "anime")
print(f"Total valid IDs with title '{title}': {len(valid)}")
exact = [i for i in valid if normalize_title_key(df.iloc[repo._id_to_index['anime'][i]]['title']) == normalize_title_key(title)]
print(f"Exact title match IDs: {exact}")

dense = dense_retrieve(q, "anime", valid, top_k=60, repo=repo)
bm25 = bm25_retrieve(q, "anime", valid, top_k=60, repo=repo)

dense_ids = [r[0] for r in dense]
bm25_ids = [r[0] for r in bm25]

print("In dense top 60:", [x for x in exact if x in dense_ids])
print("In bm25 top 60:", [x for x in exact if x in bm25_ids])
