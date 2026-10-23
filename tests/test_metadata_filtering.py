"""
Comprehensive unit and regression tests for metadata filtering (Phase 3).

Covers:
- Numeric type coercion and TypeError regression (e.g., string page counts)
- Exact boundary equality (inclusive bounds)
- Included and excluded genres, synonym mapping, and casing
- Case-insensitive and whitespace-tolerant text matching (cast, director, title, author, isbn)
- Missing values (None, NaN, empty string, 'unknown') under active constraints
- Filter combinations and zero-result queries
- Hard constraint enforcement (zero false positives)
"""

import math
import pandas as pd
import pytest

from project_black_knight.metadata_filter import (
    coerce_numeric,
    match_genre,
    normalize_text_match,
    row_matches_filters,
    get_valid_ids,
)


# --------------------------------------------------
# Fixtures
# --------------------------------------------------

@pytest.fixture
def movie_fixture():
    return pd.DataFrame([
        {
            "id": "mov_1",
            "title": "Inception",
            "genres": "Action, ScienceFiction, Mystery",
            "release_year": 2010,
            "runtime": 148.0,
            "revenue": 825532764,
            "director": "ChristopherNolan",
            "cast": "LeonardoDiCaprio, JosephGordon-Levitt, ElliotPage",
            "production_companies": "Legendary Pictures, Syncopy",
        },
        {
            "id": "mov_2",
            "title": "The Dark Knight",
            "genres": "Action, Crime, Drama",
            "release_year": 2008,
            "runtime": 152.0,
            "revenue": 1004558444,
            "director": "ChristopherNolan",
            "cast": "ChristianBale, HeathLedger",
            "production_companies": "Warner Bros., DC Comics",
        },
        {
            "id": "mov_3",
            "title": "Short Indie Film",
            "genres": "Comedy, Romance",
            "release_year": "2015",  # string numeric
            "runtime": "85",  # string numeric
            "revenue": 0,
            "director": "JaneDoe",
            "cast": "ActorA, ActorB",
            "production_companies": None,
        },
        {
            "id": "mov_4",
            "title": "Broken Metadata Movie",
            "genres": None,
            "release_year": None,
            "runtime": float("nan"),
            "revenue": None,
            "director": None,
            "cast": None,
            "production_companies": None,
        },
    ])


@pytest.fixture
def book_fixture():
    return pd.DataFrame([
        {
            "id": "book_1",
            "title": "Dune",
            "author": "Frank Herbert",
            "rating": 4.25,
            "isbn": 9780441172719,
            "genres": "Science Fiction, Fantasy",
            "characters": "Paul Atreides, Leto Atreides",
            "pages": "412",  # String pages (known defect regression fixture)
            "publisher": "Chilton Books",
            "release_year": 1965,
        },
        {
            "id": "book_2",
            "title": "The Hobbit",
            "author": "J.R.R. Tolkien",
            "rating": 4.28,
            "isbn": "9780547928227",
            "genres": "Fantasy, Adventure",
            "characters": "Bilbo Baggins, Gandalf",
            "pages": 310.0,
            "publisher": "George Allen & Unwin",
            "release_year": 1937,
        },
        {
            "id": "book_3",
            "title": "Mystery of the Unknown",
            "author": "Arthur Conan Doyle",
            "rating": "3.9",
            "isbn": 9780140439076,
            "genres": "Mystery, Detective",
            "characters": "Sherlock Holmes, Dr. John Watson",
            "pages": "unknown",  # Non-numeric string
            "publisher": "Penguin Classics",
            "release_year": "1892",
        },
    ])


@pytest.fixture
def anime_fixture():
    return pd.DataFrame([
        {
            "id": "ani_1",
            "title": "Death Note",
            "genres": "Mystery Psychological Supernatural Thriller",
            "episodes": 37.0,
            "popularity": 1,
            "ranking": 20.0,
            "release_year": 2006,
        },
        {
            "id": "ani_2",
            "title": "Steins;Gate",
            "genres": "Sci-Fi Suspense Psychological",
            "episodes": "24",
            "popularity": 7,
            "ranking": 3.0,
            "release_year": 2011,
        },
        {
            "id": "ani_3",
            "title": "Unranked Ongoing Anime",
            "genres": "Action Fantasy",
            "episodes": float("nan"),
            "popularity": 500,
            "ranking": float("nan"),
            "release_year": 2024,
        },
    ])



# --------------------------------------------------
# 1. Numeric Coercion & Regression Tests
# --------------------------------------------------

def test_coerce_numeric_valid_and_invalid():
    assert coerce_numeric(10) == 10.0
    assert coerce_numeric(15.5) == 15.5
    assert coerce_numeric("450") == 450.0
    assert coerce_numeric("  120.75  ") == 120.75
    assert coerce_numeric("0") == 0.0
    assert coerce_numeric(None) is None
    assert coerce_numeric(float("nan")) is None
    assert coerce_numeric("") is None
    assert coerce_numeric("unknown") is None
    assert coerce_numeric("NaN") is None


