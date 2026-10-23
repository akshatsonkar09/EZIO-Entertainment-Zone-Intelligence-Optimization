from pathlib import Path
import pandas as pd
import chromadb
import pytest


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PROCESSED_DIR = DATA_DIR / "processed"


def test_processed_clean_files_exist():
    expected_files = [
        "movie_metadata_clean.csv",
        "anime_metadata_clean.csv",
        "book_metadata_clean.csv",
    ]
    for fname in expected_files:
        fpath = PROCESSED_DIR / fname
        assert fpath.exists(), f"Missing clean dataset: {fname}"
        assert fpath.stat().st_size > 1000, f"File {fname} is too small or empty"

    # Music clean dataset must not exist in active processed directory
    assert not (PROCESSED_DIR / "music_metadata_clean.csv").exists()


def test_movie_metadata_clean_schema():
    df = pd.read_csv(PROCESSED_DIR / "movie_metadata_clean.csv")
    required_cols = {"title", "genres", "release_year", "runtime"}
    assert required_cols.issubset(set(df.columns))
    assert len(df) > 0


def test_book_metadata_clean_schema():
    df = pd.read_csv(PROCESSED_DIR / "book_metadata_clean.csv")
    required_cols = {"title", "author", "rating", "pages", "release_year"}
    assert required_cols.issubset(set(df.columns))
    assert len(df) > 0
    # Pages should be coercible to numeric
    numeric_pages = pd.to_numeric(df["pages"], errors="coerce")
    assert numeric_pages.notna().sum() > 10000


def test_chroma_collections():
    chroma_path = DATA_DIR / "chroma"
    assert chroma_path.exists(), "Chroma DB path missing"

    client = chromadb.PersistentClient(path=str(chroma_path))
    coll_names = {c.name for c in client.list_collections()}
    expected_colls = {"movies", "animes", "books"}

    assert expected_colls.issubset(coll_names), f"Missing collections. Found: {coll_names}"
    assert "music" not in coll_names, "Music collection must not exist in active ChromaDB"

    for coll_name in expected_colls:
        count = client.get_collection(coll_name).count()
        assert count > 0, f"Collection {coll_name} is empty"
