# Project Black Knight — Phase 5 Implementation Plan: Retrieval-Stage Observability and Diagnostics

## 1. Executive Summary & Objectives

The goal of Phase 5 is to implement comprehensive stage-level observability and diagnostics across Project Black Knight's production retrieval pipeline without modifying retrieval ranking, candidate pools, model configurations, weights, or filter logic.

This plan outlines:
1. Exact inspection findings of the current retrieval pipeline.
2. The design of a non-invasive, opt-in diagnostic instrumentation layer.
3. Target tracking across all retrieval stages (metadata filtering, dense retrieval, BM25 retrieval, RRF fusion, cross-encoder reranking, and multi-domain deduplication).
4. Failure taxonomy and automated classification logic.
5. All 9 persistent report and data files to be generated under `evaluation/results/`.
6. Validation strategy ensuring 100% parity between traced and untraced executions.

---

## 2. Inspection of Current Retrieval Pipeline

The production pipeline in `src/project_black_knight/retrieval.py` and `src/project_black_knight/metadata_filter.py` consists of the following discrete execution stages:

1. **Query Parsing & Filter Construction**:
   - Natural language queries are parsed into `BlackKnightQuery` objects (or passed directly).
   - Domain-specific filters are separated to avoid cross-domain filter leakage.
2. **Metadata Filtering (`get_valid_ids`)**:
   - Runs before retrieval on the domain catalog metadata dataframe.
   - Evaluates numeric bounds (`release_year`, `runtime`, `episodes`, `pages`, `rating`, `revenue`, `popularity`, `ranking`), entity filters (`director`, `cast`, `author`, `publisher`, `characters`, `production_companies`), and genre constraints (`genres_include`, `genres_exclude`).
   - Produces a set of `valid_ids`. If empty, retrieval halts early with an empty-catalog rejection.
3. **Similar-To Seed Resolution & Exclusion**:
   - Resolves seed item titles. If a seed belongs to the target domain, it is excluded from `valid_ids` to prevent self-recommendation.
4. **Dense Semantic Retrieval (`dense_retrieve`)**:
   - Queries ChromaDB using SentenceTransformers (`all-MiniLM-L6-v2`) embeddings.
   - Filters candidate IDs by `valid_ids`, retrieving up to `candidate_k` (60) candidates with cosine similarity scores.
5. **Lexical Retrieval (`bm25_retrieve`)**:
   - Tokenizes query text and evaluates BM25 Okapi over document text tags, filtered by `valid_ids`.
   - Retrieves up to `candidate_k` (60) candidates with BM25 scores.
6. **Reciprocal Rank Fusion (`reciprocal_rank_fusion`)**:
   - Combines Dense and BM25 candidate lists using $RRF(d) = \sum \frac{1}{60 + rank(d, L)}$.
   - Deterministically tie-breaks by $(-score, id)$. Returns up to `candidate_k` (60) candidates.
7. **Neural Cross-Encoder Reranking (`rerank_candidates`)**:
   - Architecture A (`all_cross_encoder`): Reranks all domains with `cross-encoder/ms-marco-MiniLM-L-6-v2`.
   - Architecture B (`domain_routed`): Reranks movies and mixed-domain queries; bypasses anime and books.
   - Architecture C (`rrf_only`): Bypasses reranking across all domains.
   - Score combination: $0.55 \cdot \text{norm\_ce} + 0.45 \cdot \text{norm\_rrf}$.
8. **Multi-Domain Aggregation & Deduplication**:
   - Combines candidates across domains, sorts by score descending, and deduplicates by canonical item ID.
   - Truncates to final `top_k` (10).

---

## 3. Instrumentation Architecture & Non-Invasive Tracing

To guarantee zero regression and avoid performance overhead in production:
- A new module `src/project_black_knight/diagnostics.py` will define structured data classes:
  - `StageRecord`: Captures candidate IDs, ranks, scores, timestamps, and target presence.
  - `FilterRejectionDetail`: Captures specific filter condition that rejected a candidate/target.
  - `QueryTrace`: Captures query metadata, targets, per-stage records, final rankings, latency breakdown, and failure classification.
- In `src/project_black_knight/retrieval.py`:
  - `search_black_knight` and `hybrid_retrieve` will accept an optional `trace: bool = False` or `trace_collector: QueryTraceCollector | None = None` parameter.
  - When `trace=False` (default), execution proceeds identically with zero overhead.
  - When `trace=True` or a collector is passed, stage outputs are recorded via immutable snapshots.
  - The returned response includes the trace in `response["diagnostics"]["trace"]` without altering `results` or their scores/order.

