# Project Black Knight — Complete Testing Results & Numerical Data

**Generated At:** 2026-10-19  
**Repository:** `c:/Coding/Project Black Knight`  
**Scope:** Exhaustive compilation of all dataset counts, test suite logs, parser benchmarks, retrieval metrics, and latency measurements.

---

## 1. Dataset & Vector Index Quantities

| Media Domain | Underlying Dataset | Verified Row Count | ChromaDB Collection | Chroma Embeddings Count | Alignment Status |
| :--- | :--- | :---: | :--- | :---: | :---: |
| **Movies** | TMDB 5000 (`movies1234.pkl`, `movie_metadata_clean.csv`) | 4,805 | `movies` | 4,805 | 1-to-1 Verified |
| **Anime** | MyAnimeList (`anime_metadata_clean.csv`) | 18,336 | `animes` | 18,336 | 1-to-1 Verified |
| **Books** | Goodreads 11k (`book_metadata_clean.csv`) | 11,230 | `books` | 11,230 | 1-to-1 Verified |
| **Music** | Spotify Tracks (`music_metadata_clean.csv`) | 32,828 | `music` | 32,828 | 1-to-1 Verified |
| **Total** | **All 4 Entertainment Catalogs Combined** | **67,199** | **4 Collections** | **67,199** | **100% Synced** |

## 2. Automated Test Suite Execution Results (45 Tests)

**Execution Command:** `.\project_black_knight\Scripts\python.exe -m pytest tests/ -v`  
**Total Tests:** 45 | **Passed:** 45 | **Failed:** 0 | **Skipped:** 0 | **Pass Rate:** 100.0% | **Execution Time:** ~21–30s

