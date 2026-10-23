# Project Black Knight — Phase 5 Artifact Audit and Metric Reconciliation Report

## 1. Executive Summary

This audit independently inspects, recalculates, and reconciles all artifacts, metrics, failure classifications, and claims produced during **Phase 5: Retrieval-Stage Observability and Diagnostics**.

### Key Audit Verdicts
- **Audit Status:** **PASS WITH RECONCILED FINDINGS**
- **Artifact Consistency:** **PASS**. All 10 Phase 5 files exist, parse cleanly, and cross-reference consistently.
- **Metric Reproducibility:** **PASS**. All 27 ranking metrics across 3 architectures reproduce independently from the trace result lists with 0 mismatches.
- **Target Count Discrepancy (33,971 vs. 11,503):** **RECONCILED & PROVEN**. 11,503 is the number of query-target pairs in a single benchmark run ($11,503 \times 3 = 34,509$ total evaluations across 3 architectures). The 33,971 rows in `failure_analysis.csv` represent every evaluated query-target instance that did not achieve `success_top5` ($34,509 - 538 = 33,971$).
- **Cross-Encoder Demotions:** **VERIFIED**. Architecture A produced 56 demotions (18 movie, 27 anime, 11 book). Architecture B produced 18 demotions (18 movie, 0 anime, 0 book), confirming a **67.9% reduction** via domain routing.
- **Production Parity:** **VERIFIED**. A reproducible stratified parity check on 20 queries across all 3 architectures (60 total comparisons) yielded a **100% exact match** on candidate IDs, candidate ordering, and scores.
- **Absence Queries:** **QUALIFIED**. All 11 absence queries correctly returned 0 results (100% rejection rate). However, the audit confirms that all 11 are rejected at metadata filtering (`valid_ids=0`) due to conflicting hard constraints, meaning they evaluate filter-driven absence rather than vector-threshold semantic rejection.

---

## 2. Target Count Reconciliation (33,971 vs. 11,503)

### Investigation Findings
The user query highlighted an apparent contradiction between:
- **33,971 target evaluations** in `retrieval_113_phase5_failure_analysis.csv`
- **11,503 target evaluations** in `retrieval_113_phase5_stage_summary.csv` and report tables

### Independent Mathematical Reconciliation
1. **Benchmark Ground Truth Structure:**
   - Total queries: **113** (102 positive queries, 11 absence queries).
   - In the 102 positive queries, summing the ground-truth `relevant_ids` list yields **11,503 query-target pairs**.
   - These 11,503 pairs comprise **10,211 unique item IDs** (some items are relevant to multiple queries).
2. **Three-Architecture Evaluation Space:**
   - Because each query is executed across 3 architectures (Architecture A, Architecture B, Pure RRF), the total number of query-target evaluations is:
     $$\text{Total Target Evaluations} = 11,503 \times 3 = 34,509$$
3. **Distribution of Target Outcomes:**
   - Out of the 34,509 target evaluations, exactly **538 instances achieved top-5 ranking** (`success_top5`):
     - Architecture A: 181
     - Architecture B: 180
     - Pure RRF: 177
     - Total: $181 + 180 + 177 = 538$
   - Targets achieving `success_top5` are not failures and are therefore excluded from `retrieval_113_phase5_failure_analysis.csv`.
   - The remaining target evaluations that suffered a failure, demotion, drop, or cutoff are:
     $$\text{Non-Success Targets} = 34,509 - 538 = 33,971$$
   - Breakdown by architecture in `retrieval_113_phase5_failure_analysis.csv`:
     - Architecture A: $11,503 - 181 = 11,322$ rows
     - Architecture B: $11,503 - 180 = 11,323$ rows
     - Pure RRF: $11,503 - 177 = 11,326$ rows
     - Total rows: $11,322 + 11,323 + 11,326 = \mathbf{33,971}$ rows.
4. **Conclusion & Typographical Root Cause:**
   - Both denominators are valid and mathematically sound: **11,503** is the per-architecture denominator, while **33,971** is the 3-architecture failure count ($34,509 - 538$).
   - A typographical error was identified in `retrieval_113_phase5_report.md` line 47:
     *Reported:* `Target survival counts and survival rates across pipeline stages (Total positive targets: 102):`
     *Correction:* The figure 102 is the number of **positive queries**, not positive targets. The target denominator used in the table calculations is 11,503.

---

## 3. Audit of Failure Classifications

Every failure record in `retrieval_113_phase5_failure_analysis.csv` was verified against its trace progression:

