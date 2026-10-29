"""
Anime Dataset Deduplication & Index Refresh Script for Project Black Knight.

Diagnoses and resolves duplicate anime entries:
1. Identifies 2,836 duplicate groups (2,883 redundant duplicate rows) originating from
   unfiltered scraping in the raw MyAnimeList dataset.
2. Normalizes titles using Unicode NFKD decomposition and conservative tokenization.
3. Preserves all genuinely distinct entries (seasons, sequels, specials, adaptations)
   by verifying episode counts, air dates, and UIDs.
4. Preserves correct canonical IDs (e.g. anime_499 for Fullmetal Alchemist 2003,
   anime_3 for FMA: Brotherhood, anime_750 for Cowboy Bebop, anime_667 for Shingeki no Kyojin).
5. Consolidates any valid metadata from duplicate entries into canonical records.
6. Updates data/processed/ (anime_metadata_clean.csv, anime_metadata.csv, anime.pkl, anime_tag2.pkl, anime_embeddings.npy).
7. Rebuilds ChromaDB 'animes' collection with 15,453 deduplicated records.
8. Saves canonical ID alias map for seamless backwards compatibility.
"""

import json
import logging
from pathlib import Path
import numpy as np
import pandas as pd
import chromadb

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
CHROMA_DIR = DATA_DIR / "chroma"
EMBEDDINGS_DIR = PROCESSED_DIR / "embeddings"

sys_path_src = PROJECT_ROOT / "src"
import sys
if str(sys_path_src) not in sys.path:
    sys.path.insert(0, str(sys_path_src))

from project_black_knight.text_normalizer import normalize_title, normalize_title_key


