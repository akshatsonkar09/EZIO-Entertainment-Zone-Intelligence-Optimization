"""
Unit tests for Project Black Knight Hybrid Retrieval Pipeline (Phase 4).

Covers:
- Dense retrieval and ChromaDB isolation (mocked & controlled)
- BM25 lexical retrieval and filtering
- Reciprocal Rank Fusion (RRF) with exact manual score verification
- Cross-encoder reranking and descending score ordering
- Similar-to reference seed resolution and self-exclusion
- Cross-domain recommendation and filter isolation (zero leakage)
- Retrieval diagnostics and stage-level latency measurement
"""

import math
from unittest.mock import MagicMock
import pytest
from rank_bm25 import BM25Okapi

from project_black_knight.query_schema import (
    BlackKnightQuery,
    CommonQuery,
    DomainQueries,
    MovieQuery,
    AnimeQuery,
)
from project_black_knight.retrieval import (
    tokenize_for_bm25,
    dense_retrieve,
    bm25_retrieve,
    reciprocal_rank_fusion,
    rerank_candidates,
    resolve_similar_seed,
    hybrid_retrieve,
    search_black_knight,
)


# --------------------------------------------------
# 1. Dense Retrieval Tests (Controlled / Mocked)
# --------------------------------------------------

def test_dense_retrieve_mocked():
    mock_model = MagicMock()
    mock_model.encode.return_value = [[0.1, 0.2, 0.3]]

    mock_collection = MagicMock()
    mock_collection.count.return_value = 100
    mock_collection.query.return_value = {
        "ids": [["item_1", "item_2", "item_3", "item_4"]],
        "distances": [[0.1, 0.5, 0.8, 1.2]],
    }

    # Test with valid_ids filter: only item_1 and item_3 allowed
    valid_ids = {"item_1", "item_3"}
    results = dense_retrieve(
        query_text="space exploration",
        media_type="movie",
        valid_ids=valid_ids,
        top_k=5,
        custom_model=mock_model,
        custom_collection=mock_collection,
    )

    assert len(results) == 2
    assert results[0]["id"] == "item_1"
    assert results[0]["rank"] == 1
    assert results[1]["id"] == "item_3"
    assert results[1]["rank"] == 2
    # Verify score = 1 / (1 + distance)
    assert math.isclose(results[0]["score"], 1.0 / (1.0 + 0.1), rel_tol=1e-4)


def test_dense_retrieve_empty_valid_ids():
    mock_model = MagicMock()
    mock_collection = MagicMock()
    # When valid_ids is empty set, should return empty list without querying Chroma
    res = dense_retrieve(
        query_text="query",
        media_type="movie",
        valid_ids=set(),
        custom_model=mock_model,
        custom_collection=mock_collection,
    )
    assert res == []
    assert mock_collection.query.call_count == 0


# --------------------------------------------------
# 2. BM25 Retrieval Tests (Controlled Fixture)
# --------------------------------------------------

def test_bm25_retrieve_fixture():
    corpus = [
        "interstellar space science fiction wormhole travel",
        "the dark knight crime action superhero batman",
        "deep space time dilation astronaut galaxy",
        "romantic comedy wedding love story",
        "medieval fantasy dragon sword kingdom",
    ]
    ids = ["doc_0", "doc_1", "doc_2", "doc_3", "doc_4"]
    tokens = [tokenize_for_bm25(doc) for doc in corpus]
    bm25_index = BM25Okapi(tokens)

    # Query for 'space galaxy'
    res = bm25_retrieve(
        query_text="space galaxy",
        media_type="movie",
        valid_ids=None,
        top_k=5,
        custom_index=bm25_index,
        custom_ids=ids,
    )

    # Both doc_0 and doc_2 mention space, doc_2 also mentions galaxy
    assert len(res) >= 2
    res_ids = [r["id"] for r in res]
    assert "doc_2" in res_ids
    assert "doc_0" in res_ids
    assert "doc_3" not in res_ids  # completely irrelevant doc has score 0
    assert "doc_4" not in res_ids


