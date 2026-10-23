# Project Black Knight — Final Architecture Evaluation Report

**Evaluation Date:** October 2026  
**Evaluator:** Project Black Knight Independent Automated Evaluation  
**Subject:** Comparative Evaluation of Architecture A (`all_cross_encoder`) vs Architecture B (`domain_routed`)  
**Target Path:** `evaluation/results/retrieval_113_final_architecture_evaluation_report.md`  

---

## 1. Test Scope and Objective

This evaluation provides a comprehensive, empirical, and reproducible comparison of the two primary candidate retrieval architectures for Project Black Knight:

- **Architecture A (`all_cross_encoder`):** Evaluates dense and lexical candidates using Reciprocal Rank Fusion (RRF, $k=60$), followed unconditionally by cross-encoder neural reranking (`cross-encoder/ms-marco-MiniLM-L-6-v2`) across all query domains.
- **Architecture B (`domain_routed`):** Dynamically routes queries based on domain classification:
  - Single-domain **Movie** queries $\rightarrow$ RRF fusion + Cross-Encoder reranking.
  - Single-domain **Anime** queries $\rightarrow$ RRF-only consensus ranking (cross-encoder bypassed).
  - Single-domain **Book** queries $\rightarrow$ RRF-only consensus ranking (cross-encoder bypassed).
  - **Mixed-domain** queries $\rightarrow$ RRF fusion + Cross-Encoder reranking.

### Strict Governance and Boundaries
In strict adherence to evaluation guidelines:
1. **Testing and Reporting Only:** This report presents measured metrics, operational data, failure categorizations, and observed trade-offs. No architecture is declared a "winner", no recommendation is made, and no decision on readiness for Phase 6 is asserted.
2. **Tolerance Rules Withheld:** The user's 3.5-percentage-point decision heuristic is not applied as an automatic selection mechanism.
3. **Immutability of Production Systems:** No production ranking parameters, weights, candidate pool sizes ($k=60$), routing definitions, catalog datasets, or benchmark queries were modified during this evaluation.
4. **Historical Artifact Integrity:** All Phase 5 audit records and diagnostic baselines remain untouched.

---

## 2. Environment, Configuration, and Execution Details

### 2.1 Execution Environment
- **Host OS:** Windows 11
- **Runtime Shell:** PowerShell
- **Python Environment:** Virtual environment located at `.\project_black_knight\Scripts\python.exe`
- **Working Directory:** `c:\Coding\Project Black Knight`
- **Execution Timestamp:** 2026-10-22

### 2.2 Production Retrieval Pipeline Configuration
- **Candidate Pool Depth:** `candidate_k = 60` candidates per retriever per domain.
- **Dense Retriever:** SentenceTransformers `all-MiniLM-L6-v2`, cosine distance search.
- **Lexical Retriever:** BM25 (`rank-bm25`), tokenized lowercase lexical matching.
- **First-Stage Fusion:** Reciprocal Rank Fusion (RRF) with constant $k = 60$:
  $$S_{RRF}(d) = \sum_{m \in \{dense, bm25\}} \frac{1}{60 + \text{rank}_m(d)}$$
- **Neural Reranker:** Cross-Encoder `cross-encoder/ms-marco-MiniLM-L-6-v2`.
- **Reranking Blend Formula (when Cross-Encoder is active):**
  $$S_{final}(d) = 0.45 \cdot S_{RRF}(d) + 0.55 \cdot S_{CE}(d)$$
  Where $S_{CE}(d)$ is normalized via min-max scaling over the candidate pool.
- **RRF-Only Formula (when Cross-Encoder is bypassed):**
  $$S_{final}(d) = S_{RRF}(d)$$
- **Multi-Domain Interleaving:** Round-robin interleaving sorted by domain score with duplicate suppression.

