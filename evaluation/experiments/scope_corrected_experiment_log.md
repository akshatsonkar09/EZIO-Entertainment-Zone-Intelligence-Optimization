# Scope-Corrected Autonomous Experiment Log

## Project Information
- **Project:** Project Black Knight
- **Phase:** Autonomous Scope-Corrected Audit & Search Quality Optimization
- **Date:** October 23, 2026
- **Operating Rule:** Filesystem checkpoints only (Strictly NO Git / GitHub).
- **In-Scope Boundary:** Unified cross-domain search across movies, anime, and books without explicit domain requirements. Similar-to queries (`SI_*`) explicitly excluded from active optimization objectives.

---

## Pre-Audit Baseline Verification Checkpoint

- **Checkpoint ID:** `pre_scope_corrected_audit_20261023_080500`
- **External Path:** `C:\AI_ML\Project\Project_Black_Knight_Backups\pre_scope_corrected_audit_20261023_080500\`
- **Local Path:** `backups\pre_scope_corrected_audit_20261023_080500\`
- **Total Tracked Files:** 281
- **Total Size:** 1,185.44 MB (1,243,037,422 bytes)
- **Manifest:** Verified SHA-256 hash manifest present in both directories.
- **Verification Status:** 100% matched, zero discrepancies.

---

## Scope Definition & Reconciled Query Counts

- **Total Canonical Benchmark Queries:** 113 (`black_knight_eval_queries_113_audited.csv`)
- **Excluded Queries:** 15 (`SI_001` through `SI_015`)
- **Exclusion Rationale:** All `SI_*` queries represent item-to-item similarity recommendation ("like X", "similar to Y"). Under the product requirements, search is defined as discovery and retrieval across domains. Recommendation features and seed exclusions are out of scope.
- **In-Scope Total Queries:** 98
- **In-Scope Positive Queries:** 87
- **In-Scope Absence/Negative Queries:** 11
- **Unscored / Ignored Queries:** 0

---

## Experiment 1 (Exact Title Promotion) — Independent Scope-Corrected Re-Evaluation

### Hypothesis
Pre-normalizing titles in memory and prioritizing exact case-insensitive matches ahead of dense+BM25 and cross-encoder reranking eliminates false negatives on known-item queries caused by neural score dilution or BM25 vocabulary variations.

### Code Modifications
- File: `src/project_black_knight/retrieval.py`
  - Added pre-normalized title cache (`_title_normalized_to_item_id`) per domain in `RetrievalRepository`.
  - Added exact title promotion hook in `hybrid_retrieve` that injects exact-match items directly at rank 1 with score 1.0, preserving all hard metadata filters.
  - Added regression test `tests/test_text_normalizer.py`.

### Evaluation Results on In-Scope Queries (N=87 Positive, Architecture B)

| Metric | Scope-Corrected Baseline | Experiment 1 (Retained) | Absolute Delta | Relative Change |
| :--- | :--- | :--- | :--- | :--- |
| **MRR** | **0.7170** | **0.7925** | **+0.0756** | **+10.54%** |
| **Hit@1** | 0.6437 (56/87) | 0.7471 (65/87) | +0.1034 (+9 queries) | +16.06% |
| **Hit@5** | 0.8276 (72/87) | 0.8506 (74/87) | +0.0230 (+2 queries) | +2.78% |
| **Hit@10** | 0.8506 (74/87) | 0.8621 (75/87) | +0.0115 (+1 query) | +1.35% |
| **nDCG@5** | 0.6932 | 0.7578 | +0.0646 | +9.32% |
| **nDCG@10** | 0.7062 | 0.7637 | +0.0576 | +8.16% |

### Statistical Significance (N=87 In-Scope Positive Queries)
- **Wins / Losses / Ties:** 9 wins, 0 losses, 78 ties.
- **Paired Student's t-test:** $t = 3.0920, p = 0.002680$ (Significant at $p < 0.01$).
- **Paired Wilcoxon signed-rank test:** $W = 0.0, p = 0.007161$ (Significant at $p < 0.01$).
- **Bootstrap 95% Confidence Interval (10,000 resamples):** `[+0.0322, +0.1259]`, strictly positive.

### Regression & Integrity Tests
- **Full Test Suite:** 122 passed, 0 failed in 97.70s.
- **Hard-Filter Violations:** 0 / 23 constraint queries.
- **Absence False Acceptances:** 0 / 11 negative queries.
- **Duplicates:** 0.
- **Latency Impact:** Negligible (< 1 ms overhead from dict lookup).

### Decision
**RETAIN**. Statistically verified, zero regressions, full test suite passing.

---

## Evaluation of Potential Next Improvements

### Investigation 1: Candidate Depth Expansion (`candidate_k` 60 -> 80/100)
- **Findings:** Prior autonomous experiments demonstrated no gain in Hit@10 or MRR, with slight degradation in Hit@5 at 100, and a 20-30% latency increase.
- **Decision:** REJECT without code modifications.

### Investigation 2: Multi-Domain Query Tuning
- **Findings:** `search_black_knight` properly routes multi-domain queries across detected domains, performs cross-encoder reranking across all domains to align score distributions, and sorts/deduplicates. Low benchmark scores on `MD_*` queries stem from benchmark label corruption (`MD_005` labeling Inception for Hayao Miyazaki) and sparse subjective ground-truth labels.
- **Decision:** No code change justified. Retaining existing architecture preserves stability and correctness.

---

## Final Retained State
- Current retained implementation in `src/project_black_knight/retrieval.py` represents the highest-quality, fully verified search pipeline.
