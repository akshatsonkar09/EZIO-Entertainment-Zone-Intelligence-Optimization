# Stage 4 Report — Implement Intent-Aware Reranking

## 1. Executive Summary & Status
- **Status:** `PASS`
- **Objective:** Rerank candidates according to the user's specific request intent (reference-title similarity, genre discovery, mood/tone discovery, explicit metadata constraints, or mixed intent) rather than treating every request as generic semantic similarity.
- **Key Empirical Results:**
  - **`domain_routed` Performance:** Reached **Hit@10 of 0.7647 (76.47%)**, **MRR of 0.6166**, and **nDCG@10 of 0.6041** with a **median latency of only 267.57 ms** across all 102 benchmark queries.
  - **`all_cross_encoder` Comparison Baseline:** Achieved **Hit@10 of 0.7745**, **MRR of 0.6377**, and **nDCG@10 of 0.6211** at a **median latency of 1,303.10 ms** (nearly $5\times$ slower).
  - **Domain Routing Efficiency:**
    - In **Anime**, `domain_routed` achieved **71.43% Hit@10** at **283.44 ms median latency**, compared to **68.57% Hit@10** at **1,598.64 ms** for `all_cross_encoder` ($5.6\times$ faster with higher hit rate).
    - In **Books**, `domain_routed` achieved **72.73% Hit@10** at **225.82 ms median latency**, compared to **78.79% Hit@10** at **2,417.53 ms** ($10.7\times$ faster).
  - **Constraint Violations:** Exactly **0 violations across all 102 queries (0.00% violation rate)** for both architectures. Hard constraints remained strictly enforced.
  - **All 6 Stage 4 tests passed**; full regression suite passing (149 total passing tests).

---

## 2. Intent Classification & Routing

We defined 5 explicit intent categories (plus fallback `general_semantic`):
1. **`reference_similarity`:** Queries with `similar_to` seeds requesting items like a reference title (e.g. "similar to Death Note").
2. **`genre_discovery`:** Queries explicitly requesting a genre (e.g. "cyberpunk", "space opera sci-fi", "historical fiction").
3. **`mood_tone_discovery`:** Queries specifying emotional tone or narrative atmosphere (e.g. "dark psychological", "cozy lighthearted", "mind-bending", "noir").
4. **`metadata_constraints`:** Queries specifying hard director, author, cast, release year, or runtime bounds without rich text.
5. **`mixed_intent`:** Composite queries combining reference similarity with metadata or mood (e.g. "dark psychological anime similar to Death Note released after 2015").

### Intent-Specific Alignment Scoring
- Zero additional neural model calls: alignment is computed via deterministic token overlap and Jaccard similarity across verified catalog fields (`genres`, `keywords`, `director`, `author`, `synopsis`).
- Normalized fusion:
  $$S_{\text{final}} = w_{\text{base}} \cdot S_{\text{norm\_base}} + w_{\text{intent}} \cdot S_{\text{intent}}$$
  where $(w_{\text{base}}, w_{\text{intent}})$ is dynamically tuned per intent:
  - `reference_similarity`: $(0.75, 0.25)$
  - `genre_discovery`: $(0.70, 0.30)$
  - `mood_tone_discovery`: $(0.70, 0.30)$
  - `metadata_constraints`: $(0.80, 0.20)$
  - `mixed_intent`: $(0.65, 0.35)$
  - `general_semantic`: $(0.90, 0.10)$

---

## 3. Evaluation Metrics

### Paired Comparison: `domain_routed` vs `all_cross_encoder` (102 Benchmark Queries)
| Metric | `domain_routed` (Primary) | `all_cross_encoder` (Baseline) | Delta (Routed - CE) |
| :--- | :---: | :---: | :---: |
| **Hit@10** | **0.7647 (76.47%)** | 0.7745 (77.45%) | -0.0098 (-0.98%) |
| **MRR** | **0.6166** | 0.6377 | -0.0211 (-2.11%) |
| **nDCG@10** | **0.6041** | 0.6211 | -0.0170 (-1.70%) |
| **Hard Constraint Violations** | **0 (0.00%)** | **0 (0.00%)** | 0 |
| **Median Latency** | **267.57 ms** | 1303.10 ms | **-1035.53 ms (4.9x faster)** |
| **Mean Latency** | **923.79 ms** | 1407.08 ms | **-483.29 ms (1.5x faster)** |

