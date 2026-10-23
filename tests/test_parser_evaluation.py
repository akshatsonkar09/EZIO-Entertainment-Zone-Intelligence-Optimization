"""
Unit tests for query parser evaluation, mock API responses, schema validation,
retry/fallback behaviors, and evaluation cache infrastructure.
"""

import json
import pytest
from unittest.mock import MagicMock
from groq import RateLimitError

from project_black_knight.query_schema import (
    BlackKnightQuery,
    CommonQuery,
    DomainQueries,
    MovieQuery,
)
from project_black_knight.query_parser import parse_query, MODELS_TO_TRY


def _make_mock_response(content: str):
    """Helper to mock a Groq chat completion response."""
    choice = MagicMock()
    choice.message.content = content
    response = MagicMock()
    response.choices = [choice]
    return response


def test_parse_query_success_mocked():
    """Test successful parse with mocked Groq client."""
    mock_client = MagicMock()
    valid_payload = json.dumps({
        "media_types": ["movie"],
        "common": {
            "title": "Interstellar",
            "genres_include": ["sci-fi"],
            "genres_exclude": [],
            "release_year_min": 2014,
            "release_year_max": None,
        },
        "domain_queries": {
            "movie": {
                "production_companies": [],
                "cast": ["Matthew McConaughey"],
                "director": ["Christopher Nolan"],
                "revenue_min": None,
                "runtime_min": 100,
                "runtime_max": 180,
            },
            "anime": None,
            "book": None,
        },
        "semantic_query": "deep space exploration",
        "similar_to": ["Contact"],
    })
    mock_client.chat.completions.create.return_value = _make_mock_response(valid_payload)

    result = parse_query("find space movies like Contact", client=mock_client)

    assert isinstance(result, BlackKnightQuery)
    assert result.media_types == ["movie"]
    assert result.common.title == "Interstellar"
    assert result.domain_queries.movie.director == ["Christopher Nolan"]
    assert result.semantic_query == "deep space exploration"
    assert result.similar_to == ["Contact"]
    assert mock_client.chat.completions.create.call_count == 1


def test_parse_query_missing_optional_fields_mocked():
    """Test parse when optional fields are null or default in the model response."""
    mock_client = MagicMock()
    minimal_payload = json.dumps({
        "media_types": ["anime"],
        "common": {
            "title": None,
            "genres_include": [],
            "genres_exclude": [],
            "release_year_min": None,
            "release_year_max": None,
        },
        "domain_queries": {
            "movie": None,
            "anime": None,
            "book": None,
        },
        "semantic_query": "fantasy journey",
        "similar_to": [],
    })
    mock_client.chat.completions.create.return_value = _make_mock_response(minimal_payload)

    result = parse_query("recommend fantasy anime", client=mock_client)

    assert result.media_types == ["anime"]
    assert result.common.title is None
    assert result.domain_queries.anime is None
    assert result.similar_to == []


def test_parse_query_malformed_json_fallback_mocked():
    """Test that malformed JSON triggers fallback to the next model in MODELS_TO_TRY."""
    mock_client = MagicMock()
    valid_payload = json.dumps({
        "media_types": ["book"],
        "common": {
            "title": "Dune",
            "genres_include": [],
            "genres_exclude": [],
            "release_year_min": None,
            "release_year_max": None,
        },
        "domain_queries": {
            "movie": None,
            "anime": None,
            "book": None,
        },
        "semantic_query": "",
        "similar_to": [],
    })

    # Model 1 returns broken JSON; Model 2 returns valid JSON
    mock_client.chat.completions.create.side_effect = [
        _make_mock_response("{malformed json..."),
        _make_mock_response(valid_payload),
    ]

    result = parse_query("find Dune book", client=mock_client)

    assert result.media_types == ["book"]
    assert result.common.title == "Dune"
    assert mock_client.chat.completions.create.call_count == 2
    # Verify first call was model 0, second was model 1
    calls = mock_client.chat.completions.create.call_args_list
    assert calls[0].kwargs["model"] == MODELS_TO_TRY[0]
    assert calls[1].kwargs["model"] == MODELS_TO_TRY[1]


def test_parse_query_rate_limit_retry_mocked(monkeypatch):
    """Test that RateLimitError triggers exponential backoff retry on same model."""
    mock_client = MagicMock()
    valid_payload = json.dumps({
        "media_types": ["movie"],
        "common": {
            "title": None,
            "genres_include": [],
            "genres_exclude": [],
            "release_year_min": None,
            "release_year_max": None,
        },
        "domain_queries": {
            "movie": None,
            "anime": None,
            "book": None,
        },
        "semantic_query": "ambient chill",
        "similar_to": [],
    })

    # Avoid real sleep during test
    sleep_mock = MagicMock()
    monkeypatch.setattr("time.sleep", sleep_mock)

    mock_rate_limit = RateLimitError(
        message="Rate limit exceeded",
        response=MagicMock(status_code=429),
        body={"error": {"message": "Rate limit reached"}},
    )

    # Attempt 1: RateLimitError; Attempt 2: Success
    mock_client.chat.completions.create.side_effect = [
        mock_rate_limit,
        _make_mock_response(valid_payload),
    ]

    result = parse_query("chill movies", client=mock_client)

    assert result.media_types == ["movie"]
    assert sleep_mock.call_count == 1
    assert mock_client.chat.completions.create.call_count == 2
    # Both calls should be on the first model
    assert mock_client.chat.completions.create.call_args_list[0].kwargs["model"] == MODELS_TO_TRY[0]
    assert mock_client.chat.completions.create.call_args_list[1].kwargs["model"] == MODELS_TO_TRY[0]