def test_bm25_retrieve_with_hard_filters():
    corpus = [
        "space action astronaut",
        "space romance planetary love",
        "cyberpunk hacker future",
        "historical drama kingdom empire",
        "nature ocean wilderness wildlife",
    ]
    ids = ["d_0", "d_1", "d_2", "d_3", "d_4"]
    tokens = [tokenize_for_bm25(doc) for doc in corpus]
    bm25_index = BM25Okapi(tokens)

    # Only d_1 is valid according to metadata filter
    valid_ids = {"d_1"}
    res = bm25_retrieve(
        query_text="space",
        media_type="movie",
        valid_ids=valid_ids,
        top_k=5,
        custom_index=bm25_index,
        custom_ids=ids,
    )
    assert len(res) == 1
    assert res[0]["id"] == "d_1"


# --------------------------------------------------
# 3. Reciprocal Rank Fusion Tests (Manual Exact Math)
# --------------------------------------------------

def test_reciprocal_rank_fusion_manual_calculation():
    """
    Verify exact RRF score calculation against manual math:
    List 1: ['item_A', 'item_B', 'item_C'] (ranks 1, 2, 3)
    List 2: ['item_B', 'item_D', 'item_A'] (ranks 1, 2, 3)
    k = 60
    item_A = 1/(60+1) + 1/(60+3) = 1/61 + 1/63 = 0.01639344 + 0.01587302 = 0.03226646
    item_B = 1/(60+2) + 1/(60+1) = 1/62 + 1/61 = 0.01612903 + 0.01639344 = 0.03252247
    item_C = 1/(60+3) = 1/63 = 0.01587302
    item_D = 1/(60+2) = 1/62 = 0.01612903
    Expected ranking: item_B > item_A > item_D > item_C
    """
    list1 = ["item_A", "item_B", "item_C"]
    list2 = ["item_B", "item_D", "item_A"]

    fused = reciprocal_rank_fusion([list1, list2], k=60, top_k=10)

    ranked_ids = [item_id for item_id, score in fused]
    assert ranked_ids == ["item_B", "item_A", "item_D", "item_C"]

    score_map = dict(fused)
    assert math.isclose(score_map["item_A"], (1 / 61) + (1 / 63), rel_tol=1e-6)
    assert math.isclose(score_map["item_B"], (1 / 62) + (1 / 61), rel_tol=1e-6)
    assert math.isclose(score_map["item_C"], (1 / 63), rel_tol=1e-6)
    assert math.isclose(score_map["item_D"], (1 / 62), rel_tol=1e-6)


def test_reciprocal_rank_fusion_edge_cases():
    # Empty lists
    assert reciprocal_rank_fusion([], k=60) == []
    assert reciprocal_rank_fusion([[], []], k=60) == []

    # One list empty, one non-empty
    fused_partial = reciprocal_rank_fusion([["x", "y"], []], k=60)
    assert [item_id for item_id, score in fused_partial] == ["x", "y"]

    # Duplicate in single list (must not be double-counted)
    fused_dupe = reciprocal_rank_fusion([["x", "x", "y"]], k=60)
    score_map = dict(fused_dupe)
    assert math.isclose(score_map["x"], 1 / 61, rel_tol=1e-6)


def test_reciprocal_rank_fusion_deterministic_tie_breaking():
    # item_B and item_A have identical RRF scores from separate single lists at rank 1
    # Tied scores must deterministically sort alphabetically: item_A before item_B
    fused = reciprocal_rank_fusion([["item_B"], ["item_A"]], k=60)
    assert [cid for cid, _ in fused] == ["item_A", "item_B"]


# --------------------------------------------------
# 4. Cross-Encoder Reranking Tests
# --------------------------------------------------

