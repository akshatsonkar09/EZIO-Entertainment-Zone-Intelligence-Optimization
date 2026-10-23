"""
Tests for Phase 5: Retrieval-Stage Observability and Diagnostics.

Verifies:
1. Exact ranking parity between traced and untraced searches.
2. Tracing completeness across all stages (dense, BM25, RRF, cross-encoder, final).
3. Target progression tracking and failure classification.
4. Explainable metadata filter rejection reasons.
5. Valid JSON serialization of query traces.
6. Support for all three architectures (all_cross_encoder, domain_routed, rrf_only).
"""

import json
import pytest

from project_black_knight.query_schema import BlackKnightQuery, CommonQuery, DomainQueries
from project_black_knight.retrieval import RetrievalRepository, search_black_knight
from project_black_knight.diagnostics import (
    RetrievalTrace,
    TargetTrackingRecord,
    explain_filter_rejection,
)


@pytest.fixture(scope="module")
def shared_repo():
    repo = RetrievalRepository()
    # Pre-warm
    for d in ("movie", "anime", "book"):
        repo.get_metadata_df(d)
        repo.get_documents_and_ids(d)
        repo.get_bm25_index(d)
    repo.get_embedding_model()
    repo.get_reranker_model()
    return repo


def test_traced_untraced_exact_parity(shared_repo):
    """Verifies that enabling tracing does NOT change results, ranking, or scores."""
    queries = [
        BlackKnightQuery(
            media_types=["movie"],
            semantic_query="Christopher Nolan science fiction movies",
            common=CommonQuery(genres_include=["Science Fiction"]),
            domain_queries=DomainQueries(),
        ),
        BlackKnightQuery(
            media_types=["anime"],
            semantic_query="Cyberpunk anime series",
            common=CommonQuery(genres_include=["Cyberpunk"]),
            domain_queries=DomainQueries(),
        ),
        BlackKnightQuery(
            media_types=["book"],
            semantic_query="Fantasy novels with magic",
            common=CommonQuery(genres_include=["Fantasy"]),
            domain_queries=DomainQueries(),
        ),
    ]
    architectures = ["all_cross_encoder", "domain_routed", "rrf_only"]

    for query_obj in queries:
        for arch in architectures:
            res_untraced = search_black_knight(
                parsed_query=query_obj,
                top_k=10,
                repo=shared_repo,
                architecture=arch,
                trace=False,
            )
            res_traced = search_black_knight(
                parsed_query=query_obj,
                top_k=10,
                repo=shared_repo,
                architecture=arch,
                trace=True,
            )

            untraced_results = res_untraced["results"]
            traced_results = res_traced["results"]

            assert len(untraced_results) == len(traced_results), f"Length mismatch for '{query_obj.semantic_query}' on {arch}"
            for r_u, r_t in zip(untraced_results, traced_results):
                assert r_u["id"] == r_t["id"], f"ID mismatch for '{query_obj.semantic_query}' on {arch}: {r_u['id']} vs {r_t['id']}"
                assert r_u["score"] == r_t["score"], f"Score mismatch for '{query_obj.semantic_query}' on {arch}: {r_u['score']} vs {r_t['score']}"
                assert r_u["title"] == r_t["title"], f"Title mismatch for '{query_obj.semantic_query}' on {arch}"


def test_trace_completeness_and_structure(shared_repo):
    """Verifies that all required stage counts, latencies, and candidate lists are populated."""
    res = search_black_knight(
        user_query="Find Inception directed by Christopher Nolan.",
        top_k=10,
        repo=shared_repo,
        architecture="domain_routed",
        trace=True,
        query_id="KI_002",
        target_ids=["movie_96"],
        category="known_item",
        domain="movie",
    )

    assert "diagnostics" in res
    assert "trace" in res["diagnostics"]
    trace = res["diagnostics"]["trace"]

    assert trace["query_id"] == "KI_002"
    assert trace["domain"] == "movie"
    assert trace["architecture"] == "domain_routed"
    assert "movie" in trace["catalog_item_counts"]
    assert trace["catalog_item_counts"]["movie"] > 0
    assert trace["valid_ids_counts"]["movie"] > 0
    assert trace["dense_counts"]["movie"] > 0
    assert trace["bm25_counts"]["movie"] > 0
    assert trace["rrf_counts"]["movie"] > 0
    assert trace["final_count"] > 0

    # Cross encoder is applied for movie in domain_routed
    assert trace["cross_encoder_applied"]["movie"] is True

    # Check stage candidates
    assert len(trace["dense_candidates"]["movie"]) > 0
    assert len(trace["bm25_candidates"]["movie"]) > 0
    assert len(trace["rrf_candidates"]["movie"]) > 0
    assert len(trace["final_candidates"]) > 0

    # Check latencies
    assert "movie_dense" in trace["latencies_ms"]
    assert "movie_bm25" in trace["latencies_ms"]
    assert "movie_rrf" in trace["latencies_ms"]
    assert "movie_cross_encoder" in trace["latencies_ms"]
    assert trace["total_latency_ms"] > 0


