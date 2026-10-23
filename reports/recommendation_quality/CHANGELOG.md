# Project Black Knight — Recommendation Quality Implementation Changelog

All notable changes, test validations, and stage checkpoints are recorded chronologically in this file.

---

## [Initial Baseline] — 2026-10-22
- Repository inspected: `src/project_black_knight/query_parser.py`, `src/project_black_knight/retrieval.py`, `src/project_black_knight/metadata_filter.py`, `src/project_black_knight/text_normalizer.py`.
- Verified working tree: Standalone local directory (no Git repository initialized).
- Baseline test suite executed: **117 / 117 tests passed** (`reports/recommendation_quality/artifacts/baseline_tests.txt`).
- Baseline architecture: Primary `domain_routed` (Movie CE, Anime/Book RRF), Comparison baseline `all_cross_encoder`.

---

## [Stage 1: Reference-Based Similarity] — 2026-10-22
- **Implemented:**
  - Created `src/project_black_knight/title_aliases.py` with verified cross-lingual and subtitle alias mappings (Anime, Movie, Book).
  - Pre-indexed normalized title keys in `RetrievalRepository` for $O(1)$ dictionary lookup.
  - Multi-ID canonical self-exclusion in `resolve_similar_seed` and `hybrid_retrieve`, closing the catalog duplicate leak across 2,848 anime and 153 book duplicates.
  - Distinct works protection: release year separation ($\ge 5$ years) and author validation to prevent false merges of distinct adaptations.
  - Query augmentation token budget bounding (350 chars) to prevent MiniLM cross-encoder truncation.
  - Grounded similarity explanation generation in `search_black_knight`.
- **Tested:**
  - Added `tests/test_stage_01_reference_similarity.py` (11 unit and integration tests, all passed).
  - Full test suite: **128 / 128 passed** (`reports/recommendation_quality/artifacts/stage_01/stage_01_tests.txt`).
- **Validated:**
  - Seed leak count dropped from 100% in Anime / 40% in Books to **0% (zero leaks)**.
  - Movie Hit@10 improved from 0.4000 to **0.6000**.
  - Anime median latency reduced by $4.2\times$ (377.6ms vs 1,606.9ms).
  - Generated artifacts: `stage_01_metrics.json`, `stage_01_query_traces.json`, `stage_01_tests.txt`.

---

## [Stage 2: Better Item Representations] — 2026-10-22
- **Implemented:**
  - Created `src/project_black_knight/item_representations.py` providing structured, domain-aware representations for movies (title, director, cast, genres, year, themes, synopsis), anime (title, genres, year, episodes, ranking tier, synopsis), and books (title, author, genres, characters, length tier, synopsis).
  - Built zero-hallucination, deterministic representation generation with whitespace and comma normalization.
  - Added versioning support (`v1_legacy` vs `v2_structured_semantic`) in `RetrievalRepository.get_documents_and_ids`, `get_bm25_index`, `bm25_retrieve`, `rerank_candidates`, `hybrid_retrieve`, and `search_black_knight`.
- **Tested:**
  - Added `tests/test_stage_02_item_representations.py` (9 tests covering field formatting, missing value handling, determinism, domain isolation, and versioning).
  - All 9 unit tests passed; full test suite: **137 / 137 passed**.
- **Validated:**
  - Movie BM25 Recall@100 increased from **44.77% to 56.46% (+11.69 percentage points)**.
  - Overall BM25 Recall@100 increased from **53.06% to 56.96% (+3.90 percentage points)** across all 102 benchmark queries.
  - Overall BM25 Recall@50 increased from **49.67% to 54.36% (+4.69 percentage points)**.
  - Overall RRF candidate Recall@100 improved to **57.71%**.
  - Generated artifacts: `stage_02_metrics.json`, `stage_02_representation_samples.json`, `stage_02_tests.txt`.

---

## [Stage 3: Better Candidate Retrieval] — 2026-10-22
- **Implemented:**
  - Empirically evaluated independent Dense and BM25 retrievers across 102 benchmark queries.
  - Measured retriever complementarity: Dense and BM25 exhibit only **8.28% Jaccard overlap @ 100**, with Dense finding 230 unique relevant targets and BM25 finding 193 unique targets.
  - Conducted candidate pool depth ablation: selected `candidate_k=80` (improving candidate pool recall from 55.76% to **57.07% overall**, and **+3.15 percentage points in Books: 60.52% -> 63.67%**).
  - Extended `reciprocal_rank_fusion` with optional list weighting (`weights: list[float] | None = None`) and configurable smoothing (`k: int = 60`).
  - Updated `hybrid_retrieve` and `search_black_knight` to route `candidate_k=80`.
- **Tested:**
  - Added `tests/test_stage_03_candidate_retrieval.py` (6 unit and integration tests covering retriever independence, duplicate handling, determinism, hard filter enforcement, pool depth, and RRF weights).
  - All 6 unit tests passed; full test suite: **143 / 143 passed**.
- **Validated:**
  - Overall candidate pool recall reached **57.07%** at `candidate_k=80`.
  - Generated artifacts: `stage_03_metrics.json`, `stage_03_candidates.json`, `stage_03_tests.txt`.

---

