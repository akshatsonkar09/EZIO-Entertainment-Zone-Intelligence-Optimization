# Project Black Knight — Scope-Corrected Retrieval Quality Report

## Executive Summary
This report presents the reproducible, scope-corrected evaluation of Project Black Knight after retaining Experiment 1 (Exact Title Promotion).
In accordance with product scope requirements, all 15 similar-to (`SI_*`) recommendation queries have been excluded from the active benchmark, yielding a focused 98-query evaluation suite (87 positive queries and 11 absence queries).

## Benchmark Scope Definition
- **Total In-Scope Queries:** 98
- **Positive Relevance Queries:** 87
- **Absence Queries:** 11
- **Excluded Queries:** 15 (`SI_001` through `SI_015`)
- **Exclusion Justification:** Queries seeking items "similar to" a named seed work represent cross-domain item-to-item recommendation rather than unified cross-domain search. These are excluded from active search optimization.

## Key Performance Metrics (Architecture B - Default Production)

| Metric | Scope-Corrected Baseline | Experiment 1 (Retained) | Absolute Delta | Relative Gain |
| :--- | :--- | :--- | :--- | :--- |
| **MRR** | **0.7170** | **0.7925** | **+0.0756** | **+10.54%** |
| **Hit@1** | 0.6437 (56/87) | 0.7471 (65/87) | +0.1034 (+9 queries) | +16.06% |
| **Hit@5** | 0.8276 (72/87) | 0.8506 (74/87) | +0.0230 (+2 queries) | +2.78% |
| **Hit@10** | 0.8506 (74/87) | 0.8621 (75/87) | +0.0115 (+1 query) | +1.35% |
| **nDCG@5** | 0.6932 | 0.7578 | +0.0646 | +9.32% |
| **nDCG@10** | 0.7062 | 0.7637 | +0.0576 | +8.16% |

## Architectural Comparison Across In-Scope Queries

| Configuration | Baseline MRR | Exp 1 MRR | Baseline Hit@1 | Exp 1 Hit@1 | Baseline nDCG@10 | Exp 1 nDCG@10 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Architecture B (Routed, Default)** | 0.7170 | **0.7925** | 0.6437 | **0.7471** | 0.7062 | **0.7637** |
| **Architecture A (All Cross-Encoder)** | 0.7334 | **0.8036** | 0.6667 | **0.7701** | 0.7172 | **0.7671** |
| **Architecture C (RRF Only)** | 0.6779 | **0.7688** | 0.5862 | **0.7241** | 0.6768 | **0.7456** |

## Performance by In-Scope Query Category (Architecture B)

| Category | N | Baseline MRR | Exp 1 MRR | Delta MRR | Baseline Hit@1 | Exp 1 Hit@1 | Hit@10 | nDCG@10 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Known-Item (`KI_*`)** | 30 | 0.7142 | **0.9333** | **+0.2191** | 0.6333 (19/30) | **0.9333 (28/30)** | 0.9333 | 0.9333 |
| **Constraint (`CQ_*`)** | 23 | 1.0000 | **1.0000** | +0.0000 | 1.0000 (23/23) | **1.0000 (23/23)** | 1.0000 | 0.9889 |
| **Descriptive (`DQ_*`)** | 23 | 0.7080 | **0.7080** | +0.0000 | 0.5652 (13/23) | **0.5652 (13/23)** | 0.9130 | 0.6451 |
| **Multi-Domain (`MD_*`)** | 11 | 0.1515 | **0.1515** | +0.0000 | 0.0909 (1/11) | **0.0909 (1/11)** | 0.2727 | 0.0784 |

## Performance by Domain (Architecture B)

| Domain | N | Baseline MRR | Exp 1 MRR | Delta MRR | Baseline Hit@10 | Exp 1 Hit@10 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Movie** | 29 | 0.8563 | **0.9023** | +0.0460 | 0.9655 | 0.9655 |
| **Anime** | 30 | 0.5820 | **0.7400** | **+0.1580** | 0.7667 | **0.8000** |
| **Book** | 28 | 0.7173 | **0.7351** | +0.0179 | 0.8214 | 0.8214 |

## Correctness & Integrity Verification
- **Hard-Filter Violations:** 0 (100% compliance across all 23 constraint queries)
- **Absence-Query False Acceptances:** 0 (0 out of 11 absence queries returned false positive results)
- **Duplicate Results:** 0 across all queries and candidate lists
- **Full Test Suite:** 122 / 122 tests passing with zero failures.
