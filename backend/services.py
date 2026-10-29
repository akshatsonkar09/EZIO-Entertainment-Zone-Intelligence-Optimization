"""
Backend service and adapter layer for Project Black Knight.
Integrates FastAPI endpoints directly with the existing retrieval pipeline,
metadata filters, and catalog datasets without altering core algorithms.
"""

from __future__ import annotations

import json
import math
import random
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd

# Add src and project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from project_black_knight.retrieval import _REPO, search_black_knight, SUPPORTED_DOMAINS
from project_black_knight.query_parser import parse_query
from project_black_knight.query_schema import (
    BlackKnightQuery,
    CommonQuery,
    DomainQueries,
    MovieQuery,
    AnimeQuery,
    BookQuery,
)
from project_black_knight.metadata_filter import get_valid_ids

from .schemas import (
    BrowseRequest,
    ItemDetail,
    MetadataCategoriesResponse,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
)


class CatalogManager:
    """Manages lazy-loaded catalog overviews, synopses, and genre listings."""

    def __init__(self, data_dir: Path = PROJECT_ROOT / "data" / "processed"):
        self.data_dir = data_dir
        self._movie_overview_df: pd.DataFrame | None = None
        self._anime_synopsis_df: pd.DataFrame | None = None
        self._book_description_df: pd.DataFrame | None = None
        self._categories_cache: MetadataCategoriesResponse | None = None

    def get_overview(self, domain: str, index: int) -> str | None:
        """Retrieve overview/synopsis/description text from source dataset."""
        try:
            if domain == "movie":
                if self._movie_overview_df is None:
                    pkl_path = self.data_dir / "movies1234.pkl"
                    if pkl_path.exists():
                        self._movie_overview_df = pd.read_pickle(pkl_path)
                    else:
                        self._movie_overview_df = pd.read_pickle(self.data_dir / "movies.pkl")
                if 0 <= index < len(self._movie_overview_df):
                    val = self._movie_overview_df.iloc[index].get("overview")
                    if isinstance(val, str) and val.strip() and val.lower() != "nan":
                        return val.strip()

            elif domain == "anime":
                if self._anime_synopsis_df is None:
                    self._anime_synopsis_df = pd.read_pickle(self.data_dir / "anime.pkl")
                if 0 <= index < len(self._anime_synopsis_df):
                    val = self._anime_synopsis_df.iloc[index].get("synopsis")
                    if isinstance(val, str) and val.strip() and val.lower() != "nan":
                        return val.strip()

            elif domain == "book":
                if self._book_description_df is None:
                    self._book_description_df = pd.read_pickle(self.data_dir / "books.pkl")
                if 0 <= index < len(self._book_description_df):
                    val = self._book_description_df.iloc[index].get("Description")
                    if isinstance(val, str) and val.strip() and val.lower() != "nan":
                        return val.strip()
        except Exception:
            pass
        return None

    def get_categories(self) -> MetadataCategoriesResponse:
        """Extract and cache unique genres and year ranges from real catalog data."""
        if self._categories_cache is not None:
            return self._categories_cache

        genres_per_domain: dict[str, list[str]] = {}
        years_per_domain: dict[str, dict[str, int | None]] = {}

        for domain in SUPPORTED_DOMAINS:
            df = _REPO.get_metadata_df(domain)
            genres_set: set[str] = set()

            # Extract genres
            if "genres" in df.columns:
                raw_genres = df["genres"].dropna().astype(str).tolist()
                for item in raw_genres:
                    if domain == "anime":
                        # Anime clean metadata genres are space-separated or comma-separated
                        parts = re.split(r"[,/]\s*|\s{2,}", item)
                        for part in parts:
                            p = part.strip()
                            if p and len(p) > 1 and not p.isdigit():
                                genres_set.add(p)
                    else:
                        for part in item.split(","):
                            p = part.strip().strip("'\"[]")
                            if p and len(p) > 1 and not p.isdigit():
                                genres_set.add(p)

            # Extract year range
            min_yr, max_yr = None, None
            if "release_year" in df.columns:
                valid_yrs = df["release_year"].dropna()
                valid_yrs = valid_yrs[valid_yrs > 1800]
                if not valid_yrs.empty:
                    min_yr = int(valid_yrs.min())
                    max_yr = int(valid_yrs.max())

            genres_per_domain[domain] = sorted(list(genres_set))
            years_per_domain[domain] = {"min": min_yr, "max": max_yr}

        self._categories_cache = MetadataCategoriesResponse(
            domains=list(SUPPORTED_DOMAINS),
            genres=genres_per_domain,
            years=years_per_domain,
        )
        return self._categories_cache


_CATALOG_MGR = CatalogManager()


