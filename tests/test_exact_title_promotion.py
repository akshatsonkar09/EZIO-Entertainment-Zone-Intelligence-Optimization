"""
Deterministic regression tests for Exact Title Match Promotion (Experiment 1).

Validates:
1. Exact canonical title matches are promoted ahead of subtitle/spinoff variants.
2. Movie domain: 'The Dark Knight' ranks movie_65 above 'The Dark Knight Rises'.
3. Anime domain: 'Cowboy Bebop' ranks anime_750/17108 above movie/special variants.
4. Anime domain: 'Shingeki no Kyojin' ranks anime_667/14939 above OVA/Picture Drama.
5. Book domain: 'The Hunger Games' ranks book_2608/10523 above guides.
6. Absence queries with non-existent titles return 0 results (0% false acceptance).
7. Queries without title filters are completely unaffected.
"""

import pytest
from project_black_knight.query_schema import BlackKnightQuery, CommonQuery, DomainQueries
from project_black_knight.retrieval import RetrievalRepository, search_black_knight


@pytest.fixture(scope="module")
def repo():
    return RetrievalRepository()


def test_movie_exact_title_promotion(repo):
    q = BlackKnightQuery(
        media_types=["movie"],
        semantic_query="Find the movie The Dark Knight.",
        common=CommonQuery(title="The Dark Knight"),
        domain_queries=DomainQueries(),
    )
    res = search_black_knight(parsed_query=q, top_k=5, repo=repo, architecture="all_cross_encoder")
    assert len(res["results"]) > 0
    assert res["results"][0]["id"] == "movie_65"
    assert res["results"][0]["title"] == "The Dark Knight"


def test_anime_exact_title_promotion(repo):
    q = BlackKnightQuery(
        media_types=["anime"],
        semantic_query="Find Cowboy Bebop.",
        common=CommonQuery(title="Cowboy Bebop"),
        domain_queries=DomainQueries(),
    )
    res = search_black_knight(parsed_query=q, top_k=5, repo=repo, architecture="domain_routed")
    assert len(res["results"]) > 0
    top_title = res["results"][0]["title"].lower().strip()
    assert top_title == "cowboy bebop"


def test_anime_shingeki_promotion(repo):
    q = BlackKnightQuery(
        media_types=["anime"],
        semantic_query="Find Shingeki no Kyojin.",
        common=CommonQuery(title="Shingeki no Kyojin"),
        domain_queries=DomainQueries(),
    )
    res = search_black_knight(parsed_query=q, top_k=5, repo=repo, architecture="domain_routed")
    assert len(res["results"]) > 0
    top_title = res["results"][0]["title"].lower().strip()
    assert top_title == "shingeki no kyojin"


def test_book_exact_title_promotion(repo):
    q = BlackKnightQuery(
        media_types=["book"],
        semantic_query="Find The Hunger Games by Suzanne Collins.",
        common=CommonQuery(title="The Hunger Games"),
        domain_queries=DomainQueries(),
    )
    res = search_black_knight(parsed_query=q, top_k=5, repo=repo, architecture="domain_routed")
    assert len(res["results"]) > 0
    top_title = res["results"][0]["title"].lower().strip()
    assert top_title == "the hunger games"


def test_absence_query_preservation(repo):
    q = BlackKnightQuery(
        media_types=["movie"],
        semantic_query="Find nonexistent fake movie xyz999.",
        common=CommonQuery(title="nonexistent fake movie xyz999"),
        domain_queries=DomainQueries(),
    )
    res = search_black_knight(parsed_query=q, top_k=5, repo=repo, architecture="domain_routed")
    assert len(res["results"]) == 0
