# Project Black Knight — Phase 5 Final Regression & System Evaluation Report

**Generated:** 2026-10-19  
**Evaluation Scope:** Phases 1–5 Comprehensive Verification  
**Repository State:** 45 Passing Unit & Integration Tests, 0 Failed, 0 Skipped  

---

## 1. Architecture and Evaluation Scope

Project Black Knight is a multi-modal discovery and recommendation engine spanning four entertainment domains:
- **Movies**: 4,805 TMDB records (plot overview, keywords, genres, cast, director, revenue, runtime, release date)
- **Anime**: 18,336 anime titles (episodes, popularity, ranking, aired dates, genres)
- **Books**: 11,230 Goodreads records (authors, ratings, page counts, ISBNs, publishers, characters)
- **Music**: 32,828 Spotify tracks (track names, artists, albums, durations, playlist genres and subgenres)

```
                            [ User Query / API Request ]
                                         │
                                         ▼
                     [ Pydantic Query Schema (BlackKnightQuery) ]
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
     [ Single-Domain Request ]                       [ Multi-Domain Request ]
                 │                                               │
                 ├───────────────────────┬───────────────────────┤
                 ▼                       ▼                       ▼
           [ Movie Flow ]          [ Anime Flow ]          [ Book/Music Flow ]
                 │                       │                       │
                 ▼                       ▼                       ▼
         [ Metadata Filter ]      [ Metadata Filter ]     [ Metadata Filter ]
         (get_valid_ids)          (get_valid_ids)         (get_valid_ids)
                 │                       │                       │
         ┌───────┴───────┐       ┌───────┴───────┐       ┌───────┴───────┐
         ▼               ▼       ▼               ▼       ▼               ▼
      [ Dense ]       [ BM25 ] [ Dense ]       [ BM25 ] [ Dense ]       [ BM25 ]
         │               │       │               │       │               │
         └───────┬───────┘       └───────┬───────┘       └───────┬───────┘
                 ▼                       ▼                       ▼
           [ RRF Fusion ]          [ RRF Fusion ]          [ RRF Fusion ]
           (k=60, Top-30)          (k=60, Top-30)          (k=60, Top-30)
                 │                       │                       │
                 ▼                       ▼                       ▼
        [ Cross-Encoder ]       [ Cross-Encoder ]       [ Cross-Encoder ]
        (ms-marco-MiniLM)       (ms-marco-MiniLM)       (ms-marco-MiniLM)
                 │                       │                       │
                 └───────────────────────┬───────────────────────┘
                                         ▼
                           [ Score Aggregation & Sort ]
                                         │
                                         ▼
                             [ Enriched Output JSON ]
```

---

## 2. Baseline and Final Test Results

### Test Execution Summary
All tests were executed using the dedicated virtual environment Python 3.13.16 test runner:
```powershell
$env:PYTHONPATH='src'; .\project_black_knight\Scripts\python.exe -m pytest tests/ -v
```