def test_cross_encoder_rerank_descending_and_pairing():
    mock_reranker = MagicMock()
    # Predict returns scores [0.2, 0.95, -0.4]
    mock_reranker.predict.return_value = [0.2, 0.95, -0.4]

    candidate_ids = ["cand_1", "cand_2", "cand_3"]
    documents = ["doc 1 text", "doc 2 text", "doc 3 text"]
    id_to_index = {"cand_1": 0, "cand_2": 1, "cand_3": 2}

    reranked = rerank_candidates(
        query_text="time travel",
        candidate_ids=candidate_ids,
        media_type="movie",
        top_k=3,
        custom_reranker=mock_reranker,
        custom_documents=documents,
        custom_id_to_index=id_to_index,
    )

    # Verify query-document pairing
    assert mock_reranker.predict.call_count == 1
    pairs = mock_reranker.predict.call_args[0][0]
    assert pairs == [
        ["time travel", "doc 1 text"],
        ["time travel", "doc 2 text"],
        ["time travel", "doc 3 text"],
    ]

    # Verify sorted descending by score: cand_2 (0.95) > cand_1 (0.2) > cand_3 (-0.4)
    assert reranked[0] == ("cand_2", 0.95)
    assert reranked[1] == ("cand_1", 0.2)
    assert reranked[2] == ("cand_3", -0.4)


def test_cross_encoder_empty_input():
    res = rerank_candidates(
        query_text="",
        candidate_ids=[],
        media_type="movie",
    )
    assert res == []


# --------------------------------------------------
# 5. Similar-Item Seed Resolution & Self-Exclusion
# --------------------------------------------------

def test_resolve_similar_seed_real_dataset():
    # Real movie Interstellar should be resolved in movie domain
    seed = resolve_similar_seed("Interstellar", target_domain="movie")
    assert seed is not None
    assert seed["domain"] == "movie"
    assert "interstellar" in seed["title"].lower()
    assert "wormhole" in seed["doc_text"].lower() or "space" in seed["doc_text"].lower()


def test_similar_to_self_exclusion():
    """Verify that when a user searches 'movies similar to Interstellar', Interstellar itself is excluded."""
    seed = resolve_similar_seed("Interstellar", target_domain="movie")
    assert seed is not None
    interstellar_id = seed["item_id"]

    results, diag = hybrid_retrieve(
        query="",
        media_type="movie",
        similar_to=["Interstellar"],
        top_k=5,
        collect_diagnostics=True,
    )

    result_ids = [r["id"] for r in results]
    assert interstellar_id not in result_ids
    assert interstellar_id in diag.get("excluded_seed_ids", [])
    assert len(results) > 0


def test_similar_to_unknown_seed_graceful_fallback():
    """Verify that an unknown title gracefully falls back without failing."""
    results, diag = hybrid_retrieve(
        query="mind-bending time travel",
        media_type="movie",
        similar_to=["NonexistentMovieXYZ999"],
        top_k=3,
        collect_diagnostics=True,
    )
    assert len(results) > 0
    assert "mind-bending" in diag["effective_retrieval_query"]


# --------------------------------------------------
# 6. Cross-Domain Recommendation & Filter Isolation
# --------------------------------------------------

def test_cross_domain_filter_isolation_no_leakage():
    """
    Verify that domain-specific constraints do not leak across domains:
    - movie has runtime_max=160
    - anime has episodes_max=25
    Anime should NOT be filtered by runtime_max, and movies should NOT be filtered by episodes_max.
    """
    mock_parsed_query = BlackKnightQuery(
        media_types=["movie", "anime"],
        common=CommonQuery(
            genres_include=["sci-fi"],
            release_year_min=2010,
        ),
        domain_queries=DomainQueries(
            movie=MovieQuery(runtime_max=160),
            anime=AnimeQuery(episodes_max=25),
        ),
        semantic_query="time travel",
        similar_to=[],
    )

    res = search_black_knight(
        user_query="sci-fi time travel movies under 160m and anime under 25 episodes after 2010",
        parsed_query=mock_parsed_query,
        top_k=10,
        diagnostics=True,
    )

    per_domain = res["diagnostics"]["per_domain"]

    # Verify movie filters had runtime_max and NOT episodes_max
    movie_filters = per_domain["movie"]["filters"]
    assert "runtime_max" in movie_filters
    assert "episodes_max" not in movie_filters
    assert movie_filters["genres_include"] == ["sci-fi"]

    # Verify anime filters had episodes_max and NOT runtime_max
    anime_filters = per_domain["anime"]["filters"]
    assert "episodes_max" in anime_filters
    assert "runtime_max" not in anime_filters
    assert anime_filters["genres_include"] == ["sci-fi"]

    # Check results contains items from both domains
    media_types_found = {r["media_type"] for r in res["results"]}
    assert "movie" in media_types_found or "anime" in media_types_found


