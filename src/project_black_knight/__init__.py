"""
EZIO — Entertainment Zone Intelligence & Optimization
AI-powered Search & Retrieval Engine for Movies, Anime, and Books.
(Internal package name preserved for backward compatibility: project_black_knight)
"""

from .query_schema import (
    BlackKnightQuery,
    CommonQuery,
    DomainQueries,
    MovieQuery,
    AnimeQuery,
    BookQuery,
)

EzioQuery = BlackKnightQuery
from .query_parser import (
    parse_query,
    make_groq_strict_schema,
    get_groq_client,
    SYSTEM_PROMPT,
    MODELS_TO_TRY,
)
from .text_normalizer import Text_Normalization

from .metadata_filter import (
    get_valid_ids,
    row_matches_filters,
    match_genre,
    coerce_numeric,
    match_entity,
    clean_isbn_str,
    GENRE_MAP,
    LEXICAL_CANONICAL_MAP,
    DOMAIN_EQUIVALENTS,
    COMPOUND_GENRE_RULES,
    is_bypassed_genre_filter,
)

from .retrieval import (
    dense_retrieve,
    bm25_retrieve,
    reciprocal_rank_fusion,
    rerank_candidates,
    resolve_similar_seed,
    hybrid_retrieve,
    search_black_knight,
    tokenize_for_bm25,
)

search_ezio = search_black_knight
from .diagnostics import (
    RetrievalTrace,
    TargetTrackingRecord,
    explain_filter_rejection,
)

__all__ = [
    "BlackKnightQuery",
    "CommonQuery",
    "DomainQueries",
    "MovieQuery",
    "AnimeQuery",
    "BookQuery",
    "parse_query",
    "make_groq_strict_schema",
    "get_groq_client",
    "SYSTEM_PROMPT",
    "MODELS_TO_TRY",
    "Text_Normalization",
    "get_valid_ids",
    "row_matches_filters",
    "match_genre",
    "coerce_numeric",
    "match_entity",
    "clean_isbn_str",
    "GENRE_MAP",
    "LEXICAL_CANONICAL_MAP",
    "DOMAIN_EQUIVALENTS",
    "COMPOUND_GENRE_RULES",
    "is_bypassed_genre_filter",
    "dense_retrieve",
    "bm25_retrieve",
    "reciprocal_rank_fusion",
    "rerank_candidates",
    "resolve_similar_seed",
    "hybrid_retrieve",
    "search_black_knight",
    "tokenize_for_bm25",
    "RetrievalTrace",
    "TargetTrackingRecord",
    "explain_filter_rejection",
    "EzioQuery",
    "search_ezio",
    "main",
]


def main() -> None:
    print("EZIO — Entertainment Zone Intelligence & Optimization")

