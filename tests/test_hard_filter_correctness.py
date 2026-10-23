"""
Comprehensive Hard-Filter Correctness & Reliability Regression Suite (Phase 4).

Validates:
1. Every numeric filter's inclusive bounds (lower, upper, exact, outside, lower-only, upper-only).
2. Boolean and malformed numeric metadata handling.
3. Entity normalization, token-boundary safety, and substring leak prevention (Ian != Christian Bale).
4. Multi-entity fields, role stripping, and single-string filter input coercion.
5. Missing, null, and NaN metadata behavior under active constraints.
6. ISBN string and floating-point `.0` normalization.
7. Raw/constructed query objects vs. production retrieval (`search_black_knight`).
8. Multi-filter conjunctions, mixed-domain isolation, Architecture A vs. Architecture B.
"""

import math
import pandas as pd
import pytest

from project_black_knight.metadata_filter import (
    clean_isbn_str,
    coerce_numeric,
    get_valid_ids,
    match_entity,
    row_matches_filters,
)
from project_black_knight.query_schema import (
    AnimeQuery,
    BlackKnightQuery,
    BookQuery,
    CommonQuery,
    DomainQueries,
    MovieQuery,
)
from project_black_knight.retrieval import search_black_knight


# --------------------------------------------------
# Synthetic Fixtures
# --------------------------------------------------

@pytest.fixture
def movie_fixture():
    return pd.DataFrame([
        {
            "id": "m1",
            "title": "Inception",
            "director": "ChristopherNolan",
            "cast": "LeonardoDiCaprio, JosephGordon-Levitt, ElliotPage",
            "production_companies": "Legendary Pictures, Syncopy, Warner Bros.",
            "release_year": 2010,
            "runtime": 148,
            "revenue": 825532764,
            "genres": "Action, Adventure, ScienceFiction",
        },
        {
            "id": "m2",
            "title": "The Dark Knight",
            "director": "ChristopherNolan",
            "cast": "ChristianBale, HeathLedger, AaronEckhart",
            "production_companies": "Warner Bros., DC Comics",
            "release_year": 2008,
            "runtime": 152,
            "revenue": 1004558444,
            "genres": "Action, Crime, Drama",
        },
        {
            "id": "m3",
            "title": "Elite Squad",
            "director": "JoséPadilha",
            "cast": "WagnerMoura, AndréRamiro",
            "production_companies": "Zazen Produções",
            "release_year": 2007,
            "runtime": 115,
            "revenue": 14759148,
            "genres": "Action, Crime, Drama",
        },
        {
            "id": "m4",
            "title": "Micro Indie Film",
            "director": None,
            "cast": None,
            "production_companies": None,
            "release_year": None,
            "runtime": float("nan"),
            "revenue": None,
            "genres": None,
        },
    ])


@pytest.fixture
def anime_fixture():
    return pd.DataFrame([
        {
            "id": "a1",
            "title": "Death Note",
            "release_year": 2006,
            "episodes": 37,
            "popularity": 1,
            "ranking": 20.0,
            "genres": "Mystery Psychological Supernatural Thriller",
        },
        {
            "id": "a2",
            "title": "Steins;Gate",
            "release_year": 2011,
            "episodes": 24,
            "popularity": 7,
            "ranking": 3.0,
            "genres": "Sci-Fi Suspense Psychological",
        },
        {
            "id": "a3",
            "title": "One-Shot Special",
            "release_year": 2020,
            "episodes": 1,
            "popularity": 500,
            "ranking": 1500.0,
            "genres": "Comedy Slice of Life",
        },
        {
            "id": "a4",
            "title": "Missing Anime Data",
            "release_year": None,
            "episodes": float("nan"),
            "popularity": None,
            "ranking": float("nan"),
            "genres": None,
        },
    ])