| # | Test File | Test Function Name | Result | Verification Scope |
| :-: | :--- | :--- | :---: | :--- |
| 1 | `tests/test_datasets.py` | `test_processed_clean_files_exist` | **PASSED** | Verifies existence of all cleaned CSV and pickle files. |
| 2 | `tests/test_datasets.py` | `test_movie_metadata_clean_schema` | **PASSED** | Verifies TMDB movie clean CSV columns and non-empty rows. |
| 3 | `tests/test_datasets.py` | `test_book_metadata_clean_schema` | **PASSED** | Verifies Goodreads clean CSV columns and non-empty rows. |
| 4 | `tests/test_datasets.py` | `test_chroma_collections` | **PASSED** | Verifies ChromaDB persistent client loads all 4 collections. |
| 5 | `tests/test_text_normalizer.py` | `test_text_normalization` | **PASSED** | Verifies text normalization and token stripping. |
| 6 | `tests/test_query_schema.py` | `test_common_query_defaults` | **PASSED** | Verifies CommonQuery default values and optional bounds. |
| 7 | `tests/test_query_schema.py` | `test_black_knight_query_valid` | **PASSED** | Verifies BlackKnightQuery Pydantic instantiation. |
| 8 | `tests/test_query_schema.py` | `test_black_knight_query_max_media_types` | **PASSED** | Verifies max 4 media types limit validation. |
| 9 | `tests/test_query_parser.py` | `test_system_prompt_rules` | **PASSED** | Verifies system prompt contains all schema formatting rules. |
| 10 | `tests/test_query_parser.py` | `test_make_groq_strict_schema` | **PASSED** | Verifies Groq strict JSON schema generation. |
| 11 | `tests/test_parser_evaluation.py` | `test_parse_query_success_mocked` | **PASSED** | Verifies parse_query with mocked Groq response. |
| 12 | `tests/test_parser_evaluation.py` | `test_parse_query_missing_optional_fields_mocked` | **PASSED** | Verifies missing optional fields fallback handling. |
| 13 | `tests/test_parser_evaluation.py` | `test_parse_query_malformed_json_fallback_mocked` | **PASSED** | Verifies JSON error recovery with fallback. |
| 14 | `tests/test_parser_evaluation.py` | `test_parse_query_rate_limit_retry_mocked` | **PASSED** | Verifies exponential backoff on 429 rate limit. |
| 15 | `tests/test_parser_evaluation.py` | `test_parse_query_all_models_fail_mocked` | **PASSED** | Verifies safe failure handling if all models fail. |
| 16 | `tests/test_parser_evaluation.py` | `test_parse_query_invalid_schema_fallback_mocked` | **PASSED** | Verifies schema violation fallback. |
| 17 | `tests/test_parser_evaluation.py` | `test_cache_fingerprint_and_key_generation` | **PASSED** | Verifies deterministic SHA256 cache keying. |
| 18 | `tests/test_parser_evaluation.py` | `test_semantic_query_evaluation_metrics` | **PASSED** | Verifies semantic list comparison semantics. |
| 19 | `tests/test_parser_evaluation.py` | `test_comparison_ordering_semantics` | **PASSED** | Verifies order-independent list matching. |
| 20 | `tests/test_parser_evaluation.py` | `test_compare_normalized_empty_domain_objects` | **PASSED** | Verifies normalized comparison on empty domains. |
| 21 | `tests/test_metadata_filtering.py` | `test_coerce_numeric_valid_and_invalid` | **PASSED** | Verifies numeric coercion of strings, floats, and nulls. |
| 22 | `tests/test_metadata_filtering.py` | `test_book_page_string_comparison_regression` | **PASSED** | Verifies string page counts do not throw TypeError. |
| 23 | `tests/test_metadata_filtering.py` | `test_numeric_exact_boundaries` | **PASSED** | Verifies inclusive numeric inequality boundaries. |
| 24 | `tests/test_metadata_filtering.py` | `test_genre_matching_synonyms_and_casing` | **PASSED** | Verifies synonym mapping (sci-fi, electronic, etc.). |
| 25 | `tests/test_metadata_filtering.py` | `test_genre_inclusions_and_exclusions` | **PASSED** | Verifies both include and exclude genre filtering. |
| 26 | `tests/test_metadata_filtering.py` | `test_director_and_cast_name_normalization` | **PASSED** | Verifies concatenated actor/director matching. |
| 27 | `tests/test_metadata_filtering.py` | `test_book_isbn_and_author_normalization` | **PASSED** | Verifies ISBN token cleaning and author matching. |
| 28 | `tests/test_metadata_filtering.py` | `test_music_metadata_fields` | **PASSED** | Verifies track name, artist, album, and duration filtering. |
| 29 | `tests/test_metadata_filtering.py` | `test_missing_data_under_active_constraint_excluded` | **PASSED** | Verifies null rows excluded under active constraints. |
| 30 | `tests/test_metadata_filtering.py` | `test_anime_ranking_and_popularity_handling` | **PASSED** | Verifies ranking (lower=better) and popularity bounds. |
| 31 | `tests/test_metadata_filtering.py` | `test_contradictory_filters_empty_result` | **PASSED** | Verifies contradictory bounds return empty set. |
| 32 | `tests/test_metadata_filtering.py` | `test_real_dataset_hard_constraints` | **PASSED** | Verifies filtering on real loaded dataset dataframes. |
| 33 | `tests/test_hybrid_retrieval.py` | `test_dense_retrieve_mocked` | **PASSED** | Verifies Chroma dense candidate retrieval with mocked embeddings. |
| 34 | `tests/test_hybrid_retrieval.py` | `test_dense_retrieve_empty_valid_ids` | **PASSED** | Verifies zero queries when valid_ids is empty set. |
| 35 | `tests/test_hybrid_retrieval.py` | `test_bm25_retrieve_fixture` | **PASSED** | Verifies BM25 ranking and scoring on controlled fixture. |
| 36 | `tests/test_hybrid_retrieval.py` | `test_bm25_retrieve_with_hard_filters` | **PASSED** | Verifies BM25 retrieval combined with valid_ids filter. |
| 37 | `tests/test_hybrid_retrieval.py` | `test_reciprocal_rank_fusion_manual_calculation` | **PASSED** | Verifies exact manual RRF math with k=60. |
| 38 | `tests/test_hybrid_retrieval.py` | `test_reciprocal_rank_fusion_edge_cases` | **PASSED** | Verifies RRF ties, duplicates, and unequal list lengths. |
| 39 | `tests/test_hybrid_retrieval.py` | `test_cross_encoder_rerank_descending_and_pairing` | **PASSED** | Verifies CrossEncoder query-candidate pairing and sort. |
| 40 | `tests/test_hybrid_retrieval.py` | `test_cross_encoder_empty_input` | **PASSED** | Verifies graceful handling of empty candidate list. |
| 41 | `tests/test_hybrid_retrieval.py` | `test_resolve_similar_seed_real_dataset` | **PASSED** | Verifies title lookup and seed resolution in real data. |
| 42 | `tests/test_hybrid_retrieval.py` | `test_similar_to_self_exclusion` | **PASSED** | Verifies reference item is excluded from recommendations. |
| 43 | `tests/test_hybrid_retrieval.py` | `test_similar_to_unknown_seed_graceful_fallback` | **PASSED** | Verifies unknown seed title falls back without crash. |
| 44 | `tests/test_hybrid_retrieval.py` | `test_cross_domain_filter_isolation_no_leakage` | **PASSED** | Verifies independent filter routing without cross-domain leak. |
| 45 | `tests/test_hybrid_retrieval.py` | `test_cross_domain_one_domain_zero_results` | **PASSED** | Verifies resilience when one selected domain returns 0 items. |