### 2.3 Evaluation Metric Definitions
For each query $q$ with relevant ground-truth set $R_q$ ($|R_q| > 0$) and ranked results $\hat{D}_q = [d_1, d_2, \dots]$:
- **Hit Rate@K:** $\mathbb{I}\left(\sum_{i=1}^K \mathbb{I}(d_i \in R_q) \ge 1\right)$
- **Precision@K:** $\frac{1}{K} \sum_{i=1}^K \mathbb{I}(d_i \in R_q)$
- **Recall@K:** $\frac{1}{|R_q|} \sum_{i=1}^{\min(K, |\hat{D}_q|)} \mathbb{I}(d_i \in R_q)$
- **MRR (Mean Reciprocal Rank):** $\frac{1}{\min \{i \le 10 \mid d_i \in R_q\}}$ (0 if no relevant target in top 10).
- **nDCG@K:** $\frac{\text{DCG@K}}{\text{IDCG@K}}$, where $\text{DCG@K} = \sum_{i=1}^K \frac{2^{\mathbb{I}(d_i \in R_q)} - 1}{\log_2(i + 1)}$, and $\text{IDCG@K}$ is the ideal DCG for binary relevance.
- **Metric Difference:** Expressed strictly as $\Delta = B - A$. Rate-based metrics report difference in percentage points ($\text{pp} = 100 \cdot (B - A)$).

---

## 3. Preflight and Parity-Check Results

Before running the comparative evaluation, preflight integrity and parity checks were performed against the production system.

### 3.1 Preflight Verification Summary
| Verification Step | Target / Specification | Observed Result | Status |
| :--- | :--- | :--- | :--- |
| **Git Working Tree** | Clean working state | Clean working directory | **PASS** |
| **Benchmark Query Count** | 113 total queries | 113 queries in audited benchmark | **PASS** |
| **Active Catalogs** | Movies, Anime, Books | Movies, Anime, Books loaded | **PASS** |
| **Excluded Catalogs** | Music catalog disabled | Music catalog confirmed excluded | **PASS** |
| **Historical Phase 5 Artifacts** | Unmodified | Intact in `evaluation/results/` | **PASS** |
| **Trace Parity Status** | Exact candidate & score parity | Confirmed via `verify_parity.py` | **PASS** |

### 3.2 Production Search Parity Execution
The formal parity check was executed using the production test suite:
- **Command:** `.\project_black_knight\Scripts\python.exe evaluation/verify_parity.py`
- **Exit Code:** `0`
- **Execution Summary:**
  - 20 benchmark queries sampled across all domains (Movie, Anime, Book, Mixed-domain, Absence).
  - 3 architectures validated (`all_cross_encoder`, `domain_routed`, `rrf_only`).
  - Total checks executed: **60 / 60 passed (100.0% parity)**.
  - Zero discrepancies detected in candidate IDs, candidate ordering, or candidate scores between untraced production `search_black_knight` and instrumented `search_with_diagnostics`.

---

## 4. Benchmark Composition and Domain Counts

The audited benchmark (`evaluation/black_knight_eval_queries_113_audited.csv`) comprises 113 queries. Queries are categorized into mutually exclusive domain partitions:

| Domain Partition | Query Count ($N$) | Ground-Truth Targets | Query Types Represented |
| :--- | :---: | :---: | :--- |
| **Movie-Only** | 31 | 1,422 | Known-item (KI), Description (DE), Similar-item (SI) |
| **Anime-Only** | 31 | 7,207 | Known-item (KI), Description (DE), Similar-item (SI) |
| **Book-Only** | 29 | 2,827 | Known-item (KI), Description (DE), Similar-item (SI) |
| **Mixed-Domain** | 11 | 47 | Multi-domain explicit (MD) |
| **Subtotal Positive Queries** | **102** | **11,503** | **All positive queries with ground-truth targets** |
| **Absence Queries** | 11 | 0 | Unmatchable / contradictory constraints (AB) |
| **Total Benchmark** | **113** | **11,503** | **Full audited benchmark suite** |

Reconciliation check:
- Group queries: $31 + 31 + 29 + 11 = 102$ positive queries $+ 11$ absence queries $= 113$ total queries.
- Target reconciliation: $1,422 + 7,207 + 2,827 + 47 = 11,503$ targets.
- Zero double counting: Mixed-domain queries are isolated into their own evaluation group and are not included in single-domain groups.

---

## 5. Overall Ranking Metrics (Positive Queries, N=102)