---

## 4. Stage-Wise Target Tracking & Failure Taxonomy

For every benchmark query and architecture:
1. **Target Identification**:
   - Extract `relevant_ids` from benchmark ground truth (`black_knight_eval_queries_113_audited.csv`).
   - For absence queries (`relevant_ids` is empty), track correct rejection vs false acceptance.
2. **Stage Progression Tracking**:
   For each target item ID:
   - *Catalog Presence*: Does the ID exist in the catalog?
   - *Metadata Filtering*: Did the target pass `valid_ids`? If rejected, record the exact failing field (e.g., `release_year_min`, `genre_exclude`).
   - *Seed Exclusion*: Was the target excluded as a seed reference?
   - *Dense Retrieval*: Was the target in top 60 dense results? What was its rank and score?
   - *BM25 Retrieval*: Was the target in top 60 BM25 results? What was its rank and score?
   - *RRF Fusion*: Did the target survive fusion? What was its fused rank and score?
   - *Cross-Encoder Reranking*: Did the cross-encoder promote, demote, or drop the target? Pre-CE rank vs post-CE rank.
   - *Cutoff*: Did the target appear in top 5 / top 10 / top 60?
3. **Failure Classification Taxonomy**:
   - `metadata_filter_rejection`: Relevant target was excluded by hard filter.
   - `dense_and_bm25_miss`: Target was not retrieved by either dense or BM25 first-stage retrieval.
   - `dense_only_miss`: Retrieved by BM25, missed by dense.
   - `bm25_only_miss`: Retrieved by dense, missed by BM25.
   - `rrf_fusion_drop`: Retrieved in first stage but fell below `candidate_k` in RRF fusion.
   - `cross_encoder_demotion`: Target was in top 10 post-fusion, but cross-encoder demoted it below cutoff.
   - `rank_cutoff_top5`: Target present in final top 10, but missed top 5.
   - `rank_cutoff_top10`: Target present in RRF/reranked list (ranks 11–60), but missed top 10.
   - `absence_false_acceptance`: Absence query returned non-empty results.
   - `success`: Target successfully retrieved in top 10 (or top 5).

---

## 5. Required Deliverables & Schemas

The following 9 files will be generated under `evaluation/results/`:

1. `retrieval_113_phase5_report.md`: Comprehensive executive report with tables, stage survival metrics, and latency analysis.
2. `retrieval_113_phase5_report.json`: Machine-readable summary with all configuration metrics.
3. `retrieval_113_phase5_query_traces.jsonl`: 339 full query traces (113 queries $\times$ 3 architectures).
4. `retrieval_113_phase5_failure_analysis.csv`: Detailed failure instances per target with earliest failure stage and evidence.
5. `retrieval_113_phase5_architecture_comparison.csv`: Direct tabular comparison across Architecture A, Architecture B, and Pure RRF.
6. `retrieval_113_phase5_stage_summary.csv`: Aggregated candidate counts, target survival rates, and latencies per stage.
7. `retrieval_113_phase5_test_report.md`: Test execution results and pass/fail counts.
8. `retrieval_113_phase5_query_traces.csv`: Flattened spreadsheet view of all traces.
9. `retrieval_113_phase5_known_issues.md`: Verified defects, failure patterns, and architectural recommendations for future phases.

---

## 6. Execution & Validation Steps

1. **Step 1: Diagnostics Module Implementation**
   - Create `src/project_black_knight/diagnostics.py` with trace collectors and serialization.
2. **Step 2: Retrieval Pipeline Instrumentation**
   - Wire diagnostic hooks into `src/project_black_knight/retrieval.py` (`hybrid_retrieve` and `search_black_knight`).
3. **Step 3: Verification & Parity Tests**
   - Create `tests/test_retrieval_diagnostics.py` verifying:
     - Exact parity: `search_black_knight(..., trace=False)` and `search_black_knight(..., trace=True)` produce identical candidates, ordering, and scores.
     - Trace completeness: all stages (metadata, dense, BM25, RRF, cross-encoder, final) recorded.
     - Correct failure classification.
     - JSON/JSONL serialization validity.
4. **Step 4: Run Complete Test Suite**
   - Ensure all 111+ tests pass.
5. **Step 5: Run 113-Query Diagnostic Evaluation**
   - Execute benchmark evaluation across all 3 architectures with full tracing.
6. **Step 6: Generate All Required Deliverables**
   - Validate formatting and non-emptiness of JSON, JSONL, CSV, and Markdown files.