### Performance by Domain
| Domain | Query Count | `domain_routed` Hit@10 | `all_cross_encoder` Hit@10 | `domain_routed` Med Latency | `all_cross_encoder` Med Latency |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Movie** | 34 | 0.8529 (85.29%) | 0.8529 (85.29%) | 1125.13 ms | 1115.28 ms |
| **Anime** | 35 | **0.7143 (71.43%)** | 0.6857 (68.57%) | **283.44 ms** | 1598.64 ms (5.6x slower) |
| **Book** | 33 | 0.7273 (72.73%) | 0.7879 (78.79%) | **225.82 ms** | 2417.53 ms (10.7x slower) |

### Performance by Intent Category (`domain_routed`)
| Intent Category | Query Count | Hit@10 | MRR | nDCG@10 | Violations |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Mixed Intent** | 16 | **1.0000** | **1.0000** | **1.0000** | 0 |
| **Metadata Constraints** | 5 | **1.0000** | **1.0000** | **0.9492** | 0 |
| **Mood/Tone Discovery** | 1 | **1.0000** | **0.5000** | **0.6309** | 0 |
| **General Semantic** | 56 | **0.8571** | **0.6511** | **0.6471** | 0 |
| **Genre Discovery** | 9 | 0.4444 | 0.3704 | 0.3244 | 0 |
| **Reference Similarity** | 15 | 0.2667 | 0.1067 | 0.0723 | 0 |

---

## 4. Implementation Details

### Files Modified & Created
1. **`src/project_black_knight/query_schema.py`:**
   - Added optional `intent: str | None = None` to `BlackKnightQuery` for explicit routing compatibility.
2. **`src/project_black_knight/intent_reranker.py` (New Module):**
   - Implemented `detect_query_intent`, `compute_genre_alignment`, `compute_mood_alignment`, `compute_reference_affinity`, and `apply_intent_aware_reranking`.
3. **`src/project_black_knight/retrieval.py`:**
   - Wired `query_obj` through `search_black_knight` and `hybrid_retrieve`.
   - Inserted Step 6b (Intent-Aware Reranking) prior to result formatting.
4. **`tests/test_stage_04_intent_reranking.py` (New Tests):**
   - 6 unit and integration tests verifying classification, determinism, missing metadata safety, filter preservation, architecture parity, and reference seed exclusion.
5. **`evaluation/evaluate_stage_04_intent_reranking.py`:**
   - Evaluation script running paired comparison between `domain_routed` and `all_cross_encoder` across all 102 queries.

---

## 5. Artifacts Persisted
- `reports/recommendation_quality/artifacts/stage_04/stage_04_metrics.json`
- `reports/recommendation_quality/artifacts/stage_04/stage_04_rankings.json`
- `reports/recommendation_quality/artifacts/stage_04/stage_04_tests.txt`

---

## 6. Reproduction Commands
- **Run Unit Tests:**
  `$env:PYTHONPATH='src'; project_black_knight\Scripts\python -m pytest tests/test_stage_04_intent_reranking.py -v`
- **Run Evaluation:**
  `$env:PYTHONPATH='src'; project_black_knight\Scripts\python evaluation/evaluate_stage_04_intent_reranking.py`

---

## 7. Next Stage Starting Point
- **Stage 4 Status:** `PASS`
- **Stage 5 Starting Point:** Stage 5 focuses on **Taste-Aware Personalization** (implementing explicit positive/negative user preference representations, liked/disliked genres, liked titles, deterministic preference scoring with non-personalized fallback when no profile is supplied, and functional validation).