def test_book_page_string_comparison_regression(book_fixture):
    """
    Regression Test:
    Prior defect: When book pages were stored as strings (e.g. '412'),
    direct comparison `row['pages'] > filters['pages_max']` threw TypeError.
    Verify filtering now succeeds cleanly.
    """
    current_ids = book_fixture["id"].tolist()

    # Filter with integer pages_max
    filters = {"pages_max": 450}
    valid_ids = get_valid_ids(book_fixture, current_ids, filters, media_type="book")
    assert "book_1" in valid_ids  # '412' <= 450
    assert "book_2" in valid_ids  # 310 <= 450
    assert "book_3" not in valid_ids  # 'unknown' safely excluded

    # Filter with string numeric bound
    filters_str = {"pages_max": "400"}
    valid_ids_str = get_valid_ids(book_fixture, current_ids, filters_str, media_type="book")
    assert "book_1" not in valid_ids_str  # 412 > 400
    assert "book_2" in valid_ids_str  # 310 <= 400


# --------------------------------------------------
# 2. Boundary Value Equality (Exact Bounds)
# --------------------------------------------------

def test_numeric_exact_boundaries(movie_fixture):
    current_ids = movie_fixture["id"].tolist()

    # Exactly equal to lower bound (148.0)
    res_min = get_valid_ids(movie_fixture, current_ids, {"runtime_min": 148}, "movie")
    assert "mov_1" in res_min
    assert "mov_2" in res_min

    # Exactly equal to upper bound (148.0)
    res_max = get_valid_ids(movie_fixture, current_ids, {"runtime_max": 148}, "movie")
    assert "mov_1" in res_max
    assert "mov_2" not in res_max  # 152 > 148

    # Closed range [148, 152] inclusive
    res_range = get_valid_ids(movie_fixture, current_ids, {"runtime_min": 148, "runtime_max": 152}, "movie")
    assert "mov_1" in res_range
    assert "mov_2" in res_range
    assert "mov_3" not in res_range  # 85 < 148


# --------------------------------------------------
# 3. Genre Matching, Synonyms, Casing & Exclusions
# --------------------------------------------------

def test_genre_matching_synonyms_and_casing():
    # Casing
    assert match_genre("action", "Action, Adventure")
    assert match_genre("ACTION", "action, adventure")

    # Synonyms in GENRE_MAP
    assert match_genre("sci-fi", "Action, ScienceFiction")
    assert match_genre("science fiction", "Action, ScienceFiction")
    assert match_genre("scifi", "Action, Sci-Fi")
    assert match_genre("electronic", "edm, dance")
    assert match_genre("synthwave", "retrowave electronic")

    # Mismatch
    assert not match_genre("horror", "Action, Romance, Comedy")
    assert not match_genre("sci-fi", "Documentary, History")


def test_genre_inclusions_and_exclusions(movie_fixture):
    current_ids = movie_fixture["id"].tolist()

    # Include sci-fi
    inc_scifi = get_valid_ids(movie_fixture, current_ids, {"genres_include": ["sci-fi"]}, "movie")
    assert "mov_1" in inc_scifi
    assert "mov_2" not in inc_scifi

    # Exclude crime
    exc_crime = get_valid_ids(movie_fixture, current_ids, {"genres_exclude": ["crime"]}, "movie")
    assert "mov_1" in exc_crime
    assert "mov_2" not in exc_crime  # Dark Knight is Crime

    # Include action but exclude mystery
    inc_act_exc_mys = get_valid_ids(
        movie_fixture,
        current_ids,
        {"genres_include": ["action"], "genres_exclude": ["mystery"]},
        "movie",
    )
    assert "mov_1" not in inc_act_exc_mys  # Inception has Mystery
    assert "mov_2" in inc_act_exc_mys  # Dark Knight has Action, no Mystery


# --------------------------------------------------
# 4. Text Matching (Normalized Names, ISBN, Entities)
# --------------------------------------------------

def test_director_and_cast_name_normalization(movie_fixture):
    current_ids = movie_fixture["id"].tolist()

    # Query with spaced name against joined name in dataset (Christopher Nolan vs ChristopherNolan)
    res_dir = get_valid_ids(movie_fixture, current_ids, {"director": ["Christopher Nolan"]}, "movie")
    assert "mov_1" in res_dir
    assert "mov_2" in res_dir
    assert "mov_3" not in res_dir

    # Cast match
    res_cast = get_valid_ids(movie_fixture, current_ids, {"cast": ["Leonardo DiCaprio"]}, "movie")
    assert "mov_1" in res_cast
    assert "mov_2" not in res_cast


def test_book_isbn_and_author_normalization(book_fixture):
    current_ids = book_fixture["id"].tolist()

    # ISBN with hyphens against integer/unhyphenated ISBN in dataset
    res_isbn = get_valid_ids(book_fixture, current_ids, {"isbn": "978-0441172719"}, "book")
    assert res_isbn == {"book_1"}

    # Author case-insensitive match
    res_author = get_valid_ids(book_fixture, current_ids, {"author": ["frank herbert"]}, "book")
    assert res_author == {"book_1"}


