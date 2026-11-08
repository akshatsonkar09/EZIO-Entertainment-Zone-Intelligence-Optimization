"""
Metadata filtering module for Project Black Knight.

Provides robust, type-safe filtering across all entertainment domains:
- movie
- anime
- book

Handles numeric conversions, missing/null values, case-insensitivity,
genre synonym expansion, and boundary conditions without mutating dataframes.
"""

import math
import re
from typing import Any
import pandas as pd

from .text_normalizer import normalize_title, normalize_title_key


# --------------------------------------------------
# Genre Canonicalization, Domain Equivalents & Compound Rules
# --------------------------------------------------

COMPOUND_GENRE_RULES: dict[str, list[str]] = {
    "rom-com": ["romance", "comedy"],
    "romcom": ["romance", "comedy"],
    "romantic comedy": ["romance", "comedy"],
    "action-adventure": ["action", "adventure"],
    "action adventure": ["action", "adventure"],
    "actionadventure": ["action", "adventure"],
    "comedy-drama": ["comedy", "drama"],
    "comedy drama": ["comedy", "drama"],
    "dramedy": ["comedy", "drama"],
    "sci-fi fantasy": ["science fiction", "fantasy"],
    "scifi fantasy": ["science fiction", "fantasy"],
    "science fiction fantasy": ["science fiction", "fantasy"],
}

LEXICAL_CANONICAL_MAP: dict[str, str] = {
    # Science Fiction lexical variants
    "sci-fi": "science fiction",
    "scifi": "science fiction",
    "science-fiction": "science fiction",
    "sciencefiction": "science fiction",
    "science fiction": "science fiction",
    # Dystopia lexical variants (book domain)
    "dystopia": "dystopia",
    "dystopian": "dystopia",
    # Slice of Life (anime domain)
    "slice-of-life": "slice of life",
    "slice of life": "slice of life",
    "sliceoflife": "slice of life",
    # Super Power (anime domain)
    "super-power": "super power",
    "super power": "super power",
    "superpower": "super power",
    "superpowers": "super power",
    # Nonfiction lexical variants
    "non-fiction": "nonfiction",
    "nonfiction": "nonfiction",
    "non fiction": "nonfiction",
    # TV Movie (movie domain)
    "tv-movie": "tv movie",
    "tv movie": "tv movie",
    "tvmovie": "tv movie",
    # Hip-hop
    "hip-hop": "hip-hop",
    "hip hop": "hip-hop",
    "hiphop": "hip-hop",
    "rap": "hip-hop",
    # Electronic & Synthwave
    "electronic": "electronic",
    "edm": "electronic",
    "electropop": "electronic",
    "electro": "electronic",
    "dance": "electronic",
    "synth": "electronic",
    "synthwave": "synthwave",
    "retrowave": "synthwave",
    # Standard catalog genres canonicalizing to self
    "action": "action",
    "adventure": "adventure",
    "animation": "animation",
    "comedy": "comedy",
    "humor": "comedy",
    "parody": "comedy",
    "crime": "crime",
    "detective": "detective",
    "documentary": "documentary",
    "drama": "drama",
    "family": "family",
    "fantasy": "fantasy",
    "foreign": "foreign",
    "history": "history",
    "historical": "historical",
    "historical fiction": "historical fiction",
    "horror": "horror",
    "kids": "kids",
    "childrens": "childrens",
    "children's": "childrens",
    "mecha": "mecha",
    "middle grade": "middle grade",
    "music": "music",
    "mystery": "mystery",
    "paranormal": "paranormal",
    "psychological": "psychological",
    "romance": "romance",
    "romantic": "romance",
    "space": "space",
    "supernatural": "supernatural",
    "thriller": "thriller",
    "suspense": "thriller",
    "war": "war",
    "western": "western",
    "fiction": "fiction",
}