## [Stage 4: Intent-Aware Reranking] — 2026-10-22
- **Implemented:**
  - Created `src/project_black_knight/intent_reranker.py` supporting deterministic intent classification across 5 categories (`reference_similarity`, `genre_discovery`, `mood_tone_discovery`, `metadata_constraints`, `mixed_intent`) and `general_semantic`.
  - Built intent-specific alignment scoring based on verified catalog metadata (genres, keywords, themes, director, author) with dynamic fusion weighting.
  - Extended `BlackKnightQuery` schema with optional `intent` field.
  - Integrated intent-aware reranking into `hybrid_retrieve` and `search_black_knight` with zero extra neural model calls.
- **Tested:**
  - Added `tests/test_stage_04_intent_reranking.py` (6 unit and integration tests covering intent routing, determinism, missing metadata safety, filter preservation, architecture parity, and seed exclusion).
  - All 6 unit tests passed; full test suite: **149 / 149 passed**.
- **Validated:**
  - `domain_routed` achieved **Hit@10 = 0.7647**, **MRR = 0.6166**, **nDCG@10 = 0.6041** at **267.57 ms median latency** with **0 constraint violations**.
  - `domain_routed` proved $5.6\times$ faster than `all_cross_encoder` in Anime and $10.7\times$ faster in Books.
  - Generated artifacts: `stage_04_metrics.json`, `stage_04_rankings.json`, `stage_04_tests.txt`.

---

## [Stage 5: Taste-Aware Personalization] — 2026-10-22
- **Implemented:**
  - Created `src/project_black_knight/personalization.py` with `UserPreferences` schema supporting liked/disliked items, preferred/disliked genres, preferred creators, and reference titles.
  - Built stateless, privacy-preserving personalization re-ranking with deterministic conflict resolution (negative safety prioritization).
  - Integrated `user_profile` into `hybrid_retrieve` and `search_black_knight` with bit-for-bit identical non-personalized fallback.
  - Hard filters verified strictly inviolable (cannot be bypassed by personalization).
- **Tested:**
  - Added `tests/test_stage_05_personalization.py` (8 unit and integration tests covering baseline identity, positive boosting, negative demotion, explicit item penalties, conflict safety, hard filter inviolability, and session isolation).
  - All 8 unit tests passed; full test suite: **157 / 157 passed**.
- **Validated:**
  - Functionally evaluated across 6 synthetic profiles (demonstrated targeted candidate shifts, e.g. demoting horror hybrid *Lake Placid* out of top 3 for horror-averse profile).
  - Production recommendation quality marked as **NOT VALIDATED** per protocol due to lack of ground-truth human user histories in repository datasets.
  - Generated artifacts: `stage_05_metrics.json`, `stage_05_profile_tests.json`, `stage_05_tests.txt`.

---

## [Stage 6: Relevance Evaluation Framework] — 2026-10-22
- **Implemented:**
  - Created `evaluation/benchmark_v2_graded_relevance.json`: 30 held-out evaluation queries with verified catalog IDs, 4-tier graded relevance (3=Highly Relevant, 2=Partially Relevant, 1=Weakly Relevant, 0=Irrelevant/Distractor/Seed), and hard seed exclusion bounds.
  - Created `reports/recommendation_quality/artifacts/benchmark_manifest.json` recording catalog snapshots, splits, seeds, model configurations, and formal metric formulas.
  - Created `evaluation/run_final_benchmark_evaluation.py`: automated evaluation runner comparing `domain_routed` against `all_cross_encoder` and executing a 5-configuration per-stage ablation suite.
  - Added `enable_intent_rerank` parameter to `search_black_knight` to enable clean ablation isolation of intent reranking.
  - Added Dune book alias mapping to `BOOK_TITLE_ALIASES` in `title_aliases.py`.
- **Tested:**
  - Added `tests/test_stage_06_evaluation_framework.py` (4 unit tests covering manifest validity, v2 dataset schema, graded DCG/nDCG computation, and ranking evaluation metrics).
  - All 4 tests passed; full test suite: **161 / 161 passed**.
- **Validated:**
  - Evaluated on 30 held-out benchmark v2 queries across Movie, Anime, and Book domains:
    - Primary architecture `domain_routed`: Hit@10 = **0.5000**, MRR = **0.2950**, nDCG@10 = **0.2532**, Seed Leak Rate = **0.0000 (0 leaks)**, Hard Constraint Violations = **0**, Median Latency = **337.99 ms** ($5.1\times$ faster than `all_cross_encoder`).
    - Comparison baseline `all_cross_encoder`: Hit@10 = 0.5333, MRR = 0.2915, nDCG@10 = 0.2718, Seed Leak Rate = 0.0000, Median Latency = 1723.98 ms.
    - Anime domain: `domain_routed` achieved higher MRR (**0.2000** vs. **0.0694**) and higher nDCG@10 (**0.1200** vs. **0.0857**) due to preserving dense-lexical consensus without cross-encoder domain distortion.
    - Full ablation confirmed Intent Reranking directly boosted MRR from 0.2733 to **0.2950 (+7.9% relative)**.
  - Generated artifacts: `stage_06_metrics.json`, `stage_06_query_results.json`, `stage_06_tests.txt`, `benchmark_manifest.json`, and root `FINAL_METRICS.json`.

