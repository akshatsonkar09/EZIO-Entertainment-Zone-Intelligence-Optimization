# Project Black Knight — Post-Optimization Experiment Log

This log documents all audit and experimental evaluations performed during the Post-Optimization Audit & Next-Phase Protocol.
All experiments adhere strictly to filesystem-based recovery checkpoints, verified metric calculations, paired statistical significance testing, and non-destructive data handling.

---

## Experiment 1 Audit: Exact Title Prioritization & Score Promotion

- **Experiment ID**: `EXP_001`
- **Component**: `src/project_black_knight/retrieval.py`
- **Initial Execution**: October 23, 2026, 01:45:00+05:30
- **Audit Verification Date**: October 23, 2026, 07:45:00+05:30
- **Status**: **RETAINED & VERIFIED**
- **Hypothesis**:
  Known-item queries with title constraints frequently suffer from sequel/spinoff intrusion in dense/lexical retrieval where entities with longer descriptive overviews outrank the exact canonical title entity. Prioritizing exact normalized title matches (`normalize_token_str(title) == normalize_token_str(filter_title)`) in candidate generation with a +10.0 score boost elevates exact canonical entities to Rank 1 without perturbing semantic queries.
- **Files Modified**:
  - `src/project_black_knight/retrieval.py`: Added pre-indexed $O(1)$ `RetrievalRepository.get_normalized_titles(domain)`, injected exact matches into `rrf_fused`, and applied deterministic score promotion (+10.0) in cross-encoder and RRF branches.
  - `tests/test_exact_title_promotion.py`: Added 5 targeted regression tests.
- **Test Verification**:
  - Command: `powershell -Command "$env:PYTHONPATH='src;.'; uv run --with pytest pytest"`
  - Result: **122 / 122 tests passed** in 92.25s (100% pass rate).
- **Metric Verification (Architecture B: Domain-Routed Production Pipeline)**:
  - **Overall MRR**: 0.6287 -> **0.6931** (+0.0644, +10.2% relative gain)
  - **Overall Hit@1**: 0.5588 -> **0.6471** (+0.0882, net gain of +9 queries to Rank 1)
  - **Overall Hit@5**: 0.7353 -> **0.7549** (+0.0196, +2 queries gained)
  - **Overall Hit@10**: 0.7549 -> **0.7647** (+0.0098, +1 query gained)
  - **Known-Item MRR**: 0.7142 -> **0.9333** (+0.2191, target ≥ 0.85 exceeded)
  - **Known-Item Hit@1**: 0.6333 -> **0.9333** (28/30 queries placed at Rank 1, target ≥ 0.75 exceeded)
  - **Movie MRR**: 0.7598 -> **0.7990** (+0.0392, target ≥ 0.75 met)
  - **Anime MRR**: 0.5131 -> **0.6486** (+0.1354, +26.4% gain)
  - **Book MRR**: 0.6162 -> **0.6313** (+0.0152)
  - **Hard Filter Violations**: 0.0% (0 / 113)
  - **Absence Rejection Rate**: 100.0% (11 / 11 correctly rejected, 0 false acceptances)
  - **Duplicate Result Rate**: 0.0%
- **Statistical Significance (Verified)**:
  - Paired t-test: $t = 3.0696$, $p = 0.00275$ ($p < 0.01$)
  - Wilcoxon Signed-Rank: $W = 0.0$, $p = 0.00716$ ($p < 0.01$)
  - Paired Bootstrap 95% CI: `[+0.0275, +0.1081]` (strictly excludes zero)
  - **Conclusion**: Statistically significant improvement confirmed.
- **Latency Overhead**:
  - Pre-computed normalized title arrays execute lookups in **< 0.35ms** per query.
- **Decision**: **RETAIN**.

---

## Experiment 2 Audit: Candidate Pool Depth Exploration (`candidate_k` 60 vs 80 vs 100)

- **Experiment ID**: `EXP_002_SIM`
- **Component**: `src/project_black_knight/retrieval.py`
- **Execution Date**: October 23, 2026, 02:05:00+05:30
- **Status**: **REJECTED (Falsified)**
- **Hypothesis**:
  Increasing candidate pool generation depth `candidate_k` from 60 to 80 or 100 will allow missed positive candidates from dense retrieval and BM25 to enter the candidate pool and improve Hit@10 for descriptive and multi-domain queries.
- **Controlled Simulation Methodology**:
  - Evaluated on all 102 positive benchmark queries using identical models, weights, indexes, and queries.
  - Tested `candidate_k` $\in \{60, 80, 100\}$.
- **Results**:
  - `candidate_k = 60`: MRR = **0.6931**, Hit@5 = **0.7549**, Hit@10 = **0.7647**
  - `candidate_k = 80`: MRR = **0.6931**, Hit@5 = **0.7549**, Hit@10 = **0.7647**
  - `candidate_k = 100`: MRR = **0.6928**, Hit@5 = **0.7451**, Hit@10 = **0.7647**
- **Findings & Rationale**:
  - `candidate_k = 80` produces identical results to 60 with zero metric gains.
  - `candidate_k = 100` slightly reduces Hit@5 (from 0.7549 to 0.7451) due to candidate dilution in reciprocal rank fusion.
  - Neither 80 nor 100 improves Hit@10 because zero-hit queries fail due to vocabulary mismatch (`DE_011`), benchmark label errors (`KI_016`, `KI_023`, `MD_005`), or seed exclusion contracts (`SI_001` - `SI_015`), none of which are solved by deeper candidate generation.
- **Decision**: **REJECT**. Maintain `candidate_k = 60`.
