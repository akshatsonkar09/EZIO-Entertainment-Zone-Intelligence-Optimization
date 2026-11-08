"""
Hybrid Retrieval and Recommendation Engine for Project Black Knight (Phase 4).

Features:
- Dense retrieval with SentenceTransformers and persistent ChromaDB collections
- BM25 lexical retrieval using rank_bm25 with regex tokenization
- Reciprocal Rank Fusion (RRF) with deterministic tie-breaking
- Neural cross-encoder reranking with cross-encoder/ms-marco-MiniLM-L-6-v2
- Phase 3 metadata filtering integration (get_valid_ids)
- Similar-item seed resolution and reference self-exclusion
- Cross-domain multi-media recommendations without filter leakage
- Comprehensive stage-level diagnostics and latency measurement
"""

import math
import os
import re
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from rank_bm25 import BM25Okapi

from .metadata_filter import get_valid_ids, normalize_token_str, is_bypassed_genre_filter
from .query_schema import BlackKnightQuery
from .diagnostics import RetrievalTrace, TargetTrackingRecord, explain_filter_rejection
from .text_normalizer import normalize_title


# --------------------------------------------------
# Paths & Default Configuration
# --------------------------------------------------

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
CHROMA_DIR = DATA_DIR / "chroma"


def get_model_cache_dir() -> str:
    """Resolve shared model cache directory across preload and runtime retrieval."""
    env_dir = os.getenv("HF_HOME") or os.getenv("MODEL_CACHE_DIR")
    if env_dir and env_dir.strip():
        return str(Path(env_dir.strip()).resolve())
    return str((PROJECT_ROOT / "data" / "models").resolve())

SUPPORTED_DOMAINS = ("movie", "anime", "book")

CHROMA_COLLECTIONS = {
    "movie": "movies",
    "anime": "animes",
    "book": "books",
}

TITLE_FIELDS = {
    "movie": "title",
    "anime": "title",
    "book": "title",
}


# --------------------------------------------------
# Tokenizer
# --------------------------------------------------

def tokenize_for_bm25(text: str) -> list[str]:
    """Tokenize query and documents for BM25 Okapi."""
    if not text:
        return []
    return re.findall(r"\b\w+\b", str(text).lower())


# --------------------------------------------------
# Lazy Data & Model Repository
# --------------------------------------------------