Performance across all 102 positive queries ($11,503$ total ground-truth targets):

| Metric | Architecture A (`all_ce`) | Architecture B (`routed`) | Absolute Difference ($B - A$) | Percentage Point Diff (pp) | Direction / Magnitude |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Hit Rate@5** | **0.7353** | **0.7353** | **+0.0000** | **+0.00 pp** | Neutral (identical 75/102 hits) |
| **Hit Rate@10** | **0.7647** | **0.7549** | **-0.0098** | **-0.98 pp** | Arch A higher (78 vs 77 hits) |
| **Precision@5** | 0.3549 | 0.3529 | -0.0020 | - | Arch A higher (-0.0020) |
| **Precision@10**| 0.2833 | 0.2814 | -0.0020 | - | Arch A higher (-0.0020) |
| **Recall@5** | 0.4690 | 0.4665 | -0.0025 | - | Arch A higher (-0.0025) |
| **Recall@10** | 0.5313 | 0.5239 | -0.0074 | - | Arch A higher (-0.0074) |
| **MRR** | 0.6426 | 0.6287 | -0.0139 | - | Arch A higher (-0.0139) |
| **nDCG@5** | 0.6098 | 0.6015 | -0.0082 | - | Arch A higher (-0.0082) |
| **nDCG@10** | 0.6229 | 0.6126 | -0.0102 | - | Arch A higher (-0.0102) |

---

## 6. Ranking Metrics by Query Domain Group

### 6.1 Movie-Only Queries ($N=31$, 1,422 Targets)
In Architecture B, movie queries are explicitly routed to the cross-encoder, identical to Architecture A.

| Metric | Architecture A | Architecture B | Absolute Diff ($B - A$) | Percentage Point Diff |
| :--- | :---: | :---: | :---: | :---: |
| **Hit Rate@5** | 0.8710 | 0.8710 | 0.0000 | 0.00 pp |
| **Hit Rate@10** | 0.8710 | 0.8710 | 0.0000 | 0.00 pp |
| **Precision@5** | 0.4000 | 0.4000 | 0.0000 | - |
| **Precision@10**| 0.3032 | 0.3032 | 0.0000 | - |
| **Recall@5** | 0.6296 | 0.6296 | 0.0000 | - |
| **Recall@10** | 0.6799 | 0.6799 | 0.0000 | - |
| **MRR** | 0.7957 | 0.7957 | 0.0000 | - |
| **nDCG@5** | 0.7731 | 0.7731 | 0.0000 | - |
| **nDCG@10** | 0.7763 | 0.7763 | 0.0000 | - |

*Observation:* Movie rankings are 100% mathematically identical between Architecture A and Architecture B.

### 6.2 Anime-Only Queries ($N=31$, 7,207 Targets)
In Architecture B, anime queries bypass the cross-encoder and use RRF consensus ranking.

| Metric | Architecture A | Architecture B | Absolute Diff ($B - A$) | Percentage Point Diff |
| :--- | :---: | :---: | :---: | :---: |
| **Hit Rate@5** | **0.7097** | **0.7419** | **+0.0323** | **+3.23 pp** |
| **Hit Rate@10** | 0.7742 | 0.7742 | 0.0000 | 0.00 pp |
| **Precision@5** | 0.4000 | 0.4000 | 0.0000 | - |
| **Precision@10**| 0.3452 | 0.3419 | -0.0032 | - |
| **Recall@5** | 0.3491 | 0.3491 | 0.0000 | - |
| **Recall@10** | 0.4374 | 0.4213 | -0.0161 | - |
| **MRR** | 0.5826 | 0.5793 | -0.0032 | - |
| **nDCG@5** | 0.5453 | 0.5404 | -0.0049 | - |
| **nDCG@10** | 0.5780 | 0.5665 | -0.0115 | - |

*Observation:* In Architecture B, Hit Rate@5 is **+3.23 percentage points higher** (23/31 vs 22/31). The specific query gaining top-5 hit is `KI_014` ("Find the anime One Punch Man."), where cross-encoder reranking in Architecture A demoted the title to rank 7, while Architecture B's RRF consensus ranked it at rank 1. Hit Rate@10 remains identical at 77.42% (24/31).

