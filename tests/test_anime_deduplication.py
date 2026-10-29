"""
Regression tests for Anime Dataset Deduplication and Canonical Identity Preservation.

Validates:
1. Anime dataset has zero duplicate source UIDs in processed catalogs.
2. Searching for 'alchemist' returns 'Fullmetal Alchemist (2003)' exactly once.
3. Canonical item IDs are preserved:
   - Fullmetal Alchemist (2003): anime_499
   - Fullmetal Alchemist: Brotherhood (2009): anime_3
   - Fullmetal Alchemist: Brotherhood Specials: anime_339
   - Cowboy Bebop: anime_750
   - Shingeki no Kyojin: anime_667
4. Genuinely distinct catalog items (different seasons, specials, adaptations)
   are preserved and not merged.
5. Backwards-compatible alias resolution: looking up a former duplicate ID
   resolves to the canonical entity.
"""

from pathlib import Path
import pandas as pd
import pytest

from project_black_knight.retrieval import RetrievalRepository, search_black_knight
from project_black_knight.query_schema import BlackKnightQuery, CommonQuery, DomainQueries
from backend.services import get_item_by_id

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"


@pytest.fixture(scope="module")
def repo():
    return RetrievalRepository()


def test_anime_no_duplicate_uids():
    """Verify that processed anime catalogs have 0 duplicate UIDs."""
    df_clean = pd.read_csv(DATA_DIR / "anime_metadata_clean.csv")
    df_pkl = pd.read_pickle(DATA_DIR / "anime.pkl")
    df_tag2 = pd.read_pickle(DATA_DIR / "anime_tag2.pkl")

    assert len(df_clean) == 15453
    assert len(df_pkl) == 15453
    assert len(df_tag2) == 15453

    assert df_pkl["uid"].is_unique, "anime.pkl contains duplicate UIDs!"
    assert df_clean["title"].isna().sum() == 0, "Missing titles found!"


def test_canonical_ids_preserved():
    """Verify key canonical IDs remain aligned with the catalog."""
    df_clean = pd.read_csv(DATA_DIR / "anime_metadata_clean.csv")

    assert df_clean.iloc[499]["title"] == "Fullmetal Alchemist"
    assert int(float(df_clean.iloc[499]["release_year"])) == 2003

    assert df_clean.iloc[3]["title"] == "Fullmetal Alchemist: Brotherhood"
    assert int(float(df_clean.iloc[3]["release_year"])) == 2009

    assert df_clean.iloc[339]["title"] == "Fullmetal Alchemist: Brotherhood Specials"
    assert df_clean.iloc[750]["title"] == "Cowboy Bebop"
    assert df_clean.iloc[667]["title"] == "Shingeki no Kyojin"


def test_alchemist_search_no_duplicates(repo):
    """Verify searching for 'alchemist' returns Fullmetal Alchemist exactly once."""
    query = BlackKnightQuery(
        media_types=["anime"],
        common=CommonQuery(),
        domain_queries=DomainQueries(),
        semantic_query="alchemist",
        similar_to=[],
    )
    res = search_black_knight("alchemist", top_k=20, parsed_query=query, repo=repo)
    results = res["results"]

    # Check for exact title Fullmetal Alchemist
    fma_2003_results = [r for r in results if r["title"] == "Fullmetal Alchemist"]
    assert len(fma_2003_results) == 1, (
        f"Expected 'Fullmetal Alchemist' once, found {len(fma_2003_results)}: "
        f"{[r['id'] for r in fma_2003_results]}"
    )
    assert fma_2003_results[0]["id"] == "anime_499"

    # Check that Brotherhood also appears at most once
    bro_results = [r for r in results if r["title"] == "Fullmetal Alchemist: Brotherhood"]
    assert len(bro_results) <= 1


def test_distinct_anime_works_preserved(repo):
    """Verify that different adaptations, seasons, and specials remain distinct catalog entries."""
    df_clean = pd.read_csv(DATA_DIR / "anime_metadata_clean.csv")

    # Fullmetal Alchemist vs Fullmetal Alchemist: Brotherhood vs Brotherhood Specials
    fma_idx = df_clean[df_clean["title"] == "Fullmetal Alchemist"].index.tolist()
    bro_idx = df_clean[df_clean["title"] == "Fullmetal Alchemist: Brotherhood"].index.tolist()
    spec_idx = df_clean[df_clean["title"] == "Fullmetal Alchemist: Brotherhood Specials"].index.tolist()

    assert len(fma_idx) == 1
    assert len(bro_idx) == 1
    assert len(spec_idx) == 1
    assert fma_idx[0] != bro_idx[0] != spec_idx[0]

    # K-On! vs K-On!!
    kon1 = df_clean[df_clean["title"] == "K-On!"].index.tolist()
    kon2 = df_clean[df_clean["title"] == "K-On!!"].index.tolist()
    assert len(kon1) == 1 and len(kon2) == 1 and kon1[0] != kon2[0]


def test_alias_resolution():
    """Verify that looking up a former duplicate ID resolves to its canonical record."""
    # anime_9220 was duplicate of anime_499 (Fullmetal Alchemist)
    item = get_item_by_id("anime_9220")
    assert item is not None
    assert item.title == "Fullmetal Alchemist"
    assert item.release_year == 2003
    assert item.id == "anime_499"