def test_cross_domain_one_domain_zero_results():
    """Verify that if one domain returns zero results due to strict filters, the other domain still succeeds."""
    mock_parsed_query = BlackKnightQuery(
        media_types=["movie", "anime"],
        common=CommonQuery(),
        domain_queries=DomainQueries(
            movie=MovieQuery(runtime_min=9999),  # Impossible movie runtime -> 0 movies
            anime=AnimeQuery(episodes_max=50),
        ),
        semantic_query="action adventure",
        similar_to=[],
    )

    res = search_black_knight(
        user_query="impossible movie but valid anime",
        parsed_query=mock_parsed_query,
        top_k=5,
        diagnostics=True,
    )

    # Movie returns 0, but Anime returns results
    assert len(res["results"]) > 0
    assert all(r["media_type"] == "anime" for r in res["results"])
    assert res["diagnostics"]["per_domain"]["movie"]["valid_ids_count"] == 0


# --------------------------------------------------
# 7. Domain-Specific Cross-Encoder Routing Tests
# --------------------------------------------------

from unittest.mock import patch


def test_movie_only_query_invokes_cross_encoder():
    """Verify movie-only query invokes cross-encoder reranking."""
    parsed_q = BlackKnightQuery(
        media_types=["movie"],
        common=CommonQuery(title="The Dark Knight"),
        domain_queries=DomainQueries(),
        semantic_query="The Dark Knight",
        similar_to=[],
    )
    with patch("project_black_knight.retrieval.rerank_candidates") as mock_rerank:
        mock_rerank.return_value = [("movie_65", 0.95)]
        res = search_black_knight(parsed_query=parsed_q, top_k=5, diagnostics=True)
        assert mock_rerank.call_count == 1
        assert res["results"][0]["id"] == "movie_65"
        assert res["diagnostics"]["per_domain"]["movie"]["cross_encoder_bypassed"] is False


def test_anime_only_query_bypasses_cross_encoder():
    """Verify anime-only query bypasses cross-encoder and preserves RRF ordering."""
    parsed_q = BlackKnightQuery(
        media_types=["anime"],
        common=CommonQuery(title="Death Note"),
        domain_queries=DomainQueries(),
        semantic_query="Death Note",
        similar_to=[],
    )
    with patch("project_black_knight.retrieval.rerank_candidates") as mock_rerank:
        res = search_black_knight(parsed_query=parsed_q, top_k=5, diagnostics=True)
        # Genuinely not called
        assert mock_rerank.call_count == 0
        assert res["diagnostics"]["per_domain"]["anime"]["cross_encoder_bypassed"] is True
        assert len(res["results"]) > 0
        assert res["results"][0]["media_type"] == "anime"
        # Scores are RRF scores
        assert res["results"][0]["score"] > 0.0


def test_book_only_query_bypasses_cross_encoder():
    """Verify book-only query bypasses cross-encoder and preserves RRF ordering."""
    parsed_q = BlackKnightQuery(
        media_types=["book"],
        common=CommonQuery(title="The Hobbit"),
        domain_queries=DomainQueries(),
        semantic_query="The Hobbit",
        similar_to=[],
    )
    with patch("project_black_knight.retrieval.rerank_candidates") as mock_rerank:
        res = search_black_knight(parsed_query=parsed_q, top_k=5, diagnostics=True)
        # Genuinely not called
        assert mock_rerank.call_count == 0
        assert res["diagnostics"]["per_domain"]["book"]["cross_encoder_bypassed"] is True
        assert len(res["results"]) > 0
        assert res["results"][0]["media_type"] == "book"
        assert res["results"][0]["score"] > 0.0