### 6.3 Book-Only Queries ($N=29$, 2,827 Targets)
In Architecture B, book queries bypass the cross-encoder and use RRF consensus ranking.

| Metric | Architecture A | Architecture B | Absolute Diff ($B - A$) | Percentage Point Diff |
| :--- | :---: | :---: | :---: | :---: |
| **Hit Rate@5** | **0.8276** | **0.7931** | **-0.0345** | **-3.45 pp** |
| **Hit Rate@10** | **0.8276** | **0.7931** | **-0.0345** | **-3.45 pp** |
| **Precision@5** | 0.3793 | 0.3724 | -0.0069 | - |
| **Precision@10**| 0.2897 | 0.2862 | -0.0034 | - |
| **Recall@5** | 0.5861 | 0.5775 | -0.0086 | - |
| **Recall@10** | 0.6426 | 0.6340 | -0.0086 | - |
| **MRR** | 0.7293 | 0.6839 | -0.0454 | - |
| **nDCG@5** | 0.7134 | 0.6897 | -0.0237 | - |
| **nDCG@10** | 0.7134 | 0.6897 | -0.0237 | - |

*Observation:* In Architecture B, Hit Rate@5 and Hit Rate@10 are **-3.45 percentage points lower** (23/29 vs 24/29). Exactly one query accounts for this difference: `SI_014` ("Recommend books similar to The Final Empire."). Target `book_1083` is ranked #5 in Architecture A (cross-encoder promoted it from #12 to #5), but remains at rank #12 in Architecture B's RRF consensus ranking.

### 6.4 Mixed-Domain Queries ($N=11$, 47 Targets)
In Architecture B, mixed-domain queries are explicitly routed to the cross-encoder, identical to Architecture A.

| Metric | Architecture A | Architecture B | Absolute Diff ($B - A$) | Percentage Point Diff |
| :--- | :---: | :---: | :---: | :---: |
| **Hit Rate@5** | 0.1818 | 0.1818 | 0.0000 | 0.00 pp |
| **Hit Rate@10** | 0.2727 | 0.2727 | 0.0000 | 0.00 pp |
| **Precision@5** | 0.0364 | 0.0364 | 0.0000 | - |
| **Precision@10**| 0.0364 | 0.0364 | 0.0000 | - |
| **Recall@5** | 0.0455 | 0.0455 | 0.0000 | - |
| **Recall@10** | 0.0833 | 0.0833 | 0.0000 | - |
| **MRR** | 0.1515 | 0.1515 | 0.0000 | - |
| **nDCG@5** | 0.0579 | 0.0579 | 0.0000 | - |
| **nDCG@10** | 0.0784 | 0.0784 | 0.0000 | - |

*Observation:* Mixed-domain rankings are 100% mathematically identical between Architecture A and Architecture B.

---

## 7. Overall and Domain-Specific Latency Comparisons

Latency was captured across all retrieval and ranking stages for every query trace.

| Domain Group | Arch | P50 (ms) | Mean (ms) | P95 (ms) | P50 Diff ($B - A$) | P50 Rel Change |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Overall (All 113)** | **A** | 972.9 | 1,274.5 | 3,327.6 | **-686.4 ms** | **-70.6%** |
| | **B** | **286.5** | **650.2** | **2,596.5** | | |
| **Movie-Only ($N=31$)** | A | 822.7 | 692.5 | 1,587.8 | +6.1 ms | +0.7% |
| | B | 828.8 | 671.7 | 1,566.9 | | |
| **Anime-Only ($N=31$)** | A | 1,071.9 | 1,328.0 | 3,384.1 | **-786.4 ms** | **-73.4%** |
| | B | **285.5** | **321.0** | **789.6** | | |
| **Book-Only ($N=29$)** | A | 1,798.6 | 1,388.2 | 3,374.5 | **-1,575.2 ms** | **-87.6%** |
| | B | **223.4** | **294.5** | **783.5** | | |
| **Mixed-Domain ($N=11$)** | A | 2,612.8 | 2,463.8 | 3,081.4 | -13.8 ms | -0.5% |
| | B | 2,599.0 | 2,455.5 | 3,085.4 | | |
| **Absence ($N=11$)** | A | 20.3 | 24.3 | 43.1 | -0.1 ms | -0.5% |
| | B | 20.2 | 24.1 | 42.9 | | |