DOMAIN_EQUIVALENTS: dict[str, dict[str, list[str]]] = {
    "movie": {
        "science fiction": ["sciencefiction", "science fiction", "sci-fi"],
        "family": ["family"],
        "kids": ["family"],
        "childrens": ["family"],
        "history": ["history"],
        "historical": ["history"],
        "historical fiction": ["history"],
        "detective": ["mystery"],
        "anime": ["animation"],
        "animation": ["animation"],
        "tv movie": ["tvmovie", "tv movie"],
    },
    "anime": {
        "science fiction": ["sci-fi", "scifi", "science fiction"],
        "family": ["kids"],
        "kids": ["kids"],
        "childrens": ["kids"],
        "history": ["historical"],
        "historical": ["historical"],
        "historical fiction": ["historical"],
        "supernatural": ["supernatural"],
        "paranormal": ["supernatural"],
        "detective": ["mystery"],
        "slice of life": ["slice of life"],
        "super power": ["super power", "superpower"],
    },
    "book": {
        "science fiction": ["science fiction", "sci-fi"],
        "kids": ["childrens", "kids", "family"],
        "childrens": ["childrens", "family"],
        "family": ["family", "childrens"],
        "historical fiction": ["historical fiction"],
        "history": ["history", "historical"],
        "historical": ["historical", "historical fiction"],
        "paranormal": ["paranormal"],
        "supernatural": ["supernatural", "paranormal"],
        "detective": ["detective", "mystery"],
        "dystopia": ["dystopia", "dystopian"],
        "middle grade": ["middle grade"],
        "fiction": ["fiction"],
        "nonfiction": ["nonfiction", "non-fiction", "non fiction"],
    },
}

DEFAULT_TARGETS: dict[str, list[str]] = {
    "science fiction": ["science fiction", "sciencefiction", "sci-fi", "scifi"],
    "romance": ["romance", "romantic"],
    "comedy": ["comedy", "humor", "parody"],
    "action": ["action"],
    "adventure": ["adventure"],
    "drama": ["drama"],
    "mystery": ["mystery"],
    "crime": ["crime"],
    "detective": ["detective", "mystery"],
    "thriller": ["thriller", "suspense"],
    "horror": ["horror"],
    "fantasy": ["fantasy", "magic"],
    "animation": ["animation", "anime"],
    "anime": ["anime", "animation"],
    "family": ["family", "kids", "childrens"],
    "kids": ["kids", "family", "childrens"],
    "childrens": ["childrens", "family", "kids"],
    "history": ["history", "historical"],
    "historical": ["historical", "history"],
    "historical fiction": ["historical fiction", "historical", "history"],
    "supernatural": ["supernatural", "paranormal"],
    "paranormal": ["paranormal", "supernatural"],
    "dystopia": ["dystopia", "dystopian"],
    "slice of life": ["slice of life"],
    "super power": ["super power", "superpower"],
    "middle grade": ["middle grade"],
    "mecha": ["mecha"],
    "space": ["space"],
    "cyberpunk": ["cyberpunk"],
    "psychological": ["psychological"],
    "fiction": ["fiction"],
    "nonfiction": ["nonfiction", "non-fiction", "non fiction"],
    "tv movie": ["tvmovie", "tv movie"],
    "hip-hop": ["hip-hop", "hip hop", "rap"],
    "electronic": ["electronic", "edm", "dance", "synth"],
    "synthwave": ["synthwave", "retrowave"],
}

# Backward compatibility alias
GENRE_MAP: dict[str, list[str]] = DEFAULT_TARGETS

NARRATIVE_DESCRIPTORS: set[str] = {
    "dark",
    "grim",
    "mind-bending",
    "mindbending",
    "mind bending",
    "philosophical",
    "epic",
    "cozy",
    "slow burn",
    "slow-burn",
    "slowburn",
}

BOOK_ONLY_GENRES: set[str] = {
    "fiction",
    "middle grade",
    "middlegrade",
    "middle-grade",
}


