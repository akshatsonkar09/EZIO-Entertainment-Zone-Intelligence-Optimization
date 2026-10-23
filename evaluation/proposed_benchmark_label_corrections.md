# Project Black Knight — Proposed Benchmark Label Corrections

**Document Version**: `v1.0.0`  
**Date**: October 23, 2026  
**Status**: `PROPOSED` (Strictly non-destructive; canonical benchmark CSV remains 100% immutable)  
**Target Canonical File**: `evaluation/black_knight_eval_queries_113_audited.csv`  

---

## 1. Overview & Protocol Compliance

Under Operating Rules 2, 4, and Phase 5 of the Autonomous Protocol:
- The canonical benchmark file `black_knight_eval_queries_113_audited.csv` is **strictly immutable**.
- No benchmark labels may be edited, removed, or fabricated to inflate evaluation metrics.
- This document formally records verified catalog anomalies, label corruption, and contract contradictions discovered through query-level execution traces for future dataset curators.

---

## 2. Itemized Proposed Label Corrections

### Correction 1: `KI_016` (Anime Known-Item)
- **Query ID**: `KI_016`
- **Query Text**: *"Find Code Geass: Hangyaku no Lelouch."*
- **Current Canonical Label**: `["anime_732", "anime_9"]`
  - `anime_732` in anime catalog: **Tengen Toppa Gurren Lagann** (completely incorrect entity).
  - `anime_9` in anime catalog: **Code Geass: Hangyaku no Lelouch R2** (Season 2 sequel, partial match).
- **Actual Exact Catalog Match**:
  - `anime_745`: **Code Geass: Hangyaku no Lelouch** (Canonical Season 1 parent work).
- **Proposed Label**: `["anime_745", "anime_9"]`
- **Evidence**:
  - The retriever correctly placed `anime_745` at Rank 1, but received MRR = 0.0 because the ground truth benchmark erroneously specified `anime_732` (*Tengen Toppa Gurren Lagann*).
- **Confidence**: `VERY HIGH (1.00)`

---

### Correction 2: `KI_023` (Book Known-Item)
- **Query ID**: `KI_023`
- **Query Text**: *"Find Mansfield Park by Jane Austen."*
- **Current Canonical Label**: `["book_10435"]`
  - `book_10435` in book catalog: **"Revealed" by Tamera Alexander (Goodreads Author)** (completely incorrect book and author).
- **Actual Exact Catalog Match**:
  - `book_3338`: **"Mansfield Park" by Jane Austen, Kathryn Sutherland (Editor)**.
- **Proposed Label**: `["book_3338"]`
- **Evidence**:
  - Row 3338 of `book_metadata_clean.csv` contains title *"Mansfield Park"* and author *"Jane Austen"*.
  - Row 10435 contains title *"Revealed"* by *"Tamera Alexander"*.
  - The retriever correctly placed `book_3338` at Rank 1, but received MRR = 0.0 because the ground truth expected row 10435.
- **Confidence**: `VERY HIGH (1.00)`

---

### Correction 3: `MD_005` (Multi-Domain Hayao Miyazaki Query)
- **Query ID**: `MD_005`
- **Query Text**: *"Find movies and anime directed by Hayao Miyazaki."*
- **Current Canonical Label**: `["anime_721", "anime_741", "anime_723", "movie_96"]`
  - `anime_721`: **Haikyuu!!** (directed by Susumu Mitsunaka — NOT Hayao Miyazaki).
  - `anime_741`: **Rurouni Kenshin: Meiji Kenkaku Romantan - Tsuioku-hen** (directed by Kazuhiro Furuhashi — NOT Hayao Miyazaki).
  - `anime_723`: **Fate/stay night Movie: Heaven's Feel - II. Lost Butterfly** (directed by Tomonori Sudou — NOT Hayao Miyazaki).
  - `movie_96`: **Inception** (directed by Christopher Nolan — NOT Hayao Miyazaki).
- **Actual Exact Catalog Matches**:
  - `movie_1989`: **Howl's Moving Castle** (director: `HayaoMiyazaki`).
  - `movie_2249`: **Princess Mononoke** (director: `HayaoMiyazaki`).
  - `movie_2296`: **Spirited Away** (director: `HayaoMiyazaki`).
  - `anime_9825`: **Nagagutsu wo Haita Neko no Bouken** (animator / concept: Hayao Miyazaki).
- **Proposed Label**: `["movie_1989", "movie_2249", "movie_2296", "anime_15229"]`
- **Evidence**:
  - All four labeled items in the canonical benchmark have zero connection to Hayao Miyazaki.
  - The search engine correctly returned *Howl's Moving Castle*, *Princess Mononoke*, and *Spirited Away* in its top results.
- **Confidence**: `VERY HIGH (1.00)`

---

## 3. Similarity Query Ground-Truth Contract Clarification

In 12 out of 15 `SI_` queries (`SI_001`, `SI_002`, `SI_004`, `SI_005`, `SI_006`, `SI_007`, `SI_009`, `SI_010`, `SI_011`, `SI_012`, `SI_014`, `SI_015`):
- The benchmark's labeled `relevant_ids` list includes the seed work itself:
  - `SI_001`: `movie_96` (Inception)
  - `SI_002`: `movie_3339` (The Godfather)
  - `SI_004`: `movie_65` (The Dark Knight)
  - `SI_005`: `movie_662` (Fight Club)
  - `SI_006`: `anime_726` (Death Note)
  - `SI_007`: `anime_141` (Naruto)
  - `SI_009`: `anime_667` (Shingeki no Kyojin)
  - `SI_010`: `anime_759` (Steins;Gate)
  - `SI_011`: `book_1083` (The Way of Kings)
  - `SI_012`: `book_10523` (The Hunger Games)
  - `SI_014`: `book_530` (The Final Empire)
  - `SI_015`: `book_6016` (Brave New World)

### Recommendation Contract vs Benchmark Collision
In production recommendation systems, recommending the seed entity back to a user asking for items *similar to X* violates core recommendation principles. In `project_black_knight.retrieval`, seed deduplication is enforced:
```python
effective_valid_ids = valid_ids - excluded_seed_ids
```
**Recommendation for Future Benchmark Releases**:
Future benchmark revisions should explicitly remove the seed item ID from `relevant_ids` for similarity queries and curate 3–5 genuine thematic/stylistic counterparts with verified lexical and vector alignment.
