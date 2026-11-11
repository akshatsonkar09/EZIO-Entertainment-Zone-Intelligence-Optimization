from typing import Literal
from pydantic import BaseModel, Field


class CommonQuery(BaseModel):
    title: str | None = None

    genres_include: list[str] = Field(default_factory=list)
    genres_exclude: list[str] = Field(default_factory=list)

    release_year_min: int | None = None
    release_year_max: int | None = None


class MovieQuery(BaseModel):
    production_companies: list[str] = Field(default_factory=list)
    cast: list[str] = Field(default_factory=list)
    director: list[str] = Field(default_factory=list)

    revenue_min: float | None = None

    runtime_min: int | None = None
    runtime_max: int | None = None


class AnimeQuery(BaseModel):
    episodes_min: int | None = None
    episodes_max: int | None = None

    popularity_min: float | None = None
    ranking_max: float | None = None


class BookQuery(BaseModel):
    author: list[str] = Field(default_factory=list)

    rating_min: float | None = None

    isbn: str | None = None

    characters: list[str] = Field(default_factory=list)

    pages_min: int | None = None
    pages_max: int | None = None

    publisher: str | None = None


class DomainQueries(BaseModel):
    movie: MovieQuery | None = None
    anime: AnimeQuery | None = None
    book: BookQuery | None = None


class BlackKnightQuery(BaseModel):
    media_types: list[
        Literal["movie", "anime", "book"]
    ] = Field(max_length=2)

    common: CommonQuery

    domain_queries: DomainQueries

    semantic_query: str

    similar_to: list[str] = Field(default_factory=list)


# Rebranded alias for EZIO
EzioQuery = BlackKnightQuery