class RetrievalRepository:
    """Manages lazy-loaded dataframes, Chroma collections, BM25 indexes, and models."""

    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir
        self.processed_dir = data_dir / "processed"
        persist_env = os.getenv("CHROMA_PERSIST_DIR")
        self.chroma_dir = Path(persist_env).resolve() if persist_env else (data_dir / "chroma")

        self._metadata_dfs: dict[str, pd.DataFrame] = {}
        self._document_texts: dict[str, list[str]] = {}
        self._item_ids: dict[str, list[str]] = {}
        self._id_to_index: dict[str, dict[str, int]] = {}
        self._bm25_indexes: dict[str, BM25Okapi] = {}
        self._normalized_titles: dict[str, list[str]] = {}

        self._chroma_client = None
        self._embedding_model = None
        self._reranker_model = None

    def get_normalized_titles(self, domain: str) -> list[str]:
        """Return cached pre-normalized titles list aligned with item indices for zero-overhead exact matching."""
        if domain not in self._normalized_titles:
            df = self.get_metadata_df(domain)
            title_col = TITLE_FIELDS.get(domain, "title")
            raw_titles = df[title_col].fillna("").astype(str).tolist()
            self._normalized_titles[domain] = [normalize_token_str(t) for t in raw_titles]
        return self._normalized_titles[domain]

    def get_metadata_df(self, domain: str) -> pd.DataFrame:
        """Load and cache clean metadata dataframe for a domain."""
        if domain not in self._metadata_dfs:
            fname = {
                "movie": "movie_metadata_clean.csv",
                "anime": "anime_metadata_clean.csv",
                "book": "book_metadata_clean.csv",
            }[domain]
            df = pd.read_csv(self.processed_dir / fname)
            self._metadata_dfs[domain] = df
        return self._metadata_dfs[domain]

    def get_documents_and_ids(self, domain: str) -> tuple[list[str], list[str]]:
        """Load text representations and corresponding item IDs."""
        if domain not in self._document_texts:
            df_meta = self.get_metadata_df(domain)
            n_rows = len(df_meta)

            if domain == "movie":
                # Use movies1234.pkl which has exact 4805 rows aligned 1-to-1 with metadata and Chroma
                pkl_path = self.processed_dir / "movies1234.pkl"
                if pkl_path.exists():
                    df_pkl = pd.read_pickle(pkl_path)
                    docs = df_pkl["tag"].fillna("").astype(str).tolist()
                else:
                    df_pkl = pd.read_pickle(self.processed_dir / "movies.pkl")
                    docs = df_pkl["tag"].iloc[:n_rows].fillna("").astype(str).tolist()
            elif domain == "anime":
                df_pkl = pd.read_pickle(self.processed_dir / "anime_tag2.pkl")
                docs = df_pkl["tag2"].fillna("").astype(str).tolist()
            elif domain == "book":
                df_pkl = pd.read_pickle(self.processed_dir / "books_tag2.pkl")
                docs = df_pkl["tag2"].fillna("").astype(str).tolist()
            else:
                raise ValueError(f"Unknown domain: {domain}")

            ids = [f"{domain}_{i}" for i in range(len(docs))]
            self._document_texts[domain] = docs
            self._item_ids[domain] = ids
            self._id_to_index[domain] = {item_id: idx for idx, item_id in enumerate(ids)}

        return self._document_texts[domain], self._item_ids[domain]

    def get_bm25_index(self, domain: str) -> BM25Okapi:
        """Return or lazily construct BM25Okapi index."""
        if domain not in self._bm25_indexes:
            docs, _ = self.get_documents_and_ids(domain)
            tokens = [tokenize_for_bm25(doc) for doc in docs]
            self._bm25_indexes[domain] = BM25Okapi(tokens)
        return self._bm25_indexes[domain]

    def get_chroma_collection(self, domain: str):
        """Return persistent ChromaDB collection for domain."""
        if self._chroma_client is None:
            import chromadb
            self._chroma_client = chromadb.PersistentClient(path=str(self.chroma_dir))
        coll_name = CHROMA_COLLECTIONS[domain]
        try:
            return self._chroma_client.get_collection(coll_name)
        except Exception:
            try:
                from scripts.build_chroma_index import ensure_chroma_indexes
            except ImportError:
                import sys
                if str(PROJECT_ROOT) not in sys.path:
                    sys.path.insert(0, str(PROJECT_ROOT))
                from scripts.build_chroma_index import ensure_chroma_indexes
            ensure_chroma_indexes(self.data_dir)
            return self._chroma_client.get_collection(coll_name)

    def get_embedding_model(self):
        """Return lazy-loaded SentenceTransformer embedding model."""
        if self._embedding_model is None:
            from sentence_transformers import SentenceTransformer
            cache_dir = get_model_cache_dir()
            try:
                self._embedding_model = SentenceTransformer("all-MiniLM-L6-v2", cache_folder=cache_dir)
            except Exception as exc:
                raise RuntimeError(
                    f"Failed to load SentenceTransformer model 'all-MiniLM-L6-v2' from cache '{cache_dir}': {exc}. "
                    "Ensure models are preloaded using 'python scripts/preload_models.py' during build."
                ) from exc
        return self._embedding_model

    def get_reranker_model(self):
        """Return lazy-loaded CrossEncoder reranking model."""
        if self._reranker_model is None:
            from sentence_transformers import CrossEncoder
            cache_dir = get_model_cache_dir()
            try:
                self._reranker_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", cache_folder=cache_dir)
            except Exception as exc:
                raise RuntimeError(
                    f"Failed to load CrossEncoder model 'cross-encoder/ms-marco-MiniLM-L-6-v2' from cache '{cache_dir}': {exc}. "
                    "Ensure models are preloaded using 'python scripts/preload_models.py' during build."
                ) from exc
        return self._reranker_model


_REPO = RetrievalRepository()


# --------------------------------------------------
# 1. Dense Retrieval (ChromaDB + SentenceTransformers)
# --------------------------------------------------

def dense_retrieve(
    query_text: str,
    media_type: str,
    valid_ids: set[str] | None = None,
    top_k: int = 30,
    repo: RetrievalRepository = _REPO,
    custom_model: Any = None,
    custom_collection: Any = None,
) -> list[dict[str, Any]]:
    """
    Query ChromaDB dense embeddings, filtering candidate IDs.
    Returns list of {'id': item_id, 'score': distance_or_similarity, 'rank': 1-indexed}.
    """
    if not query_text or (valid_ids is not None and len(valid_ids) == 0):
        return []

    model = custom_model or repo.get_embedding_model()
    collection = custom_collection or repo.get_chroma_collection(media_type)

    query_embedding = model.encode([query_text])

    # Pre-filtering optimization: if valid_ids is selective (<= 250), score valid_ids directly
    if valid_ids is not None and 0 < len(valid_ids) <= 250 and custom_collection is None and hasattr(collection, "get"):
        try:
            got = collection.get(ids=list(valid_ids), include=["embeddings"])
            if got and got.get("ids") and got.get("embeddings") and len(got["ids"]) > 0:
                retrieved_ids = got["ids"]
                raw_embs = np.array(got["embeddings"])
                query_vector = np.array(query_embedding).flatten()
                q_norm = np.linalg.norm(query_vector)
                if q_norm > 0:
                    item_norms = np.linalg.norm(raw_embs, axis=1)
                    item_norms[item_norms == 0] = 1e-9
                    cos_sims = np.dot(raw_embs, query_vector) / (item_norms * q_norm)
                else:
                    cos_sims = np.zeros(len(retrieved_ids))

                sorted_indices = np.argsort(-cos_sims)
                candidates = []
                for rank_idx, s_idx in enumerate(sorted_indices[:top_k], start=1):
                    item_id = retrieved_ids[s_idx]
                    candidates.append({
                        "id": item_id,
                        "score": float(cos_sims[s_idx]),
                        "distance": float(1.0 - cos_sims[s_idx]),
                        "rank": rank_idx,
                    })
                return candidates
        except Exception:
            pass

    # Fetch larger candidate pool to accommodate filtering
    fetch_k = min(max(top_k * 10, 500), collection.count())
    if fetch_k <= 0:
        return []

    embeddings_list = (
        query_embedding.tolist()
        if hasattr(query_embedding, "tolist")
        else list(query_embedding)
    )

    res = collection.query(
        query_embeddings=embeddings_list,
        n_results=fetch_k,
    )

    ids_raw = res["ids"][0] if res.get("ids") else []
    distances_raw = res["distances"][0] if res.get("distances") else [0.0] * len(ids_raw)

    dense_candidates = []
    seen = set()

    for item_id, dist in zip(ids_raw, distances_raw):
        if item_id in seen:
            continue
        if valid_ids is not None and item_id not in valid_ids:
            continue

        seen.add(item_id)
        # Convert distance to similarity score
        score = 1.0 / (1.0 + float(dist)) if dist >= 0 else 0.0
        dense_candidates.append({
            "id": item_id,
            "score": score,
            "distance": float(dist),
        })

        if len(dense_candidates) >= top_k:
            break

    for r_idx, c in enumerate(dense_candidates, start=1):
        c["rank"] = r_idx

    return dense_candidates