def search_content(request: SearchRequest) -> SearchResponse:
    """Execute search query using the real Project Black Knight search pipeline."""
    clean_query = request.query.strip()
    if not clean_query:
        raise ValueError("Query string cannot be empty or whitespace only.")

    target_domain = request.domain if request.domain and request.domain != "all" else None

    # Parse query using real LLM parser, with graceful fallback on rate limits
    parsed = None
    try:
        parsed = parse_query(clean_query)
        if target_domain:
            parsed.media_types = [target_domain]
    except Exception:
        # Resilient fallback if LLM endpoint encounters network/rate limit
        media_types = [target_domain] if target_domain else ["movie", "anime", "book"]
        parsed = BlackKnightQuery(
            media_types=media_types[:2],
            common=CommonQuery(),
            domain_queries=DomainQueries(),
            semantic_query=clean_query,
            similar_to=[],
        )

    # Execute search pipeline (preserves exact rank ordering)
    raw_response = search_black_knight(
        user_query=clean_query,
        top_k=request.top_k,
        parsed_query=parsed,
    )

    results_items: list[SearchResultItem] = []
    for item in raw_response.get("results", []):
        item_id = str(item["id"])
        domain = item.get("media_type") or item_id.split("_")[0]
        
        # Parse index for overview lookup
        overview = None
        try:
            idx = int(item_id.split("_")[1])
            overview = _CATALOG_MGR.get_overview(domain, idx)
        except Exception:
            pass

        # Extract extra compact fields from catalog
        extra: dict[str, Any] = {}
        try:
            idx = int(item_id.split("_")[1])
            df = _REPO.get_metadata_df(domain)
            if 0 <= idx < len(df):
                row = df.iloc[idx].to_dict()
                if domain == "movie":
                    if row.get("director") and str(row["director"]).lower() != "nan":
                        extra["director"] = str(row["director"])
                    if row.get("runtime") and not pd.isna(row["runtime"]):
                        extra["runtime"] = f"{int(row['runtime'])} min"
                elif domain == "anime":
                    if row.get("episodes") and not pd.isna(row["episodes"]):
                        extra["episodes"] = f"{int(row['episodes'])} eps"
                    if row.get("ranking") and not pd.isna(row["ranking"]):
                        extra["ranking"] = f"Rank #{int(row['ranking'])}"
                elif domain == "book":
                    if row.get("author") and str(row["author"]).lower() != "nan":
                        extra["author"] = str(row["author"])
                    if row.get("rating") and not pd.isna(row["rating"]):
                        extra["rating"] = f"★ {float(row['rating']):.2f}"
                    if row.get("pages") and not pd.isna(row["pages"]):
                        extra["pages"] = f"{int(row['pages'])} pages"
        except Exception:
            pass

        results_items.append(
            SearchResultItem(
                id=item_id,
                title=item.get("title", "Untitled"),
                media_type=domain,
                score=float(item.get("score", 0.0)),
                release_year=item.get("release_year"),
                genres=item.get("genres"),
                overview=overview,
                extra=extra,
            )
        )

    return SearchResponse(
        user_query=clean_query,
        domain=target_domain,
        total_results=len(results_items),
        results=results_items,
    )


_ANIME_ALIAS_MAP: dict[str, str] | None = None


def _get_anime_alias_map() -> dict[str, str]:
    global _ANIME_ALIAS_MAP
    if _ANIME_ALIAS_MAP is None:
        map_path = PROJECT_ROOT / "data" / "processed" / "anime_canonical_id_map.json"
        if map_path.exists():
            try:
                with open(map_path, "r", encoding="utf-8") as f:
                    _ANIME_ALIAS_MAP = json.load(f)
            except Exception:
                _ANIME_ALIAS_MAP = {}
        else:
            _ANIME_ALIAS_MAP = {}
    return _ANIME_ALIAS_MAP


def get_item_by_id(item_id: str) -> ItemDetail:
    """Retrieve complete metadata for a catalog item by its canonical ID."""
    # Resolve aliases from prior duplicate records to their canonical ID
    alias_map = _get_anime_alias_map()
    if item_id in alias_map:
        item_id = alias_map[item_id]

    parts = item_id.split("_")
    if len(parts) != 2:
        raise ValueError(f"Invalid canonical item ID format: '{item_id}'. Expected '<domain>_<index>'.")

    domain, idx_str = parts[0], parts[1]
    if domain not in SUPPORTED_DOMAINS:
        raise ValueError(f"Unsupported media domain: '{domain}'. Must be one of {SUPPORTED_DOMAINS}.")

    try:
        index = int(idx_str)
    except ValueError:
        raise ValueError(f"Invalid item index in ID: '{item_id}'.")

    df = _REPO.get_metadata_df(domain)
    if index < 0 or index >= len(df):
        raise KeyError(f"Item ID '{item_id}' not found in catalog (index out of range).")

    row = df.iloc[index].to_dict()

    title = str(row.get("title", "Untitled"))
    release_year = row.get("release_year")
    if pd.isna(release_year):
        release_year = None
    else:
        try:
            release_year = int(float(release_year))
        except Exception:
            pass

    # Extract overview
    overview = _CATALOG_MGR.get_overview(domain, index)

    # Parse genres into a clean list
    genres_list: list[str] = []
    raw_genres = row.get("genres")
    if isinstance(raw_genres, str) and raw_genres.strip() and raw_genres.lower() != "nan":
        if domain == "anime":
            parts = re.split(r"[,/]\s*|\s{2,}", raw_genres)
            genres_list = [p.strip() for p in parts if p.strip()]
        else:
            genres_list = [g.strip().strip("'\"[]") for g in raw_genres.split(",") if g.strip()]

    # Collect clean, domain-specific non-empty metadata
    metadata: dict[str, Any] = {}
    for key, val in row.items():
        if key in ("title", "release_year", "genres"):
            continue
        if pd.isna(val) or val is None:
            continue
        val_str = str(val).strip()
        if not val_str or val_str.lower() in ("nan", "none", "[]", "{}"):
            continue

        # Format numeric floats nicely if whole numbers
        if isinstance(val, (float, int)):
            if isinstance(val, float) and val.is_integer():
                metadata[key] = int(val)
            else:
                metadata[key] = val
        else:
            metadata[key] = val_str

    return ItemDetail(
        id=item_id,
        media_type=domain,
        title=title,
        release_year=release_year,
        overview=overview,
        genres=genres_list,
        metadata=metadata,
    )


