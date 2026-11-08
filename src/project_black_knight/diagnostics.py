"""
Project Black Knight — Retrieval Diagnostics & Stage-Level Observability (Phase 5).

Provides non-invasive, opt-in intermediate stage tracing for hybrid retrieval:
- Tracks candidates and known relevant targets across:
  1. Metadata filtering (and seed exclusion)
  2. Dense retrieval (ChromaDB)
  3. Lexical retrieval (BM25)
  4. Reciprocal Rank Fusion (RRF)
  5. Neural Cross-Encoder Reranking
  6. Multi-domain aggregation and canonical deduplication
- Diagnoses failure points (earliest stage of failure and root cause evidence).
- Preserves 100% parity with production retrieval.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass, field
from typing import Any

import pandas as pd

from .metadata_filter import (
    clean_isbn_str,
    coerce_numeric,
    is_bypassed_genre_filter,
    match_entity,
    normalize_text_match,
    match_genre,
)


def explain_filter_rejection(
    row: dict[str, Any],
    filters: dict[str, Any],
    media_type: str,
) -> str | None:
    """
    Evaluates a catalog row against active filters and returns the exact reason
    if rejected, or None if the row passes.
    """
    if not filters:
        return None

    def get_val(col_name: str) -> Any:
        if col_name in row and pd.notna(row[col_name]):
            return row[col_name]
        return None

    # 1. Title
    filter_title = filters.get("title")
    if filter_title:
        row_title = str(get_val("title") or "")
        if not row_title or not normalize_text_match(filter_title, row_title):
            return f"title_mismatch: '{row_title}' != '{filter_title}'"

    # 2. Release Year
    year_val = coerce_numeric(get_val("release_year"))
    year_min = coerce_numeric(filters.get("release_year_min") or filters.get("year_min"))
    year_max = coerce_numeric(filters.get("release_year_max") or filters.get("year_max"))
    if year_min is not None or year_max is not None:
        if year_val is None:
            return "release_year_missing_or_invalid"
        if year_min is not None and year_val < year_min:
            return f"release_year_below_min: {year_val} < {year_min}"
        if year_max is not None and year_val > year_max:
            return f"release_year_above_max: {year_val} > {year_max}"

    # 3. Genres Include
    raw_genres = get_val("genres")
    row_genres = str(raw_genres) if raw_genres is not None and not (isinstance(raw_genres, float) and pd.isna(raw_genres)) else ""
    genres_include = filters.get("genres_include") or filters.get("genres") or []
    if isinstance(genres_include, str):
        genres_include = [genres_include]

    for req_g in genres_include:
        if is_bypassed_genre_filter(req_g, media_type):
            continue
        if not row_genres:
            return f"genres_empty: required '{req_g}'"
        if not match_genre(req_g, row_genres, media_type=media_type):
            return f"genre_not_matched: '{req_g}' not in '{row_genres[:40]}'"

    # 4. Genres Exclude
    genres_exclude = filters.get("genres_exclude") or []
    if isinstance(genres_exclude, str):
        genres_exclude = [genres_exclude]
    if genres_exclude and row_genres:
        for exc_g in genres_exclude:
            if is_bypassed_genre_filter(exc_g, media_type):
                continue
            if match_genre(exc_g, row_genres, media_type=media_type):
                return f"genre_excluded: contains '{exc_g}'"
    for exc_g in genres_exclude:
        exc_norm = exc_g.strip().lower()
        exc_targets = DEFAULT_TARGETS.get(exc_norm, [exc_norm])
        if any(check_boundary_match(t, row_genres_raw) for t in exc_targets):
            return f"genre_excluded: contains '{exc_g}'"

    # 5. Domain: Movie
    if media_type == "movie":
        runtime_min = coerce_numeric(filters.get("runtime_min"))
        runtime_max = coerce_numeric(filters.get("runtime_max"))
        if runtime_min is not None or runtime_max is not None:
            runtime_val = coerce_numeric(get_val("runtime"))
            if runtime_val is None:
                return "runtime_missing"
            if runtime_min is not None and runtime_val < runtime_min:
                return f"runtime_below_min: {runtime_val} < {runtime_min}"
            if runtime_max is not None and runtime_val > runtime_max:
                return f"runtime_above_max: {runtime_val} > {runtime_max}"

        directors = filters.get("director") or []
        if isinstance(directors, str):
            directors = [directors]
        if directors:
            row_dir = str(get_val("director") or "")
            if not row_dir or not any(match_entity(d, row_dir) for d in directors):
                return f"director_mismatch: required {directors}, found '{row_dir}'"

        cast = filters.get("cast") or []
        if isinstance(cast, str):
            cast = [cast]
        if cast:
            row_cast = str(get_val("cast") or "")
            if not row_cast or not any(match_entity(c, row_cast) for c in cast):
                return f"cast_mismatch: required {cast}, found '{row_cast[:40]}'"

    # 6. Domain: Anime
    elif media_type == "anime":
        ep_min = coerce_numeric(filters.get("episodes_min"))
        ep_max = coerce_numeric(filters.get("episodes_max"))
        if ep_min is not None or ep_max is not None:
            ep_val = coerce_numeric(get_val("episodes"))
            if ep_val is None:
                return "episodes_missing"
            if ep_min is not None and ep_val < ep_min:
                return f"episodes_below_min: {ep_val} < {ep_min}"
            if ep_max is not None and ep_val > ep_max:
                return f"episodes_above_max: {ep_val} > {ep_max}"

        rating_min = coerce_numeric(filters.get("rating_min"))
        rating_max = coerce_numeric(filters.get("rating_max"))
        if rating_min is not None or rating_max is not None:
            rating_val = coerce_numeric(get_val("rating"))
            if rating_val is None:
                return "rating_missing"
            if rating_min is not None and rating_val < rating_min:
                return f"rating_below_min: {rating_val} < {rating_min}"
            if rating_max is not None and rating_val > rating_max:
                return f"rating_above_max: {rating_val} > {rating_max}"

    # 7. Domain: Book
    elif media_type == "book":
        rating_min = coerce_numeric(filters.get("rating_min"))
        rating_max = coerce_numeric(filters.get("rating_max"))
        if rating_min is not None or rating_max is not None:
            rating_val = coerce_numeric(get_val("rating"))
            if rating_val is None:
                return "rating_missing"
            if rating_min is not None and rating_val < rating_min:
                return f"rating_below_min: {rating_val} < {rating_min}"
            if rating_max is not None and rating_val > rating_max:
                return f"rating_above_max: {rating_val} > {rating_max}"

        pages_min = coerce_numeric(filters.get("pages_min"))
        pages_max = coerce_numeric(filters.get("pages_max"))
        if pages_min is not None or pages_max is not None:
            pages_val = coerce_numeric(get_val("pages"))
            if pages_val is None:
                return "pages_missing"
            if pages_min is not None and pages_val < pages_min:
                return f"pages_below_min: {pages_val} < {pages_min}"
            if pages_max is not None and pages_val > pages_max:
                return f"pages_above_max: {pages_val} > {pages_max}"

        authors = filters.get("author") or []
        if isinstance(authors, str):
            authors = [authors]
        if authors:
            row_author = str(get_val("author") or "")
            if not row_author or not any(match_entity(a, row_author) for a in authors):
                return f"author_mismatch: required {authors}, found '{row_author}'"

    return None


@dataclass
class TargetTrackingRecord:
    """Tracks a single ground-truth target item through retrieval stages."""
    target_id: str
    target_title: str
    media_type: str
    in_catalog: bool = True
    passed_metadata_filter: bool = True
    filter_rejection_reason: str | None = None
    excluded_as_seed: bool = False
    dense_retrieved: bool = False
    dense_rank: int | None = None
    dense_score: float | None = None
    bm25_retrieved: bool = False
    bm25_rank: int | None = None
    bm25_score: float | None = None
    rrf_survived: bool = False
    rrf_rank: int | None = None
    rrf_score: float | None = None
    ce_reranked: bool = False
    ce_rank: int | None = None
    ce_score: float | None = None
    in_final_top10: bool = False
    final_rank: int | None = None
    final_score: float | None = None
    in_final_top5: bool = False
    earliest_failure_stage: str | None = None
    failure_category: str | None = None
    failure_evidence: str | None = None


@dataclass
class StageCandidateRecord:
    """Lightweight representation of a candidate at an intermediate stage."""
    item_id: str
    title: str
    rank: int
    score: float


@dataclass
class RetrievalTrace:
    """Comprehensive diagnostic trace for a single query execution."""
    query_id: str
    query_text: str
    domain: str
    category: str
    architecture: str
    is_absence_query: bool
    media_types: list[str]
    active_filters: dict[str, Any]
    target_ids: list[str] = field(default_factory=list)
    targets: dict[str, TargetTrackingRecord] = field(default_factory=dict)
    
    # Stage counts
    catalog_item_counts: dict[str, int] = field(default_factory=dict)
    valid_ids_counts: dict[str, int] = field(default_factory=dict)
    dense_counts: dict[str, int] = field(default_factory=dict)
    bm25_counts: dict[str, int] = field(default_factory=dict)
    rrf_counts: dict[str, int] = field(default_factory=dict)
    reranked_counts: dict[str, int] = field(default_factory=dict)
    final_count: int = 0
    
    # Candidate lists per stage (top candidates for inspection)
    dense_candidates: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    bm25_candidates: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    rrf_candidates: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    reranked_candidates: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    final_candidates: list[dict[str, Any]] = field(default_factory=list)
    
    # Deduplication and filtering
    duplicate_ids_detected: list[str] = field(default_factory=list)
    excluded_seed_ids: list[str] = field(default_factory=list)
    cross_encoder_applied: dict[str, bool] = field(default_factory=dict)
    
    # Stage-level latencies in ms
    latencies_ms: dict[str, float] = field(default_factory=dict)
    total_latency_ms: float = 0.0

    def classify_target_failures(self) -> None:
        """Classify failure causes for each target based on observed stage evidence."""
        if self.is_absence_query:
            # Absence query: expect final_count == 0
            if self.final_count > 0:
                t_rec = TargetTrackingRecord(
                    target_id="ABSENCE_QUERY_TARGET",
                    target_title="NO_EXPECTED_MATCH",
                    media_type=self.domain,
                    in_final_top10=True,
                    earliest_failure_stage="final_results",
                    failure_category="absence_false_acceptance",
                    failure_evidence=f"Expected 0 results for absence query, but retrieved {self.final_count} candidates.",
                )
                self.targets["ABSENCE_QUERY_TARGET"] = t_rec
            return

        for tid, t in self.targets.items():
            # 1. Did target succeed in top 5 / 10?
            if t.in_final_top5:
                t.earliest_failure_stage = "none"
                t.failure_category = "success_top5"
                t.failure_evidence = f"Target {tid} ranked #{t.final_rank} (score: {t.final_score})."
                continue
            elif t.in_final_top10:
                t.earliest_failure_stage = "final_cutoff_top5"
                t.failure_category = "rank_cutoff_top5"
                t.failure_evidence = f"Target {tid} achieved top-10 rank #{t.final_rank} but missed top-5 cutoff."
                continue

            # 2. Hard filter failure
            if not t.passed_metadata_filter:
                t.earliest_failure_stage = "metadata_filtering"
                t.failure_category = "metadata_filter_rejection"
                t.failure_evidence = f"Target {tid} rejected by metadata filter: {t.filter_rejection_reason or 'unknown'}."
                continue

            # 3. Seed exclusion
            if t.excluded_as_seed:
                t.earliest_failure_stage = "seed_exclusion"
                t.failure_category = "seed_self_exclusion"
                t.failure_evidence = f"Target {tid} was specified as a reference seed and excluded from recommendations."
                continue

            # 4. Dense & BM25 first-stage retrieval
            if not t.dense_retrieved and not t.bm25_retrieved:
                t.earliest_failure_stage = "first_stage_retrieval"
                t.failure_category = "dense_and_bm25_miss"
                t.failure_evidence = f"Target {tid} missed by both Dense retrieval and BM25 lexical search (candidate_k=60)."
                continue
            elif not t.dense_retrieved:
                t.earliest_failure_stage = "dense_retrieval"
                t.failure_category = "dense_only_miss"
                t.failure_evidence = f"Target {tid} missed by Dense retrieval, but found by BM25 (rank #{t.bm25_rank})."
            elif not t.bm25_retrieved:
                t.earliest_failure_stage = "bm25_retrieval"
                t.failure_category = "bm25_only_miss"
                t.failure_evidence = f"Target {tid} missed by BM25, but found by Dense retrieval (rank #{t.dense_rank})."

            # 5. RRF Fusion
            if not t.rrf_survived:
                t.earliest_failure_stage = "rrf_fusion"
                t.failure_category = "rrf_fusion_drop"
                t.failure_evidence = (
                    f"Target {tid} was retrieved (Dense rank: {t.dense_rank}, BM25 rank: {t.bm25_rank}) "
                    f"but was pushed below top 60 during RRF fusion."
                )
                continue

            # 6. Cross-Encoder Demotion
            ce_applied = self.cross_encoder_applied.get(t.media_type, False)
            if ce_applied and t.rrf_rank is not None and t.rrf_rank <= 10 and (t.ce_rank is None or t.ce_rank > 10):
                t.earliest_failure_stage = "cross_encoder_rerank"
                t.failure_category = "cross_encoder_demotion"
                t.failure_evidence = (
                    f"Target {tid} was rank #{t.rrf_rank} after RRF fusion, but cross-encoder "
                    f"demoted it to rank #{t.ce_rank} (score: {t.ce_score})."
                )
                continue

            # 7. Rank Cutoff (Survives RRF/CE, but rank 11-60)
            best_rank = t.ce_rank if (ce_applied and t.ce_rank is not None) else t.rrf_rank
            t.earliest_failure_stage = "final_cutoff_top10"
            t.failure_category = "rank_cutoff_top10"
            t.failure_evidence = (
                f"Target {tid} survived fusion and reranking at rank #{best_rank}, "
                f"but fell outside final top-10 cutoff."
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert trace to a JSON-serializable dictionary."""
        d = asdict(self)
        return d