### Timing Context and Notes
- **Boundaries:** Timing represents total query processing duration, from query receipt through metadata filtering, candidate generation, RRF fusion, cross-encoder scoring (where invoked), and final formatting.
- **Cold-Start Elimination:** Models and catalogs were initialized in memory before evaluation iterations commenced.
- **Root Cause of Divergence:** Architecture B achieves an overall **70.6% reduction in median latency** primarily by bypassing neural cross-encoder inference for the 31 anime queries (-73.4%) and 29 book queries (-87.6%). Movie and mixed-domain latencies remain comparable as both architectures execute the full cross-encoder model.

---

## 8. Correctness, Duplicate, Filter, Empty-Result, and Error Statistics

Operational integrity was tracked for all 113 benchmark queries:

| Metric | Architecture A | Architecture B | Delta | Operational Status |
| :--- | :---: | :---: | :---: | :--- |
| **Total Queries Evaluated** | 113 | 113 | 0 | 100% coverage |
| **Successful Executions** | 113 | 113 | 0 | 100% success rate |
| **Uncaught Exceptions / Errors** | 0 | 0 | 0 | 0.00% error rate |
| **Empty Results (Positive Queries)** | 0 / 102 | 0 / 102 | 0 | 0.00% empty rate |
| **Duplicate Result Rate** | 0.00% (0 / 1,130) | 0.00% (0 / 1,130) | 0 | Verified duplicate-free |
| **Hard-Filter Violation Rate** | 0.00% (0 / 1,130) | 0.00% (0 / 1,130) | 0 | 100% filter compliance |

Both architectures exhibit zero runtime errors, zero empty results on valid queries, zero candidate duplicates, and zero metadata filter violations.

---

## 9. Failure-Category Analysis

Target-level failure attribution maps where relevant ground-truth targets ($N=11,503$) were lost during pipeline progression:

| Failure Category | Architecture A Count | Architecture B Count | Difference ($B - A$) | Stage Description |
| :--- | :---: | :---: | :---: | :--- |
| `dense_and_bm25_miss` | 8,370 | 8,370 | 0 | Target absent from top-60 dense and BM25 pools |
| `metadata_filter_rejection` | 1,658 | 1,658 | 0 | Target excluded by valid query metadata constraints |
| `rank_cutoff_top10` | 726 | 766 | +40 | Target ranked between position 11 and 60 |
| `rrf_fusion_drop` | 389 | 389 | 0 | Target retrieved but dropped during RRF pool fusion |
| `rank_cutoff_top5` | 108 | 107 | -1 | Target ranked between position 6 and 10 |
| `cross_encoder_demotion` | **56** | **18** | **-38** | Target in top-10 RRF, pushed out by cross-encoder |
| `seed_self_exclusion` | 15 | 15 | 0 | Seed entity correctly excluded from recommendations |

### Breakdown of Cross-Encoder Demotions by Domain
The cross-encoder demotion category records relevant items that achieved a top-10 rank under RRF consensus, but were subsequently pushed beyond rank 10 when cross-encoder blending was applied:

| Target Domain | Architecture A | Architecture B | Difference ($B - A$) |
| :--- | :---: | :---: | :---: |
| **Movie** | 18 | 18 | 0 |
| **Anime** | 27 | 0 | **-27 (-100.0%)** |
| **Book** | 11 | 0 | **-11 (-100.0%)** |
| **Total Demotions** | **56** | **18** | **-38 (-67.9%)** |

*Analysis:* Bypassing the cross-encoder in Architecture B eliminates 100% of the 27 anime demotions and 11 book demotions observed in Architecture A.

---

## 10. Absence-Query Evaluation (N=11)

All 11 absence queries (`AB_001` through `AB_011`) were designed to evaluate rejection accuracy under impossible or contradictory constraints.