| Failure Category | Architecture A | Architecture B | Pure RRF | Total Non-Successes | Failure Mechanism & Evidence |
|---|---:|---:|---:|---:|---|
| `dense_and_bm25_miss` | 8,370 | 8,370 | 8,370 | 25,110 | Target not in top 60 of either Dense ChromaDB or BM25 lexical retrieval. Dominates large categorical queries (e.g. genre queries with >3,000 ground truth items). |
| `metadata_filter_rejection` | 1,658 | 1,658 | 1,658 | 4,974 | Target excluded by hard filter (e.g. title mismatch, release year bound, or genre exclusion). Confirmed via `explain_filter_rejection`. |
| `rank_cutoff_top10` | 726 | 766 | 786 | 2,278 | Target survived fusion and reranking at ranks 11–60, but was cut off by the top-10 result limit. |
| `rrf_fusion_drop` | 389 | 389 | 389 | 1,167 | Target was retrieved in first stage (Dense or BM25), but multi-list rank reciprocal fusion pushed it below rank 60. |
| `rank_cutoff_top5` | 108 | 107 | 108 | 323 | Target achieved a top-10 position (ranks 6–10) but missed top 5. |
| `cross_encoder_demotion` | **56** | **18** | **0** | **74** | Target had an RRF rank $\le 10$, but the cross-encoder demoted it out of the top 10. |
| `seed_self_exclusion` | 15 | 15 | 15 | 45 | Target was requested as a reference seed (`similar_to`) and excluded to prevent self-recommendation. |
| `absence_false_acceptance` | **0** | **0** | **0** | **0** | Zero false acceptances across all 11 absence queries (33 executions). |
| **Sum** | **11,322** | **11,323** | **11,326** | **33,971** | Exactly reconciles with `failure_analysis.csv` row count. |

### Domain-Specific Cross-Encoder Demotion Verification
The audit examined which catalog domains suffered the 56 and 18 cross-encoder demotions:
- **Architecture A (All Cross-Encoder):**
  - Movie demotions: 18
  - Anime demotions: 27
  - Book demotions: 11
  - Total: $18 + 27 + 11 = 56$
- **Architecture B (Domain-Routed):**
  - Movie demotions: 18
  - Anime demotions: **0** (bypassed)
  - Book demotions: **0** (bypassed)
  - Total: **18**
- **Arithmetic Reduction:** $(56 - 18) / 56 = 38 / 56 = \mathbf{67.86\%}$ (reported as 67.9%). The claim is arithmetically exact and empirically verified.

---

## 4. Trace Completeness and Syntactic Validation

1. **File Format & Syntax:**
   - `retrieval_113_phase5_query_traces.jsonl` contains exactly **339 lines**.
   - Every line parses into a valid JSON object without syntax errors, missing brackets, or unexpected types.
2. **Query & Architecture Coverage:**
   - 113 unique benchmark query IDs (`KI_001`–`KI_030`, `TH_001`–`TH_025`, `CO_001`–`CO_020`, `MC_001`–`MC_016`, `MD_001`–`MD_011`, `AB_001`–`AB_011`).
   - Each query ID has exactly 3 trace entries corresponding to `all_cross_encoder`, `domain_routed`, and `rrf_only`.
3. **Trace Content Scope:**
   - Traces track candidate counts for all 60 pool candidates.
   - For file size optimization (~28 MB total), stage candidate lists (`dense_candidates`, `bm25_candidates`, `rrf_candidates`) record the top 10 items.
   - 100% of ground-truth target items are tracked in full detail with their exact ranks and scores across all stages.

---

## 5. Independent Metric Recalculation

All 27 ranking metrics were recalculated independently from candidate IDs in `retrieval_113_phase5_query_traces.jsonl` against benchmark ground truth:

| Metric | Architecture A (Reported / Recalculated) | Architecture B (Reported / Recalculated) | Pure RRF (Reported / Recalculated) | Delta (B vs A) | Match Status |
|---|:---:|:---:|:---:|:---:|:---:|
| Hit Rate@5 | 0.7353 / 0.7353 | 0.7353 / 0.7353 | 0.7157 / 0.7157 | +0.0000 | PASS |
| Hit Rate@10 | 0.7647 / 0.7647 | 0.7549 / 0.7549 | 0.7549 / 0.7549 | -0.0098 | PASS |
| Precision@5 | 0.3549 / 0.3549 | 0.3529 / 0.3529 | 0.3471 / 0.3471 | -0.0020 | PASS |
| Precision@10 | 0.2833 / 0.2833 | 0.2814 / 0.2814 | 0.2794 / 0.2794 | -0.0020 | PASS |
| Recall@5 | 0.4690 / 0.4690 | 0.4665 / 0.4665 | 0.4477 / 0.4477 | -0.0025 | PASS |
| Recall@10 | 0.5313 / 0.5313 | 0.5239 / 0.5239 | 0.5157 / 0.5157 | -0.0074 | PASS |
| MRR | 0.6426 / 0.6426 | 0.6287 / 0.6287 | 0.5954 / 0.5954 | -0.0139 | PASS |
| nDCG@5 | 0.6098 / 0.6098 | 0.6015 / 0.6015 | 0.5730 / 0.5730 | -0.0082 | PASS |
| nDCG@10 | 0.6229 / 0.6229 | 0.6126 / 0.6126 | 0.5876 / 0.5876 | -0.0102 | PASS |
| Duplicate Rate | 0.00% / 0.00% | 0.00% / 0.00% | 0.00% / 0.00% | 0.00% | PASS |
| Filter Violations | 0.00% / 0.00% | 0.00% / 0.00% | 0.00% / 0.00% | 0.00% | PASS |
| Absence Rejection | 100.0% / 100.0% | 100.0% / 100.0% | 100.0% / 100.0% | 0.00% | PASS |

