# Project Black Knight - Experiment 1: Exact Title Promotion

## 1. Executive Summary & Evaluator Parity

This benchmark evaluates Project Black Knight across **113 audited queries** using shared production retrieval (`search_black_knight`) with 100% production/evaluator parity:
- **Architecture A (Baseline):** Hybrid retrieval (Dense + BM25, candidate_k=60), RRF fusion ($k=60$), cross-encoder reranking across all domains.
- **Architecture B (Domain-Routed):** Cross-encoder reranking for movies and mixed-domain queries; pure RRF for anime and books.
- **Pure RRF Baseline:** Cross-encoder bypassed across all domains.

## 2. Overall Ranking Performance (Positive Queries, N=102)

| Metric | Architecture A (All CE) | Architecture B (Domain-Routed) | Pure RRF | Delta (B vs A) |
|---|---:|---:|---:|---:|
| Hit Rate@5 | 0.7549 | 0.7549 | 0.7353 | +0.0000 |
| Hit Rate@10 | 0.7647 | 0.7647 | 0.7647 | +0.0000 |
| Precision@5 | 0.3627 | 0.3627 | 0.3569 | +0.0000 |
| Precision@10 | 0.2833 | 0.2833 | 0.2814 | +0.0000 |
| Recall@5 | 0.4886 | 0.4910 | 0.4722 | +0.0025 |
| Recall@10 | 0.5313 | 0.5337 | 0.5255 | +0.0025 |
| MRR | 0.7025 | 0.6931 | 0.6729 | -0.0093 |
| nDCG@5 | 0.6603 | 0.6567 | 0.6377 | -0.0036 |
| nDCG@10 | 0.6654 | 0.6617 | 0.6462 | -0.0036 |

## 3. Correctness & Integrity Metrics

| Metric | Architecture A | Architecture B | Pure RRF |
|---|---:|---:|---:|
| Duplicate-Result Rate | 0.00% | 0.00% | 0.00% |
| Hard-Filter Violation Rate | 0.00% | 0.00% | 0.00% |
| Absence Correct Rejection Rate | 100.0% | 100.0% | 100.0% |

## 4. Latency Analysis (Milliseconds)

| Architecture | Median / P50 (ms) | Mean (ms) | P95 (ms) | Steady-State Mean (ms) |
|---|---:|---:|---:|---:|
| architecture_a | 992.5 | 1386.6 | 3921.9 | 1391.5 |
| architecture_b | 319.2 | 813.5 | 3228.2 | 819.7 |
| rrf_only | 260.7 | 422.1 | 1235.5 | 424.8 |

## 5. Per-Domain Performance Breakdown

### Domain: Movie (N=38)

| Metric | Architecture A (All CE) | Architecture B (Domain-Routed) | Pure RRF | Delta (B vs A) |
|---|---:|---:|---:|---:|
| Hit Rate@5 | 0.8235 | 0.8235 | 0.7647 | +0.0000 |
| Hit Rate@10 | 0.8529 | 0.8529 | 0.8529 | +0.0000 |
| Precision@5 | 0.3706 | 0.3706 | 0.3529 | +0.0000 |
| Precision@10 | 0.2853 | 0.2853 | 0.2794 | +0.0000 |
| Recall@5 | 0.5814 | 0.5814 | 0.5250 | +0.0000 |
| Recall@10 | 0.6395 | 0.6395 | 0.6150 | +0.0000 |
| MRR | 0.7990 | 0.7990 | 0.7431 | +0.0000 |
| nDCG@5 | 0.7458 | 0.7458 | 0.6903 | +0.0000 |
| nDCG@10 | 0.7553 | 0.7553 | 0.7103 | +0.0000 |

### Domain: Anime (N=38)

| Metric | Architecture A (All CE) | Architecture B (Domain-Routed) | Pure RRF | Delta (B vs A) |
|---|---:|---:|---:|---:|
| Hit Rate@5 | 0.6857 | 0.7143 | 0.7143 | +0.0286 |
| Hit Rate@10 | 0.6857 | 0.7143 | 0.7143 | +0.0286 |
| Precision@5 | 0.3771 | 0.3829 | 0.3829 | +0.0057 |
| Precision@10 | 0.3057 | 0.3086 | 0.3086 | +0.0029 |
| Recall@5 | 0.3663 | 0.3806 | 0.3806 | +0.0143 |
| Recall@10 | 0.3874 | 0.4017 | 0.4017 | +0.0143 |
| MRR | 0.6381 | 0.6486 | 0.6486 | +0.0105 |
| nDCG@5 | 0.5877 | 0.6002 | 0.6002 | +0.0125 |
| nDCG@10 | 0.5932 | 0.6057 | 0.6057 | +0.0125 |

### Domain: Book (N=37)

| Metric | Architecture A (All CE) | Architecture B (Domain-Routed) | Pure RRF | Delta (B vs A) |
|---|---:|---:|---:|---:|
| Hit Rate@5 | 0.7576 | 0.7273 | 0.7273 | -0.0303 |
| Hit Rate@10 | 0.7576 | 0.7273 | 0.7273 | -0.0303 |
| Precision@5 | 0.3394 | 0.3333 | 0.3333 | -0.0061 |
| Precision@10 | 0.2576 | 0.2545 | 0.2545 | -0.0030 |
| Recall@5 | 0.5226 | 0.5150 | 0.5150 | -0.0076 |
| Recall@10 | 0.5723 | 0.5647 | 0.5647 | -0.0076 |
| MRR | 0.6712 | 0.6313 | 0.6263 | -0.0399 |
| nDCG@5 | 0.6493 | 0.6247 | 0.6232 | -0.0245 |
| nDCG@10 | 0.6493 | 0.6247 | 0.6232 | -0.0245 |

## 6. Query-Level Comparison (Architecture B vs Architecture A)

- **Wins (B > A):** 3
- **Regressions (B < A):** 5
- **Neutral (B == A):** 94