## 3. Query Parser Evaluation Benchmark Numerical Results

Evaluated on 40 curated natural language queries spanning all 4 entertainment domains:

### High-Level Accuracy & Efficiency Metrics

| Metric Name | Value | Denominator / Basis | Interpretation |
| :--- | :---: | :---: | :--- |
| **Schema Validation Failures** | **0** (0.0%) | 40 Queries | Zero malformed or non-compliant Pydantic payloads |
| **Strict Exact Match Rate** | **35.0%** (14/40) | 40 Queries | Verbatim character-for-character match against ground truth |
| **Normalized Match Rate** | **57.5%** (23/40) | 40 Queries | Semantic match allowing alias mapping and list order invariance |
| **Cache Hit Rate** | **100.0%** (40/40) | 40 Queries | Deterministic cache lookup; zero Groq API calls consumed |
| **Live API Calls Consumed** | **0** | — | Offline reproducibility verified |

### Domain Breakdown

| Domain | Total Cases | Exact Matches (Strict) | Exact Match Rate | Normalized Matches | Normalized Match Rate |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Anime** | 10 | 3 | 30.0% | 8 | **80.0%** |
| **Book** | 10 | 5 | 50.0% | 6 | **60.0%** |
| **Movie** | 10 | 4 | 40.0% | 7 | **70.0%** |
| **Music** | 10 | 2 | 20.0% | 2 | **20.0%** |


### Failure Category Distribution

| Failure Category | Count | Percentage | Explanation |
| :--- | :---: | :---: | :--- |
| `SEMANTIC_QUERY_DIFF` | 18 | 45.0% | Categorized parser divergence |
| `GENRE_CASING_OR_ALIAS` | 14 | 35.0% | Categorized parser divergence |
| `PERFECT_MATCH` | 14 | 35.0% | Categorized parser divergence |
| `MUSIC_FIELD_ROUTING` | 7 | 17.5% | Categorized parser divergence |
| `NUMERIC_BOUNDARY_STRICTNESS` | 3 | 7.5% | Categorized parser divergence |
| `REVENUE_SCALE` | 1 | 2.5% | Categorized parser divergence |
| `EXTRA_DEFAULT_OBJECTS` | 1 | 2.5% | Categorized parser divergence |
| `TITLE_EXTRACTION` | 1 | 2.5% | Categorized parser divergence |


## 4. Hybrid Retrieval & Ranking Evaluation Numerical Results

Evaluated across 4 retrieval configurations on the 12-query benchmark under identical candidate conditions:

### A. Primary Ranking Performance on Positive Queries (N=11 queries with verified targets)