| Test Suite | Phase Introduced | Tests Count | Passed | Failed | Skipped | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| [`tests/test_datasets.py`](file:///c:/Coding/Project%20Black%20Knight/tests/test_datasets.py) | Phase 1 | 4 | 4 | 0 | 0 | **PASSED** |
| [`tests/test_text_normalizer.py`](file:///c:/Coding/Project%20Black%20Knight/tests/test_text_normalizer.py) | Phase 1 | 1 | 1 | 0 | 0 | **PASSED** |
| [`tests/test_query_schema.py`](file:///c:/Coding/Project%20Black%20Knight/tests/test_query_schema.py) | Phase 1 | 3 | 3 | 0 | 0 | **PASSED** |
| [`tests/test_query_parser.py`](file:///c:/Coding/Project%20Black%20Knight/tests/test_query_parser.py) | Phase 1 | 2 | 2 | 0 | 0 | **PASSED** |
| [`tests/test_parser_evaluation.py`](file:///c:/Coding/Project%20Black%20Knight/tests/test_parser_evaluation.py) | Phase 2 | 10 | 10 | 0 | 0 | **PASSED** |
| [`tests/test_metadata_filtering.py`](file:///c:/Coding/Project%20Black%20Knight/tests/test_metadata_filtering.py) | Phase 3 | 12 | 12 | 0 | 0 | **PASSED** |
| [`tests/test_hybrid_retrieval.py`](file:///c:/Coding/Project%20Black%20Knight/tests/test_hybrid_retrieval.py) | Phase 4 | 13 | 13 | 0 | 0 | **PASSED** |
| **Total Test Suite** | **Phases 1–5** | **45** | **45** | **0** | **0** | **100% PASS** |

---

## 3. Query Parser Evaluation & API Usage

Evaluated on the 40-case comprehensive benchmark (`evaluation/benchmark.jsonl`).

- **Total Test Cases**: 40
- **Schema Validation Failures**: **0** (100% Pydantic conformance)
- **Strict Exact Match Rate**: **35.0%** (14 / 40)
- **Normalized Match Rate**: **57.5%** (23 / 40)
- **Live Groq API Calls in Test/Evaluation**: **0** (100% cache hit rate via deterministic query fingerprinting)

### Domain-Level Parser Accuracy
- **Anime**: 80.0% normalized match rate (8/10)
- **Movies**: 70.0% normalized match rate (7/10)
- **Books**: 60.0% normalized match rate (6/10)
- **Music**: 20.0% normalized match rate (2/10) — bottleneck is taxonomy mismatch between `playlist_genre` vs `playlist_subgenre` (e.g., synthwave vs electronic).

---

## 4. Metadata-Filtering Correctness

Phase 3 established `metadata_filter.py`, delivering type-safe hard filtering across all data types:
1. **String-to-Numeric Boundary Coercion**: Resolved legacy crash where string columns (e.g. Goodreads `pages="350"`) caused `TypeError` when compared against numeric bounds.
2. **Missing/Null Constraint Exclusion**: Enforced strict exclusion of items with missing/null values under active constraints, preventing empty fields from leaking through.
3. **TMDB Concatenated Name Normalization**: Handled both raw TMDB concatenated strings (`"JamesCameron"`) and natural-language strings (`"James Cameron"`).
4. **ISBN Cleaning & Token Matching**: Normalized ISBN strings, removing hyphens and non-alphanumeric noise.
5. **Boundary Inclusivity**: Verified exact boundary behavior ($x \ge \text{min}$, $x \le \text{max}$).

---

## 5. Retrieval Metrics & Benchmark Evaluation

Evaluated across four configurations under identical candidate conditions on the 12-query benchmark ([`evaluation/retrieval_benchmark.jsonl`](file:///c:/Coding/Project%20Black%20Knight/evaluation/retrieval_benchmark.jsonl)):

### Primary Ranking Metrics on Positive Queries ($N=11$)
*Queries containing verified ground truth items in dataset:*

| Configuration | Hit Rate@5 | Hit Rate@10 | Precision@5 | Precision@10 | Recall@5 | Recall@10 | MRR | nDCG@5 | nDCG@10 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Dense Only (ChromaDB)** | 0.2727 | 0.2727 | 0.1455 | 0.1000 | 0.2323 | 0.2626 | 0.2045 | 0.2274 | 0.2210 |
| **BM25 Lexical Only** | 0.1818 | 0.1818 | 0.1273 | 0.0909 | 0.1414 | 0.1717 | 0.1136 | 0.1365 | 0.1300 |
| **RRF Hybrid ($k=60$)** | 0.2727 | 0.2727 | 0.1455 | 0.1000 | 0.2323 | 0.2626 | 0.2045 | 0.2274 | 0.2210 |
| **Cross-Encoder Reranked (Full)** | **0.6364** | **0.6364** | **0.3636** | **0.2091** | **0.5960** | **0.6263** | **0.5682** | **0.5910** | **0.5846** |

### Absence Detection Performance ($N=1$ negative query)
*Query `RET_BOOK_002` (*The Alchemist* by Paulo Coelho — verified absent from the 11k Goodreads dataset):*
- **Correct Rejection Rate**: **1.0000 (100%)** across all four configurations.
- Handled cleanly: returns 0 items rather than hallucinating irrelevant books.

---

## 6. Investigation of Phase 4 Evaluation Caveats

### Caveat A: Why Were Dense Only and RRF Metrics Identical?
In the initial Phase 4 run, Dense Only and RRF Hybrid displayed identical aggregate metrics. 

**Root Cause Analysis:**
- In 7 of the 12 queries, BM25 contributed novel candidate items, and RRF altered the relative ranking of candidates.
- However, on this specific 12-query benchmark:
  1. For queries where the relevant item was located in raw retrieval (`MOV_003`, `ANI_001`, `MUS_002`), both Dense and RRF placed the targets at the identical top positions (#1, #4-#5, and top 5 respectively).
  2. For queries where relevant items were outside the raw candidate window, both scored 0.0.
  3. Consequently, the evaluated metrics matched not because candidate lists were identical, but because on this small sample, the target items occupied identical top rank slots prior to neural reranking.
- Cross-Encoder reranking was the true differentiator, jumping Hit Rate from 0.2727 to 0.6364 and MRR from 0.2045 to 0.5682.

### Caveat B: Absence Query Scoring
- Previously, an absence query returning 0 items was credited with `hit_rate_at_5 = 1.0`, inflating conventional IR metrics.
- In Phase 5, absence detection has been formally separated:
  - Positive evaluation denominator is strictly $N=11$.
  - Absence detection is reported as a separate metric: **Correct Rejection Rate = 1.0 (100%)**.

### Caveat C: Benchmark Scope
- The 12-query benchmark is a targeted diagnostic suite covering exact matches, complex filters, absence handling, and multi-domain queries. It provides strong directional verification, but does not substitute for a large-scale statistical test collection (e.g. 1,000+ labeled pairs).

---

## 7. Cross-Domain and Similar-Item Findings

### Similar-Item Retrieval (`similar_to`)
- **Seed Resolution**: `resolve_similar_seed()` accurately resolves titles (e.g., `"Interstellar"`, `"Death Note"`) against metadata indices.
- **Self-Exclusion**: Verified that the seed item itself is strictly excluded from recommendations, preventing trivial self-recommendation (`test_similar_to_self_exclusion` passing).
- **Graceful Fallback**: Unknown reference titles trigger an informative diagnostic warning and fall back to semantic search without crashing (`test_similar_to_unknown_seed_graceful_fallback` passing).

### Cross-Domain Recommendations
- **Filter Isolation**: Queries spanning multiple domains (e.g., `["movie", "anime"]`) route domain-specific filters independently (`test_cross_domain_filter_isolation_no_leakage` passing). No leakage of movie-specific attributes (`director`) into anime or book attributes into music.
- **Zero-Result Resilience**: If one domain returns 0 items due to strict filters, the engine continues processing remaining domains without failing (`test_cross_domain_one_domain_zero_results` passing).

---

## 8. Defect Classification & Remaining Limitations

| ID | Title | Category | Status | Details & Recommended Action |
| :--- | :--- | :---: | :---: | :--- |
| **DEF-001** | Movie title omitted from original tags | DATA_LIMITATION | **Mitigated** | Original `movies1234.pkl` tags omitted film titles. Mitigated in Phase 4 via selective pre-filtering vector scoring on `valid_ids`. *Recommendation: Re-embed with title prepended in future index refresh.* |
| **DEF-002** | Catalog omissions (e.g. *The Alchemist*) | DATA_LIMITATION | **Mitigated** | Popular titles absent from the 11k Goodreads dataset return 0 items. Mitigated via clean absence handling. *Recommendation: Ingest larger book catalog.* |
| **DEF-003** | Sparse book characters | DATA_LIMITATION | **Documented** | Nulls in character field safely exclude rows under active character constraints. |
| **DEF-004** | Missing anime rankings | DATA_LIMITATION | **Documented** | Unranked anime titles lack numerical ranking; handled via null-safe boundary checks. |
| **DEF-005** | Music genre taxonomy routing | PARSER_GAP | **Documented** | Query parser exhibits 20% match on music due to `playlist_genre` vs `playlist_subgenre` ambiguity. *Recommendation: Update system prompt with few-shot examples.* |

---

## 9. Reproduction Commands

To reproduce all evaluations and test suites without Groq API keys:

```powershell
# 1. Run full unit and integration test suite (45 tests)
$env:PYTHONPATH='src'; .\project_black_knight\Scripts\python.exe -m pytest tests/ -v

# 2. Run cached Query Parser evaluation (40 benchmark cases)
$env:PYTHONPATH='src'; .\project_black_knight\Scripts\python.exe evaluation/run_evaluation.py --mode cached

# 3. Run Hybrid Retrieval & Reranking evaluation (12 benchmark queries, 4 configurations)
$env:PYTHONPATH='src'; .\project_black_knight\Scripts\python.exe evaluation/run_retrieval_evaluation.py
```

---

## 10. Prioritized Next Steps

1. **Phase 6: Production API Layer (FastAPI)**: Wrap `search_black_knight` in a high-throughput REST API with pydantic request validation and async handlers.
2. **Phase 7: Vector Index Tag Enrichment**: Re-index `movies` in ChromaDB with `title` prepended to the text embeddings to maximize raw unconstrained dense similarity.
3. **Phase 8: Music Parser Taxonomy Fine-Tuning**: Add few-shot examples to Groq system prompt mapping ambiguous electronic/synthwave terms to Spotify's exact hierarchy.
4. **Phase 9: Interactive Discovery Web UI**: Build modern reactive frontend with rich media cards, domain filters, and interactive cross-domain recommendations.

---

### System Readiness Assessment
**Readiness Level: BETA / PILOT READY**  
The hybrid retrieval engine, metadata filtering module, RRF fusion, and cross-encoder reranker have been verified end-to-end with 45 passing automated tests and zero API cost. The system is ready for internal pilot integration and API development. Full public release should follow vector index tag enrichment (DEF-001) and music genre few-shot prompt updates (DEF-005).