def is_bypassed_genre_filter(requested_genre: str, media_type: str | None = None) -> bool:
    """
    Check if a genre constraint should be bypassed as a boolean hard filter:
    1. Narrative descriptors (dark, grim, etc.) are semantic preferences, not hard filters.
    2. Book-only constraints (fiction, middle grade) must not act as hard filters on movies/anime.
    """
    if not requested_genre:
        return False
    norm = requested_genre.strip().lower()
    clean = re.sub(r"[^a-z0-9 ]", "", norm).strip()

    if norm in NARRATIVE_DESCRIPTORS or clean in NARRATIVE_DESCRIPTORS:
        return True

    if media_type in ("movie", "anime"):
        if norm in BOOK_ONLY_GENRES or clean in BOOK_ONLY_GENRES:
            return True

    return False


def check_boundary_match(target: str, text: str) -> bool:
    """
    Escaped token-boundary match. Ensures target is bounded by start/end or delimiters (, ; / | whitespace).
    Prevents false-positive matches such as 'war' in 'Star Wars' or 'action' in 'Reaction'.
    """
    if not target or not text:
        return False
    pattern = re.compile(r"(?:^|[,\s;/|])" + re.escape(target) + r"(?:$|[,\s;/|])", re.IGNORECASE)
    return bool(pattern.search(text))


def normalize_token_str(s: str) -> str:
    """Normalize text using Unicode-safe NFKD decomposition and delimiter standardization."""
    return normalize_title_key(str(s) if s is not None else "")


def match_genre(requested_genre: str, row_genre_str: str, media_type: str | None = None) -> bool:
    """
    Check if requested_genre matches row_genre_str using:
    1. Compound genre decomposition (AND semantics: all constituents must match)
    2. Lexical canonicalization (spelling, formatting, and hyphens)
    3. Domain-specific catalog equivalents (when media_type is provided)
    4. Safe token-boundary delimiter matching (preventing false-positive substring leaks)
    """
    if not requested_genre or not row_genre_str:
        return False

    norm_req = requested_genre.strip().lower()
    cleaned_row = re.sub(r"[\[\]\(\)\"\']", " ", str(row_genre_str)).strip()

    # 1. Compound genre decomposition (AND semantics)
    if norm_req in COMPOUND_GENRE_RULES:
        constituents = COMPOUND_GENRE_RULES[norm_req]
        return all(match_genre(c, row_genre_str, media_type=media_type) for c in constituents)

    # 2. Canonicalize requested genre
    canonical = LEXICAL_CANONICAL_MAP.get(norm_req, norm_req)

    # 3. Resolve target catalog labels (domain-aware)
    candidates = None
    if media_type and media_type in DOMAIN_EQUIVALENTS:
        candidates = DOMAIN_EQUIVALENTS[media_type].get(canonical) or DOMAIN_EQUIVALENTS[media_type].get(norm_req)

    if not candidates:
        candidates = DEFAULT_TARGETS.get(canonical) or DEFAULT_TARGETS.get(norm_req) or [canonical, norm_req]

    # 4. Safe boundary matching against catalog row
    for cand in candidates:
        if check_boundary_match(cand, cleaned_row):
            return True

    return False


def coerce_numeric(val: Any) -> float | None:
    """
    Safely convert an input (int, float, numeric string) to float.
    Returns None if val is missing, empty string, NaN, boolean, or non-numeric.
    """
    if val is None or isinstance(val, bool):
        return None
    if isinstance(val, (int, float)):
        if math.isnan(val):
            return None
        return float(val)

    # If it's a string, attempt conversion
    s = str(val).strip()
    if not s or s.lower() in ("nan", "none", "null", "unknown", "n/a"):
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def clean_entity_text(text: str) -> str:
    """Normalize unicode accents, strip diacritics, and standardize apostrophes."""
    if not text:
        return ""
    import unicodedata
    normalized = unicodedata.normalize("NFKD", str(text))
    ascii_text = "".join(c for c in normalized if not unicodedata.combining(c))
    ascii_text = ascii_text.replace("’", "'").replace("`", "'")
    return ascii_text.strip()