def test_parse_query_all_models_fail_mocked():
    """Test that if all models fail, parse_query raises the last exception."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = RuntimeError("Provider down")

    with pytest.raises(RuntimeError, match="Provider down"):
        parse_query("test query", client=mock_client)


def test_parse_query_invalid_schema_fallback_mocked():
    """Test that invalid Pydantic schema (e.g. 3 media types) triggers fallback."""
    mock_client = MagicMock()
    invalid_schema_payload = json.dumps({
        "media_types": ["movie", "anime", "book"],  # Violates max_length=2
        "common": {
            "title": None,
            "genres_include": [],
            "genres_exclude": [],
            "release_year_min": None,
            "release_year_max": None,
        },
        "domain_queries": {
            "movie": None,
            "anime": None,
            "book": None,
        },
        "semantic_query": "epic crossover",
        "similar_to": [],
    })
    valid_payload = json.dumps({
        "media_types": ["movie", "anime"],
        "common": {
            "title": None,
            "genres_include": [],
            "genres_exclude": [],
            "release_year_min": None,
            "release_year_max": None,
        },
        "domain_queries": {
            "movie": None,
            "anime": None,
            "book": None,
        },
        "semantic_query": "epic crossover",
        "similar_to": [],
    })

    mock_client.chat.completions.create.side_effect = [
        _make_mock_response(invalid_schema_payload),
        _make_mock_response(valid_payload),
    ]

    result = parse_query("crossover", client=mock_client)
    assert result.media_types == ["movie", "anime"]
    assert mock_client.chat.completions.create.call_count == 2


def test_cache_fingerprint_and_key_generation():
    """Test configuration fingerprinting and cache key determinism."""
    from evaluation.run_evaluation import compute_config_fingerprint, make_cache_key

    fp1 = compute_config_fingerprint("v1")
    fp2 = compute_config_fingerprint("v1")
    assert fp1 == fp2
    assert len(fp1) == 16

    key1 = make_cache_key("recommend sci-fi movies")
    key2 = make_cache_key("recommend sci-fi movies")
    assert key1 == key2

    diff_key = make_cache_key("recommend drama anime")
    assert key1 != diff_key


def test_semantic_query_evaluation_metrics():
    """Test semantic query token overlap and jaccard metrics."""
    from evaluation.run_evaluation import evaluate_semantic_query

    # Both empty
    eval_empty = evaluate_semantic_query("", "")
    assert eval_empty["exact_match"] is True
    assert eval_empty["is_acceptable"] is True

    # High overlap paraphrase
    eval_overlap = evaluate_semantic_query(
        "mind-bending science fiction with time travel and alternate realities",
        "mind-bending time travel alternate realities",
    )
    assert eval_overlap["exact_match"] is False
    assert eval_overlap["token_f1"] > 0.6
    assert eval_overlap["is_acceptable"] is True

    # Completely disjoint
    eval_disjoint = evaluate_semantic_query(
        "romantic comedy in Paris",
        "dark apocalyptic horror",
    )
    assert eval_disjoint["is_acceptable"] is False
    assert eval_disjoint["token_f1"] == 0.0


def test_comparison_ordering_semantics():
    """Test that media_types respects ordering while genres ignores ordering."""
    from evaluation.run_evaluation import compare_normalized

    # media_types: ORDER MATTERS
    errs_ordered = compare_normalized(["movie", "anime"], ["anime", "movie"], "media_types")
    assert len(errs_ordered) > 0

    # genres: UNORDERED, CASE-INSENSITIVE
    errs_genres = compare_normalized(
        ["action", "sci-fi"],
        ["Sci-Fi", "Action"],
        "common.genres_include",
    )
    assert len(errs_genres) == 0


def test_compare_normalized_empty_domain_objects():
    """Test that empty domain query objects are normalized to None."""
    from evaluation.run_evaluation import compare_normalized

    empty_domain = {
        "production_companies": [],
        "cast": [],
        "director": [],
        "revenue_min": None,
        "runtime_min": None,
        "runtime_max": None,
    }
    errs = compare_normalized(None, empty_domain, "domain_queries.movie")
    assert len(errs) == 0

