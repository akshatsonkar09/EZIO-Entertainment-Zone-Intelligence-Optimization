# Project Black Knight — Phase 4 Hybrid Retrieval Evaluation Report

**Generated:** 2026-10-19T06:39:17Z  
**Phase:** 4 (Hybrid Retrieval, Ranking, Similar-Item, Cross-Domain)  

## 1. Executive Summary & Metric Comparison

### Primary Ranking Metrics on Positive Queries (N=11 queries with verified relevant targets)

| Configuration | Hit Rate@5 | Hit Rate@10 | Precision@5 | Precision@10 | Recall@5 | Recall@10 | MRR | nDCG@5 | nDCG@10 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Dense Retrieval Only (ChromaDB)** | 0.2727 | 0.2727 | 0.1455 | 0.1000 | 0.2323 | 0.2626 | 0.2045 | 0.2274 | 0.2210 |
| **BM25 Lexical Only** | 0.1818 | 0.1818 | 0.1273 | 0.0909 | 0.1414 | 0.1717 | 0.1136 | 0.1365 | 0.1300 |
| **RRF Hybrid (Dense + BM25, k=60)** | 0.2727 | 0.2727 | 0.1455 | 0.1000 | 0.2323 | 0.2626 | 0.2045 | 0.2274 | 0.2210 |
| **Cross-Encoder Reranked Hybrid (Full Pipeline)** | 0.6364 | 0.6364 | 0.3636 | 0.2091 | 0.5960 | 0.6263 | 0.5682 | 0.5910 | 0.5846 |

### Absence Detection Performance (N=1 negative query with 0 relevant targets in dataset)

| Configuration | Absence Query | Expected Target | Retrieved Items | Correct Rejection Rate |
| :--- | :--- | :--- | :--- | :---: |
| **Dense Retrieval Only (ChromaDB)** | RET_BOOK_002 (*The Alchemist*) | None (absent from dataset) | 0 items (correctly empty) | **1.0000 (100%)** |
| **BM25 Lexical Only** | RET_BOOK_002 (*The Alchemist*) | None (absent from dataset) | 0 items (correctly empty) | **1.0000 (100%)** |
| **RRF Hybrid (Dense + BM25, k=60)** | RET_BOOK_002 (*The Alchemist*) | None (absent from dataset) | 0 items (correctly empty) | **1.0000 (100%)** |
| **Cross-Encoder Reranked Hybrid (Full Pipeline)** | RET_BOOK_002 (*The Alchemist*) | None (absent from dataset) | 0 items (correctly empty) | **1.0000 (100%)** |

### Combined Overall Metrics (N=12 total benchmark queries)

| Configuration | Hit Rate@5 | Hit Rate@10 | Precision@5 | Precision@10 | Recall@5 | Recall@10 | MRR | nDCG@5 | nDCG@10 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Dense Retrieval Only (ChromaDB)** | 0.2500 | 0.2500 | 0.1333 | 0.0917 | 0.2323 | 0.2626 | 0.1875 | 0.2084 | 0.2025 |
| **BM25 Lexical Only** | 0.1667 | 0.1667 | 0.1167 | 0.0833 | 0.1414 | 0.1717 | 0.1042 | 0.1251 | 0.1192 |
| **RRF Hybrid (Dense + BM25, k=60)** | 0.2500 | 0.2500 | 0.1333 | 0.0917 | 0.2323 | 0.2626 | 0.1875 | 0.2084 | 0.2025 |
| **Cross-Encoder Reranked Hybrid (Full Pipeline)** | 0.5833 | 0.5833 | 0.3333 | 0.1917 | 0.5960 | 0.6263 | 0.5208 | 0.5418 | 0.5359 |

### Metric Definitions & Benchmark Integrity Rules

- **Positive Evaluation ($N=11$)**: Evaluates queries that have at least one ground-truth target in the dataset. Standard denominator for IR precision, recall, and ranking quality.
- **Hit Rate@K**: 1.0 if at least one ground-truth relevant item appears in the top $K$, else 0.0.
- **Precision@K**: $\frac{|\text{Retrieved@K} \cap \text{Relevant}|}{K}$.
- **Recall@K**: $\frac{|\text{Retrieved@K} \cap \text{Relevant}|}{|\text{Relevant}|}$. Undefined for absence queries.
- **MRR (Mean Reciprocal Rank)**: $\frac{1}{\text{rank of first relevant item}}$ (0.0 if not retrieved in top candidates).
- **nDCG@K**: Normalized Discounted Cumulative Gain with graded relevance ($2$ for exact/primary match, $1$ for partial match).
- **Absence Handling ($N=1$)**: Negative queries with zero targets are reported separately as Correct Rejection Rate (1.0 = correctly returning 0 items). They do not inflate conventional positive hit rates.

## 2. Pipeline Tracing and Component Integration

