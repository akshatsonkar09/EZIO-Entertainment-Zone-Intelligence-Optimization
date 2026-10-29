"""
Unit and integration tests for the Project Black Knight FastAPI Backend.
Tests health, search, item retrieval, random discovery, metadata browsing,
and validation/error handling.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_search_empty_query(client):
    response = client.post("/search", json={"query": "   "})
    assert response.status_code in (422, 400)


def test_search_valid_query(client):
    response = client.post("/search", json={"query": "space adventure", "domain": "movie", "top_k": 3})
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total_results" in data
    assert len(data["results"]) <= 3
    if data["results"]:
        first = data["results"][0]
        assert "id" in first
        assert "title" in first
        assert "score" in first
        assert first["media_type"] == "movie"


def test_get_item_valid_movie(client):
    response = client.get("/items/movie_0")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "movie_0"
    assert data["media_type"] == "movie"
    assert data["title"] == "Avatar"
    assert "metadata" in data


def test_get_item_valid_anime(client):
    response = client.get("/items/anime_0")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "anime_0"
    assert data["media_type"] == "anime"
    assert "title" in data


def test_get_item_valid_book(client):
    response = client.get("/items/book_0")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "book_0"
    assert data["media_type"] == "book"
    assert "title" in data


def test_get_item_invalid_format(client):
    response = client.get("/items/invalid_format_id")
    assert response.status_code == 404


def test_get_item_out_of_range(client):
    response = client.get("/items/movie_999999")
    assert response.status_code == 404


def test_get_random_item(client):
    response = client.get("/random?domain=movie")
    assert response.status_code == 200
    data = response.json()
    assert data["media_type"] == "movie"
    assert "id" in data
    assert "title" in data


def test_get_metadata_categories(client):
    response = client.get("/metadata/categories")
    assert response.status_code == 200
    data = response.json()
    assert "domains" in data
    assert "genres" in data
    assert "years" in data
    assert "movie" in data["genres"]
    assert "anime" in data["genres"]
    assert "book" in data["genres"]


def test_browse_by_metadata(client):
    response = client.post(
        "/browse",
        json={"domain": "movie", "genre": "Action", "limit": 5},
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) <= 5
    if data["results"]:
        assert data["results"][0]["media_type"] == "movie"


def test_browse_by_metadata_informative(client):
    response = client.post(
        "/browse",
        json={"genre": "Informative", "limit": 15},
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert data["total_results"] > 0
    # Check that at least one result has documentary, historical, or nonfiction
    genres_seen = [r.get("genres", "").lower() for r in data["results"]]
    assert any("documentary" in g or "historical" in g or "nonfiction" in g for g in genres_seen)