def extract_entity_records(candidate_field: str) -> list[list[str]]:
    """
    Split candidate field into discrete entity entries (by comma/semicolon)
    and parse each entity into lowercase discrete word tokens.
    Handles PascalCase concatenation (e.g. 'ChristopherNolan' -> ['christopher', 'nolan'])
    and strips role annotations in parentheses (e.g. '(Goodreads Author)').
    """
    if not candidate_field:
        return []
    cleaned_field = clean_entity_text(candidate_field)
    records = []
    raw_entities = re.split(r"[,;]", cleaned_field)
    for raw in raw_entities:
        raw_clean = re.sub(r"\s*\([^)]*\)", "", raw).strip()
        if not raw_clean:
            continue
        tokens = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)|[0-9]+", raw_clean)
        if not tokens:
            tokens = [t.lower() for t in raw_clean.split() if t]
        else:
            tokens = [t.lower() for t in tokens]
        if tokens:
            records.append(tokens)
    return records


def match_entity(query_entity: str, candidate_field: str) -> bool:
    """
    Match query_entity against candidate_field (which may contain one or multiple entities).
    Safe matching semantics:
    1. Exact token sequence match (e.g. ['christopher', 'nolan'] == ['christopher', 'nolan'])
    2. Contiguous sub-sequence match for single names or expanded prefix (e.g. ['nolan'] in ['christopher', 'nolan'])
    3. Initialism compatibility (e.g. ['george', 'martin'] matches ['george', 'r', 'r', 'martin'])
    4. Prohibits arbitrary substring leaks (e.g. 'Ian' will NOT match 'Christian Bale', 'Dan' will NOT match 'Robert Jordan')
    """
    if not query_entity or not candidate_field:
        return False
    q_clean = clean_entity_text(query_entity)
    q_tokens = [t.lower() for t in re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)|[0-9]+", q_clean)]
    if not q_tokens:
        return False

    candidate_records = extract_entity_records(candidate_field)
    for c_tokens in candidate_records:
        if q_tokens == c_tokens:
            return True
        len_q = len(q_tokens)
        len_c = len(c_tokens)
        if len_q < len_c:
            for i in range(len_c - len_q + 1):
                if c_tokens[i : i + len_q] == q_tokens:
                    return True
        if len_q == 2 and len_c > 2 and q_tokens[0] == c_tokens[0] and q_tokens[1] == c_tokens[-1]:
            if all(len(t) == 1 for t in c_tokens[1:-1]):
                return True

    return False


def clean_isbn_str(val: Any) -> str:
    """Normalize ISBN string, stripping hyphens, spaces, and floating .0 suffixes."""
    if val is None or isinstance(val, bool):
        return ""
    s = str(val).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return normalize_token_str(s)


def normalize_text_match(query_text: str, candidate_text: str) -> bool:
    """Case-insensitive, whitespace-tolerant substring matching."""
    if not query_text or not candidate_text:
        return False
    q_norm = normalize_token_str(query_text)
    c_norm = normalize_token_str(candidate_text)
    return q_norm in c_norm


