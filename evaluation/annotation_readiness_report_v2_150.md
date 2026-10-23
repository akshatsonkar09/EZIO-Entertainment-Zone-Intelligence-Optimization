# Project Black Knight — Annotation-Readiness Report: 150-Query Benchmark

**Target Benchmark File**: `evaluation/black_knight_eval_queries_v2_150.csv`  
**Date**: October 23, 2026  
**Auditor**: Autonomous AI/ML Evaluation Agent  
**Status**: `NOT_ANNOTATED` / `ANNOTATION_PENDING`  

---

## 1. Executive Summary

An audit of the intended next-generation benchmark file `evaluation/black_knight_eval_queries_v2_150.csv` was conducted under Phase 2 and Phase 5 of the Autonomous Protocol.

### Critical Finding
- **Total Rows**: Exactly **150** query rows.
- **Annotated Rows**: **0 out of 150** (0.0%).
- **Missing Ground Truth**: `relevant_ids` is `NaN` across **all 150 rows** (100.0% unannotated).
- **Label Status**: `label_status` is marked as `'todo'` across **all 150 rows** (100.0%).

### Protocol Determination
Under the Operating Rules of the Master Autonomous Protocol:
> *"Do not use it to calculate ranking metrics while its ground-truth labels are missing. Do not fabricate labels or automatically declare the retriever correct based only on its own results. Produce an annotation-readiness report identifying queries that need labels and any ambiguous cases."*

**No ranking evaluation, held-out validation, or generalization claim may be derived from `v2_150.csv` until ground-truth annotations are provided and independently verified.**

---

## 2. Dataset Schema & Column Specification

The dataset contains 17 columns defining query metadata, expected splits, and evaluation criteria:

| Column Name | Data Type | Non-Null Count | Description |
|---|---|---|---|
| `query_id` | String | 150 / 150 | Unique query identifier (e.g., `N_KI_001` to `N_AM_009`) |
| `category` | String | 150 / 150 | Category code (A through I) |
| `category_name` | String | 150 / 150 | Full category descriptor |
| `domain` | String | 150 / 150 | Primary domain (`book`, `movie`, `anime`, `multi`, `none`) |
| `expected_domains`| String | 150 / 150 | JSON list of expected domains (e.g. `["movie"]`, `["anime", "movie"]`) |
| `split` | String | 150 / 150 | Benchmark partition (`dev` = 100, `test` = 50) |
| `difficulty` | String | 150 / 150 | Difficulty tier (`easy` = 24, `medium` = 75, `hard` = 51) |
| `query_text` | String | 150 / 150 | Natural language query prompt |
| `expected_behavior`| String | 150 / 150 | Human-readable specification of expected retriever behavior |
| `primary_metric` | String | 150 / 150 | Target evaluation metric |
| `label_method` | String | 150 / 150 | Intended labeling methodology (`human_curated`, `filter_driven`, etc.) |
| `fields_used` | String | 150 / 150 | Metadata fields invoked |
| `relevant_ids` | Float / NaN | **0 / 150 (ALL NULL)** | Target catalog IDs for positive evaluation |
| `expected_parse` | String | 150 / 150 | JSON representation of expected `BlackKnightQuery` parse |
| `label_status` | String | 150 / 150 | Status flag (**all 150 rows set to `'todo'`**) |
| `legacy_overlap` | Boolean | 150 / 150 | Whether query overlaps with v1 audited queries |
| `notes` | String | 150 / 150 | Contextual notes and intent descriptions |

---

## 3. Benchmark Distribution & Composition

### 3.1 Domain Breakdown
- **Book**: 39 queries (26.0%)
- **Movie**: 38 queries (25.3%)
- **Anime**: 38 queries (25.3%)
- **Multi-Domain**: 27 queries (18.0%)
- **None (Absence/Negative)**: 8 queries (5.3%)

### 3.2 Category Distribution
- **Known-Item Exact**: 24 queries
- **Descriptive**: 24 queries
- **Constraint Only**: 24 queries
- **Multi-Domain**: 18 queries
- **Absence Robustness**: 18 queries
- **Known-Item Variant / Typo**: 15 queries
- **Vague / Mood**: 9 queries
- **Hybrid Descriptive + Constraint**: 9 queries
- **Ambiguous Title**: 9 queries

### 3.3 Split Partitioning (Dev vs. Test)
The proposed partition is cleanly divided:
- **Development Split (`dev`)**: 100 queries
  - Anime: 24 | Book: 24 | Movie: 29 | Multi: 18 | None: 5
- **Held-Out Test Split (`test`)**: 50 queries
  - Anime: 14 | Book: 15 | Movie: 9 | Multi: 9 | None: 3

---

## 4. Annotation Guidelines & Recommended Next Steps

To bring `v2_150.csv` to evaluation readiness:

1. **Pre-Filtering Script Execution**:
   - For `constraint_only` and `absence_robustness` queries, execute deterministic filter queries against `metadata_clean.csv` to generate candidate candidate ground truth sets.
2. **Catalog Verification for Known-Item Queries**:
   - For the 39 known-item queries (exact + variant), verify that the canonical entity exists in the corresponding catalog dataset before labeling.
   - Cross-reference title variants and Romaji/English aliases to ensure the expected catalog ID matches the intended work (avoiding anomalies like `KI_016` and `KI_023`).
3. **Multi-Domain Query Balancing**:
   - For multi-domain queries (`N_MD_001` to `N_MD_018`), ensure ground truth contains balanced representation from both targeted domains.
4. **Independent Human Adjudication**:
   - Have at least two annotators independently review descriptive, vague, and ambiguous queries before finalizing `relevant_ids`.
5. **Freeze & Version**:
   - Once labeled, update `label_status` to `'audited'` and freeze the dataset under a new version tag (e.g. `black_knight_eval_queries_v2_150_audited.csv`).
