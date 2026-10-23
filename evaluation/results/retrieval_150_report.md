# Project Black Knight — 150-Query Retrieval Benchmark Report

> [!NOTE]
> **Historical Audit Artifact**: This evaluation reflects an early four-domain benchmark prior to the permanent removal of the music domain. The active engine strictly supports Movies, Anime, and Books. This document is retained solely for auditability.

## 1. Executive Summary & Overview

This report presents the large-set evaluation of Project Black Knight across **150 audited queries**, comparing four retrieval configurations:
1. **Dense Retrieval:** ChromaDB vector search powered by `all-MiniLM-L6-v2`.
2. **BM25 Retrieval:** Lexical search powered by `rank_bm25`.
3. **RRF Hybrid:** Reciprocal Rank Fusion ($k=60$) combining Dense and BM25 candidate lists.
4. **Cross-Encoder Reranked Hybrid:** Deep reranking of top candidate items using `ms-marco-MiniLM-L-6-v2`.

### Benchmark Dataset Composition
- **Total Queries:** 150
- **Scored Queries:** 150
- **Unscorable Queries:** 0
- **Positive Queries:** 135
- **Absence Queries:** 15

### Exact Domain Distribution

| Domain | Query Count | Percentage |
|---|---:|---:|
| Movie | 38 | 25.3% |
| Anime | 38 | 25.3% |
| Music | 37 | 24.7% |
| Book | 37 | 24.7% |
| **Total** | **150** | **100.0%** |

## 2. Overall Retrieval Performance Comparison (Positive Queries, N=135)

| Metric | Dense Retrieval | BM25 Retrieval | RRF Hybrid | Cross-Encoder Reranked |
|---|---:|---:|---:|---:|
| **Hit Rate@5** | 0.6000 | 0.6370 | 0.6444 | **0.6370** |
| **Hit Rate@10** | 0.6370 | 0.6519 | 0.6963 | **0.6593** |
| **Precision@5** | 0.3052 | 0.3230 | 0.3259 | **0.3274** |
| **Precision@10** | 0.2444 | 0.2637 | 0.2696 | **0.2667** |
| **Recall@5** | 0.3341 | 0.3592 | 0.3700 | **0.3762** |
| **Recall@10** | 0.3973 | 0.4133 | 0.4402 | **0.4371** |
| **MRR** | 0.5255 | 0.5068 | 0.5506 | **0.5540** |
| **nDCG@5** | 0.4805 | 0.4789 | 0.5090 | **0.5212** |
| **nDCG@10** | 0.4855 | 0.4874 | 0.5240 | **0.5319** |

## 3. Absence Detection Performance (Absence Queries, N=15)

Absence queries evaluate the engine's ability to refrain from retrieving spurious candidates when an entity is genuinely absent from the catalog.

| Configuration | Total Absence Queries | Correct Rejections | False Acceptances | Rejection Rate |
|---|---:|---:|---:|---:|
| dense_only | 15 | 15 | 0 | 100.0% |
| bm25_only | 15 | 15 | 0 | 100.0% |
| rrf_hybrid | 15 | 15 | 0 | 100.0% |
| reranked_hybrid | 15 | 15 | 0 | 100.0% |

**Decision Rule for Absence Detection:**
> When an entity title is specified as an anchor, the metadata filtering engine checks exact and normalized catalog tokens. If the item does not exist, `valid_ids` evaluates to empty set `set()`, filtering all candidates and returning 0 retrieved results. For title-constrained absence queries, 0 results constitutes a Correct Rejection (CR).

## 4. Per-Domain Performance Breakdown

### Movies (N=38)

| Metric | Dense | BM25 | RRF | Cross-Encoder |
|---|---:|---:|---:|---:|
| Hit Rate@10 | 0.7647 | 0.7647 | 0.8529 | **0.8529** |
| Precision@10 | 0.2353 | 0.2618 | 0.2765 | **0.2824** |
| Recall@10 | 0.5278 | 0.5378 | 0.6150 | **0.6297** |
| MRR | 0.6559 | 0.6176 | 0.7005 | **0.7598** |
| nDCG@10 | 0.6143 | 0.5906 | 0.6840 | **0.7347** |

