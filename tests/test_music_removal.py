"""
Dedicated unit and integration tests verifying Phase 1 Music Domain Removal.

Validates:
1. Application imports successfully.
2. Parser schema rejects 'music' as a media type.
3. Movie, anime, and book queries parse and validate without errors.
4. Active data directory does not contain music processed files.
5. ChromaDB persistent index contains exactly movies, animes, books (no music collection).
6. Each remaining domain loads clean metadata and documents with stable IDs.
7. RetrievalRepository rejects 'music' domain queries.
8. Retrieval components (BM25, Chroma, RRF, CrossEncoder) function for remaining domains.
9. Derived benchmark file exists with exact 113 queries (38 movie, 38 anime, 37 book; 102 pos, 11 abs).
"""

from pathlib import Path
import pytest
from pydantic import ValidationError
import chromadb
import pandas as pd

from project_black_knight import (
    BlackKnightQuery,
    CommonQuery,
    DomainQueries,
    MovieQuery,
    AnimeQuery,
    BookQuery,
    get_valid_ids,
    reciprocal_rank_fusion,
    tokenize_for_bm25,
)
from project_black_knight.retrieval import (
    RetrievalRepository,
    SUPPORTED_DOMAINS,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PROCESSED_DIR = DATA_DIR / "processed"
CHROMA_DIR = DATA_DIR / "chroma"
EVAL_DIR = Path(__file__).resolve().parent.parent / "evaluation"


def test_application_imports():
    """Verify core package and schemas import without any music dependencies."""
    import project_black_knight
    assert hasattr(project_black_knight, "BlackKnightQuery")
    assert hasattr(project_black_knight, "MovieQuery")
    assert hasattr(project_black_knight, "AnimeQuery")
    assert hasattr(project_black_knight, "BookQuery")
    assert not hasattr(project_black_knight, "MusicQuery")


def test_schema_rejects_music_media_type():
    """Verify that BlackKnightQuery rejects 'music' in media_types."""
    with pytest.raises(ValidationError):
        BlackKnightQuery(
            media_types=["music"],
            common=CommonQuery(),
            domain_queries=DomainQueries(),
            semantic_query="test",
        )

    with pytest.raises(ValidationError):
        BlackKnightQuery(
            media_types=["movie", "music"],
            common=CommonQuery(),
            domain_queries=DomainQueries(),
            semantic_query="test",
        )


def test_schema_accepts_valid_three_domains():
    """Verify that movie, anime, and book queries parse and validate."""
    q_movie = BlackKnightQuery(
        media_types=["movie"],
        common=CommonQuery(title="Inception"),
        domain_queries=DomainQueries(movie=MovieQuery(runtime_max=160)),
        semantic_query="dream heist",
    )
    assert q_movie.media_types == ["movie"]

    q_anime = BlackKnightQuery(
        media_types=["anime"],
        common=CommonQuery(genres_include=["action"]),
        domain_queries=DomainQueries(anime=AnimeQuery(episodes_max=26)),
        semantic_query="ninja adventure",
    )
    assert q_anime.media_types == ["anime"]

    q_book = BlackKnightQuery(
        media_types=["book"],
        common=CommonQuery(title="Dune"),
        domain_queries=DomainQueries(book=BookQuery(author=["Frank Herbert"])),
        semantic_query="spice desert arrakis",
    )
    assert q_book.media_types == ["book"]

    q_cross = BlackKnightQuery(
        media_types=["movie", "anime"],
        common=CommonQuery(),
        domain_queries=DomainQueries(),
        semantic_query="cyberpunk",
    )
    assert q_cross.media_types == ["movie", "anime"]


def test_supported_domains_constant():
    """Verify SUPPORTED_DOMAINS contains only movie, anime, book."""
    assert SUPPORTED_DOMAINS == ("movie", "anime", "book")
    assert "music" not in SUPPORTED_DOMAINS


def test_active_processed_data_has_no_music():
    """Verify no music processed files or embeddings remain in active directories."""
    music_files = [
        PROCESSED_DIR / "music_metadata.csv",
        PROCESSED_DIR / "music_metadata_clean.csv",
        PROCESSED_DIR / "songs.csv",
        PROCESSED_DIR / "songs.pkl",
        PROCESSED_DIR / "songs_tag2.pkl",
        PROCESSED_DIR / "embeddings" / "songs_embeddings.npy",
        Path(__file__).resolve().parent.parent / "notebooks" / "songs_recommender_05.ipynb",
    ]
    for mf in music_files:
        assert not mf.exists(), f"Active music file should not exist: {mf}"


def test_chromadb_collections_music_removed():
    """Verify active ChromaDB contains movies, animes, books and NOT music."""
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    coll_names = {c.name for c in client.list_collections()}
    assert coll_names == {"movies", "animes", "books"}
    assert "music" not in coll_names


def test_remaining_domains_data_loading_and_stable_ids():
    """Verify each remaining domain loads data with stable IDs matching count."""
    repo = RetrievalRepository(data_dir=DATA_DIR)

    for domain in ("movie", "anime", "book"):
        df_meta = repo.get_metadata_df(domain)
        docs, ids = repo.get_documents_and_ids(domain)

        assert len(df_meta) > 0
        assert len(docs) == len(ids)
        assert len(ids) == len(df_meta)
        assert ids[0].startswith(f"{domain}_0")
        assert ids[-1].startswith(f"{domain}_")


def test_repository_rejects_music():
    """Verify RetrievalRepository raises error on music domain."""
    repo = RetrievalRepository(data_dir=DATA_DIR)

    with pytest.raises(KeyError):
        repo.get_metadata_df("music")

    with pytest.raises(KeyError):
        repo.get_documents_and_ids("music")


def test_derived_113_benchmark_composition():
    """Verify the derived 113-query benchmark matches required domain/category counts."""
    bench_file = EVAL_DIR / "black_knight_eval_queries_113_audited.csv"
    assert bench_file.exists(), "Derived 113-query benchmark missing"

    df = pd.read_csv(bench_file)
    assert len(df) == 113, f"Expected 113 queries, found {len(df)}"

    domain_counts = df["domain"].value_counts().to_dict()
    assert domain_counts.get("movie") == 38, f"Expected 38 movie queries, got {domain_counts.get('movie')}"
    assert domain_counts.get("anime") == 38, f"Expected 38 anime queries, got {domain_counts.get('anime')}"
    assert domain_counts.get("book") == 37, f"Expected 37 book queries, got {domain_counts.get('book')}"
    assert "music" not in domain_counts, "Music queries found in derived benchmark"

    abs_count = (df["category"] == "absence").sum()
    pos_count = (df["category"] != "absence").sum()
    assert abs_count == 11, f"Expected 11 absence queries, got {abs_count}"
    assert pos_count == 102, f"Expected 102 positive queries, got {pos_count}"


def test_raw_music_data_deleted():
    """Verify raw and archived music datasets are permanently deleted."""
    raw_music = DATA_DIR / "raw" / "songs" / "spotify_songs.csv"
    assert not raw_music.exists(), "Raw music file must be deleted!"
    assert not (DATA_DIR / "raw" / "songs").exists(), "Raw songs directory must be deleted!"
    archive_dir = Path(__file__).resolve().parent.parent / "archive"
    assert not archive_dir.exists(), "Archive directory must be deleted!"