1. **Metadata Filtering Integration**: `get_valid_ids()` from `metadata_filter.py` (Phase 3) is executed *first* on every request, enforcing all hard constraints across release year, runtime, episodes, genres include/exclude, author, artist, and director.
2. **Selective Pre-Filtering Optimization**: When `valid_ids` is selective ($\le 250$ items), direct vector dot-product scoring is performed against candidate embeddings, overcoming the vector database pre/post-filtering dilemma where selective metadata constraints cause top-K drops in global nearest neighbor queries.
3. **Lexical BM25 Retrieval**: `BM25Okapi` retrieves term-frequency ranked candidates within the hard-filtered candidate pool.
4. **Reciprocal Rank Fusion**: RRF formula $RRF(d) = \sum_{m \in M} \frac{1}{60 + r_m(d)}$ merges dense and lexical rankings with deterministic tie-breaking.
5. **Neural Cross-Encoder Reranking**: `cross-encoder/ms-marco-MiniLM-L-6-v2` reranks top fused candidates against the effective query.
6. **Similar-To Seed Resolution**: Reference titles (`similar_to`) resolve to real dataset items, seed text enriches the query, and seed IDs are strictly excluded from recommendations to prevent self-recommendation.
7. **Cross-Domain Routing**: Multi-domain queries independently execute each domain pipeline without filter leakage, merging results by reranker confidence.

## 3. Detailed Per-Query Results

| Query ID | Domains | Query Text | Relevant Items | Retrieved Top-3 | Hit@5 | MRR | Latency |
| :--- | :---: | :--- | :--- | :--- | :---: | :---: | :---: |
| **RET_MOV_001** | `movie` | Find the movie Avatar. | movie_0 | movie_0 | 1.0 | 1.000 | 14121.24ms |
| **RET_MOV_002** | `movie` | Recommend thriller movies starring Leonardo DiCaprio and directed by Christopher Nolan. | movie_96 | movie_96 | 1.0 | 1.000 | 407.5ms |
| **RET_MOV_003** | `movie` | Find movies about a father travelling through a wormhole to save humanity while trying to reunite with his daughter. | movie_95 | movie_95, movie_781, movie_2998 | 1.0 | 1.000 | 1674.34ms |
| **RET_MOV_004** | `movie` | Recommend movies similar to Interstellar. | movie_1270, movie_222, movie_31 | movie_365, movie_363, movie_454 | 0.0 | 0.000 | 2449.68ms |
| **RET_ANI_001** | `anime` | Find Fullmetal Alchemist: Brotherhood. | anime_2864, anime_3 | anime_6094, anime_339, anime_5945 | 1.0 | 0.250 | 2010.05ms |
| **RET_ANI_002** | `anime` | Recommend anime similar to Death Note, featuring intelligent protagonists, psychological warfare, and strategic mind games. | anime_17103, anime_19, anime_24 | anime_16811, anime_978, anime_18237 | 0.0 | 0.000 | 5246.44ms |
| **RET_ANI_003** | `anime` | Recommend action anime released from 2010 through 2018, with between 12 and 50 episodes inclusive. | anime_11061, anime_16498, anime_667 | anime_4949, anime_3125, anime_10650 | 0.0 | 0.000 | 2437.25ms |
| **RET_BOOK_001** | `book` | Find books by Brandon Sanderson published by Tor Books. | book_1083, book_1602, book_1915 | book_1083, book_1915, book_2081 | 1.0 | 1.000 | 2692.0ms |
| **RET_BOOK_002** | `book` | Find The Alchemist by Paulo Coelho. | *(None - Absence test)* | *(Empty)* | 0.0 | 0.000 | 115.54ms |
| **RET_MUS_001** | `music` | Find tracks from the album Random Access Memories by Daft Punk. | music_1223, music_2679, music_3033 | music_2679, music_1223, music_3035 | 1.0 | 1.000 | 1701.68ms |
| **RET_MUS_002** | `music` | Find the song Blinding Lights by The Weeknd. | music_1605, music_16614, music_18304 | music_4713, music_1605, music_18304 | 1.0 | 1.000 | 725.67ms |
| **RET_CROSS_001** | `movie, anime` | Recommend sci-fi movies and anime about time travel. | anime_9253, movie_115, movie_73 | anime_10980, anime_13030, movie_1570 | 0.0 | 0.000 | 4419.51ms |

## 4. Key Findings, Fixed Defects & Remaining Gaps

### Confirmed Defects Fixed in Phase 4

1. **Chroma Post-Filtering Drop for Constrained Queries**: In global vector search, fetching only $K=100$ neighbors before applying metadata filters caused known-item queries (e.g. `title='Avatar'`) to return zero results because `Avatar` was ranked at 547 in the unconstrained global vector space. Fixed by adding direct vector scoring on `valid_ids` when candidate count is selective ($\le 250$).
2. **BM25 Negative IDF on Small/Ubiquitous Fixtures**: Robertson BM25 IDF is negative when $df > N/2$. In test fixtures with high document frequency, breaking on `score <= 0.0` dropped matching documents. Fixed in fixtures and safe-guarded in retrieval.
3. **Missing `title` in Filter Routing**: `common.title` was previously omitted in filter parameter mapping in `search_black_knight`. Added to domain filter dictionaries.
4. **`similar_to` Historical Functional Gap**: Previous repository code ignored `similar_to`. Implemented `resolve_similar_seed()` with title resolution, query augmentation, and seed self-exclusion.
5. **Cross-Domain Filter Leakage Protection**: Strict domain-specific filter dictionary construction prevents book attributes from polluting movie queries and vice versa.

### Remaining Functional Gaps for Future Phases

- **Dataset Tag Omission**: In `data/processed/movies1234.pkl`, the original preprocessor constructed `tag = keywords + overview + cast + director` without prepending the film's title. While metadata filtering and fallback vector scoring recover exact titles, indexing titles in future re-embeddings would improve raw unconstrained dense similarity.
- **Goodreads Book Corpus Gaps**: High-profile titles like Paulo Coelho's *The Alchemist* are not in the 11,230 Goodreads sample. The system correctly returns 0 results rather than hallucinating irrelevant books.