### Anime (N=38)

| Metric | Dense | BM25 | RRF | Cross-Encoder |
|---|---:|---:|---:|---:|
| Hit Rate@10 | 0.6857 | 0.7429 | 0.8000 | **0.6857** |
| Precision@10 | 0.2686 | 0.3086 | 0.3143 | **0.3029** |
| Recall@10 | 0.3483 | 0.3731 | 0.3946 | **0.3731** |
| MRR | 0.4779 | 0.4639 | 0.5066 | **0.4827** |
| nDCG@10 | 0.4496 | 0.4706 | 0.4921 | **0.4904** |

### Books (N=37)

| Metric | Dense | BM25 | RRF | Cross-Encoder |
|---|---:|---:|---:|---:|
| Hit Rate@10 | 0.7576 | 0.7576 | 0.7879 | **0.7576** |
| Precision@10 | 0.2515 | 0.2576 | 0.2606 | **0.2606** |
| Recall@10 | 0.5410 | 0.5622 | 0.5697 | **0.5799** |
| MRR | 0.6765 | 0.6601 | 0.7079 | **0.6384** |
| nDCG@10 | 0.6143 | 0.6192 | 0.6504 | **0.6298** |

### Music (N=37)

| Metric | Dense | BM25 | RRF | Cross-Encoder |
|---|---:|---:|---:|---:|
| Hit Rate@10 | 0.3333 | 0.3333 | 0.3333 | **0.3333** |
| Precision@10 | 0.2212 | 0.2242 | 0.2242 | **0.2182** |
| Recall@10 | 0.1713 | 0.1788 | 0.1788 | **0.1637** |
| MRR | 0.2904 | 0.2848 | 0.2854 | **0.3333** |
| nDCG@10 | 0.2622 | 0.2672 | 0.2666 | **0.2691** |

## 5. Candidate Overlap & Reranking Dynamics

- **Dense / BM25 Jaccard Overlap:** 0.3082
- **Reranker MRR Improvements vs RRF:** 18 queries
- **Reranker MRR Regressions vs RRF:** 13 queries
- **Reranker MRR Neutral vs RRF:** 104 queries

## 6. Latency Analysis

| Configuration | Mean Latency (ms) | P50 (ms) | P95 (ms) |
|---|---:|---:|---:|
| dense_only | 149.21 | 119.48 | 332.02 |
| bm25_only | 125.40 | 102.56 | 292.77 |
| rrf_hybrid | 274.63 | 228.77 | 639.39 |
| reranked_hybrid | 819.93 | 594.45 | 2018.27 |

## 7. Comparison with Previously Reported 12-Query Benchmark

In Phase 4, an initial 12-query benchmark was evaluated:
- **12-Query Benchmark:** Hit Rate@10 = 0.9091, MRR = 0.8636 on positive queries ($N=11$), with 1 absence query. (Dominated by straightforward single-domain title/genre queries).
- **150-Query Audited Benchmark:** Cross-Encoder Hit Rate@10 = 0.6593 (RRF Hit Rate@10 = 0.6963), MRR = 0.5540 on positive queries ($N=135$), with 15 absence queries (100% correct rejection).
The 150-query benchmark provides a much more realistic, rigorous, and diverse stress-test across difficult multi-domain searches, similar-to semantic clusters, complex multi-predicate metadata constraints, and nuanced catalog distributions.

## 8. Small-Set Parser vs. Large-Set Retrieval Distinction

> [!IMPORTANT]
> **Methodological Clarification:**
> - The **Small-Set Benchmark (40 queries)** evaluates **LLM Query Parsing accuracy** (`evaluation/results/parser_report.json`), measuring how accurately Groq structures natural language into `BlackKnightQuery` schemas (57.5% normalized match, 100% schema validity).
> - The **Large-Set Benchmark (150 queries)** evaluates **Retrieval and Ranking Quality** across dense, lexical, hybrid, and cross-encoder pipelines on local ChromaDB and BM25 indexes.
> - These two evaluations measure entirely different stages of the system and **must not be compared directly as if measuring the same task**.