# --------------------------------------------------
# 2. Lexical Retrieval (BM25)
# --------------------------------------------------

def bm25_retrieve(
    query_text: str,
    media_type: str,
    valid_ids: set[str] | None = None,
    top_k: int = 30,
    repo: RetrievalRepository = _REPO,
    custom_index: BM25Okapi | None = None,
    custom_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Lexical BM25 retrieval over tokenized document tags, filtered by valid_ids.
    Returns list of {'id': item_id, 'score': bm25_score, 'rank': 1-indexed}.
    """
    query_tokens = tokenize_for_bm25(query_text)
    if not query_tokens or (valid_ids is not None and len(valid_ids) == 0):
        return []

    bm25_index = custom_index or repo.get_bm25_index(media_type)
    _, item_ids = repo.get_documents_and_ids(media_type) if custom_ids is None else (None, custom_ids)

    scores = bm25_index.get_scores(query_tokens)
    top_indices = scores.argsort()[::-1]

    bm25_candidates = []
    seen = set()

    for idx in top_indices:
        score = float(scores[idx])
        if score <= 0.0:
            break

        item_id = item_ids[idx]
        if item_id in seen:
            continue
        if valid_ids is not None and item_id not in valid_ids:
            continue

        seen.add(item_id)
        bm25_candidates.append({
            "id": item_id,
            "score": score,
        })

        if len(bm25_candidates) >= top_k:
            break

    for r_idx, c in enumerate(bm25_candidates, start=1):
        c["rank"] = r_idx

    return bm25_candidates


# --------------------------------------------------
# 3. Reciprocal Rank Fusion (RRF)
# --------------------------------------------------

def reciprocal_rank_fusion(
    result_lists: list[list[str] | list[dict[str, Any]]],
    k: int = 60,
    top_k: int = 30,
) -> list[tuple[str, float]]:
    """
    Reciprocal Rank Fusion over multiple candidate lists.
    Formula: RRF(d) = sum(1 / (k + rank(d, L)))
    Handles duplicate candidate IDs, unequal lengths, and empty lists.
    Deterministic tie-breaking: higher RRF score, then alphabetical ID.
    """
    rrf_scores: dict[str, float] = defaultdict(float)

    for res_list in result_lists:
        seen_in_list = set()
        for rank, item in enumerate(res_list, start=1):
            item_id = item["id"] if isinstance(item, dict) else str(item)
            if item_id in seen_in_list:
                continue
            seen_in_list.add(item_id)
            rrf_scores[item_id] += 1.0 / (k + rank)

    # Sort descending by score, deterministic tie-break by ascending ID
    ranked = sorted(
        rrf_scores.items(),
        key=lambda x: (-x[1], str(x[0])),
    )

    return ranked[:top_k]


# --------------------------------------------------
# 4. Neural Cross-Encoder Reranking
# --------------------------------------------------

def rerank_candidates(
    query_text: str,
    candidate_ids: list[str],
    media_type: str,
    top_k: int = 10,
    candidate_scores: dict[str, float] | None = None,
    alpha: float = 0.7,
    repo: RetrievalRepository = _REPO,
    custom_reranker: Any = None,
    custom_documents: list[str] | None = None,
    custom_id_to_index: dict[str, int] | None = None,
) -> list[tuple[str, float]]:
    """
    Score [query_text, document_text] candidate pairs with CrossEncoder.
    If candidate_scores (e.g. from RRF) are provided, combines normalized CrossEncoder scores
    with normalized first-stage retrieval scores (alpha * norm_ce + (1 - alpha) * norm_rrf)
    to prevent catastrophic demotion of high-consensus candidates.
    Returns sorted list of (item_id, score) descending, with deterministic tie-breaking.
    """
    if not candidate_ids or not query_text:
        return [(cid, 0.0) for cid in candidate_ids[:top_k]]

    reranker = custom_reranker or repo.get_reranker_model()

    if custom_documents is not None and custom_id_to_index is not None:
        docs = custom_documents
        id_to_idx = custom_id_to_index
        df_meta = None
    else:
        docs, _ = repo.get_documents_and_ids(media_type)
        id_to_idx = repo._id_to_index[media_type]
        df_meta = repo.get_metadata_df(media_type) if media_type == "movie" else None

    title_col = TITLE_FIELDS.get(media_type, "title")

    # Build pairs (deduplicating incoming candidate IDs preserving order)
    seen_cids = set()
    unique_candidate_ids = []
    for cid in candidate_ids:
        if cid not in seen_cids:
            seen_cids.add(cid)
            unique_candidate_ids.append(cid)

    pairs = []
    valid_cids = []
    for cid in unique_candidate_ids:
        if cid in id_to_idx:
            row_idx = id_to_idx[cid]
            doc_text = docs[row_idx]
            # Ensure movie representation includes title prefix if not already present
            if df_meta is not None and not doc_text.lower().startswith("title:"):
                t_val = str(df_meta.iloc[row_idx][title_col])
                doc_text = f"title: {t_val} {doc_text}"
            pairs.append([query_text, doc_text])
            valid_cids.append(cid)

    if not pairs:
        return []

    scores = reranker.predict(pairs)

    if candidate_scores and len(scores) > 0:
        min_ce = float(min(scores))
        max_ce = float(max(scores))
        ce_range = (max_ce - min_ce) if max_ce > min_ce else 1.0

        rrf_vals = [candidate_scores.get(cid, 0.0) for cid in valid_cids]
        min_r = min(rrf_vals)
        max_r = max(rrf_vals)
        r_range = (max_r - min_r) if max_r > min_r else 1.0

        combined_scores = []
        for cid, raw_ce in zip(valid_cids, scores):
            norm_ce = (float(raw_ce) - min_ce) / ce_range
            norm_r = (candidate_scores.get(cid, 0.0) - min_r) / r_range
            final_s = alpha * norm_ce + (1.0 - alpha) * norm_r
            combined_scores.append(final_s)

        ranked = sorted(
            zip(valid_cids, combined_scores),
            key=lambda x: (-x[1], str(x[0])),
        )
    else:
        ranked = sorted(
            zip(valid_cids, [float(s) for s in scores]),
            key=lambda x: (-x[1], str(x[0])),
        )

    return ranked[:top_k]


# --------------------------------------------------
# 5. Similar-Item Seed Resolution
# --------------------------------------------------

def resolve_similar_seed(
    reference_title: str,
    target_domain: str | None = None,
    repo: RetrievalRepository = _REPO,
) -> dict[str, Any] | None:
    """
    Locate a reference title in the metadata datasets to extract its document
    representation and seed ID. Searches target_domain first, then other domains.
    """
    if not reference_title:
        return None

    clean_ref = normalize_token_str(reference_title)
    if not clean_ref:
        return None

    search_domains = [target_domain] if target_domain else []
    search_domains.extend([d for d in SUPPORTED_DOMAINS if d != target_domain])

    for dom in search_domains:
        if not dom:
            continue
        df = repo.get_metadata_df(dom)
        title_col = TITLE_FIELDS[dom]
        docs, ids = repo.get_documents_and_ids(dom)

        # Match normalized title
        for idx, row in df.iterrows():
            item_title = str(row[title_col])
            if clean_ref == normalize_token_str(item_title):
                return {
                    "domain": dom,
                    "item_id": ids[idx],
                    "title": item_title,
                    "doc_text": docs[idx],
                    "metadata": row.to_dict(),
                }

    return None


# --------------------------------------------------
# 6. Unified Hybrid Retrieval Function
# --------------------------------------------------

def hybrid_retrieve(
    query: str,
    media_type: str,
    filters: dict[str, Any] | None = None,
    similar_to: list[str] | None = None,
    top_k: int = 10,
    candidate_k: int = 60,
    rerank: bool | None = None,
    repo: RetrievalRepository = _REPO,
    collect_diagnostics: bool = False,
    trace_collector: RetrievalTrace | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Unified end-to-end hybrid retrieval pipeline for a single media domain:
    1. Metadata hard filtering (Phase 3)
    2. Similar-to seed resolution and query augmentation
    3. Dense ChromaDB retrieval
    4. Lexical BM25 retrieval
    5. Reciprocal Rank Fusion
    6. Cross-Encoder neural reranking
    7. Result formatting & diagnostics
    """
    diagnostics: dict[str, Any] = {
        "media_type": media_type,
        "input_query": query,
        "filters": filters or {},
        "similar_to": similar_to or [],
        "latencies_ms": {},
    }

    t_start = time.perf_counter()

    # 1. METADATA FILTERING
    t0 = time.perf_counter()
    df_meta = repo.get_metadata_df(media_type)
    _, item_ids = repo.get_documents_and_ids(media_type)
    id_to_idx = repo._id_to_index[media_type]

    valid_ids = get_valid_ids(
        dataframe=df_meta,
        current_ids=item_ids,
        filters=filters or {},
        media_type=media_type,
    )
    diagnostics["latencies_ms"]["metadata_filtering"] = round((time.perf_counter() - t0) * 1000, 2)
    diagnostics["valid_ids_count"] = len(valid_ids)

    if filters and filters.get("genres_include"):
        bypassed = [g for g in filters["genres_include"] if is_bypassed_genre_filter(g, media_type)]
        if bypassed:
            diagnostics["bypassed_domain_filters"] = bypassed

    if trace_collector is not None:
        trace_collector.catalog_item_counts[media_type] = len(item_ids)
        trace_collector.valid_ids_counts[media_type] = len(valid_ids)
        trace_collector.latencies_ms[f"{media_type}_metadata_filtering"] = diagnostics["latencies_ms"]["metadata_filtering"]
        for t in trace_collector.targets.values():
            if t.media_type == media_type:
                t.in_catalog = (t.target_id in id_to_idx)
                t.passed_metadata_filter = (t.target_id in valid_ids)
                if not t.passed_metadata_filter and t.in_catalog:
                    row_idx = id_to_idx[t.target_id]
                    row_dict = df_meta.iloc[row_idx].to_dict()
                    t.filter_rejection_reason = explain_filter_rejection(row_dict, filters or {}, media_type)

    if not valid_ids:
        diagnostics["empty_reason"] = "No items in database satisfied the metadata hard filters."
        diagnostics["latencies_ms"]["total"] = round((time.perf_counter() - t_start) * 1000, 2)
        return [], diagnostics

    # 2. SIMILAR-TO RESOLUTION & SEED EXCLUSION
    effective_query = query.strip() if query else ""
    excluded_seed_ids = set()
    seed_info = []

    if similar_to:
        for seed_title in similar_to:
            resolved = resolve_similar_seed(seed_title, target_domain=media_type, repo=repo)
            if resolved:
                seed_info.append(resolved)
                # If seed item belongs to this domain, exclude it from recommendations
                if resolved["domain"] == media_type:
                    excluded_seed_ids.add(resolved["item_id"])

                # Augment effective query if query is blank or sparse
                seed_doc = resolved["doc_text"]
                if not effective_query:
                    effective_query = seed_doc
                else:
                    effective_query = f"{effective_query} {seed_doc}"

        diagnostics["resolved_seeds"] = [s["title"] for s in seed_info]
        diagnostics["excluded_seed_ids"] = list(excluded_seed_ids)

    if trace_collector is not None and excluded_seed_ids:
        trace_collector.excluded_seed_ids.extend(list(excluded_seed_ids))
        for t in trace_collector.targets.values():
            if t.target_id in excluded_seed_ids:
                t.excluded_as_seed = True

    # Exclude seeds from valid candidates
    effective_valid_ids = valid_ids - excluded_seed_ids
    if not effective_valid_ids:
        diagnostics["empty_reason"] = "Only the seed items matched the criteria and were excluded."
        return [], diagnostics

    # Fallback query text if completely empty
    if not effective_query:
        if filters and filters.get("title"):
            effective_query = str(filters["title"])
        else:
            effective_query = "popular recommended entertainment"

    diagnostics["effective_retrieval_query"] = effective_query[:150]

    # 3. DENSE RETRIEVAL
    t0 = time.perf_counter()
    dense_results = dense_retrieve(
        query_text=effective_query,
        media_type=media_type,
        valid_ids=effective_valid_ids,
        top_k=candidate_k,
        repo=repo,
    )
    diagnostics["latencies_ms"]["dense_retrieval"] = round((time.perf_counter() - t0) * 1000, 2)
    diagnostics["dense_candidates_count"] = len(dense_results)
    diagnostics["dense_top_scores"] = [round(c["score"], 4) for c in dense_results[:3]]

    if trace_collector is not None:
        trace_collector.dense_counts[media_type] = len(dense_results)
        trace_collector.dense_candidates[media_type] = [
            {"id": c["id"], "score": round(c["score"], 4), "rank": c["rank"]}
            for c in dense_results[:10]
        ]
        trace_collector.latencies_ms[f"{media_type}_dense"] = diagnostics["latencies_ms"]["dense_retrieval"]
        for t in trace_collector.targets.values():
            if t.media_type == media_type:
                d_match = [c for c in dense_results if c["id"] == t.target_id]
                if d_match:
                    t.dense_retrieved = True
                    t.dense_rank = d_match[0]["rank"]
                    t.dense_score = round(d_match[0]["score"], 4)

    # 4. LEXICAL BM25 RETRIEVAL
    t0 = time.perf_counter()
    bm25_results = bm25_retrieve(
        query_text=effective_query,
        media_type=media_type,
        valid_ids=effective_valid_ids,
        top_k=candidate_k,
        repo=repo,
    )
    diagnostics["latencies_ms"]["bm25_retrieval"] = round((time.perf_counter() - t0) * 1000, 2)
    diagnostics["bm25_candidates_count"] = len(bm25_results)
    diagnostics["bm25_top_scores"] = [round(c["score"], 4) for c in bm25_results[:3]]

    if trace_collector is not None:
        trace_collector.bm25_counts[media_type] = len(bm25_results)
        trace_collector.bm25_candidates[media_type] = [
            {"id": c["id"], "score": round(c["score"], 4), "rank": c["rank"]}
            for c in bm25_results[:10]
        ]
        trace_collector.latencies_ms[f"{media_type}_bm25"] = diagnostics["latencies_ms"]["bm25_retrieval"]
        for t in trace_collector.targets.values():
            if t.media_type == media_type:
                b_match = [c for c in bm25_results if c["id"] == t.target_id]
                if b_match:
                    t.bm25_retrieved = True
                    t.bm25_rank = b_match[0]["rank"]
                    t.bm25_score = round(b_match[0]["score"], 4)

    # 5. RECIPROCAL RANK FUSION
    t0 = time.perf_counter()
    rrf_fused = reciprocal_rank_fusion(
        result_lists=[
            [c["id"] for c in dense_results],
            [c["id"] for c in bm25_results],
        ],
        k=60,
        top_k=candidate_k,
    )
    diagnostics["latencies_ms"]["rrf_fusion"] = round((time.perf_counter() - t0) * 1000, 2)
    diagnostics["rrf_candidates_count"] = len(rrf_fused)

    if trace_collector is not None:
        trace_collector.rrf_counts[media_type] = len(rrf_fused)
        trace_collector.rrf_candidates[media_type] = [
            {"id": cid, "score": round(s, 4), "rank": r_idx}
            for r_idx, (cid, s) in enumerate(rrf_fused[:10], start=1)
        ]
        trace_collector.latencies_ms[f"{media_type}_rrf"] = diagnostics["latencies_ms"]["rrf_fusion"]
        for t in trace_collector.targets.values():
            if t.media_type == media_type:
                r_match = [(r_idx, s) for r_idx, (cid, s) in enumerate(rrf_fused, start=1) if cid == t.target_id]
                if r_match:
                    t.rrf_survived = True
                    t.rrf_rank = r_match[0][0]
                    t.rrf_score = round(r_match[0][1], 4)

    # 5.5. TITLE EXACT-MATCH CANDIDATE PRIORITIZATION
    filter_title = str(filters.get("title", "")).strip() if filters else ""
    norm_filter_key = normalize_token_str(filter_title) if filter_title else ""

    if norm_filter_key:
        norm_titles = repo.get_normalized_titles(media_type)
        exact_valid_ids = [
            vid for vid in effective_valid_ids
            if id_to_idx.get(vid) is not None and norm_titles[id_to_idx[vid]] == norm_filter_key
        ]

        if exact_valid_ids:
            exact_set = set(exact_valid_ids)
            if rrf_fused:
                exact_rrf = [p for p in rrf_fused if p[0] in exact_set]
                missed_exact = [(eid, 1.0) for eid in exact_valid_ids if eid not in {p[0] for p in exact_rrf}]
                other_rrf = [p for p in rrf_fused if p[0] not in exact_set]
                rrf_fused = exact_rrf + missed_exact + other_rrf
            else:
                effective_valid_ids = exact_valid_ids + [vid for vid in effective_valid_ids if vid not in exact_set]

    if not rrf_fused:
        if effective_valid_ids:
            candidate_ids = list(effective_valid_ids)[:candidate_k]
            candidate_scores = None
        else:
            diagnostics["empty_reason"] = "Both dense and BM25 returned 0 candidates."
            diagnostics["latencies_ms"]["total"] = round((time.perf_counter() - t_start) * 1000, 2)
            return [], diagnostics
    else:
        candidate_ids = [cid for cid, score in rrf_fused]
        candidate_scores = dict(rrf_fused)

    if rerank is None:
        should_rerank = (media_type == "movie")
    else:
        should_rerank = bool(rerank)

    # 6. CROSS-ENCODER RERANKING OR RRF BYPASS
    if should_rerank:
        t0 = time.perf_counter()
        reranked = rerank_candidates(
            query_text=effective_query,
            candidate_ids=candidate_ids,
            media_type=media_type,
            top_k=top_k,
            candidate_scores=candidate_scores,
            repo=repo,
        )
        diagnostics["latencies_ms"]["cross_encoder_rerank"] = round((time.perf_counter() - t0) * 1000, 2)
        diagnostics["cross_encoder_bypassed"] = False
        if norm_filter_key:
            norm_titles = repo.get_normalized_titles(media_type)
            exact_pairs = [
                (p[0], p[1] + 10.0)
                for p in reranked
                if id_to_idx.get(p[0]) is not None and norm_titles[id_to_idx[p[0]]] == norm_filter_key
            ]
            other_pairs = [p for p in reranked if p[0] not in {x[0] for x in exact_pairs}]
            final_candidate_pairs = (exact_pairs + other_pairs)[:top_k]
        else:
            final_candidate_pairs = reranked[:top_k]
        diagnostics["reranked_top_scores"] = [round(s, 4) for _, s in final_candidate_pairs[:3]]
    else:
        # Bypassed cross-encoder: preserve RRF ordering and scores according to existing contract
        diagnostics["latencies_ms"]["cross_encoder_rerank"] = 0.0
        diagnostics["cross_encoder_bypassed"] = True
        if norm_filter_key and rrf_fused:
            norm_titles = repo.get_normalized_titles(media_type)
            exact_pairs = [
                (p[0], p[1] + 10.0)
                for p in rrf_fused
                if id_to_idx.get(p[0]) is not None and norm_titles[id_to_idx[p[0]]] == norm_filter_key
            ]
            other_pairs = [p for p in rrf_fused if p[0] not in {x[0] for x in exact_pairs}]
            final_candidate_pairs = (exact_pairs + other_pairs)[:top_k]
        elif rrf_fused:
            final_candidate_pairs = rrf_fused[:top_k]
        else:
            final_candidate_pairs = [(cid, 0.0) for cid in candidate_ids[:top_k]]
        diagnostics["reranked_top_scores"] = [round(s, 4) for _, s in final_candidate_pairs[:3]]

    if trace_collector is not None:
        trace_collector.cross_encoder_applied[media_type] = should_rerank
        trace_collector.latencies_ms[f"{media_type}_cross_encoder"] = diagnostics["latencies_ms"]["cross_encoder_rerank"]
        trace_collector.reranked_counts[media_type] = len(final_candidate_pairs)
        trace_collector.reranked_candidates[media_type] = [
            {"id": cid, "score": round(s, 4), "rank": r_idx}
            for r_idx, (cid, s) in enumerate(final_candidate_pairs[:10], start=1)
        ]
        if should_rerank:
            for t in trace_collector.targets.values():
                if t.media_type == media_type:
                    ce_match = [(r_idx, s) for r_idx, (cid, s) in enumerate(final_candidate_pairs, start=1) if cid == t.target_id]
                    if ce_match:
                        t.ce_reranked = True
                        t.ce_rank = ce_match[0][0]
                        t.ce_score = round(ce_match[0][1], 4)

    # 7. FORMAT FINAL RESULTS
    title_col = TITLE_FIELDS[media_type]

    final_results = []
    for item_id, score in final_candidate_pairs:
        row_idx = id_to_idx[item_id]
        row_data = df_meta.iloc[row_idx]

        final_results.append({
            "id": item_id,
            "title": str(row_data[title_col]),
            "media_type": media_type,
            "score": round(float(score), 4),
            "release_year": row_data.get("release_year"),
            "genres": str(row_data.get("genres", "")),
        })

    diagnostics["final_results_count"] = len(final_results)
    diagnostics["latencies_ms"]["total"] = round((time.perf_counter() - t_start) * 1000, 2)

    return final_results, diagnostics


# --------------------------------------------------
# 7. Main Search & Recommendation Entry Point
# --------------------------------------------------

def search_black_knight(
    user_query: str | Any = None,
    top_k: int = 10,
    parsed_query: Any = None,
    client: Any = None,
    diagnostics: bool = False,
    repo: RetrievalRepository = _REPO,
    architecture: str = "domain_routed",
    trace: bool = False,
    query_id: str | None = None,
    target_ids: list[str] | None = None,
    category: str | None = None,
    domain: str | None = None,
) -> dict[str, Any]:
    """
    Main discovery & recommendation entry point:
    1. Parse natural-language query into BlackKnightQuery schema (or reuse parsed_query).
    2. Route domain-specific filters without cross-domain leakage.
    3. Execute hybrid retrieval per domain according to selected architecture:
       - Architecture A ("all_cross_encoder" / "baseline"): all domains reranked by cross-encoder.
       - Architecture B ("domain_routed" / "routed", default): movie & mixed reranked, anime & book RRF-only.
       - Architecture C ("rrf_only"): pure RRF across all domains.
    4. Aggregate and rank cross-domain items with canonical deduplication.
    5. Return final recommendation payload.
    When trace=True, attaches a complete RetrievalTrace object to response['diagnostics']['trace'].
    """
    t_start = time.perf_counter()

    if isinstance(user_query, BlackKnightQuery) and parsed_query is None:
        parsed_query = user_query
        user_query = user_query.semantic_query or ""
    elif parsed_query is None:
        if not user_query:
            raise ValueError("Either user_query string or parsed_query must be provided.")
        from .query_parser import parse_query
        parsed_query = parse_query(user_query, client=client)

    if not parsed_query.media_types:
        raise ValueError("No media type detected in query.")

    common = parsed_query.common
    domain_queries = parsed_query.domain_queries
    semantic_query = parsed_query.semantic_query
    similar_to = parsed_query.similar_to

    all_domain_results = []
    per_domain_results = {}
    per_domain_diagnostics = {}
    unique_media_types = list(dict.fromkeys(parsed_query.media_types))
    is_mixed = len(unique_media_types) > 1

    # Initialize tracing collector if requested
    trace_obj: RetrievalTrace | None = None
    if trace:
        targets_dict: dict[str, TargetTrackingRecord] = {}
        if target_ids:
            for tid in target_ids:
                m_type = tid.split("_")[0] if "_" in tid else "unknown"
                t_title = tid
                if m_type in SUPPORTED_DOMAINS:
                    try:
                        if m_type not in repo._id_to_index:
                            repo.get_documents_and_ids(m_type)
                        idx = repo._id_to_index[m_type].get(tid)
                        if idx is not None:
                            df_m = repo.get_metadata_df(m_type)
                            t_col = TITLE_FIELDS.get(m_type, "title")
                            t_title = str(df_m.iloc[idx][t_col])
                    except Exception:
                        pass
                targets_dict[tid] = TargetTrackingRecord(
                    target_id=tid,
                    target_title=t_title,
                    media_type=m_type,
                )

        trace_obj = RetrievalTrace(
            query_id=query_id or "adhoc_query",
            query_text=user_query if isinstance(user_query, str) else str(semantic_query or ""),
            domain=domain or (unique_media_types[0] if len(unique_media_types) == 1 else "mixed"),
            category=category or "adhoc",
            architecture=architecture,
            is_absence_query=(len(target_ids) == 0 if target_ids is not None else False),
            media_types=unique_media_types,
            active_filters={
                "common": common.model_dump(exclude_none=True) if hasattr(common, "model_dump") else {},
            },
            target_ids=target_ids or [],
            targets=targets_dict,
        )

    for media_type in unique_media_types:
        # Build strict domain filters without leakage
        filters = {
            "title": common.title,
            "genres_include": common.genres_include,
            "genres_exclude": common.genres_exclude,
            "release_year_min": common.release_year_min,
            "release_year_max": common.release_year_max,
        }

        domain_query = getattr(domain_queries, media_type, None)
        if domain_query is not None:
            if hasattr(domain_query, "model_dump"):
                dom_dump = domain_query.model_dump(exclude_none=True)
            else:
                dom_dump = {k: v for k, v in domain_query.__dict__.items() if v is not None}
            filters.update(dom_dump)

        # Architecture selection:
        if architecture in ("all_cross_encoder", "baseline", "architecture_a"):
            should_rerank = True
        elif architecture == "rrf_only":
            should_rerank = False
        elif is_mixed:
            should_rerank = True
        elif media_type in ("anime", "book"):
            should_rerank = False
        else:
            should_rerank = True

        domain_results, diag = hybrid_retrieve(
            query=semantic_query,
            media_type=media_type,
            filters=filters,
            similar_to=similar_to,
            top_k=top_k,
            rerank=should_rerank,
            repo=repo,
            collect_diagnostics=diagnostics,
            trace_collector=trace_obj,
        )

        all_domain_results.extend(domain_results)
        per_domain_results[media_type] = domain_results
        per_domain_diagnostics[media_type] = diag

    # Sort combined results descending by score, deterministic tie-breaking by ID
    all_domain_results.sort(key=lambda x: (-x["score"], str(x["id"])))

    # Deduplicate results by canonical item ID and canonical anime work identity
    seen_res_ids = set()
    seen_anime_works = set()
    top_results = []
    duplicate_ids = []
    for r in all_domain_results:
        item_id = str(r["id"])
        m_type = r.get("media_type") or (item_id.split("_")[0] if "_" in item_id else "unknown")

        is_dup = (item_id in seen_res_ids)
        if not is_dup and m_type == "anime":
            try:
                if m_type not in repo._id_to_index:
                    repo.get_documents_and_ids(m_type)
                idx = repo._id_to_index[m_type].get(item_id)
                if idx is not None:
                    df_m = repo.get_metadata_df(m_type)
                    row_data = df_m.iloc[idx]
                    norm_t = normalize_title(str(row_data.get("title", "")))
                    ep_val = str(row_data.get("episodes", ""))
                    yr_val = str(row_data.get("release_year", ""))
                    work_key = (norm_t, yr_val, ep_val)
                    if work_key in seen_anime_works:
                        is_dup = True
                    else:
                        seen_anime_works.add(work_key)
            except Exception:
                pass

        if not is_dup:
            seen_res_ids.add(item_id)
            top_results.append(r)
        else:
            duplicate_ids.append(item_id)
        if len(top_results) >= top_k:
            break

    response: dict[str, Any] = {
        "user_query": user_query,
        "parsed_query": parsed_query.model_dump() if hasattr(parsed_query, "model_dump") else str(parsed_query),
        "results": top_results,
        "per_domain_results": per_domain_results,
        "total_results": len(top_results),
    }

    if diagnostics or trace:
        diag_dict: dict[str, Any] = {}
        if diagnostics:
            diag_dict["per_domain"] = per_domain_diagnostics
            diag_dict["total_latency_ms"] = round((time.perf_counter() - t_start) * 1000, 2)
        if trace and trace_obj is not None:
            trace_obj.duplicate_ids_detected = duplicate_ids
            trace_obj.final_count = len(top_results)
            trace_obj.final_candidates = [
                {"id": r["id"], "title": r["title"], "score": r["score"], "rank": r_idx}
                for r_idx, r in enumerate(top_results, start=1)
            ]
            for t in trace_obj.targets.values():
                f_matches = [(r_idx, r["score"]) for r_idx, r in enumerate(top_results, start=1) if r["id"] == t.target_id]
                if f_matches:
                    t.in_final_top10 = True
                    t.final_rank = f_matches[0][0]
                    t.final_score = f_matches[0][1]
                    t.in_final_top5 = (t.final_rank <= 5)
            trace_obj.classify_target_failures()
            trace_obj.total_latency_ms = round((time.perf_counter() - t_start) * 1000, 2)
            diag_dict["trace"] = trace_obj.to_dict()
        response["diagnostics"] = diag_dict

    return response