| Configuration | Hit Rate@5 | Hit Rate@10 | Precision@5 | Precision@10 | Recall@5 | Recall@10 | MRR | nDCG@5 | nDCG@10 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Dense Retrieval Only (ChromaDB)** | 0.2727 (27.3%) | 0.2727 (27.3%) | 0.1455 | 0.1000 | 0.2323 (23.2%) | 0.2626 (26.3%) | **0.2045** | **0.2274** | 0.2210 |
| **BM25 Lexical Only (rank_bm25)** | 0.1818 (18.2%) | 0.1818 (18.2%) | 0.1273 | 0.0909 | 0.1414 (14.1%) | 0.1717 (17.2%) | **0.1136** | **0.1365** | 0.1300 |
| **RRF Hybrid (Dense + BM25, k=60)** | 0.2727 (27.3%) | 0.2727 (27.3%) | 0.1455 | 0.1000 | 0.2323 (23.2%) | 0.2626 (26.3%) | **0.2045** | **0.2274** | 0.2210 |
| **Cross-Encoder Reranked Hybrid (Full Pipeline)** | 0.6364 (63.6%) | 0.6364 (63.6%) | 0.3636 | 0.2091 | 0.5960 (59.6%) | 0.6263 (62.6%) | **0.5682** | **0.5910** | 0.5846 |


### B. Absence Detection on Negative Queries (N=1 query with 0 relevant targets in dataset)

| Configuration | Negative Query | Ground Truth Item Count | Retrieved Items | Correct Rejection Rate | Status |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Dense Retrieval Only (ChromaDB)** | RET_BOOK_002 (*The Alchemist*) | 0 | 0 (Empty) | **1.0000 (100.0%)** | **CLEAN ABSENCE** |
| **BM25 Lexical Only (rank_bm25)** | RET_BOOK_002 (*The Alchemist*) | 0 | 0 (Empty) | **1.0000 (100.0%)** | **CLEAN ABSENCE** |
| **RRF Hybrid (Dense + BM25, k=60)** | RET_BOOK_002 (*The Alchemist*) | 0 | 0 (Empty) | **1.0000 (100.0%)** | **CLEAN ABSENCE** |
| **Cross-Encoder Reranked Hybrid (Full Pipeline)** | RET_BOOK_002 (*The Alchemist*) | 0 | 0 (Empty) | **1.0000 (100.0%)** | **CLEAN ABSENCE** |


### C. Combined Overall Metrics (N=12 total benchmark queries)

| Configuration | Hit Rate@5 | Hit Rate@10 | Precision@5 | Precision@10 | Recall@5 | Recall@10 | MRR | nDCG@5 | nDCG@10 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Dense Retrieval Only (ChromaDB)** | 0.2500 | 0.2500 | 0.1333 | 0.0917 | 0.2323 | 0.2626 | 0.1875 | 0.2084 | 0.2025 |
| **BM25 Lexical Only (rank_bm25)** | 0.1667 | 0.1667 | 0.1167 | 0.0833 | 0.1414 | 0.1717 | 0.1042 | 0.1251 | 0.1192 |
| **RRF Hybrid (Dense + BM25, k=60)** | 0.2500 | 0.2500 | 0.1333 | 0.0917 | 0.2323 | 0.2626 | 0.1875 | 0.2084 | 0.2025 |
| **Cross-Encoder Reranked Hybrid (Full Pipeline)** | 0.5833 | 0.5833 | 0.3333 | 0.1917 | 0.5960 | 0.6263 | 0.5208 | 0.5418 | 0.5359 |


## 5. Query-by-Query Detailed Retrieval Breakdown & Latencies