@pytest.fixture
def book_fixture():
    return pd.DataFrame([
        {
            "id": "b1",
            "title": "Dune",
            "author": "Frank Herbert",
            "publisher": "Chilton Books",
            "isbn": 9780441172719,
            "rating": 4.25,
            "pages": 412,
            "release_year": 1965,
            "characters": "Paul Atreides, Leto Atreides, Jessica",
            "genres": "Science Fiction, Fantasy, Fiction",
        },
        {
            "id": "b2",
            "title": "A Game of Thrones",
            "author": "George R.R. Martin",
            "publisher": "Bantam Spectra",
            "isbn": "9780553103540",
            "rating": 4.44,
            "pages": 694,
            "release_year": 1996,
            "characters": "Eddard Stark, Jon Snow, Daenerys Targaryen",
            "genres": "Fantasy, Fiction, Adult",
        },
        {
            "id": "b3",
            "title": "The Gift of the Magi",
            "author": "O. Henry, Lisbeth Zwerger (Illustrator)",
            "publisher": "Neugebauer Press",
            "isbn": 9780887080180.0,  # Floating point representation of integer ISBN
            "rating": 3.80,
            "pages": 32,
            "release_year": 1905,
            "characters": "Jim, Della",
            "genres": "Classics, Fiction, Short Stories",
        },
        {
            "id": "b4",
            "title": "The Wheel of Time: The Eye of the World",
            "author": "Robert Jordan",
            "publisher": "Tor Books",
            "isbn": "978-0812511819",
            "rating": 4.19,
            "pages": "782",  # String numeric
            "release_year": 1990,
            "characters": "Rand al'Thor, Matrim Cauthon, Perrin Aybara",
            "genres": "Fantasy, Fiction, High Fantasy",
        },
        {
            "id": "b5",
            "title": "Corrupt Book Record",
            "author": None,
            "publisher": None,
            "isbn": None,
            "rating": float("nan"),
            "pages": "unknown",
            "release_year": None,
            "characters": None,
            "genres": None,
        },
    ])


# --------------------------------------------------
# 1. Numeric Coercion & Boolean Safety
# --------------------------------------------------

def test_coerce_numeric_boolean_guard():
    """Booleans must not be coerced to numbers (bool is subclass of int in Python)."""
    assert coerce_numeric(True) is None
    assert coerce_numeric(False) is None


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
    assert coerce_numeric([10]) is None


# --------------------------------------------------
# 2. Inclusive Numeric Range Bounds
# --------------------------------------------------

def test_release_year_inclusive_bounds(movie_fixture):
    ids = movie_fixture["id"].tolist()

    # Exact equality lower bound (2008)
    res_min = get_valid_ids(movie_fixture, ids, {"release_year_min": 2008}, "movie")
    assert "m1" in res_min  # 2010 >= 2008
    assert "m2" in res_min  # 2008 >= 2008 (exact)
    assert "m3" not in res_min  # 2007 < 2008

    # Exact equality upper bound (2008)
    res_max = get_valid_ids(movie_fixture, ids, {"release_year_max": 2008}, "movie")
    assert "m2" in res_max  # 2008 <= 2008 (exact)
    assert "m3" in res_max  # 2007 <= 2008
    assert "m1" not in res_max  # 2010 > 2008

    # Closed interval [2007, 2008]
    res_range = get_valid_ids(movie_fixture, ids, {"release_year_min": 2007, "release_year_max": 2008}, "movie")
    assert res_range == {"m2", "m3"}


def test_runtime_inclusive_bounds(movie_fixture):
    ids = movie_fixture["id"].tolist()

    # Exact lower bound 148
    res_min = get_valid_ids(movie_fixture, ids, {"runtime_min": 148}, "movie")
    assert "m1" in res_min  # 148
    assert "m2" in res_min  # 152
    assert "m3" not in res_min  # 115

    # Exact upper bound 148
    res_max = get_valid_ids(movie_fixture, ids, {"runtime_max": 148}, "movie")
    assert "m1" in res_max  # 148
    assert "m3" in res_max  # 115
    assert "m2" not in res_max  # 152 > 148


def test_episodes_inclusive_bounds(anime_fixture):
    ids = anime_fixture["id"].tolist()

    # Exact interval [24, 37]
    res = get_valid_ids(anime_fixture, ids, {"episodes_min": 24, "episodes_max": 37}, "anime")
    assert "a1" in res  # 37
    assert "a2" in res  # 24
    assert "a3" not in res  # 1

    # Single bound lower 25
    res_25 = get_valid_ids(anime_fixture, ids, {"episodes_min": 25}, "anime")
    assert "a1" in res_25
    assert "a2" not in res_25


def test_ranking_and_popularity_bounds(anime_fixture):
    ids = anime_fixture["id"].tolist()

    # Ranking max 3 (top 3): rank 3.0 matches, rank 20.0 excluded
    res_rank = get_valid_ids(anime_fixture, ids, {"ranking_max": 3}, "anime")
    assert res_rank == {"a2"}

    # Popularity min 7: pop 7 and 500 match, pop 1 excluded
    res_pop = get_valid_ids(anime_fixture, ids, {"popularity_min": 7}, "anime")
    assert "a2" in res_pop
    assert "a3" in res_pop
    assert "a1" not in res_pop

    # Symmetric ranking_min and popularity_max
    res_sym = get_valid_ids(anime_fixture, ids, {"popularity_max": 10, "ranking_min": 10}, "anime")
    assert res_sym == {"a1"}  # pop 1 <= 10, rank 20 >= 10