| Query ID | Domain | Query Text | Arch A Results | Arch B Results | Rejection Stage | Correct Rejection |
| :--- | :--- | :--- | :---: | :---: | :--- | :---: |
| `AB_001` | movie | Sci-fi movie directed by Christopher Nolan before 1990 | 0 | 0 | Metadata Filter (`valid_ids = 0`) | Yes (100%) |
| `AB_002` | movie | Animation movie with runtime over 240 minutes | 0 | 0 | Metadata Filter (`valid_ids = 0`) | Yes (100%) |
| `AB_003` | movie | Horror comedy directed by Quentin Tarantino | 0 | 0 | Metadata Filter (`valid_ids = 0`) | Yes (100%) |
| `AB_004` | movie | Action movie released in 1850 | 0 | 0 | Metadata Filter (`valid_ids = 0`) | Yes (100%) |
| `AB_005` | anime | Mecha anime produced by Studio Ghibli | 0 | 0 | Metadata Filter (`valid_ids = 0`) | Yes (100%) |
| `AB_006` | anime | Anime series with exactly 10,000 episodes | 0 | 0 | Metadata Filter (`valid_ids = 0`) | Yes (100%) |
| `AB_007` | anime | Sports anime rated PG released in 1960 | 0 | 0 | Metadata Filter (`valid_ids = 0`) | Yes (100%) |
| `AB_008` | book | Cyberpunk novel published in 1750 | 0 | 0 | Metadata Filter (`valid_ids = 0`) | Yes (100%) |
| `AB_009` | book | Book written by William Shakespeare in 2020 | 0 | 0 | Metadata Filter (`valid_ids = 0`) | Yes (100%) |
| `AB_010` | book | Non-fiction biology textbook by Stephen King | 0 | 0 | Metadata Filter (`valid_ids = 0`) | Yes (100%) |
| `AB_011` | book | Romance fantasy book with 50,000 pages | 0 | 0 | Metadata Filter (`valid_ids = 0`) | Yes (100%) |

*Findings:*
- False Acceptance Rate: **0.00%** (0 false acceptances across both architectures).
- Correct Rejection Rate: **100.0%** (11/11).
- Stage of Rejection: All 11 queries were rejected at the **Metadata Filtering** stage (`valid_ids_count = 0`), preventing downstream candidate generation.

---

## 11. Reproducibility Checks and Statistical Reconciliation

### 11.1 Paired Statistical Analysis ($N=102$ Positive Queries)
To determine whether observed metric differences between Architecture B and Architecture A are statistically significant or attributable to sampling variance:

| Metric | Mean Paired Diff ($B - A$) | 95% Confidence Interval | Paired $t$-statistic | $p$-value | Statistically Significant ($\alpha=0.05$)? |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Hit Rate@5** | +0.0000 | [-0.0273, +0.0273] | 0.000 | 1.0000 | No |
| **Hit Rate@10** | -0.0098 | [-0.0290, +0.0094] | -1.000 | 0.3197 | No |
| **Precision@5** | -0.0020 | [-0.0122, +0.0083] | -0.376 | 0.7074 | No |
| **Precision@10**| -0.0020 | [-0.0047, +0.0007] | -1.421 | 0.1583 | No |
| **Recall@5** | -0.0025 | [-0.0266, +0.0217] | -0.199 | 0.8426 | No |
| **Recall@10** | -0.0074 | [-0.0181, +0.0033] | -1.347 | 0.1810 | No |
| **MRR** | -0.0139 | [-0.0423, +0.0146] | -0.957 | 0.3408 | No |
| **nDCG@5** | -0.0082 | [-0.0320, +0.0156] | -0.678 | 0.4994 | No |
| **nDCG@10** | -0.0102 | [-0.0285, +0.0080] | -1.100 | 0.2740 | No |

*Inference:* None of the ranking metric differences between Architecture A and Architecture B achieve statistical significance at the 95% confidence level ($p > 0.15$ for all metrics; all 95% confidence intervals encompass zero).

### 11.2 Baseline Reconciliation
- **Phase 5 Corrected Summary:** Reconciled query counts ($N=102$ positive, $N=11$ absence, total $N=113$) and metrics match the independent scratch recalculation with 0.0000% divergence.
- **Trace Parity:** Confirmed zero divergence between traced and untraced production pipelines.