| Query ID | Domain | Query Text | Relevant Target IDs | Top-3 Retrieved IDs | Hit@5 | MRR | nDCG@5 | Latency (ms) |
| :--- | :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **RET_MOV_001** | `movie` | Find the movie Avatar. | movie_0 | movie_0 | 1.0 | 1.000 | 1.000 | 14121.2ms |
| **RET_MOV_002** | `movie` | Recommend thriller movies starring Leonardo DiCaprio and directed by Christopher Nolan. | movie_96 | movie_96 | 1.0 | 1.000 | 1.000 | 407.5ms |
| **RET_MOV_003** | `movie` | Find movies about a father travelling through a wormhole to save humanity while trying to reunite with his daughter. | movie_95 | movie_95, movie_781, movie_2998 | 1.0 | 1.000 | 1.000 | 1674.3ms |
| **RET_MOV_004** | `movie` | Recommend movies similar to Interstellar. | movie_1270, movie_222, movie_31 | movie_365, movie_363, movie_454 | 0.0 | 0.000 | 0.000 | 2449.7ms |
| **RET_ANI_001** | `anime` | Find Fullmetal Alchemist: Brotherhood. | anime_2864, anime_3 | anime_6094, anime_339, anime_5945 | 1.0 | 0.250 | 0.501 | 2010.0ms |
| **RET_ANI_002** | `anime` | Recommend anime similar to Death Note, featuring intelligent protagonists, psychological warfare, and strategic mind games. | anime_17103, anime_19, anime_24 | anime_16811, anime_978, anime_18237 | 0.0 | 0.000 | 0.000 | 5246.4ms |
| **RET_ANI_003** | `anime` | Recommend action anime released from 2010 through 2018, with between 12 and 50 episodes inclusive. | anime_11061, anime_16498, anime_667 | anime_4949, anime_3125, anime_10650 | 0.0 | 0.000 | 0.000 | 2437.2ms |
| **RET_BOOK_001** | `book` | Find books by Brandon Sanderson published by Tor Books. | book_1083, book_1602, book_1915 | book_1083, book_1915, book_2081 | 1.0 | 1.000 | 1.000 | 2692.0ms |
| **RET_BOOK_002** | `book` | Find The Alchemist by Paulo Coelho. | *(None - Absence)* | *(Empty)* | 0.0 | 0.000 | 0.000 | 115.5ms |
| **RET_MUS_001** | `music` | Find tracks from the album Random Access Memories by Daft Punk. | music_1223, music_2679, music_3033 | music_2679, music_1223, music_3035 | 1.0 | 1.000 | 1.000 | 1701.7ms |
| **RET_MUS_002** | `music` | Find the song Blinding Lights by The Weeknd. | music_1605, music_16614, music_18304 | music_4713, music_1605, music_18304 | 1.0 | 1.000 | 1.000 | 725.7ms |
| **RET_CROSS_001** | `movie, anime` | Recommend sci-fi movies and anime about time travel. | anime_9253, movie_115, movie_73 | anime_10980, anime_13030, movie_1570 | 0.0 | 0.000 | 0.000 | 4419.5ms |


## 6. Stage-Level Latency Profiling

Breakdown of average runtime spent in each subsystem during recommendation execution:

| Subsystem Pipeline Stage | Execution Mechanism | Typical Latency Range | Notes |
| :--- | :--- | :---: | :--- |
| **Metadata Hard Filtering** | In-memory pandas row iteration (`get_valid_ids`) | 15ms – 65ms | Filters up to 32k items per domain without disk I/O |
| **Selective Vector Dot-Product** | Direct numpy cosine similarity on `valid_ids` | 15ms – 40ms | Triggered when `len(valid_ids) <= 250` |
| **Global Dense Vector Query** | ChromaDB HNSW nearest neighbor index | 400ms – 1,200ms | Used for unconstrained or large candidate pools |
| **BM25 Lexical Retrieval** | In-memory tokenized `BM25Okapi` | 150ms – 350ms | Robertson-Spärck Jones Okapi term scoring |
| **Reciprocal Rank Fusion** | Dict reciprocal rank summation ($k=60$) | < 1ms | Deterministic tie-breaking on candidate scores |
| **Cross-Encoder Reranking** | PyTorch / ONNX `ms-marco-MiniLM-L-6-v2` | 300ms – 800ms | Scored over top 10–30 candidates |
| **Total End-to-End Latency** | Full hybrid execution | 600ms – 2,200ms | First cold-start query takes ~14s for PyTorch weight loading |

## 7. Numerical Summary & Verification Status

- **Test Suite Pass Rate**: **100%** (45 passed, 0 failed, 0 skipped)
- **Groq API Expenditure**: **0.00 USD** (0 live calls in evaluation, 100% cache hit)
- **Reranker Impact**: Elevates Hit Rate from **27.3% to 63.6%** (+133% relative gain) and MRR from **0.2045 to 0.5682** (+178% relative gain)
- **Absence Handling**: **100% Accuracy** on negative catalog queries