def get_random_item(domain: str | None = None) -> ItemDetail:
    """Uniformly select a random real item from the requested catalog."""
    chosen_domain = domain
    if not chosen_domain or chosen_domain == "any" or chosen_domain not in SUPPORTED_DOMAINS:
        chosen_domain = random.choice(list(SUPPORTED_DOMAINS))

    df = _REPO.get_metadata_df(chosen_domain)
    total_records = len(df)
    if total_records == 0:
        raise ValueError(f"No catalog records found for domain '{chosen_domain}'.")

    random_index = random.randint(0, total_records - 1)
    canonical_id = f"{chosen_domain}_{random_index}"
    return get_item_by_id(canonical_id)


def browse_by_metadata(request: BrowseRequest) -> SearchResponse:
    """Filter records by metadata attributes using existing filtering logic."""
    target_domains = [request.domain] if request.domain else list(SUPPORTED_DOMAINS)
    accumulated_results: list[SearchResultItem] = []

    per_domain_limit = math.ceil(request.limit / len(target_domains))

    for domain in target_domains:
        df = _REPO.get_metadata_df(domain)
        all_ids = [f"{domain}_{i}" for i in range(len(df))]

        domain_filters: dict[str, Any] = {}
        if request.release_year_min:
            domain_filters["release_year_min"] = request.release_year_min
        if request.release_year_max:
            domain_filters["release_year_max"] = request.release_year_max

        if request.genre:
            g_norm = request.genre.strip().lower()
            if g_norm == "informative":
                # Map 'Informative' to real catalog categories per domain
                if domain == "movie":
                    domain_filters["genres_include"] = ["documentary"]
                elif domain == "anime":
                    domain_filters["genres_include"] = ["historical"]
                elif domain == "book":
                    domain_filters["genres_include"] = ["nonfiction"]
            else:
                domain_filters["genres_include"] = [request.genre]
        
        valid_id_set = get_valid_ids(
            dataframe=df,
            current_ids=all_ids,
            filters=domain_filters,
            media_type=domain,
        )

        matched_ids = [cid for cid in all_ids if cid in valid_id_set][:per_domain_limit]

        for cid in matched_ids:
            idx = int(cid.split("_")[1])
            row = df.iloc[idx]
            overview = _CATALOG_MGR.get_overview(domain, idx)
            
            extra: dict[str, Any] = {}
            if domain == "movie":
                if row.get("director") and str(row["director"]).lower() != "nan":
                    extra["director"] = str(row["director"])
                if row.get("runtime") and not pd.isna(row["runtime"]):
                    extra["runtime"] = f"{int(row['runtime'])} min"
            elif domain == "anime":
                if row.get("episodes") and not pd.isna(row["episodes"]):
                    extra["episodes"] = f"{int(row['episodes'])} eps"
                if row.get("ranking") and not pd.isna(row["ranking"]):
                    extra["ranking"] = f"Rank #{int(row['ranking'])}"
            elif domain == "book":
                if row.get("author") and str(row["author"]).lower() != "nan":
                    extra["author"] = str(row["author"])
                if row.get("rating") and not pd.isna(row["rating"]):
                    extra["rating"] = f"★ {float(row['rating']):.2f}"
                if row.get("pages") and not pd.isna(row["pages"]):
                    extra["pages"] = f"{int(row['pages'])} pages"

            rel_year = row.get("release_year")
            if pd.isna(rel_year):
                rel_year = None
            else:
                try:
                    rel_year = int(float(rel_year))
                except Exception:
                    pass

            accumulated_results.append(
                SearchResultItem(
                    id=cid,
                    title=str(row.get("title", "Untitled")),
                    media_type=domain,
                    score=1.0,  # Exact metadata match
                    release_year=rel_year,
                    genres=str(row.get("genres", "")),
                    overview=overview,
                    extra=extra,
                )
            )

    return SearchResponse(
        user_query=f"Browse metadata: {request.model_dump(exclude_none=True)}",
        domain=request.domain,
        total_results=len(accumulated_results),
        results=accumulated_results[: request.limit],
    )


def get_metadata_categories() -> MetadataCategoriesResponse:
    """Retrieve available metadata categories from catalog manager."""
    return _CATALOG_MGR.get_categories()