def test_music_domain_not_in_active_filtering():
    """Verify that music-specific fields are not active filter constraints."""
    sample_df = pd.DataFrame([
        {"id": "item_1", "title": "Song Title", "release_year": 2020, "genres": "pop"},
    ])
    # Music-specific filter fields should have no domain filter branch
    res = get_valid_ids(sample_df, ["item_1"], {"artist": "Daft Punk"}, "music")
    # Without active music domain filter branch, title/genres/year apply only
    assert res == {"item_1"}


# --------------------------------------------------
# 5. Missing Data Handling & Hard Constraint Enforcement
# --------------------------------------------------

def test_missing_data_under_active_constraint_excluded(movie_fixture):
    """Items with missing fields must be excluded under active constraints."""
    current_ids = movie_fixture["id"].tolist()

    # Under active runtime_max constraint, mov_4 (NaN runtime) must be excluded
    res_active = get_valid_ids(movie_fixture, current_ids, {"runtime_max": 200}, "movie")
    assert "mov_4" not in res_active
    assert "mov_1" in res_active

    # Without active constraints, all items are valid
    res_none = get_valid_ids(movie_fixture, current_ids, {}, "movie")
    assert len(res_none) == len(movie_fixture)


def test_anime_ranking_and_popularity_handling(anime_fixture):
    current_ids = anime_fixture["id"].tolist()

    # Ranking max 10 (top 10): rank 3 is included, rank 20 and NaN are excluded
    res_top10 = get_valid_ids(anime_fixture, current_ids, {"ranking_max": 10}, "anime")
    assert res_top10 == {"ani_2"}

    # Popularity min 5: pop 1 is excluded (<5), pop 7 and 500 are included
    res_pop = get_valid_ids(anime_fixture, current_ids, {"popularity_min": 5}, "anime")
    assert "ani_1" not in res_pop
    assert "ani_2" in res_pop
    assert "ani_3" in res_pop


def test_contradictory_filters_empty_result(movie_fixture):
    """Contradictory constraints must return an empty set."""
    current_ids = movie_fixture["id"].tolist()

    # Impossible release year range
    res_impossible_year = get_valid_ids(
        movie_fixture,
        current_ids,
        {"release_year_min": 2020, "release_year_max": 2000},
        "movie",
    )
    assert res_impossible_year == set()

    # Include and exclude the same genre
    res_impossible_genre = get_valid_ids(
        movie_fixture,
        current_ids,
        {"genres_include": ["action"], "genres_exclude": ["action"]},
        "movie",
    )
    assert res_impossible_genre == set()


def test_real_dataset_hard_constraints():
    """Verify hard constraint enforcement with 0 false positives on actual datasets."""
    from pathlib import Path

    data_dir = Path("data/processed")
    movie_path = data_dir / "movie_metadata_clean.csv"
    if not movie_path.exists():
        pytest.skip("Dataset file not available")

    df_movies = pd.read_csv(movie_path)
    current_ids = [f"movie_{i}" for i in range(len(df_movies))]

    # Christopher Nolan sci-fi movie released >= 2010 with runtime <= 170
    filters = {
        "genres_include": ["science fiction"],
        "release_year_min": 2010,
        "runtime_max": 170,
        "director": ["Christopher Nolan"],
    }

    valid_ids = get_valid_ids(df_movies, current_ids, filters, "movie")
    assert len(valid_ids) > 0

    # Ensure every single returned item strictly satisfies the constraints
    for mid in valid_ids:
        idx = int(mid.split("_")[1])
        row = df_movies.iloc[idx]
        assert row["release_year"] >= 2010
        assert row["runtime"] <= 170
        assert "nolan" in str(row["director"]).lower()
        assert any(s in str(row["genres"]).lower() for s in ["sciencefiction", "sci-fi", "science fiction"])


def test_title_normalization_variations_matching():
    """Verify title filtering matches across apostrophes, accents, and subtitle punctuation."""
    sample_df = pd.DataFrame([
        {"id": "m1", "title": "Amélie", "release_year": 2001, "genres": "Romance, Comedy"},
        {"id": "m2", "title": "Dude, Where’s My Car?", "release_year": 2000, "genres": "Comedy"},
        {"id": "m3", "title": "Fullmetal Alchemist: Brotherhood", "release_year": 2009, "genres": "Action, Fantasy"},
    ])
    ids = ["m1", "m2", "m3"]

    # ASCII query matches accented title
    res_accent = get_valid_ids(sample_df, ids, {"title": "Amelie"}, "movie")
    assert res_accent == {"m1"}

    # Straight apostrophe query matches curly apostrophe catalog title
    res_apos = get_valid_ids(sample_df, ids, {"title": "Dude, Where's My Car?"}, "movie")
    assert res_apos == {"m2"}

    # Hyphen query matches colon subtitle catalog title
    res_sub = get_valid_ids(sample_df, ids, {"title": "Fullmetal Alchemist - Brotherhood"}, "anime")
    assert res_sub == {"m3"}


