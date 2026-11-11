"""
EZIO — Entertainment Zone Intelligence & Optimization
AI-powered Search & Retrieval Engine for Movies, Anime, and Books.
"""

from project_black_knight import *
from project_black_knight import __all__ as _pbk_all

EzioQuery = BlackKnightQuery
search_ezio = search_black_knight

__all__ = list(_pbk_all) + ["EzioQuery", "search_ezio"]


def main() -> None:
    print("EZIO — Entertainment Zone Intelligence & Optimization")