Zero metric discrepancies were found. All metrics match to 4 decimal places.

---

## 6. Latency and Production Parity Verification

### Latency Measurement Audit
- **P50 / Median Latency:**
  - Architecture A: 893.3 ms
  - Architecture B: 246.5 ms (72.4% reduction vs. Architecture A)
  - Pure RRF: 179.8 ms
- **Timing Consistency:**
  - In 100% of traces, total query latency exceeds the sum of individual stage execution times, confirming that all pipeline overheads are accounted for.
  - In Pure RRF and single-domain anime/book traces under Architecture B, cross-encoder execution time is explicitly recorded as 0.0 ms.

### Traced vs. Untraced Parity Audit
A dedicated reproducibility script [`evaluation/verify_parity.py`](file:///c:/Coding/Project%20Black%20Knight/evaluation/verify_parity.py) was executed to test candidate IDs, ranking, and scores:
- **Scope:** Stratified sample of 20 benchmark queries (5 movies, 5 anime, 5 books, 5 mixed/absence) across all 3 architectures = **60 total comparisons**.
- **Results:** 60 passed, 0 failed.
- **Verdict:** **100% Exact Parity**. Enabling diagnostic tracing does not alter candidate selection, candidate ordering, or candidate scores.

---

## 7. Absence Query Behavior

All 11 absence queries (`AB_001`–`AB_011`) were audited:
- 4 movie absence queries (e.g. impossible release years or non-existent combinations).
- 3 anime absence queries (e.g. impossible episode/rating bounds).
- 4 book absence queries (e.g. impossible page counts or excluded genres).
- **Audit Finding:** In all 11 queries across all 3 architectures (33 runs), `valid_ids_counts` is **0**.
- **Conclusion:** Rejection occurs at the metadata filtering stage. None of the 11 benchmark absence queries reach the semantic vector space. While the 100% rejection rate is correct, it reflects catalog filtering rather than semantic rejection.

---

## 8. Summary of Validation Checks

| Check Name | Status | Expected | Actual |
|---|:---:|---|---|
| `benchmark_query_count` | PASS | 113 (102 pos, 11 abs) | 113 (102 pos, 11 abs) |
| `trace_jsonl_count_and_syntax` | PASS | 339 valid lines | 339 valid lines |
| `traces_per_architecture` | PASS | 113 per arch | 113 per arch |
| `total_target_evaluations_in_traces` | PASS | 34,509 (11,503 * 3) | 34,509 |
| `failure_analysis_row_count_reconciliation` | PASS | 33,971 (34,509 - 538) | 33,971 |
| `cross_encoder_demotion_counts` | PASS | Arch A: 56, Arch B: 18, RRF: 0 | Arch A: 56, Arch B: 18, RRF: 0 |
| `cross_encoder_demotion_reduction_pct` | PASS | 67.9% | 67.86% |
| `domain_routed_routing_contract` | PASS | Anime/Book bypassed, Movie applied | 100% contract compliant |
| `absence_query_zero_result_rate` | PASS | 0 results across 33 runs | 0 results across 33 runs |
| `absence_rejection_mechanism_isolation` | PASS | 100% filter-driven empty catalog | valid_ids=0 for 33/33 runs |
| `independent_ranking_metric_parity` | PASS | 0 mismatches across 27 metrics | 0 mismatches across 27 metrics |
| `trace_latency_internal_consistency` | PASS | total >= stage sum | 0 anomalies |
| `latency_percentile_recalculation` | PASS | Matches reported within 1ms | 0 discrepancies |
| `trace_candidate_pool_sampling` | PASS | Documented top 10 sample + 100% targets | Verified |

---

## 9. Final Recommendations for Phase 6

1. **Phase 5 Data Integrity is Confirmed:** The metrics, traces, and latency profiles are verified and safe to use as the foundation for Phase 6.
2. **Prioritize Anime and Book Retrieval Coverage:** The primary retrieval loss occurs in first-stage retrieval (`dense_and_bm25_miss`), where BM25 Okapi misses abstract queries. Improving semantic representation or hybrid weights will yield high impact.
3. **Preserve Domain Routing:** Architecture B reduces median search latency by **72.4%** (893ms $\rightarrow$ 246ms) and eliminates 38 cross-encoder demotions without harming movie precision.