def test_target_tracking_and_success_classification(shared_repo):
    """Verifies that a known target item is tracked through stages and classified as success."""
    res = search_black_knight(
        user_query="Find Inception directed by Christopher Nolan.",
        top_k=10,
        repo=shared_repo,
        architecture="domain_routed",
        trace=True,
        query_id="KI_002",
        target_ids=["movie_96"],
    )

    trace = res["diagnostics"]["trace"]
    assert "movie_96" in trace["targets"]
    target = trace["targets"]["movie_96"]

    assert target["in_catalog"] is True
    assert target["passed_metadata_filter"] is True
    assert target["excluded_as_seed"] is False
    assert target["in_final_top10"] is True
    assert target["in_final_top5"] is True
    assert target["failure_category"] == "success_top5"
    assert target["earliest_failure_stage"] == "none"


def test_filter_rejection_explanation():
    """Verifies that explain_filter_rejection accurately identifies failing filter fields."""
    # Year below min
    row1 = {"title": "Old Movie", "release_year": 1990, "genres": "Action"}
    reason1 = explain_filter_rejection(row1, {"release_year_min": 2000}, "movie")
    assert reason1 is not None and "release_year_below_min" in reason1

    # Year above max
    row2 = {"title": "Future Movie", "release_year": 2025, "genres": "Action"}
    reason2 = explain_filter_rejection(row2, {"release_year_max": 2020}, "movie")
    assert reason2 is not None and "release_year_above_max" in reason2

    # Genre excluded
    row3 = {"title": "Romantic Comedy", "release_year": 2015, "genres": "Romance, Comedy"}
    reason3 = explain_filter_rejection(row3, {"genres_exclude": ["Romance"]}, "movie")
    assert reason3 is not None and "genre_excluded" in reason3

    # Director mismatch
    row4 = {"title": "Tenet", "release_year": 2020, "director": "Christopher Nolan"}
    reason4 = explain_filter_rejection(row4, {"director": "Steven Spielberg"}, "movie")
    assert reason4 is not None and "director_mismatch" in reason4

    # Matching row returns None
    reason5 = explain_filter_rejection(row4, {"director": "Christopher Nolan", "release_year_min": 2010}, "movie")
    assert reason5 is None


def test_architecture_cross_encoder_bypass_logging(shared_repo):
    """Verifies that rrf_only records cross_encoder_applied=False and 0 CE latency."""
    res = search_black_knight(
        user_query="Find Inception directed by Christopher Nolan.",
        top_k=10,
        repo=shared_repo,
        architecture="rrf_only",
        trace=True,
        query_id="TEST_RRF",
        target_ids=["movie_96"],
    )

    trace = res["diagnostics"]["trace"]
    assert trace["cross_encoder_applied"]["movie"] is False
    assert trace["latencies_ms"]["movie_cross_encoder"] == 0.0


def test_json_serialization_validity(shared_repo):
    """Verifies that trace dictionaries serialize to valid JSON without NaN or custom objects."""
    res = search_black_knight(
        user_query="Find the anime Death Note.",
        top_k=10,
        repo=shared_repo,
        architecture="domain_routed",
        trace=True,
        query_id="KI_011",
        target_ids=["anime_12"],
    )

    trace_dict = res["diagnostics"]["trace"]
    json_str = json.dumps(trace_dict)
    loaded = json.loads(json_str)

    assert loaded["query_id"] == "KI_011"
    assert "targets" in loaded
    assert "latencies_ms" in loaded
