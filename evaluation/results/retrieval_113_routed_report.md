# Project Black Knight — 113-Query Retrieval Benchmark Report (Domain-Specific Cross-Encoder Routing)

## 1. Executive Summary & Overview

This report presents the evaluation of Project Black Knight across **113 audited queries** (active domains: movie, anime, book), comparing four retrieval configurations:
1. **Dense Retrieval:** ChromaDB vector search powered by `all-MiniLM-L6-v2`.
2. **BM25 Retrieval:** Lexical search powered by `rank_bm25`.
3. **RRF Hybrid:** Reciprocal Rank Fusion ($k=60$) combining Dense and BM25 candidate lists.
4. **Cross-Encoder Reranked Hybrid:** Deep reranking of top candidate items using `ms-marco-MiniLM-L-6-v2`.

### Benchmark Dataset Composition
- **Total Queries:** 113
- **Scored Queries:** 113
- **Unscorable Queries:** 0
- **Positive Queries:** 102
- **Absence Queries:** 11

### Domain Distribution

| Domain | Query Count | Percentage |
|---|---:|---:|
| Movie | 38 | 33.6% |
| Anime | 38 | 33.6% |
| Book | 37 | 32.7% |
| **Total** | **113** | **100.0%** |

## 2. Overall Retrieval Performance Comparison (Positive Queries, N=102)

| Metric | Dense Retrieval | BM25 Retrieval | RRF Hybrid | Cross-Encoder Reranked |
|---|---:|---:|---:|---:|
| Hit Rate@5 | 0.6863 | 0.7353 | 0.7451 | 0.7353 |
| Hit Rate@10 | 0.7353 | 0.7549 | 0.8137 | 0.7549 |
| Precision@5 | 0.3255 | 0.3471 | 0.3510 | 0.3529 |
| Precision@10 | 0.2520 | 0.2765 | 0.2833 | 0.2814 |
| Recall@5 | 0.4075 | 0.4383 | 0.4502 | 0.4665 |
| Recall@10 | 0.4705 | 0.4892 | 0.5198 | 0.5239 |
| MRR | 0.6015 | 0.5786 | 0.6270 | 0.6287 |
| nDCG@5 | 0.5537 | 0.5497 | 0.5776 | 0.6011 |
| nDCG@10 | 0.5578 | 0.5587 | 0.5940 | 0.6122 |

## 3. Absence Query Evaluation

- **Total Absence Queries:** 11
- **dense_only:** Correct Rejections: 11.0/11 (100.0%), False Acceptances: 0
- **bm25_only:** Correct Rejections: 11.0/11 (100.0%), False Acceptances: 0
- **rrf_hybrid:** Correct Rejections: 11.0/11 (100.0%), False Acceptances: 0
- **reranked_hybrid:** Correct Rejections: 11.0/11 (100.0%), False Acceptances: 0

## 4. Per-Domain Performance Breakdown

### Domain: Movie (N=38)

| Metric | Dense Retrieval | BM25 Retrieval | RRF Hybrid | Cross-Encoder Reranked |
|---|---:|---:|---:|---:|
| Hit Rate@5 | 0.7059 | 0.7647 | 0.8529 | 0.8235 |
| Hit Rate@10 | 0.7647 | 0.7647 | 0.8529 | 0.8529 |
| Precision@5 | 0.3118 | 0.3353 | 0.3647 | 0.3706 |
| Precision@10 | 0.2353 | 0.2618 | 0.2735 | 0.2853 |
| Recall@5 | 0.4736 | 0.4919 | 0.5716 | 0.5814 |
| Recall@10 | 0.5278 | 0.5378 | 0.6003 | 0.6395 |
| MRR | 0.6559 | 0.6176 | 0.6529 | 0.7598 |
| nDCG@5 | 0.6167 | 0.5857 | 0.6456 | 0.7164 |
| nDCG@10 | 0.6143 | 0.5906 | 0.6419 | 0.7259 |

### Domain: Anime (N=38)

| Metric | Dense Retrieval | BM25 Retrieval | RRF Hybrid | Cross-Encoder Reranked |
|---|---:|---:|---:|---:|
| Hit Rate@5 | 0.6286 | 0.6857 | 0.6286 | 0.6571 |
| Hit Rate@10 | 0.6857 | 0.7429 | 0.8000 | 0.6857 |
| Precision@5 | 0.3314 | 0.3657 | 0.3486 | 0.3543 |
| Precision@10 | 0.2686 | 0.3086 | 0.3143 | 0.3029 |
| Recall@5 | 0.2729 | 0.3163 | 0.2735 | 0.3092 |
| Recall@10 | 0.3483 | 0.3731 | 0.3946 | 0.3731 |
| MRR | 0.4779 | 0.4639 | 0.5377 | 0.5131 |
| nDCG@5 | 0.4372 | 0.4492 | 0.4562 | 0.4774 |
| nDCG@10 | 0.4496 | 0.4706 | 0.5043 | 0.5005 |

### Domain: Book (N=37)

| Metric | Dense Retrieval | BM25 Retrieval | RRF Hybrid | Cross-Encoder Reranked |
|---|---:|---:|---:|---:|
| Hit Rate@5 | 0.7273 | 0.7576 | 0.7576 | 0.7273 |
| Hit Rate@10 | 0.7576 | 0.7576 | 0.7879 | 0.7273 |
| Precision@5 | 0.3333 | 0.3394 | 0.3394 | 0.3333 |
| Precision@10 | 0.2515 | 0.2576 | 0.2606 | 0.2545 |
| Recall@5 | 0.4822 | 0.5125 | 0.5125 | 0.5150 |
| Recall@10 | 0.5410 | 0.5622 | 0.5697 | 0.5647 |
| MRR | 0.6765 | 0.6601 | 0.6949 | 0.6162 |
| nDCG@5 | 0.6123 | 0.6192 | 0.6365 | 0.6135 |
| nDCG@10 | 0.6143 | 0.6192 | 0.6399 | 0.6135 |

## 5. Candidate Overlap & Reranking Impact

- **Mean Dense-BM25 Jaccard Similarity:** 0.3524
- **Cross-Encoder vs RRF Improvements (MRR increased):** 16
- **Cross-Encoder vs RRF Regressions (MRR decreased):** 11
- **Cross-Encoder vs RRF Neutrals (MRR unchanged):** 75

## 6. Latency Analysis (Milliseconds)

| Configuration | Mean (ms) | Median / P50 (ms) | P95 (ms) |
|---|---:|---:|---:|
| dense_only | 324.22 | 284.60 | 829.78 |
| bm25_only | 164.90 | 130.86 | 602.92 |
| rrf_hybrid | 489.15 | 411.48 | 1432.73 |
| reranked_hybrid | 1519.43 | 428.82 | 5440.92 |
