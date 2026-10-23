# 113-Query Benchmark Evaluation Summary Report

**Execution Timestamp:** `20261022_222218`
**Benchmark Dataset:** `evaluation/black_knight_eval_queries_113_audited.csv`
**Total Queries:** 113 (102 positive scorable queries, 11 absence queries)

## Final Benchmark Verdict: **`MIXED`**

### Executive Takeaways:
1. **Hit Rate@10:** Current `0.7647` vs Historical `0.7549` (Delta: `+0.0098`).
2. **MRR:** Current `0.6166` vs Historical `0.6287` (Delta: `-0.0121`).
3. **nDCG@10:** Current `0.6041` vs Historical `0.6126` (Delta: `-0.0085`).
4. **Seed Leakage:** Strictly **0.00% (0 leaks)** across all queries.
5. **Hard-Filter Violations:** Strictly **0 violations** (100% compliance with release years and excluded genres).
6. **Absence Correct Rejection:** Strictly **1.0000 (11/11 correct empty results)**.

### Domain Performance (`domain_routed`):

| Domain | Query Count | Hit@5 | Hit@10 | MRR | nDCG@10 | Mean Latency |
|---|---:|---:|---:|---:|---:|---:|
| **Movie** | 38 | 0.8529 | 0.8529 | 0.7314 | 0.7099 | 1114.4 ms |
| **Anime** | 38 | 0.6571 | 0.7143 | 0.5110 | 0.5013 | 573.4 ms |
| **Book** | 37 | 0.6667 | 0.7273 | 0.6104 | 0.6042 | 694.3 ms |

### Intent Breakdown (`domain_routed`):

| Intent / Category | Count | Hit@5 | Hit@10 | MRR | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| **absence** | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| **constraint** | 23 | 1.0000 | 1.0000 | 1.0000 | 0.9889 |
| **descriptive** | 23 | 0.8696 | 0.9130 | 0.6812 | 0.6176 |
| **known_item** | 30 | 0.8667 | 0.9000 | 0.7031 | 0.7627 |
| **multi_domain** | 11 | 0.2727 | 0.2727 | 0.1394 | 0.0639 |
| **similar_to** | 15 | 0.1333 | 0.2667 | 0.1067 | 0.0723 |