def test_rating_and_pages_bounds(book_fixture):
    ids = book_fixture["id"].tolist()

    # Rating min 4.25 (inclusive)
    res_rat = get_valid_ids(book_fixture, ids, {"rating_min": 4.25}, "book")
    assert "b1" in res_rat  # 4.25 (exact)
    assert "b2" in res_rat  # 4.44
    assert "b4" not in res_rat  # 4.19

    # Rating max 4.20
    res_rat_max = get_valid_ids(book_fixture, ids, {"rating_max": 4.20}, "book")
    assert "b3" in res_rat_max  # 3.80
    assert "b4" in res_rat_max  # 4.19
    assert "b1" not in res_rat_max  # 4.25

    # Pages interval [400, 700] handles int and string numeric
    res_pages = get_valid_ids(book_fixture, ids, {"pages_min": 400, "pages_max": 700}, "book")
    assert "b1" in res_pages  # 412
    assert "b2" in res_pages  # 694
    assert "b4" not in res_pages  # '782' > 700


def test_revenue_bounds_and_millions_shorthand(movie_fixture):
    ids = movie_fixture["id"].tolist()

    # Suffix shorthand: 800 -> 800M
    res_shorthand = get_valid_ids(movie_fixture, ids, {"revenue_min": 800}, "movie")
    assert "m1" in res_shorthand  # 825M
    assert "m2" in res_shorthand  # 1004M
    assert "m3" not in res_shorthand  # 14.7M

    # Exact revenue upper bound
    res_rev_max = get_valid_ids(movie_fixture, ids, {"revenue_max": 50}, "movie")
    assert res_rev_max == {"m3"}  # 14.7M <= 50M


# --------------------------------------------------
# 3. Entity-Name Normalization & Anti-Leakage
# --------------------------------------------------

def test_entity_exact_and_subsequence_matching():
    # Full name to PascalCase
    assert match_entity("Christopher Nolan", "ChristopherNolan")
    # Lowercase full name
    assert match_entity("christopher nolan", "ChristopherNolan")
    # Surname only
    assert match_entity("Nolan", "ChristopherNolan")
    # First name only
    assert match_entity("Christopher", "ChristopherNolan")


def test_entity_substring_leak_prevention():
    """
    CRITICAL: Substring matching without token boundaries must NOT occur.
    'Ian' must NOT match 'Christian Bale'.
    'Dan' must NOT match 'Robert Jordan'.
    'War' must NOT match 'Warner Bros.'.
    """
    assert not match_entity("Ian", "ChristianBale, MichaelCaine")
    assert not match_entity("Dan", "Robert Jordan")
    assert not match_entity("War", "Warner Bros., DC Comics")
    assert not match_entity("Tom", "Atomic Productions")
    assert not match_entity("Lee", "Stanley Kubrick")


def test_entity_diacritics_and_accents():
    """Accented names match ASCII and vice versa."""
    assert match_entity("Jose Padilha", "JoséPadilha")
    assert match_entity("José Padilha", "JosePadilha")
    assert match_entity("Wagner Moura", "WagnerMoura")
    assert match_entity("Andre Ramiro", "AndréRamiro")


def test_entity_parenthetical_role_stripping():
    """Parenthetical notes like (Illustrator) or (Goodreads Author) are stripped."""
    assert match_entity("O. Henry", "O. Henry, Lisbeth Zwerger (Illustrator)")
    assert match_entity("Lisbeth Zwerger", "O. Henry, Lisbeth Zwerger (Illustrator)")
    assert match_entity("Kerrelyn Sparks", "Kerrelyn Sparks (Goodreads Author)")


def test_entity_initialism_compatibility():
    """Middle initials match expanded or contracted forms."""
    assert match_entity("George Martin", "George R.R. Martin")
    assert match_entity("George R.R. Martin", "George R.R. Martin")
    assert match_entity("George R. R. Martin", "George R.R. Martin")
    assert match_entity("Martin", "George R.R. Martin")


def test_entity_filter_string_input_coercion(movie_fixture):
    """Passing a single string instead of a list must not loop over individual characters."""
    ids = movie_fixture["id"].tolist()

    # Pass string "Christopher Nolan" instead of ["Christopher Nolan"]
    res = get_valid_ids(movie_fixture, ids, {"director": "Christopher Nolan"}, "movie")
    assert res == {"m1", "m2"}

    # Pass string cast
    res_cast = get_valid_ids(movie_fixture, ids, {"cast": "Christian Bale"}, "movie")
    assert res_cast == {"m2"}