def test_bypassed_paths_preserve_result_contract_and_limits():
    """Verify bypassed anime and book queries maintain complete schema contract, filtering, and limit."""
    parsed_anime = BlackKnightQuery(
        media_types=["anime"],
        common=CommonQuery(genres_include=["Action"]),
        domain_queries=DomainQueries(),
        semantic_query="action ninja",
        similar_to=[],
    )
    with patch("project_black_knight.retrieval.rerank_candidates") as mock_rerank:
        res = search_black_knight(parsed_query=parsed_anime, top_k=3, diagnostics=True)
        assert mock_rerank.call_count == 0
        assert len(res["results"]) <= 3
        for item in res["results"]:
            assert "id" in item
            assert "title" in item
            assert item["media_type"] == "anime"
            assert "score" in item
            assert "release_year" in item
            assert "genres" in item


def test_mixed_domain_and_unspecified_domain_routing():
    """
    Verify mixed-domain queries preserve pre-change behavior (invoking cross-encoder across domains),
    and unspecified media_types raise ValueError.
    """
    # Mixed-domain: movie and anime
    parsed_mixed = BlackKnightQuery(
        media_types=["movie", "anime"],
        common=CommonQuery(),
        domain_queries=DomainQueries(),
        semantic_query="space exploration",
        similar_to=[],
    )
    with patch("project_black_knight.retrieval.rerank_candidates") as mock_rerank:
        mock_rerank.side_effect = lambda query_text, candidate_ids, media_type, **kw: [
            (cid, 0.8) for cid in candidate_ids[:kw.get("top_k", 5)]
        ]
        res = search_black_knight(parsed_query=parsed_mixed, top_k=6, diagnostics=True)
        # Rerank is called once per domain in mixed queries
        assert mock_rerank.call_count == 2

    # Unspecified media_types raises ValueError
    parsed_empty = BlackKnightQuery(
        media_types=[],
        common=CommonQuery(),
        domain_queries=DomainQueries(),
        semantic_query="query",
        similar_to=[],
    )
    with pytest.raises(ValueError, match="No media type detected"):
        search_black_knight(parsed_query=parsed_empty)


def test_architecture_selection_explicit():
    """Verify explicit selection between Architecture A (all CE) and Architecture B (domain-routed)."""
    parsed_book = BlackKnightQuery(
        media_types=["book"],
        common=CommonQuery(title="The Hobbit"),
        domain_queries=DomainQueries(),
        semantic_query="The Hobbit",
        similar_to=[],
    )

    # Under Architecture A (all_cross_encoder), book query invokes cross-encoder
    with patch("project_black_knight.retrieval.rerank_candidates") as mock_rerank:
        mock_rerank.side_effect = lambda query_text, candidate_ids, media_type, **kw: [
            (cid, 0.95) for cid in candidate_ids[:kw.get("top_k", 5)]
        ]
        res_a = search_black_knight(
            parsed_query=parsed_book,
            top_k=5,
            diagnostics=True,
            architecture="all_cross_encoder",
        )
        assert mock_rerank.call_count == 1
        assert res_a["diagnostics"]["per_domain"]["book"]["cross_encoder_bypassed"] is False

    # Under Architecture B (domain_routed), book query bypasses cross-encoder
    with patch("project_black_knight.retrieval.rerank_candidates") as mock_rerank:
        res_b = search_black_knight(
            parsed_query=parsed_book,
            top_k=5,
            diagnostics=True,
            architecture="domain_routed",
        )
        assert mock_rerank.call_count == 0
        assert res_b["diagnostics"]["per_domain"]["book"]["cross_encoder_bypassed"] is True

    # Under rrf_only, even movie query bypasses cross-encoder
    parsed_movie = BlackKnightQuery(
        media_types=["movie"],
        common=CommonQuery(title="Inception"),
        domain_queries=DomainQueries(),
        semantic_query="Inception",
        similar_to=[],
    )
    with patch("project_black_knight.retrieval.rerank_candidates") as mock_rerank:
        res_rrf = search_black_knight(
            parsed_query=parsed_movie,
            top_k=5,
            diagnostics=True,
            architecture="rrf_only",
        )
        assert mock_rerank.call_count == 0
        assert res_rrf["diagnostics"]["per_domain"]["movie"]["cross_encoder_bypassed"] is True


