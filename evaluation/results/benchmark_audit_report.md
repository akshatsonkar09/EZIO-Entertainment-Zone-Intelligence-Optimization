# Project Black Knight — 150-Query Retrieval Benchmark Audit Report

## 1. Executive Summary

- **Total Benchmark Queries:** 150
- **Domain Breakdown:** Movies: 38, Anime: 38, Music: 37, Books: 37
- **Positive Scorable Queries:** 135
- **Verified Absence Queries:** 15
- **Unscorable Queries:** 0

## 2. Category Distribution

| Category | Count | Description |
|---|---:|---|
| known_item | 40 | Exact title and creator searches anchored on verified local catalog records |
| descriptive | 30 | Semantic and narrative descriptions with human-inspected relevance targets |
| constraint | 30 | Structured metadata constraints verified against Pydantic schema and production filters |
| similar_to | 20 | Seed-item similarity queries with verified catalog seeds and thematic clusters |
| multi_domain | 15 | Cross-domain discovery queries spanning pairs or sets of media types |
| absence | 15 | Genuine absence queries with 0 catalog matches verified by exact and substring checks |

## 3. Audit Findings & Remediations

- Fixed Interstelar spelling typo in KI_009 to match catalog movie_95 (Interstellar).
- Substituted missing book titles in Goodreads 11k catalog with verified anchors: The Way of Kings (book_1083), Mansfield Park (book_10435), Brave New World (book_6016), Murder on the Orient Express (book_867), Frankenstein (book_2378), The Final Empire (book_530), The Outsider (book_449).
- Substituted absent music title 'Lose Yourself' by Eminem with verified hit 'Godzilla (feat. Juice WRLD)' (music_242).
- Substituted false absence anime 'Oshi no Ko' with genuine verified absence 'Solo Leveling' (0 matches).
- Substituted false absence song 'Flowers' by Miley Cyrus with genuine verified absence 'Espresso' by Sabrina Carpenter (0 matches).
- Rewrote unsupported book release_year constraints (CO_017, CO_023) to fully supported production metadata fields (rating_min, author, pages_min, publisher).

## 4. Metadata Schema & Filter Compliance

All 30 constraint queries strictly adhere to the `BlackKnightQuery` schema and `metadata_filter.py` rules:
- **Movie Constraints:** `director`, `cast`, `runtime_min`/`max`, `revenue_min`, `genres_include`/`exclude`, `release_year_min`/`max`.
- **Anime Constraints:** `episodes_min`/`max`, `ranking_max`, `genres_include`/`exclude`, `release_year_min`/`max`.
- **Book Constraints:** `author`, `rating_min`, `pages_min`/`max`, `genres_include` (strictly avoiding unsupported `release_year`).
- **Music Constraints:** `artist`, `album`, `duration_min`/`max` (minutes), `playlist_genre`.

All 30 constraint queries yielded non-empty, defensible candidate sets (`audit_verdict = PASS`).
