# Project Black Knight - Read-Only Baseline Audit

## 1. Executive Summary & Evaluator Parity

This benchmark evaluates Project Black Knight across **113 audited queries** using shared production retrieval (`search_black_knight`) with 100% production/evaluator parity:
- **Architecture A (Baseline):** Hybrid retrieval (Dense + BM25, candidate_k=60), RRF fusion ($k=60$), cross-encoder reranking across all domains.
- **Architecture B (Domain-Routed):** Cross-encoder reranking for movies and mixed-domain queries; pure RRF for anime and books.
- **Pure RRF Baseline:** Cross-encoder bypassed across all domains.

## 2. Overall Ranking Performance (Positive Queries, N=102)

| Metric | Architecture A (All CE) | Architecture B (Domain-Routed) | Pure RRF | Delta (B vs A) |
|---|---:|---:|---:|---:|
| Hit Rate@5 | 0.7353 | 0.7353 | 0.7157 | +0.0000 |
| Hit Rate@10 | 0.7647 | 0.7549 | 0.7549 | -0.0098 |
| Precision@5 | 0.3549 | 0.3529 | 0.3471 | -0.0020 |
| Precision@10 | 0.2833 | 0.2814 | 0.2794 | -0.0020 |
| Recall@5 | 0.4690 | 0.4665 | 0.4477 | -0.0025 |
| Recall@10 | 0.5313 | 0.5239 | 0.5157 | -0.0074 |
| MRR | 0.6426 | 0.6287 | 0.5954 | -0.0139 |
| nDCG@5 | 0.6098 | 0.6015 | 0.5730 | -0.0082 |
| nDCG@10 | 0.6229 | 0.6126 | 0.5876 | -0.0102 |

## 3. Correctness & Integrity Metrics

| Metric | Architecture A | Architecture B | Pure RRF |
|---|---:|---:|---:|
| Duplicate-Result Rate | 0.00% | 0.00% | 0.00% |
| Hard-Filter Violation Rate | 0.00% | 0.00% | 0.00% |
| Absence Correct Rejection Rate | 100.0% | 100.0% | 100.0% |

## 4. Latency Analysis (Milliseconds)

| Architecture | Median / P50 (ms) | Mean (ms) | P95 (ms) | Steady-State Mean (ms) |
|---|---:|---:|---:|---:|
| architecture_a | 888.6 | 1174.3 | 3305.7 | 1177.8 |
| architecture_b | 232.4 | 603.3 | 2631.2 | 607.5 |
| rrf_only | 167.2 | 211.7 | 775.0 | 212.7 |

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
| MRR | 0.7598 | 0.7598 | 0.6647 | +0.0000 |
| nDCG@5 | 0.7164 | 0.7164 | 0.6322 | +0.0000 |
| nDCG@10 | 0.7259 | 0.7259 | 0.6522 | +0.0000 |

### Domain: Anime (N=38)

| Metric | Architecture A (All CE) | Architecture B (Domain-Routed) | Pure RRF | Delta (B vs A) |
|---|---:|---:|---:|---:|
| Hit Rate@5 | 0.6286 | 0.6571 | 0.6571 | +0.0286 |
| Hit Rate@10 | 0.6857 | 0.6857 | 0.6857 | +0.0000 |
| Precision@5 | 0.3543 | 0.3543 | 0.3543 | +0.0000 |
| Precision@10 | 0.3057 | 0.3029 | 0.3029 | -0.0029 |
| Recall@5 | 0.3092 | 0.3092 | 0.3092 | +0.0000 |
| Recall@10 | 0.3874 | 0.3731 | 0.3731 | -0.0143 |
| MRR | 0.5160 | 0.5131 | 0.5131 | -0.0029 |
| nDCG@5 | 0.4830 | 0.4786 | 0.4786 | -0.0044 |
| nDCG@10 | 0.5119 | 0.5017 | 0.5017 | -0.0102 |

### Domain: Book (N=37)

| Metric | Architecture A (All CE) | Architecture B (Domain-Routed) | Pure RRF | Delta (B vs A) |
|---|---:|---:|---:|---:|
| Hit Rate@5 | 0.7576 | 0.7273 | 0.7273 | -0.0303 |
| Hit Rate@10 | 0.7576 | 0.7273 | 0.7273 | -0.0303 |
| Precision@5 | 0.3394 | 0.3333 | 0.3333 | -0.0061 |
| Precision@10 | 0.2576 | 0.2545 | 0.2545 | -0.0030 |
| Recall@5 | 0.5226 | 0.5150 | 0.5150 | -0.0076 |
| Recall@10 | 0.5723 | 0.5647 | 0.5647 | -0.0076 |
| MRR | 0.6561 | 0.6162 | 0.6111 | -0.0399 |
| nDCG@5 | 0.6344 | 0.6135 | 0.6120 | -0.0208 |
| nDCG@10 | 0.6344 | 0.6135 | 0.6120 | -0.0208 |

## 6. Query-Level Comparison (Architecture B vs Architecture A)

- **Wins (B > A):** 4
- **Regressions (B < A):** 8
- **Neutral (B == A):** 90
