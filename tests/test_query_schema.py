import pytest
from pydantic import ValidationError
from project_black_knight.query_schema import (
    BlackKnightQuery,
    CommonQuery,
    DomainQueries,
    MovieQuery,
    AnimeQuery,
    BookQuery,
)


def test_common_query_defaults():
    cq = CommonQuery()
    assert cq.title is None
    assert cq.genres_include == []
    assert cq.genres_exclude == []
    assert cq.release_year_min is None
    assert cq.release_year_max is None


def test_black_knight_query_valid():
    bk_query = BlackKnightQuery(
        media_types=["movie", "anime"],
        common=CommonQuery(genres_include=["sci-fi"], release_year_min=2015),
        domain_queries=DomainQueries(
            movie=MovieQuery(runtime_max=150),
            anime=AnimeQuery(episodes_max=50),
        ),
        semantic_query="mind-bending time travel",
        similar_to=["Interstellar", "Steins;Gate"],
    )

    assert bk_query.media_types == ["movie", "anime"]
    assert bk_query.common.genres_include == ["sci-fi"]
    assert bk_query.common.release_year_min == 2015
    assert bk_query.domain_queries.movie.runtime_max == 150
    assert bk_query.domain_queries.anime.episodes_max == 50
    assert bk_query.semantic_query == "mind-bending time travel"
    assert bk_query.similar_to == ["Interstellar", "Steins;Gate"]


def test_black_knight_query_max_media_types():
    # Schema specifies max_length=2 for media_types
    with pytest.raises(ValidationError):
        BlackKnightQuery(
            media_types=["movie", "anime", "book"],
            common=CommonQuery(),
            domain_queries=DomainQueries(),
            semantic_query="test",
        )


def test_black_knight_query_rejects_music():
    # Schema must reject "music" as media_type
    with pytest.raises(ValidationError):
        BlackKnightQuery(
            media_types=["music"],
            common=CommonQuery(),
            domain_queries=DomainQueries(),
            semantic_query="test",
        )
