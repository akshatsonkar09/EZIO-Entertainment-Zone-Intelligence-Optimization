# 113-Query Benchmark Baseline Comparison

**Benchmark Dataset:** `evaluation\black_knight_eval_queries_113_audited.csv` (113 queries)
**Execution Timestamp:** `20261022_222218`
**Historical Baseline Source:** `evaluation/results/retrieval_113_phase5_report.json`

## 1. Overall Metrics Comparison: `domain_routed` (Primary Architecture)

| Metric | Historical Baseline | Current Implementation | Absolute Change | Relative Change (%) | Direction |
|---|---:|---:|---:|---:|:---:|
| **Hit Rate@5** | 0.7353 | **0.7255** | -0.0098 | -1.33% | Regressed |
| **Hit Rate@10** | 0.7549 | **0.7647** | +0.0098 | +1.30% | Improved |
| **Precision@5** | 0.3529 | **0.3529** | +0.0000 | +0.00% | Unchanged |
| **Precision@10** | 0.2814 | **0.2804** | -0.0010 | -0.35% | Regressed |
| **Recall@5** | 0.4665 | **0.4641** | -0.0025 | -0.53% | Regressed |
| **Recall@10** | 0.5239 | **0.5190** | -0.0049 | -0.94% | Regressed |
| **MRR** | 0.6287 | **0.6166** | -0.0121 | -1.92% | Regressed |
| **nDCG@5** | 0.6015 | **0.5943** | -0.0073 | -1.21% | Regressed |
| **nDCG@10** | 0.6126 | **0.6041** | -0.0085 | -1.39% | Regressed |
| **Absence Rejection Rate** | 1.0000 | **1.0000** | +0.0000 | +0.00% | Unchanged |
| **Hard-Filter Violations** | 0 | **0** | 0 | 0.00% | Unchanged (Zero Violations) |
| **Seed Leakage Rate** | 0.0000 | **0.0000** | 0.0000 | 0.00% | Unchanged (Zero Leaks) |
| **Median Latency (ms)** | 246.5 ms | **279.8 ms** | +33.3 ms | +13.50% | Latency Shift |
| **Mean Latency (ms)** | 597.4 ms | **794.9 ms** | +197.5 ms | +33.06% | Latency Shift |

## 2. Comparison Baseline: `all_cross_encoder`

| Metric | Historical Baseline | Current Implementation | Absolute Change | Relative Change (%) | Direction |
|---|---:|---:|---:|---:|:---:|
| **Hit Rate@5** | 0.7353 | **0.7353** | +0.0000 | +0.00% | Unchanged |
| **Hit Rate@10** | 0.7647 | **0.7745** | +0.0098 | +1.28% | Improved |
| **Precision@5** | 0.3549 | **0.3569** | +0.0020 | +0.55% | Improved |
| **Precision@10** | 0.2833 | **0.2853** | +0.0020 | +0.69% | Improved |
| **Recall@5** | 0.4690 | **0.4616** | -0.0074 | -1.57% | Regressed |
| **Recall@10** | 0.5313 | **0.5337** | +0.0025 | +0.46% | Improved |
| **MRR** | 0.6426 | **0.6377** | -0.0049 | -0.76% | Regressed |
| **nDCG@5** | 0.6098 | **0.6043** | -0.0054 | -0.89% | Regressed |
| **nDCG@10** | 0.6229 | **0.6211** | -0.0017 | -0.28% | Regressed |

## 3. Top 10 Largest Improvements (`domain_routed`)

| Query ID | Domain | Category | Query Text | Historical MRR | Current MRR | MRR Delta | Historical nDCG@10 | Current nDCG@10 | nDCG Delta |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| `DE_016` | anime | descriptive | Humanity hides behind giant walls from man-eating humanoid giants. | 0.5000 | **1.0000** | **+0.5000** | 0.2961 | **0.4693** | **+0.1732** |
| `MD_011` | book | multi_domain | Find dystopian books and dystopian movies. | 0.5000 | **1.0000** | **+0.5000** | 0.2463 | **0.3904** | **+0.1441** |
| `KI_001` | movie | known_item | Find the movie The Dark Knight. | 0.3333 | **0.5000** | **+0.1667** | 0.5000 | **0.6309** | **+0.1309** |
| `DE_015` | anime | descriptive | Bounty hunters travel through space on their ship with a jazz soundtrack. | 0.2000 | **0.3333** | **+0.1333** | 0.2372 | **0.3066** | **+0.0694** |
| `SI_009` | anime | similar_to | Recommend anime similar to Shingeki no Kyojin. | 0.0000 | **0.1250** | **+0.1250** | 0.0000 | **0.1232** | **+0.1232** |
| `MD_003` | movie | multi_domain | Find movies and books by Stephen King. | 0.1667 | **0.2000** | **+0.0333** | 0.1078 | **0.1171** | **+0.0093** |
| `DE_003` | movie | descriptive | Toys that come to life when humans leave the room. | 1.0000 | **1.0000** | **+0.0000** | 0.8180 | **1.0000** | **+0.1820** |
| `KI_017` | anime | known_item | Find Hunter x Hunter. | 0.3333 | **0.3333** | **+0.0000** | 0.5438 | **0.5706** | **+0.0269** |

## 4. Top 10 Largest Regressions (`domain_routed`)

| Query ID | Domain | Category | Query Text | Historical MRR | Current MRR | MRR Delta | Historical nDCG@10 | Current nDCG@10 | nDCG Delta |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| `MD_001` | movie | multi_domain | Find movies and books about Sherlock Holmes. | 1.0000 | **0.3333** | **-0.6667** | 0.5079 | **0.1952** | **-0.3127** |
| `DE_006` | movie | descriptive | A computer hacker learns from mysterious rebels about the true nature of his reality. | 1.0000 | **0.5000** | **-0.5000** | 1.0000 | **0.6309** | **-0.3691** |
| `DE_020` | book | descriptive | A Belgian detective investigates a murder on a snowbound luxury train. | 1.0000 | **0.5000** | **-0.5000** | 1.0000 | **0.6309** | **-0.3691** |
| `KI_014` | anime | known_item | Find the anime One Punch Man. | 1.0000 | **0.5000** | **-0.5000** | 0.9197 | **0.6509** | **-0.2688** |
| `DE_014` | anime | descriptive | An underdog high school volleyball team aims for nationals. | 0.5000 | **0.3333** | **-0.1667** | 0.5803 | **0.4911** | **-0.0891** |
| `SI_008` | anime | similar_to | Recommend anime similar to Cowboy Bebop. | 0.5000 | **0.3333** | **-0.1667** | 0.2463 | **0.1952** | **-0.0511** |
| `SI_013` | book | similar_to | Recommend books similar to Murder on the Orient Express. | 0.2500 | **0.1429** | **-0.1071** | 0.1681 | **0.1301** | **-0.0380** |
| `DE_017` | book | descriptive | A young surgeon turned slave fights to survive on the shattered plains. | 0.2500 | **0.1667** | **-0.0833** | 0.2641 | **0.2184** | **-0.0457** |
| `DE_005` | movie | descriptive | Friends wake up after a bachelor party with no memory of the night before. | 0.5000 | **0.5000** | **+0.0000** | 0.5714 | **0.3869** | **-0.1846** |