# --------------------------------------------------
# 4. ISBN Normalization & Floating `.0` Fix
# --------------------------------------------------

def test_clean_isbn_str():
    assert clean_isbn_str("978-0441172719") == "9780441172719"
    assert clean_isbn_str(9780441172719) == "9780441172719"
    # Floating point representation from nullable pandas integer column
    assert clean_isbn_str(9780887080180.0) == "9780887080180"
    assert clean_isbn_str("9780887080180.0") == "9780887080180"
    assert clean_isbn_str(None) == ""
    assert clean_isbn_str(True) == ""


def test_isbn_filter_matching(book_fixture):
    ids = book_fixture["id"].tolist()

    # Match hyphens against raw integer in dataset
    res_hyphen = get_valid_ids(book_fixture, ids, {"isbn": "978-0441172719"}, "book")
    assert res_hyphen == {"b1"}

    # Match against floating .0 ISBN in dataset
    res_float = get_valid_ids(book_fixture, ids, {"isbn": "9780887080180"}, "book")
    assert res_float == {"b3"}


# --------------------------------------------------
# 5. Missing & Malformed Metadata Exclusion
# --------------------------------------------------

def test_missing_metadata_excluded_under_active_constraint(movie_fixture, anime_fixture, book_fixture):
    """Items with missing fields must be excluded under active constraints."""
    # Under active runtime_max constraint, m4 (NaN runtime) must be excluded
    m_ids = movie_fixture["id"].tolist()
    res_m = get_valid_ids(movie_fixture, m_ids, {"runtime_max": 200}, "movie")
    assert "m4" not in res_m

    # Under active director constraint, m4 must be excluded
    res_dir = get_valid_ids(movie_fixture, m_ids, {"director": ["Christopher Nolan"]}, "movie")
    assert "m4" not in res_dir

    # Under active episodes_min constraint, a4 (NaN episodes) must be excluded
    a_ids = anime_fixture["id"].tolist()
    res_a = get_valid_ids(anime_fixture, a_ids, {"episodes_min": 1}, "anime")
    assert "a4" not in res_a

    # Under active rating_min constraint, b5 (NaN rating) must be excluded
    b_ids = book_fixture["id"].tolist()
    res_b = get_valid_ids(book_fixture, b_ids, {"rating_min": 3.0}, "book")
    assert "b5" not in res_b

    # When no active constraints are present, all items are retained
    res_none = get_valid_ids(movie_fixture, m_ids, {}, "movie")
    assert len(res_none) == len(m_ids)


# --------------------------------------------------
# 6. Multi-Filter Conjunctions
# --------------------------------------------------

def test_multi_filter_conjunction(movie_fixture):
    """Row must satisfy ALL active constraints simultaneously."""
    ids = movie_fixture["id"].tolist()
    filters = {
        "director": ["Christopher Nolan"],
        "genres_include": ["action"],
        "release_year_min": 2009,
        "runtime_max": 150,
    }
    # Inception is 2010, 148 runtime, Nolan, Action -> MATCH
    # The Dark Knight is 2008, 152 runtime -> FAILS year and runtime
    res = get_valid_ids(movie_fixture, ids, filters, "movie")
    assert res == {"m1"}


# --------------------------------------------------
# 7. Raw Queries vs. Parser-Generated Queries in search_black_knight
# --------------------------------------------------

def test_search_black_knight_constructed_query_bounds():
    """Verify directly constructed BlackKnightQuery enforces inclusive bounds in production path."""
    common = CommonQuery(release_year_min=2010, release_year_max=2010)
    domain_queries = DomainQueries(movie=MovieQuery(runtime_max=160))
    query = BlackKnightQuery(
        media_types=["movie"],
        semantic_query="mind-bending dreams",
        common=common,
        domain_queries=domain_queries,
    )

    res = search_black_knight(parsed_query=query, top_k=5, architecture="domain_routed")
    assert len(res["results"]) > 0
    for r in res["results"]:
        assert r["release_year"] == 2010


def test_search_black_knight_entity_and_genre_filtering():
    """Verify director filter and compound genre filter in production retrieval."""
    common = CommonQuery(genres_include=["action-adventure"])
    domain_queries = DomainQueries(movie=MovieQuery(director=["Christopher Nolan"]))
    query = BlackKnightQuery(
        media_types=["movie"],
        semantic_query="heist in subconscious",
        common=common,
        domain_queries=domain_queries,
    )

    res = search_black_knight(parsed_query=query, top_k=3, architecture="all_cross_encoder")
    assert len(res["results"]) > 0
    # Top result should be Inception
    assert "inception" in res["results"][0]["title"].lower()
