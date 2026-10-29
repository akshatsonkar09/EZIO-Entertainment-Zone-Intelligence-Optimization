from typing import Any, Literal
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Natural-language search query")
    domain: Literal["all", "movie", "anime", "book"] | None = Field(
        default=None,
        description="Optional domain constraint (movie, anime, book, or all)",
    )
    top_k: int = Field(default=10, ge=1, le=50, description="Number of results to retrieve")


class SearchResultItem(BaseModel):
    id: str
    title: str
    media_type: str
    score: float
    release_year: int | float | None = None
    genres: str | None = None
    overview: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    user_query: str
    domain: str | None = None
    total_results: int
    results: list[SearchResultItem]


class ItemDetail(BaseModel):
    id: str
    media_type: str
    title: str
    release_year: int | float | None = None
    overview: str | None = None
    genres: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BrowseRequest(BaseModel):
    domain: Literal["movie", "anime", "book"] | None = None
    genre: str | None = None
    release_year_min: int | None = None
    release_year_max: int | None = None
    limit: int = Field(default=20, ge=1, le=50)


class MetadataCategoriesResponse(BaseModel):
    domains: list[str]
    genres: dict[str, list[str]]
    years: dict[str, dict[str, int | None]]
