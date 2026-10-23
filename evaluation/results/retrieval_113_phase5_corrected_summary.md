# Project Black Knight — Phase 5 Corrected Summary & Verified Findings

## 1. Executive Summary & Audit Reconciliations

This document provides a verified, corrected reference summary of Project Black Knight's **Phase 5 Retrieval-Stage Observability and Diagnostics** evaluation. All metrics, counts, and survival figures below have been independently recomputed from the underlying trace and benchmark datasets.

### Corrected Denominators & Dataset Sizing

| Concept | Verified Count | Definition & Denominator Context |
|---|---:|---|
| **Benchmark Queries Total** | **113** | Evaluated benchmark cases (`black_knight_eval_queries_113_audited.csv`). |
| **Positive Queries** | **102** | Queries with at least one ground-truth target item (`len(relevant_ids) > 0`). |
| **Absence Queries** | **11** | Queries expecting zero results (`len(relevant_ids) == 0`). |
| **Unique Target Item IDs** | **10,211** | Distinct catalog IDs across all benchmark positive queries. |
| **Query-Target Pairs (Single Run)** | **11,503** | Total instances of (query, target) evaluated per architecture. |
| **Total Target Evaluations (3 Architectures)** | **34,509** | $11,503 \times 3$ architectures evaluated across the entire benchmark run. |
| **Total Top-5 Successes** | **538** | Targets achieving rank 1–5 (181 in Arch A, 180 in Arch B, 177 in Pure RRF). |
| **Total Non-Success Targets (`failure_analysis.csv`)** | **33,971** | All targets falling outside top 5 ($34,509 - 538 = \mathbf{33,971}$ rows). |
| **Query Traces (`traces.jsonl`)** | **339** | Exactly $113 \text{ queries} \times 3 \text{ architectures}$ full execution traces. |

*Reconciliation Note:* The 33,971 count in `failure_analysis.csv` is the 3-architecture failure count, while 11,503 is the per-architecture query-target denominator. The line 47 label in the initial Phase 5 report (`Total positive targets: 102`) was a typographical label error referring to the 102 positive queries.

---

## 2. Verified Ranking Performance (Positive Queries, N=102)

All values below were independently recomputed from `retrieval_113_phase5_query_traces.jsonl` candidate IDs against ground truth:

| Metric | Architecture A (All CE) | Architecture B (Domain-Routed) | Pure RRF | Delta (B vs A) |
|---|---:|---:|---:|---:|
| **Hit Rate@5** | 0.7353 | 0.7353 | 0.7157 | +0.0000 |
| **Hit Rate@10** | 0.7647 | 0.7549 | 0.7549 | -0.0098 |
| **Precision@5** | 0.3549 | 0.3529 | 0.3471 | -0.0020 |
| **Precision@10** | 0.2833 | 0.2814 | 0.2794 | -0.0020 |
| **Recall@5** | 0.4690 | 0.4665 | 0.4477 | -0.0025 |
| **Recall@10** | 0.5313 | 0.5239 | 0.5157 | -0.0074 |
| **MRR** | 0.6426 | 0.6287 | 0.5954 | -0.0139 |
| **nDCG@5** | 0.6098 | 0.6015 | 0.5730 | -0.0082 |
| **nDCG@10** | 0.6229 | 0.6126 | 0.5876 | -0.0102 |
| **Duplicate-Result Rate** | **0.00%** | **0.00%** | **0.00%** | 0.00% |
| **Hard-Filter Violation Rate** | **0.00%** | **0.00%** | **0.00%** | 0.00% |
| **Absence Correct Rejection Rate** | **100.0%** | **100.0%** | **100.0%** | 0.00% |

---

## 3. Verified Latency Profile (Milliseconds)

Computed directly from `total_latency_ms` observations in `retrieval_113_phase5_query_traces.jsonl`:

| Architecture | Median / P50 (ms) | Mean (ms) | P95 (ms) | Steady-State Mean (ms) |
|---|---:|---:|---:|---:|
| **Architecture A (All CE)** | 893.3 | 1161.0 | 3230.0 | 1165.6 |
| **Architecture B (Domain-Routed)** | **246.5** | **597.4** | **2568.8** | **601.3** |
| **Pure RRF Baseline** | 179.8 | 217.0 | 703.2 | 218.0 |
| **Delta (Architecture B vs A)** | **-646.8 ms (-72.4%)** | **-563.6 ms (-48.5%)** | **-661.2 ms** | **-564.3 ms** |

---

## 4. Corrected Stage-Wise Target Survival Summary

Corrected table using the true per-architecture denominator of **11,503 query-target instances** (across the 102 positive queries):

| Stage | Architecture A (Survived / Rate) | Architecture B (Survived / Rate) | Pure RRF (Survived / Rate) | Mean Latency (ms) |
|---|---:|---:|---:|---:|
| **Metadata Filtering** | 9,845 (85.6%) | 9,845 (85.6%) | 9,845 (85.6%) | 93–101 ms |
| **Dense Retrieval** | 745 (6.5%) | 745 (6.5%) | 745 (6.5%) | 45–52 ms |
| **BM25 Retrieval** | 1,063 (9.2%) | 1,063 (9.2%) | 1,063 (9.2%) | 63–65 ms |
| **First-Stage Union** | 1,460 (12.7%) | 1,460 (12.7%) | 1,460 (12.7%) | 109–116 ms |
| **RRF Fusion ($k=60$)** | 1,071 (9.3%) | 1,071 (9.3%) | 1,071 (9.3%) | 0.07 ms |
| **Cross-Encoder Rerank** | 289 (2.5%) | 849 (7.4%) | 1,071 (9.3%) | 940 ms (A) / 372 ms (B) / 0 ms (RRF) |
| **Final Top 10** | 289 (2.5%) | 287 (2.5%) | 285 (2.5%) | 1161 ms (A) / 597 ms (B) / 217 ms (RRF) |
| **Final Top 5** | 181 (1.6%) | 180 (1.6%) | 177 (1.5%) | — |

---

## 5. Granular Cross-Encoder Demotion Breakdown

Cross-encoder demotions (targets with $rrf\_rank \le 10$ demoted out of top 10 by reranking) broken down by domain:

| Domain | Architecture A (All CE) | Architecture B (Domain-Routed) | Pure RRF | Demotions Avoided by Domain Routing |
|---|---:|---:|---:|---:|
| **Movie** | 18 | 18 | 0 | 0 (CE intentionally retained) |
| **Anime** | 27 | **0** | 0 | **27 (100% eliminated)** |
| **Book** | 11 | **0** | 0 | **11 (100% eliminated)** |
| **Total** | **56** | **18** | **0** | **38 (67.9% overall reduction)** |

---

## 6. Absence Query Evaluation

All 11 absence queries (`AB_001`–`AB_011`) were audited across all 3 architectures (33 runs):
- Every single run returned **0 results** (100% correct rejection rate).
- In 100% of cases, rejection occurred at **metadata filtering** (`valid_ids_count = 0`).
- *Important Qualification:* The benchmark tests catalog-constrained absence rather than vector semantic rejection. None of the absence queries reach candidate generation.

---

## 7. Verified Parity Status

- Executed `evaluation/verify_parity.py` comparing `search_black_knight(..., trace=False)` against `search_black_knight(..., trace=True)` across 20 stratified benchmark queries and 3 architectures (60 comparisons).
- **Result:** **60 / 60 passed (100% exact parity)** on item IDs, scores, and ordering.
- **Verdict:** Diagnostic instrumentation has zero impact on retrieval behavior.