def row_matches_filters(row: Any, filters: dict[str, Any], media_type: str) -> bool:
    """
    Evaluate whether a single row (dict or pd.Series) satisfies all active filters.
    A missing value in the row under an active constraint causes exclusion.
    """
    if not filters:
        return True

    def get_val(key: str) -> Any:
        if isinstance(row, dict):
            return row.get(key)
        # pd.Series
        return row[key] if key in row else None

    # --------------------------------------------------
    # 1. Common Filters: Title
    # --------------------------------------------------
    filter_title = filters.get("title")
    if filter_title:
        row_title = str(get_val("title") or "")
        if not row_title or not normalize_text_match(filter_title, row_title):
            return False

    # --------------------------------------------------
    # 2. Common Filters: Release Year
    # --------------------------------------------------
    year_val = coerce_numeric(get_val("release_year"))
    year_min = coerce_numeric(filters.get("release_year_min"))
    year_max = coerce_numeric(filters.get("release_year_max"))

    if year_min is not None:
        if year_val is None or year_val < year_min:
            return False

    if year_max is not None:
        if year_val is None or year_val > year_max:
            return False

    # --------------------------------------------------
    # 3. Common Filters: Genres Include / Exclude
    # --------------------------------------------------
    raw_genres = get_val("genres")
    row_genres = str(raw_genres) if raw_genres is not None and not (isinstance(raw_genres, float) and math.isnan(raw_genres)) else ""

    genres_include = filters.get("genres_include") or []
    if isinstance(genres_include, str):
        genres_include = [genres_include]
    if genres_include:
        for req_genre in genres_include:
            if is_bypassed_genre_filter(req_genre, media_type):
                continue
            if not row_genres:
                return False
            if not match_genre(req_genre, row_genres, media_type=media_type):
                return False

    genres_exclude = filters.get("genres_exclude") or []
    if isinstance(genres_exclude, str):
        genres_exclude = [genres_exclude]
    if genres_exclude:
        if row_genres:
            for ex_genre in genres_exclude:
                if is_bypassed_genre_filter(ex_genre, media_type):
                    continue
                if match_genre(ex_genre, row_genres, media_type=media_type):
                    return False

    # --------------------------------------------------
    # 4. Domain-Specific Filters: Movie
    # --------------------------------------------------
    if media_type == "movie":
        runtime_min = coerce_numeric(filters.get("runtime_min"))
        runtime_max = coerce_numeric(filters.get("runtime_max"))
        if runtime_min is not None or runtime_max is not None:
            runtime_val = coerce_numeric(get_val("runtime"))
            if runtime_val is None:
                return False
            if runtime_min is not None and runtime_val < runtime_min:
                return False
            if runtime_max is not None and runtime_val > runtime_max:
                return False

        revenue_min = coerce_numeric(filters.get("revenue_min"))
        revenue_max = coerce_numeric(filters.get("revenue_max"))
        if revenue_min is not None or revenue_max is not None:
            revenue_val = coerce_numeric(get_val("revenue"))
            if revenue_val is None:
                return False
            # Handle scale discrepancy: if revenue < 10000, treat as millions (e.g. 500 -> 500M)
            if revenue_min is not None:
                target_min = (revenue_min * 1e6) if (0 < revenue_min < 10000 and (revenue_val is not None and revenue_val > 100000)) else revenue_min
                if revenue_val < target_min:
                    return False
            if revenue_max is not None:
                target_max = (revenue_max * 1e6) if (0 < revenue_max < 10000 and (revenue_val is not None and revenue_val > 100000)) else revenue_max
                if revenue_val > target_max:
                    return False

        directors = filters.get("director") or []
        if isinstance(directors, str):
            directors = [directors]
        if directors:
            row_director = str(get_val("director") or "")
            if not row_director:
                return False
            for d in directors:
                if not match_entity(d, row_director):
                    return False

        cast_members = filters.get("cast") or []
        if isinstance(cast_members, str):
            cast_members = [cast_members]
        if cast_members:
            row_cast = str(get_val("cast") or "")
            if not row_cast:
                return False
            for c in cast_members:
                if not match_entity(c, row_cast):
                    return False

        prod_companies = filters.get("production_companies") or []
        if isinstance(prod_companies, str):
            prod_companies = [prod_companies]
        if prod_companies:
            row_prod = str(get_val("production_companies") or "")
            if not row_prod:
                return False
            for p in prod_companies:
                if not match_entity(p, row_prod):
                    return False

    # --------------------------------------------------
    # 5. Domain-Specific Filters: Anime
    # --------------------------------------------------
    elif media_type == "anime":
        episodes_min = coerce_numeric(filters.get("episodes_min"))
        episodes_max = coerce_numeric(filters.get("episodes_max"))
        if episodes_min is not None or episodes_max is not None:
            episodes_val = coerce_numeric(get_val("episodes"))
            if episodes_val is None:
                return False
            if episodes_min is not None and episodes_val < episodes_min:
                return False
            if episodes_max is not None and episodes_val > episodes_max:
                return False

        pop_min = coerce_numeric(filters.get("popularity_min"))
        pop_max = coerce_numeric(filters.get("popularity_max"))
        if pop_min is not None or pop_max is not None:
            pop_val = coerce_numeric(get_val("popularity"))
            if pop_val is None:
                return False
            if pop_min is not None and pop_val < pop_min:
                return False
            if pop_max is not None and pop_val > pop_max:
                return False

        rank_min = coerce_numeric(filters.get("ranking_min"))
        rank_max = coerce_numeric(filters.get("ranking_max"))
        if rank_min is not None or rank_max is not None:
            rank_val = coerce_numeric(get_val("ranking"))
            if rank_val is None:
                return False
            if rank_min is not None and rank_val < rank_min:
                return False
            if rank_max is not None and rank_val > rank_max:
                return False

    # --------------------------------------------------
    # 6. Domain-Specific Filters: Book
    # --------------------------------------------------
    elif media_type == "book":
        rating_min = coerce_numeric(filters.get("rating_min"))
        rating_max = coerce_numeric(filters.get("rating_max"))
        if rating_min is not None or rating_max is not None:
            rating_val = coerce_numeric(get_val("rating"))
            if rating_val is None:
                return False
            if rating_min is not None and rating_val < rating_min:
                return False
            if rating_max is not None and rating_val > rating_max:
                return False

        pages_min = coerce_numeric(filters.get("pages_min"))
        pages_max = coerce_numeric(filters.get("pages_max"))
        if pages_min is not None or pages_max is not None:
            pages_val = coerce_numeric(get_val("pages"))
            if pages_val is None:
                return False
            if pages_min is not None and pages_val < pages_min:
                return False
            if pages_max is not None and pages_val > pages_max:
                return False

        authors = filters.get("author") or []
        if isinstance(authors, str):
            authors = [authors]
        if authors:
            row_author = str(get_val("author") or "")
            if not row_author:
                return False
            for a in authors:
                if not match_entity(a, row_author):
                    return False

        publisher = filters.get("publisher")
        if publisher:
            row_pub = str(get_val("publisher") or "")
            if not row_pub or not match_entity(publisher, row_pub):
                return False

        isbn = filters.get("isbn")
        if isbn:
            row_isbn = get_val("isbn")
            clean_filter_isbn = clean_isbn_str(isbn)
            clean_row_isbn = clean_isbn_str(row_isbn)
            if not clean_row_isbn or clean_filter_isbn != clean_row_isbn:
                return False

        characters = filters.get("characters") or []
        if isinstance(characters, str):
            characters = [characters]
        if characters:
            row_chars = str(get_val("characters") or "")
            if not row_chars:
                return False
            for char in characters:
                if not match_entity(char, row_chars):
                    return False

    return True


def get_valid_ids(
    dataframe: pd.DataFrame,
    current_ids: list[str],
    filters: dict[str, Any],
    media_type: str,
) -> set[str]:
    """
    Filter a dataset against active filters and return the set of valid item IDs.
    Preserves 1-to-1 ID mapping with dataframe row indices.
    """
    if not filters:
        return set(current_ids)

    # Use dict records for fast, type-safe iteration
    records = dataframe.to_dict("records")
    valid_ids = set()

    for idx, row in enumerate(records):
        if row_matches_filters(row, filters, media_type):
            if idx < len(current_ids):
                valid_ids.add(current_ids[idx])

    return valid_ids