---

## 12. Factual Observations: Architecture A (`all_cross_encoder`)

### Observed Empirical Advantages
1. **Book Domain Top-Rank Quality:**
   - Achieves higher Book Hit Rate@5 and Hit Rate@10 by **+3.45 percentage points** (0.8276 vs 0.7931; 24/29 vs 23/29 hits).
   - Achieves higher Book MRR (+0.0454: 0.7293 vs 0.6839) and Book nDCG@10 (+0.0237: 0.7134 vs 0.6897).
   - In similarity query `SI_014` ("Recommend books similar to The Final Empire"), the cross-encoder successfully promoted relevant target `book_1083` from position #12 into the top 5 (position #5).
2. **Overall Hit Rate@10:**
   - Retains a **+0.98 percentage point advantage** in overall Hit Rate@10 (0.7647 vs 0.7549; 78 vs 77 hits), directly attributable to the `SI_014` book result.
3. **Architectural Uniformity:**
   - Maintains a single, homogeneous ranking pipeline across all query types without conditional branching or domain routing rules.

### Observed Empirical Disadvantages
1. **Latency Overhead:**
   - Substantially higher median latency across non-movie queries:
     - Book queries: P50 = 1,798.6 ms (8.0x slower than Architecture B's 223.4 ms).
     - Anime queries: P50 = 1,071.9 ms (3.8x slower than Architecture B's 285.5 ms).
     - Overall queries: P50 = 972.9 ms (3.4x slower than Architecture B's 286.5 ms).
2. **Anime Domain Top-5 Sensitivity:**
   - Exhibits lower Anime Hit Rate@5 by **-3.23 percentage points** (0.7097 vs 0.7419; 22/29 vs 23/29 hits).
   - In `KI_014` ("Find the anime One Punch Man"), cross-encoder reranking demoted the target title from #1 (RRF consensus) to #7, pushing it outside the top-5 window.
3. **Cross-Encoder Demotion Frequency:**
   - Pushes 56 relevant items out of the top-10 window (27 anime, 18 movie, 11 book targets).

---

## 13. Factual Observations: Architecture B (`domain_routed`)

### Observed Empirical Advantages
1. **Substantial Latency Reduction:**
   - Reduces overall median latency by **70.6%** (-686.4 ms: 972.9 ms $\rightarrow$ 286.5 ms).
   - Reduces book median latency by **87.6%** (-1,575.2 ms: 1,798.6 ms $\rightarrow$ 223.4 ms).
   - Reduces anime median latency by **73.4%** (-786.4 ms: 1,071.9 ms $\rightarrow$ 285.5 ms).
2. **Anime Domain Top-5 Quality:**
   - Achieves higher Anime Hit Rate@5 by **+3.23 percentage points** (0.7419 vs 0.7097; 23/31 vs 22/31 hits).
   - Preserves high-consensus lexical and semantic matches from RRF against general-domain cross-encoder vocabulary mismatch (e.g. promoting `KI_014` One Punch Man to #1).
3. **Elimination of Anime and Book Demotions:**
   - Completely eliminates cross-encoder demotions in anime (27 $\rightarrow$ 0) and book (11 $\rightarrow$ 0) domains, reducing total system demotions by **67.9%** (56 $\rightarrow$ 18).
4. **Exact Parity on Movie and Mixed-Domain Queries:**
   - Retains 100% mathematical ranking equivalence with Architecture A on Movie queries (Hit@5 0.8710, Hit@10 0.8710) and Mixed-Domain queries (Hit@5 0.1818, Hit@10 0.2727).

### Observed Empirical Disadvantages
1. **Book Domain Top-Rank Loss:**
   - Yields lower Book Hit Rate@5 and Hit Rate@10 by **-3.45 percentage points** (0.7931 vs 0.8276; 23/29 vs 24/29 hits).
   - Relies solely on RRF consensus for books, failing to promote `book_1083` in `SI_014` past rank #12.
   - Yields lower Book MRR (-0.0454: 0.6839 vs 0.7293) and Book nDCG@10 (-0.0237: 0.6897 vs 0.7134).
2. **Overall Hit Rate@10 Impact:**
   - Yields a **-0.98 percentage point reduction** in overall Hit Rate@10 (0.7549 vs 0.7647; 77 vs 78 hits).
3. **Pipeline Heterogeneity:**
   - Introduces routing dependencies into production retrieval, requiring domain-classification branching prior to ranking.

---

## 14. Limitations, Unresolved Discrepancies, and Incomplete Checks

1. **Excluded Music Catalog:**
   - As mandated, the music catalog remains deactivated. Operational and ranking behavior on music queries remains unmeasured.
2. **Single-Query Statistical Sensitivity:**
   - In domain subsets of moderate size ($N=29$ books, $N=31$ anime), a single query delta corresponds to a 3.23 to 3.45 percentage point swing. Aggregate metrics are heavily influenced by isolated edge cases (`KI_014` and `SI_014`).
3. **Mixed-Domain Sample Size ($N=11$):**
   - The mixed-domain evaluation subset comprises 11 queries and 47 targets. While sufficient for functional validation, it provides limited statistical resolution for multi-domain ranking dynamics.
4. **Dense / BM25 Candidate Ceiling:**
   - 72.8% of all ground-truth targets ($8,370$ targets) are missed at the first-stage retrieval step (`dense_and_bm25_miss`), placing an upper bound on second-stage reranking recall regardless of architecture.
5. **Hardware Constraints:**
   - Measurements reflect single-instance CPU inference. High-concurrency throughput and GPU batching were not evaluated.

---

## 15. Raw Results and Per-Query Divergence Evidence

Across the 113 benchmark queries, exactly **48 queries** exhibited candidate ordering or score differences between Architecture A and Architecture B.

### 15.1 Queries with Binary Hit Rate Differences
Only two queries across the entire benchmark exhibited a difference in binary Hit Rate:

| Query ID | Domain | Query Text | Metric Affected | Arch A Rank / Hit | Arch B Rank / Hit | Primary Cause |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| `KI_014` | Anime | *Find the anime One Punch Man.* | Hit@5 | Rank 7 (Hit@5 = 0) | Rank 1 (Hit@5 = 1) | MS-MARCO CE demoted anime title; RRF preserved rank 1. |
| `SI_014` | Book | *Recommend books similar to The Final Empire.* | Hit@5, Hit@10 | Rank 5 (Hit@5/10 = 1) | Rank 12 (Hit@5/10 = 0) | CE promoted `book_1083` to rank 5; RRF kept it at rank 12. |

### 15.2 Queries with Relevant Target Count Differences in Top-10
Beyond binary hits, three additional queries exhibited shifts in the number of relevant items appearing in the top 5 or top 10:

| Query ID | Domain | Query Text | Arch A Hits (Top-5 / Top-10) | Arch B Hits (Top-5 / Top-10) | Description |
| :--- | :--- | :--- | :---: | :---: | :--- |
| `KI_012` | Anime | *Find Cowboy Bebop.* | Top-5: 2, Top-10: 2 | Top-5: 1, Top-10: 2 | Relevant target `anime_750` ranked #5 in Arch A, #6 in Arch B. |
| `DE_014` | Anime | *An underdog high school volleyball team aims for nationals.* | Top-5: 2, Top-10: 2 | Top-5: 1, Top-10: 2 | Target `anime_107` ranked #5 in Arch A, #6 in Arch B. |
| `DE_015` | Anime | *Bounty hunters travel through space on their ship with a jazz soundtrack.* | Top-5: 1, Top-10: 2 | Top-5: 1, Top-10: 1 | Target `anime_750` ranked #7 in Arch A, #12 in Arch B. |

### 15.3 Trace References
Detailed trace data containing candidate IDs, dense scores, BM25 scores, RRF scores, cross-encoder scores, and latency breakdowns for every query can be independently audited at:
- `evaluation/results/retrieval_113_phase5_query_traces.jsonl`
- `evaluation/results/retrieval_113_phase5_failure_analysis.csv`
- `evaluation/results/retrieval_113_stage_summary.csv`
