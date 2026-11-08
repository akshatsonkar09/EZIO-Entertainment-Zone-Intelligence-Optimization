"""
Pre-download and cache Hugging Face embedding and reranking models.
Ensures models exist in local cache prior to server boot, avoiding cold-start latency.
"""
from __future__ import annotations

import logging
import os
import sys
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("preload_models")

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_model_cache_dir() -> str:
    """Resolve shared model cache directory across preload and runtime retrieval."""
    env_dir = os.getenv("HF_HOME") or os.getenv("MODEL_CACHE_DIR")
    if env_dir and env_dir.strip():
        return str(Path(env_dir.strip()).resolve())
    return str((PROJECT_ROOT / "data" / "models").resolve())


def preload_models(cache_dir: str | None = None) -> bool:
    """Download SentenceTransformer and CrossEncoder models to cache."""
    target_cache = cache_dir or get_model_cache_dir()
    logger.info("Preloading models into cache directory: %s", target_cache)

    try:
        from sentence_transformers import SentenceTransformer, CrossEncoder
    except ImportError as e:
        logger.error("sentence-transformers not installed: %s", e)
        return False

    # 1. Embedding Model
    logger.info("Loading / downloading 'all-MiniLM-L6-v2'...")
    t0 = time.time()
    emb_model = SentenceTransformer("all-MiniLM-L6-v2", cache_folder=target_cache)
    test_vec = emb_model.encode(["Sanity test"])
    logger.info("Embedding model verified in %.2fs. Vector shape: %s", time.time() - t0, test_vec.shape)

    # 2. CrossEncoder Model
    logger.info("Loading / downloading 'cross-encoder/ms-marco-MiniLM-L-6-v2'...")
    t0 = time.time()
    rerank_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", cache_folder=target_cache)
    test_score = rerank_model.predict([("query", "passage")])
    logger.info("CrossEncoder model verified in %.2fs. Test score: %s", time.time() - t0, test_score)

    logger.info("All Hugging Face models preloaded and cached successfully.")
    return True


if __name__ == "__main__":
    success = preload_models()
    if not success:
        sys.exit(1)
