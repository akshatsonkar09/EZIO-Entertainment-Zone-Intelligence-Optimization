# Stage 3 Report — Improve Candidate Retrieval

## 1. Executive Summary & Status
- **Status:** `PASS`
- **Objective:** Analyze and optimize first-stage candidate generation (Dense ChromaDB, BM25 lexical retrieval, and Reciprocal Rank Fusion) prior to neural reranking.
- **Key Empirical Results:**
  - **Retriever Complementarity:** Dense and BM25 candidate pools exhibit only **8.28% Jaccard overlap at top 100** (mean intersection of only 14.4 items out of 100).
  - **Incremental Coverage:** Across the 102 benchmark queries with ground-truth targets, Dense retrieval uniquely found **230 relevant targets missed by BM25**; BM25 uniquely found **193 relevant targets missed by Dense**. Both found only 144 simultaneously. This provides empirical proof of why hybrid retrieval is essential over single-retriever search.
  - **Candidate Pool Optimization:** Expanding the candidate retrieval pool from `candidate_k=60` to `candidate_k=80` increased overall candidate pool recall from **55.76% to 57.07% (+1.31 percentage points)**, with **Books gaining +3.15 percentage points (60.52% -> 63.67%)**.
  - **Fusion Enhancements:** Added list weighting support (`weights: list[float] | None = None`) and configurable smoothing (`k: int = 60`) in `reciprocal_rank_fusion` with guaranteed deterministic tie-breaking.
  - **All 6 Stage 3 tests passed**; full regression suite passing.

---

## 2. Independent Retriever Performance & Overlap Analysis

### Overlap & Jaccard Metrics (102 Benchmark Queries)
| Metric | Movie | Anime | Book | Overall |
| :--- | :---: | :---: | :---: | :---: |
| **Mean Jaccard Overlap @ 50** | 0.0680 (6.8%) | 0.1419 (14.2%) | 0.0863 (8.6%) | **0.0993 (9.9%)** |
| **Mean Jaccard Overlap @ 100** | 0.0605 (6.0%) | 0.1062 (10.6%) | 0.0810 (8.1%) | **0.0828 (8.3%)** |
| **Dense Unique Targets Found** | 80 | 98 | 52 | **230 targets** |
| **BM25 Unique Targets Found** | 41 | 101 | 51 | **193 targets** |
| **Simultaneous Target Overlap** | 36 | 49 | 59 | **144 targets** |

### Independent Recall by Domain
| Domain | Query Count | Dense Rec@50 | Dense Rec@100 | BM25 Rec@50 | BM25 Rec@100 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Movie** | 34 | 0.5525 | 0.5983 | 0.5445 | 0.5646 |
| **Anime** | 35 | 0.4344 | 0.4383 | 0.4692 | 0.4881 |
| **Book** | 33 | 0.5322 | 0.5877 | 0.6217 | 0.6612 |
| **Overall** | **102** | **0.5054** | **0.5400** | **0.5436** | **0.5696** |

---

## 3. Candidate Pool Depth Ablation (`candidate_k`)

We evaluated candidate pool depths $k \in \{40, 60, 80, 100\}$ on identical queries:

| Depth (`candidate_k`) | Movie Recall | Anime Recall | Book Recall | Overall Recall | Mean Retrieval Latency |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **40** | 0.5980 | 0.4689 | 0.5958 | 0.5530 | 11.2ms |
| **60 (Old Default)** | 0.6018 | 0.4697 | 0.6052 | 0.5576 | 13.5ms |
| **80 (New Selected)** | **0.6097** | **0.4706** | **0.6367** | **0.5707** | **15.1ms** |
| **100** | 0.6116 | 0.4733 | 0.6370 | 0.5723 | 17.8ms |

### Rationale for `candidate_k=80`:
- Moving from 60 to 80 captures significant relevant target mass in Books (+3.15%) and Movies (+0.79%) while adding less than 2ms of retrieval latency.
- Increasing further to 100 exhibits sharp diminishing returns (+0.0016 overall recall for +25% rerank candidates), making `candidate_k=80` the optimal pareto choice.

---

## 4. Implementation Modifications

### Files Modified & Created
1. **`src/project_black_knight/retrieval.py`:**
   - Updated `reciprocal_rank_fusion` to accept `weights: list[float] | None = None` allowing list-level importance weighting while preserving deterministic tie-breaking.
   - Updated `hybrid_retrieve` signature to default `candidate_k=80`, `rrf_k=60`, and accept `rrf_weights`.
   - Updated `search_black_knight` signature and call to pass `candidate_k=80` to all domains.
2. **`tests/test_stage_03_candidate_retrieval.py` (New Tests):**
   - 6 tests validating retriever independence, empty/duplicate candidate handling, deterministic generation, hard filter and exclusion enforcement, pool depth control, and RRF weighting/tie-breaking.
3. **`evaluation/tune_stage_03_retrieval.py` & `evaluation/evaluate_stage_03_retrieval.py`:**
   - Full evaluation scripts measuring independent retriever recall, Jaccard overlap, coverage breakdown, and latency.

---

## 5. Artifacts Persisted
- `reports/recommendation_quality/artifacts/stage_03/stage_03_metrics.json`
- `reports/recommendation_quality/artifacts/stage_03/stage_03_candidates.json`
- `reports/recommendation_quality/artifacts/stage_03/stage_03_tests.txt`

---

## 6. Reproduction Commands
- **Run Unit Tests:**
  `$env:PYTHONPATH='src'; project_black_knight\Scripts\python -m pytest tests/test_stage_03_candidate_retrieval.py -v`
- **Run Evaluation:**
  `$env:PYTHONPATH='src'; project_black_knight\Scripts\python evaluation/evaluate_stage_03_retrieval.py`

---

## 7. Next Stage Starting Point
- **Stage 3 Status:** `PASS`
- **Stage 4 Starting Point:** Stage 4 focuses on **Intent-Aware Reranking** (classifying and routing queries across reference similarity, genre discovery, mood/tone, explicit metadata constraints, and mixed intents, applying intent-aware neural and metadata scoring while preserving `domain_routed` as primary and `all_cross_encoder` as baseline).