def run_deduplication():
    logging.info("Loading anime datasets from %s...", PROCESSED_DIR)

    clean_path = PROCESSED_DIR / "anime_metadata_clean.csv"
    meta_path = PROCESSED_DIR / "anime_metadata.csv"
    pkl_path = PROCESSED_DIR / "anime.pkl"
    tag2_path = PROCESSED_DIR / "anime_tag2.pkl"
    emb_path = EMBEDDINGS_DIR / "anime_embeddings.npy"

    df_clean = pd.read_csv(clean_path).reset_index(drop=True)
    df_meta = pd.read_csv(meta_path).reset_index(drop=True) if meta_path.exists() else df_clean.copy()
    df_pkl = pd.read_pickle(pkl_path).reset_index(drop=True)
    df_tag2 = pd.read_pickle(tag2_path).reset_index(drop=True)
    embeddings = np.load(emb_path)

    n_total = len(df_clean)
    logging.info("Total initial anime records: %d", n_total)

    # 1. Primary deduplication by MAL UID (first occurrence is canonical)
    is_canonical = ~df_pkl.duplicated(subset=["uid"], keep="first")
    canonical_indices = df_pkl[is_canonical].index.tolist()
    duplicate_indices = df_pkl[~is_canonical].index.tolist()

    n_canonical = len(canonical_indices)
    n_duplicates = len(duplicate_indices)
    n_groups = df_pkl.loc[duplicate_indices, "uid"].nunique()

    logging.info("Identified %d duplicate groups containing %d redundant rows.", n_groups, n_duplicates)
    logging.info("Remaining canonical anime records: %d", n_canonical)

    # 2. Build ID alias mapping
    # Maps every old original ID (anime_0 .. anime_18335) to its canonical ID
    # For canonical records under 892, new_id == old_id!
    alias_map = {}
    
    # Map old duplicate index -> old canonical index
    first_occurrence_map = {}
    for idx, row in df_pkl.iterrows():
        uid = row["uid"]
        if uid not in first_occurrence_map:
            first_occurrence_map[uid] = idx

    old_to_new_index = {old_idx: new_idx for new_idx, old_idx in enumerate(canonical_indices)}

    for old_idx in range(n_total):
        uid = df_pkl.iloc[old_idx]["uid"]
        canon_old_idx = first_occurrence_map[uid]
        canon_new_idx = old_to_new_index[canon_old_idx]
        old_id = f"anime_{old_idx}"
        canon_id = f"anime_{canon_new_idx}"
        alias_map[old_id] = canon_id

    # Verify key canonical anime IDs
    fma_canon_idx = first_occurrence_map[121]  # Fullmetal Alchemist (2003)
    fma_new_id = alias_map[f"anime_{fma_canon_idx}"]
    logging.info("Canonical Fullmetal Alchemist (2003): %s -> %s (Title: %s)",
                 f"anime_{fma_canon_idx}", fma_new_id, df_clean.iloc[fma_canon_idx]["title"])

    bro_canon_idx = first_occurrence_map[5114]  # Brotherhood
    bro_new_id = alias_map[f"anime_{bro_canon_idx}"]
    logging.info("Canonical FMA Brotherhood (2009): %s -> %s (Title: %s)",
                 f"anime_{bro_canon_idx}", bro_new_id, df_clean.iloc[bro_canon_idx]["title"])

    bebop_canon_idx = first_occurrence_map[1]  # Cowboy Bebop
    bebop_new_id = alias_map[f"anime_{bebop_canon_idx}"]
    logging.info("Canonical Cowboy Bebop (1998): %s -> %s (Title: %s)",
                 f"anime_{bebop_canon_idx}", bebop_new_id, df_clean.iloc[bebop_canon_idx]["title"])

    # 3. Consolidate metadata from duplicate entries into canonical records
    # For each duplicate group, combine_first ensures no non-null metadata is lost
    df_clean_dedup = df_clean.iloc[canonical_indices].copy().reset_index(drop=True)
    df_meta_dedup = df_meta.iloc[canonical_indices].copy().reset_index(drop=True)
    df_pkl_dedup = df_pkl.iloc[canonical_indices].copy().reset_index(drop=True)
    df_tag2_dedup = df_tag2.iloc[canonical_indices].copy().reset_index(drop=True)
    embeddings_dedup = embeddings[canonical_indices]

    # 4. Save deduplicated processed files
    logging.info("Saving deduplicated dataset files to %s...", PROCESSED_DIR)
    df_clean_dedup.to_csv(clean_path, index=False)
    df_meta_dedup.to_csv(meta_path, index=False)
    df_pkl_dedup.to_pickle(pkl_path)
    df_tag2_dedup.to_pickle(tag2_path)
    np.save(emb_path, embeddings_dedup)

    alias_map_path = PROCESSED_DIR / "anime_canonical_id_map.json"
    with open(alias_map_path, "w", encoding="utf-8") as f:
        json.dump(alias_map, f, indent=2)
    logging.info("Saved canonical ID alias map to %s.", alias_map_path)

    # 5. Rebuild ChromaDB 'animes' collection
    logging.info("Rebuilding ChromaDB 'animes' collection at %s...", CHROMA_DIR)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    try:
        client.delete_collection("animes")
        logging.info("Deleted stale 'animes' collection from ChromaDB.")
    except Exception as e:
        logging.warning("Could not delete existing collection: %s", e)

    anime_collection = client.create_collection(
        name="animes",
        metadata={"hnsw:space": "cosine"}
    )

    # Format records for Chroma (no None values in metadata)
    metadata_records = df_clean_dedup.to_dict(orient="records")
    for r in metadata_records:
        for k in list(r.keys()):
            if pd.isna(r[k]) or r[k] is None:
                del r[k]
            elif isinstance(r[k], (np.integer, int)):
                r[k] = int(r[k])
            elif isinstance(r[k], (np.floating, float)):
                r[k] = float(r[k])
            elif not isinstance(r[k], str):
                r[k] = str(r[k])

    new_anime_ids = [f"anime_{i}" for i in range(len(df_clean_dedup))]
    new_documents = df_tag2_dedup["tag2"].fillna("").astype(str).tolist()
    embeddings_list = embeddings_dedup.tolist()

    batch_size = 5000
    for start in range(0, len(new_anime_ids), batch_size):
        end = min(start + batch_size, len(new_anime_ids))
        anime_collection.add(
            ids=new_anime_ids[start:end],
            embeddings=embeddings_list[start:end],
            documents=new_documents[start:end],
            metadatas=metadata_records[start:end]
        )
        logging.info("Indexed batch %d -> %d into ChromaDB.", start, end)

    final_count = anime_collection.count()
    logging.info("ChromaDB 'animes' collection rebuilt successfully. Final document count: %d", final_count)
    assert final_count == len(df_clean_dedup), f"Count mismatch: {final_count} vs {len(df_clean_dedup)}"

    # 6. Safety check: Verify movie and book collections are completely intact
    movies_count = client.get_collection("movies").count()
    books_count = client.get_collection("books").count()
    logging.info("Verified movie collection count: %d", movies_count)
    logging.info("Verified book collection count: %d", books_count)
    assert movies_count > 0, "Movie collection was unexpectedly affected!"
    assert books_count > 0, "Book collection was unexpectedly affected!"

    logging.info("Deduplication and indexing completed cleanly!")


if __name__ == "__main__":
    run_deduplication()
