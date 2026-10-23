"""
Deterministic regression tests for genre canonicalization, domain equivalents,
compound rules, and hard-filter preservation (Phase 3B).

Covers:
1. Every approved lexical alias.
2. Domain-specific mappings across movie, anime, and book catalogs.
3. The three confirmed product decisions (Fiction, Detective, Middle Grade).
4. Compound genre AND semantics (rom-com, action-adventure, etc.).
5. Strict separation of related but distinct genres (Mystery vs Crime vs Thriller).
6. Token-boundary safety (preventing false-positive substring leaks).
7. Genre inclusions and exclusions.
8. Unknown, unsupported, and narrative descriptor handling.
9. Mixed-domain query isolation.
10. Direct parsed-query and parser-produced query paths.
11. Architecture A and Architecture B retrieval execution.
12. Title normalization integration with active genre constraints.
"""

import pandas as pd
import pytest

from project_black_knight.metadata_filter import (
    COMPOUND_GENRE_RULES,
    DOMAIN_EQUIVALENTS,
    LEXICAL_CANONICAL_MAP,
    get_valid_ids,
    is_bypassed_genre_filter,
    match_genre,
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
# Fixtures
# --------------------------------------------------

@pytest.fixture
def movie_sample_df():
    return pd.DataFrame([
        {"id": "m1", "title": "Inception", "genres": "Action, Adventure, ScienceFiction", "release_year": 2010},
        {"id": "m2", "title": "The Godfather", "genres": "Crime, Drama", "release_year": 1972},
        {"id": "m3", "title": "Knives Out", "genres": "Comedy, Mystery, Drama", "release_year": 2019},
        {"id": "m4", "title": "When Harry Met Sally", "genres": "Comedy, Romance", "release_year": 1989},
        {"id": "m5", "title": "Toy Story", "genres": "Animation, Comedy, Family", "release_year": 1995},
        {"id": "m6", "title": "Schindler's List", "genres": "Drama, History, War", "release_year": 1993},
        {"id": "m7", "title": "Star Wars: A New Hope", "genres": "Adventure, ScienceFiction", "release_year": 1977},
        {"id": "m8", "title": "Early Warning", "genres": "Drama, Thriller", "release_year": 1981},
        {"id": "m9", "title": "Chemical Reaction", "genres": "Documentary", "release_year": 2009},
    ])


@pytest.fixture
def anime_sample_df():
    return pd.DataFrame([
        {"id": "a1", "title": "Cowboy Bebop", "genres": "Action Adventure Comedy Drama Sci-Fi Space", "release_year": 1998},
        {"id": "a2", "title": "Mobile Suit Gundam", "genres": "Action Military Mecha Sci-Fi", "release_year": 1979},
        {"id": "a3", "title": "Death Note", "genres": "Mystery Psychological Supernatural Thriller", "release_year": 2006},
        {"id": "a4", "title": "Pokemon", "genres": "Action Adventure Comedy Fantasy Kids", "release_year": 1997},
        {"id": "a5", "title": "Rurouni Kenshin", "genres": "Action Adventure Comedy Historical Romance Samurai", "release_year": 1996},
        {"id": "a6", "title": "Toradora!", "genres": "Comedy Romance Slice of Life", "release_year": 2008},
        {"id": "a7", "title": "Mechanical Puppet Show", "genres": "Kids Fantasy", "release_year": 2015},
    ])


@pytest.fixture
def book_sample_df():
    return pd.DataFrame([
        {"id": "b1", "title": "Dune", "genres": "Science Fiction, Fantasy, Fiction", "release_year": 1965},
        {"id": "b2", "title": "1984", "genres": "Classics, Dystopia, Fiction, Science Fiction", "release_year": 1949},
        {"id": "b3", "title": "The Hound of the Baskervilles", "genres": "Classics, Crime, Detective, Fiction, Mystery", "release_year": 1902},
        {"id": "b4", "title": "The Lightning Thief", "genres": "Fantasy, Fiction, Middle Grade, Mythology, Young Adult", "release_year": 2005},
        {"id": "b5", "title": "Where the Wild Things Are", "genres": "Childrens, Classics, Picture Books", "release_year": 1963},
        {"id": "b6", "title": "All the Light We Cannot See", "genres": "Fiction, Historical, Historical Fiction, War", "release_year": 2014},
        {"id": "b7", "title": "A People's History of the United States", "genres": "History, Nonfiction, Politics", "release_year": 1980},
        {"id": "b8", "title": "Twilight", "genres": "Fantasy, Fiction, Paranormal, Romance, Young Adult", "release_year": 2005},
        {"id": "b9", "title": "Nonfiction Tech Manual", "genres": "Computers, Nonfiction, Technology", "release_year": 2020},
    ])


# --------------------------------------------------
# 1. Lexical Aliases
# --------------------------------------------------

def test_lexical_aliases_science_fiction():
    """All approved science fiction aliases must resolve across all domains."""
    aliases = ["sci-fi", "scifi", "science-fiction", "sciencefiction", "science fiction"]
    for alias in aliases:
        assert match_genre(alias, "Action, ScienceFiction", media_type="movie")
        assert match_genre(alias, "Sci-Fi Action", media_type="anime")
        assert match_genre(alias, "Science Fiction, Adventure", media_type="book")


def test_lexical_aliases_other():
    """Approved aliases for dystopia, slice of life, super power, and tv movie."""
    assert match_genre("dystopian", "Classics, Dystopia, Fiction", media_type="book")
    assert match_genre("dystopia", "Classics, Dystopia, Fiction", media_type="book")

    assert match_genre("slice-of-life", "Comedy Romance Slice of Life", media_type="anime")
    assert match_genre("slice of life", "Comedy Romance Slice of Life", media_type="anime")
    assert match_genre("sliceoflife", "Comedy Romance Slice of Life", media_type="anime")

    assert match_genre("super-power", "Action Super Power", media_type="anime")
    assert match_genre("superpower", "Action Super Power", media_type="anime")

    assert match_genre("tv-movie", "Drama, TVMovie", media_type="movie")
    assert match_genre("tv movie", "Drama, TVMovie", media_type="movie")

    assert match_genre("non-fiction", "History, Nonfiction, Politics", media_type="book")
    assert match_genre("nonfiction", "History, Nonfiction, Politics", media_type="book")


# --------------------------------------------------
# 2. Domain-Specific Equivalents
# --------------------------------------------------

def test_domain_equivalents_family_kids_childrens(movie_sample_df, anime_sample_df, book_sample_df):
    """
    Family in movies -> 'Family'
    Kids/Family in anime -> 'Kids'
    Childrens/Kids in books -> 'Childrens'
    """
    # Movie: kids and childrens map to Family (Toy Story)
    res_mov_kids = get_valid_ids(movie_sample_df, movie_sample_df["id"].tolist(), {"genres_include": ["kids"]}, "movie")
    assert "m5" in res_mov_kids
    res_mov_child = get_valid_ids(movie_sample_df, movie_sample_df["id"].tolist(), {"genres_include": ["childrens"]}, "movie")
    assert "m5" in res_mov_child

    # Anime: family maps to Kids (Pokemon)
    res_ani_fam = get_valid_ids(anime_sample_df, anime_sample_df["id"].tolist(), {"genres_include": ["family"]}, "anime")
    assert "a4" in res_ani_fam

    # Book: kids and childrens map to Childrens (Where the Wild Things Are)
    res_bk_kids = get_valid_ids(book_sample_df, book_sample_df["id"].tolist(), {"genres_include": ["kids"]}, "book")
    assert "b5" in res_bk_kids


def test_domain_equivalents_history(movie_sample_df, anime_sample_df, book_sample_df):
    """
    Movies use 'History'
    Anime uses 'Historical'
    Books distinguish 'History' (nonfiction) and 'Historical Fiction'
    """
    # Movie: historical resolves to History (Schindler's List)
    res_m = get_valid_ids(movie_sample_df, movie_sample_df["id"].tolist(), {"genres_include": ["historical"]}, "movie")
    assert "m6" in res_m

    # Anime: history resolves to Historical (Rurouni Kenshin)
    res_a = get_valid_ids(anime_sample_df, anime_sample_df["id"].tolist(), {"genres_include": ["history"]}, "anime")
    assert "a5" in res_a

    # Books: historical fiction specifically matches historical novel (b6), not nonfiction history (b7)
    res_b_hf = get_valid_ids(book_sample_df, book_sample_df["id"].tolist(), {"genres_include": ["historical fiction"]}, "book")
    assert "b6" in res_b_hf
    assert "b7" not in res_b_hf


def test_domain_equivalents_supernatural_paranormal(anime_sample_df, book_sample_df):
    """Anime uses Supernatural; Books have Paranormal and Supernatural."""
    # Anime: paranormal resolves to Supernatural (Death Note)
    res_a = get_valid_ids(anime_sample_df, anime_sample_df["id"].tolist(), {"genres_include": ["paranormal"]}, "anime")
    assert "a3" in res_a

    # Book: paranormal matches Twilight
    res_b = get_valid_ids(book_sample_df, book_sample_df["id"].tolist(), {"genres_include": ["paranormal"]}, "book")
    assert "b8" in res_b


def test_domain_equivalents_anime_to_movie_animation(movie_sample_df):
    """Querying anime as a genre filter in movie domain maps to Animation."""
    res = get_valid_ids(movie_sample_df, movie_sample_df["id"].tolist(), {"genres_include": ["anime"]}, "movie")
    assert "m5" in res  # Toy Story has Animation


# --------------------------------------------------
# 3. Confirmed Product Decisions: A, B, C
# --------------------------------------------------

def test_decision_a_fiction_constraint(book_sample_df, movie_sample_df, anime_sample_df):
    """
    Decision A:
    - Books: Fiction is an active hard filter.
    - Movies and Anime: Fiction must NOT act as a hard genre filter.
    - Preserves other valid constraints.
    """
    # Books: Fiction filters to fiction titles (b1..b6, b8), excludes nonfiction tech (b9)
    b_ids = book_sample_df["id"].tolist()
    res_book = get_valid_ids(book_sample_df, b_ids, {"genres_include": ["fiction"]}, "book")
    assert "b1" in res_book
    assert "b9" not in res_book

    # Movie-only query with Fiction: does NOT act as a hard filter (all movies retained)
    m_ids = movie_sample_df["id"].tolist()
    res_movie = get_valid_ids(movie_sample_df, m_ids, {"genres_include": ["fiction"]}, "movie")
    assert len(res_movie) == len(m_ids)

    # Movie query with Fiction + Action: Action is enforced, Fiction is bypassed
    res_movie_act = get_valid_ids(movie_sample_df, m_ids, {"genres_include": ["fiction", "action"]}, "movie")
    assert "m1" in res_movie_act  # Inception (Action)
    assert "m2" not in res_movie_act  # Godfather is Crime, Drama (no Action)

    # Anime-only query with Fiction: bypassed
    a_ids = anime_sample_df["id"].tolist()
    res_anime = get_valid_ids(anime_sample_df, a_ids, {"genres_include": ["fiction"]}, "anime")
    assert len(res_anime) == len(a_ids)


def test_decision_b_detective_narrow_to_broad(movie_sample_df, anime_sample_df, book_sample_df):
    """
    Decision B:
    - Books: matches Detective and Mystery.
    - Movies and Anime: resolves detective to Mystery.
    - Mystery does NOT require Detective.
    - Crime does NOT automatically match Mystery.
    """
    # Detective in movies resolves to Mystery (Knives Out has Mystery)
    m_ids = movie_sample_df["id"].tolist()
    res_m = get_valid_ids(movie_sample_df, m_ids, {"genres_include": ["detective"]}, "movie")
    assert "m3" in res_m  # Knives Out
    assert "m2" not in res_m  # Godfather (Crime) must NOT match

    # Detective in anime resolves to Mystery (Death Note has Mystery)
    a_ids = anime_sample_df["id"].tolist()
    res_a = get_valid_ids(anime_sample_df, a_ids, {"genres_include": ["detective"]}, "anime")
    assert "a3" in res_a

    # Books: detective matches Sherlock Holmes (b3)
    b_ids = book_sample_df["id"].tolist()
    res_b = get_valid_ids(book_sample_df, b_ids, {"genres_include": ["detective"]}, "book")
    assert "b3" in res_b

    # Mystery does NOT require Detective label (Knives Out has Mystery, no Detective)
    res_mys = get_valid_ids(movie_sample_df, m_ids, {"genres_include": ["mystery"]}, "movie")
    assert "m3" in res_mys

    # Crime alone does NOT match Mystery
    res_crime = get_valid_ids(movie_sample_df, m_ids, {"genres_include": ["crime"]}, "movie")
    assert "m2" in res_crime  # Godfather is Crime
    assert "m3" not in res_crime  # Knives Out is Mystery, not Crime


def test_decision_c_middle_grade_constraint(book_sample_df, anime_sample_df, movie_sample_df):
    """
    Decision C:
    - Books: matches Middle Grade catalog tag.
    - Anime and Movies: does NOT act as a hard filter (bypassed).
    - Preserves other valid constraints (e.g. Adventure).
    - Does NOT map Middle Grade to Family, Kids, or Childrens.
    """
    # Books: matches The Lightning Thief (b4)
    b_ids = book_sample_df["id"].tolist()
    res_b = get_valid_ids(book_sample_df, b_ids, {"genres_include": ["middle grade"]}, "book")
    assert "b4" in res_b
    assert "b5" not in res_b  # Where the Wild Things Are is Childrens, NOT Middle Grade

    # Anime with Middle Grade: does NOT filter out all anime
    a_ids = anime_sample_df["id"].tolist()
    res_a_pure = get_valid_ids(anime_sample_df, a_ids, {"genres_include": ["middle grade"]}, "anime")
    assert len(res_a_pure) == len(a_ids)

    # Anime with Middle Grade + Adventure: Adventure constraint is enforced!
    res_a_adv = get_valid_ids(anime_sample_df, a_ids, {"genres_include": ["middle grade", "adventure"]}, "anime")
    assert "a1" in res_a_adv  # Cowboy Bebop (Adventure)
    assert "a3" not in res_a_adv  # Death Note (no Adventure)

    # Movies with Middle Grade: bypassed, does not return zero
    m_ids = movie_sample_df["id"].tolist()
    res_m = get_valid_ids(movie_sample_df, m_ids, {"genres_include": ["middle grade"]}, "movie")
    assert len(res_m) == len(m_ids)


# --------------------------------------------------
# 4. Compound Genres AND Semantics
# --------------------------------------------------

def test_compound_genre_rom_com(movie_sample_df):
    """rom-com requires BOTH Romance AND Comedy."""
    m_ids = movie_sample_df["id"].tolist()
    res = get_valid_ids(movie_sample_df, m_ids, {"genres_include": ["rom-com"]}, "movie")
    assert "m4" in res  # When Harry Met Sally (Comedy, Romance)
    assert "m3" not in res  # Knives Out (Comedy, no Romance)

    # Query for romance alone does NOT require comedy
    assert match_genre("romance", "Drama, Romance", media_type="movie")
    assert match_genre("comedy", "Comedy, Horror", media_type="movie")


def test_compound_genre_action_adventure(movie_sample_df):
    """action-adventure requires BOTH Action AND Adventure."""
    m_ids = movie_sample_df["id"].tolist()
    res = get_valid_ids(movie_sample_df, m_ids, {"genres_include": ["action-adventure"]}, "movie")
    assert "m1" in res  # Inception (Action, Adventure, ScienceFiction)

    # Action alone does NOT require Adventure
    assert match_genre("action", "Action, Crime", media_type="movie")
    # Row with Action alone does not match action-adventure
    assert not match_genre("action-adventure", "Action, Crime", media_type="movie")


def test_compound_genre_variants():
    """Spaced, hyphenated, and slurred compound forms."""
    assert match_genre("romantic comedy", "Comedy, Romance")
    assert match_genre("romcom", "Comedy, Romance")
    assert match_genre("action adventure", "Action, Adventure")
    assert match_genre("comedy-drama", "Comedy, Drama")
    assert match_genre("dramedy", "Comedy, Drama")
    assert match_genre("sci-fi fantasy", "Science Fiction, Fantasy")


# --------------------------------------------------
# 5. Strict Separation of Related Genres
# --------------------------------------------------

def test_strict_genre_separation():
    """Verify distinct genres do not cross-match."""
    # Mystery vs Crime vs Thriller
    assert not match_genre("mystery", "Crime, Drama", media_type="movie")
    assert not match_genre("crime", "Mystery, Drama", media_type="movie")
    assert not match_genre("thriller", "Mystery, Drama", media_type="movie")

    # Science Fiction vs Space / Mecha / Cyberpunk
    assert not match_genre("science fiction", "Space, Documentary", media_type="movie")
    assert not match_genre("science fiction", "Mecha, Action", media_type="anime")
    assert not match_genre("space", "Science Fiction, Drama", media_type="book")
    assert not match_genre("mecha", "Science Fiction, Action", media_type="anime")

    # Psychological vs Thriller
    assert not match_genre("psychological", "Thriller, Drama", media_type="movie")


# --------------------------------------------------
# 6. Token-Boundary Safety
# --------------------------------------------------

def test_token_boundary_safety(movie_sample_df, anime_sample_df):
    """Prevent substring false positives."""
    m_ids = movie_sample_df["id"].tolist()

    # 'war' must not match 'Star Wars' or 'Warning'
    res_war = get_valid_ids(movie_sample_df, m_ids, {"genres_include": ["war"]}, "movie")
    assert "m6" in res_war  # Schindler's List has War
    assert "m7" not in res_war  # Star Wars must NOT match
    assert "m8" not in res_war  # Early Warning must NOT match

    # 'action' must not match 'Reaction'
    res_act = get_valid_ids(movie_sample_df, m_ids, {"genres_include": ["action"]}, "movie")
    assert "m1" in res_act
    assert "m9" not in res_act  # Chemical Reaction must NOT match

    # 'mecha' must not match 'Mechanical Puppet Show'
    a_ids = anime_sample_df["id"].tolist()
    res_mecha = get_valid_ids(anime_sample_df, a_ids, {"genres_include": ["mecha"]}, "anime")
    assert "a2" in res_mecha  # Gundam
    assert "a7" not in res_mecha  # Mechanical Puppet Show must NOT match


# --------------------------------------------------
# 7. Inclusions and Exclusions
# --------------------------------------------------

def test_inclusions_and_exclusions(movie_sample_df):
    """Include Comedy, exclude Romance."""
    m_ids = movie_sample_df["id"].tolist()
    filters = {
        "genres_include": ["comedy"],
        "genres_exclude": ["romance"],
    }
    res = get_valid_ids(movie_sample_df, m_ids, filters, "movie")
    assert "m3" in res  # Knives Out (Comedy, Mystery)
    assert "m5" in res  # Toy Story (Animation, Comedy, Family)
    assert "m4" not in res  # When Harry Met Sally (Comedy, Romance) -> Excluded


# --------------------------------------------------
# 8. Unknown and Unsupported Genres
# --------------------------------------------------

def test_unknown_genre_returns_zero(movie_sample_df):
    """Unknown genre term must not match any row."""
    m_ids = movie_sample_df["id"].tolist()
    res = get_valid_ids(movie_sample_df, m_ids, {"genres_include": ["nonexistent_genre_xyz"]}, "movie")
    assert res == set()


def test_narrative_descriptors_bypassed_as_hard_filters(movie_sample_df):
    """Narrative descriptors like 'dark', 'grim', 'mind-bending' are semantic, not hard filters."""
    assert is_bypassed_genre_filter("dark", "movie")
    assert is_bypassed_genre_filter("mind-bending", "movie")
    assert is_bypassed_genre_filter("slow-burn", "movie")

    m_ids = movie_sample_df["id"].tolist()
    # Query with 'dark' + 'action': Action is enforced, 'dark' does not zero out the catalog
    res = get_valid_ids(movie_sample_df, m_ids, {"genres_include": ["dark", "action"]}, "movie")
    assert "m1" in res


# --------------------------------------------------
# 9. Mixed-Domain Query Isolation
# --------------------------------------------------

def test_mixed_domain_fiction_isolation():
    """
    In mixed-domain query (movie + book), Fiction constraint applies
    only to the book branch, not eliminating movie candidates.
    """
    common = CommonQuery(genres_include=["fiction", "sci-fi"])
    domain_queries = DomainQueries(movie=MovieQuery(), book=BookQuery())
    query = BlackKnightQuery(
        media_types=["movie", "book"],
        semantic_query="futuristic sci-fi world",
        common=common,
        domain_queries=domain_queries,
    )

    res = search_black_knight(parsed_query=query, top_k=5, architecture="domain_routed")
    assert "results" in res
    media_types_found = {r["media_type"] for r in res["results"]}
    # Both movie and book results should be present
    assert "movie" in media_types_found
    assert "book" in media_types_found


# --------------------------------------------------
# 10. Direct Parsed-Query vs Natural Language Path
# --------------------------------------------------

def test_direct_parsed_query_object():
    """Verify directly constructed BlackKnightQuery behaves identically to parsed query."""
    common = CommonQuery(genres_include=["rom-com"])
    domain_queries = DomainQueries(movie=MovieQuery())
    query = BlackKnightQuery(
        media_types=["movie"],
        semantic_query="romantic comedy",
        common=common,
        domain_queries=domain_queries,
    )

    res = search_black_knight(parsed_query=query, top_k=5, architecture="domain_routed")
    assert len(res["results"]) > 0
    for r in res["results"]:
        genres_lower = r["genres"].lower()
        assert "romance" in genres_lower
        assert "comedy" in genres_lower


# --------------------------------------------------
# 11. Architecture A and Architecture B Execution
# --------------------------------------------------

def test_architecture_a_and_b_with_genre_filters():
    """Both Architecture A and Architecture B must execute cleanly with canonical filters."""
    common = CommonQuery(genres_include=["science fiction"])
    domain_queries = DomainQueries(movie=MovieQuery())
    query = BlackKnightQuery(
        media_types=["movie"],
        semantic_query="space exploration",
        common=common,
        domain_queries=domain_queries,
    )

    res_a = search_black_knight(parsed_query=query, top_k=3, architecture="all_cross_encoder")
    res_b = search_black_knight(parsed_query=query, top_k=3, architecture="domain_routed")

    assert len(res_a["results"]) == 3
    assert len(res_b["results"]) == 3
    for r in res_a["results"]:
        assert any(g in r["genres"].lower() for g in ["sciencefiction", "sci-fi", "science fiction"])
    for r in res_b["results"]:
        assert any(g in r["genres"].lower() for g in ["sciencefiction", "sci-fi", "science fiction"])


# --------------------------------------------------
# 12. Title Normalization Integration with Active Genre Filter
# --------------------------------------------------

def test_title_normalization_with_genre_constraint():
    """Verify title normalization (diacritics, punctuation) functions alongside canonical genre filters."""
    sample_df = pd.DataFrame([
        {"id": "m1", "title": "Amélie", "release_year": 2001, "genres": "Romance, Comedy"},
        {"id": "m2", "title": "Amelie: The Sequel", "release_year": 2005, "genres": "Action"},
    ])
    ids = ["m1", "m2"]

    # Match normalized title 'Amelie' AND compound genre 'rom-com'
    filters = {
        "title": "Amelie",
        "genres_include": ["rom-com"],
    }
    res = get_valid_ids(sample_df, ids, filters, "movie")
    assert res == {"m1"}