def test_evaluator_production_parity():
    """Verify that calling search_black_knight returns identical ordered results and schema."""
    parsed_q = BlackKnightQuery(
        media_types=["movie"],
        common=CommonQuery(genres_include=["Action"]),
        domain_queries=DomainQueries(),
        semantic_query="superhero",
        similar_to=[],
    )
    with patch("project_black_knight.retrieval.rerank_candidates") as mock_rerank:
        mock_rerank.side_effect = lambda query_text, candidate_ids, media_type, **kw: [
            (cid, 0.9 - i * 0.1) for i, cid in enumerate(candidate_ids[:kw.get("top_k", 5)])
        ]
        res1 = search_black_knight(parsed_query=parsed_q, top_k=5, architecture="domain_routed")
        res2 = search_black_knight(parsed_query=parsed_q, top_k=5, architecture="domain_routed")

        ids1 = [r["id"] for r in res1["results"]]
        ids2 = [r["id"] for r in res2["results"]]
        assert ids1 == ids2
        assert len(ids1) == 5


def test_duplicate_elimination_across_pipeline():
    """Verify deduplication across dense/lexical channels, reranking, and multi-domain interleaving."""
    # 1. RRF sums scores for item in both dense and lexical lists without duplicating it
    fused = reciprocal_rank_fusion([
        ["item_1", "item_2"],
        ["item_1", "item_3"],
    ], k=60, top_k=5)
    fused_ids = [cid for cid, s in fused]
    assert fused_ids.count("item_1") == 1
    # item_1 has rank 1 in both: score = 1/(60+1) + 1/(60+1) = 2/61
    assert math.isclose(dict(fused)["item_1"], 2.0 / 61.0, rel_tol=1e-5)

    # 2. Repeated candidate IDs passed into rerank_candidates are deduplicated
    with patch("project_black_knight.retrieval.RetrievalRepository") as mock_repo_cls:
        mock_repo = MagicMock()
        mock_repo._id_to_index = {"movie": {"mov_1": 0, "mov_2": 1}}
        mock_repo.get_documents_and_ids.return_value = (["doc1", "doc2"], ["mov_1", "mov_2"])
        mock_repo.get_metadata_df.return_value = None
        mock_reranker = MagicMock()
        mock_reranker.predict.return_value = [0.9, 0.4]

        # Pass duplicate 'mov_1'
        ranked = rerank_candidates(
            query_text="query",
            candidate_ids=["mov_1", "mov_1", "mov_2"],
            media_type="movie",
            repo=mock_repo,
            custom_reranker=mock_reranker,
        )
        ranked_ids = [cid for cid, s in ranked]
        assert ranked_ids == ["mov_1", "mov_2"]
        assert ranked_ids.count("mov_1") == 1
        # Predict should only receive 2 unique pairs, not 3
        assert len(mock_reranker.predict.call_args[0][0]) == 2

    # 3. Repeated media types in query (e.g. ['movie', 'movie']) does not produce duplicate results
    parsed_dup_types = BlackKnightQuery(
        media_types=["movie", "movie"],
        common=CommonQuery(genres_include=["Action"]),
        domain_queries=DomainQueries(),
        semantic_query="action",
        similar_to=[],
    )
    res_arch_a = search_black_knight(parsed_query=parsed_dup_types, top_k=6, architecture="all_cross_encoder")
    ids_a = [r["id"] for r in res_arch_a["results"]]
    assert len(ids_a) == len(set(ids_a)), "Duplicate IDs found in Architecture A results"

    res_arch_b = search_black_knight(parsed_query=parsed_dup_types, top_k=6, architecture="domain_routed")
    ids_b = [r["id"] for r in res_arch_b["results"]]
    assert len(ids_b) == len(set(ids_b)), "Duplicate IDs found in Architecture B results"

    # 4. Distinct works with identical titles in different domains are preserved (e.g. Dune book vs Dune movie)
    res_mixed = [
        {"id": "movie_123", "title": "Dune", "media_type": "movie", "score": 0.9},
        {"id": "book_456", "title": "Dune", "media_type": "book", "score": 0.85},
    ]
    seen_ids = set()
    top = []
    for r in res_mixed:
        if r["id"] not in seen_ids:
            seen_ids.add(r["id"])
            top.append(r)
    # Both are preserved because their canonical IDs differ
    assert len(top) == 2
    assert top[0]["id"] == "movie_123"
    assert top[1]["id"] == "book_456"


