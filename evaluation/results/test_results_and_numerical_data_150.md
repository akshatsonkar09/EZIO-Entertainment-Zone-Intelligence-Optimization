# Project Black Knight — 150-Query Dataset Test Results & Numerical Data

> [!NOTE]
> **Historical Audit Artifact**: This evaluation reflects an early four-domain benchmark prior to the permanent removal of the music domain. The active engine strictly supports Movies, Anime, and Books. This document is retained solely for auditability.

**Generated:** 2026-10-20T17:50:30Z  
**Evaluation Suite:** Audited 150-Query Multi-Modal Retrieval Benchmark  
**Configurations Evaluated:** Dense Retrieval (ChromaDB), BM25 Lexical, RRF Hybrid ($k=60$), Cross-Encoder Reranked Hybrid (`ms-marco-MiniLM-L-6-v2`)  
**Canonical Dataset:** `evaluation/black_knight_eval_queries_150_audited.csv`  

---

## 1. Benchmark Composition & Domain Balance

| Domain | Total Queries | Positive Queries | Absence Queries | Percentage of Benchmark |
| :--- | :---: | :---: | :---: | :---: |
| **Movie** | 38 | 34 | 4 | 25.3% |
| **Anime** | 38 | 35 | 3 | 25.3% |
| **Music** | 37 | 33 | 4 | 24.7% |
| **Book** | 37 | 33 | 4 | 24.7% |
| **Total** | **150** | **135** | **15** | **100.0%** |

### Query Category Breakdown

| Category | Query Count | Percentage | Description |
| :--- | :---: | :---: | :--- |
| `known_item` | 40 | 26.7% | Exact entity searches anchored on verified local catalog titles and stable record IDs.
| `descriptive` | 30 | 20.0% | Narrative and thematic descriptions with human-inspected catalog relevance targets.
| `constraint` | 30 | 20.0% | Deterministic metadata constraints evaluated via production `metadata_filter.py`.
| `similar_to` | 20 | 13.3% | Recommendations anchored on verified seeds with independent thematic clusters.
| `absence` | 15 | 10.0% | Verified catalog absences testing resilience against spurious hallucinated retrieval.
| `multi_domain` | 15 | 10.0% | Cross-domain discovery spanning combinations of movies, anime, music, and books.

---

## 2. Overall Numerical Retrieval Metrics (Positive Queries, N=135)

| Metric | Dense Retrieval | BM25 Retrieval | RRF Hybrid ($k=60$) | Cross-Encoder Reranked | Best Configuration |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Hit Rate@5** | 0.6000 | 0.6370 | 0.6444 | **0.6370** | `RRF Hybrid` |
| **Hit Rate@10** | 0.6370 | 0.6519 | 0.6963 | **0.6593** | `RRF Hybrid` |
| **Precision@5** | 0.3052 | 0.3230 | 0.3259 | **0.3274** | `Cross-Encoder` |
| **Precision@10** | 0.2444 | 0.2637 | 0.2696 | **0.2667** | `RRF Hybrid` |
| **Recall@5** | 0.3341 | 0.3592 | 0.3700 | **0.3762** | `Cross-Encoder` |
| **Recall@10** | 0.3973 | 0.4133 | 0.4402 | **0.4371** | `RRF Hybrid` |
| **MRR (Mean Reciprocal Rank)** | 0.5255 | 0.5068 | 0.5506 | **0.5540** | `Cross-Encoder` |
| **nDCG@5** | 0.4805 | 0.4789 | 0.5090 | **0.5212** | `Cross-Encoder` |
| **nDCG@10** | 0.4855 | 0.4874 | 0.5240 | **0.5319** | `Cross-Encoder` |

---

## 3. Absence Detection Numerical Results (Absence Queries, N=15)

| Retrieval Pipeline | Total Absence Queries | Correct Rejections | False Acceptances | Rejection Rate | Precision on Absences |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `dense_only` | 15 | 15 | 0 | **100.0%** | 100.0% |
| `bm25_only` | 15 | 15 | 0 | **100.0%** | 100.0% |
| `rrf_hybrid` | 15 | 15 | 0 | **100.0%** | 100.0% |
| `reranked_hybrid` | 15 | 15 | 0 | **100.0%** | 100.0% |

> **Absence Decision Rule:** When an entity title is specified as an anchor, the metadata filter checks exact and normalized catalog tokens. If the item does not exist, `valid_ids` evaluates to an empty set `set()`, filtering all candidates and returning 0 retrieved results. For title-constrained absence queries, 0 retrieved results constitutes a Correct Rejection (CR).

---

## 4. Per-Domain Numerical Breakdown

### 4.1 Movie Domain (Total Queries = 38)

| Metric | Dense Retrieval | BM25 Retrieval | RRF Hybrid | Cross-Encoder Reranked |
| :--- | :---: | :---: | :---: | :---: |
| Hit Rate@5 | 0.7059 | 0.7647 | 0.8529 | **0.8529** |
| Hit Rate@10 | 0.7647 | 0.7647 | 0.8529 | **0.8529** |
| Precision@5 | 0.3118 | 0.3353 | 0.3647 | **0.3765** |
| Precision@10 | 0.2353 | 0.2618 | 0.2765 | **0.2824** |
| Recall@5 | 0.4736 | 0.4919 | 0.5716 | **0.5863** |
| Recall@10 | 0.5278 | 0.5378 | 0.6150 | **0.6297** |
| MRR (Mean Reciprocal Rank) | 0.6559 | 0.6176 | 0.7005 | **0.7598** |
| nDCG@5 | 0.6167 | 0.5857 | 0.6825 | **0.7322** |
| nDCG@10 | 0.6143 | 0.5906 | 0.6840 | **0.7347** |

### 4.2 Anime Domain (Total Queries = 38)

| Metric | Dense Retrieval | BM25 Retrieval | RRF Hybrid | Cross-Encoder Reranked |
| :--- | :---: | :---: | :---: | :---: |
| Hit Rate@5 | 0.6286 | 0.6857 | 0.6571 | **0.6286** |
| Hit Rate@10 | 0.6857 | 0.7429 | 0.8000 | **0.6857** |
| Precision@5 | 0.3314 | 0.3657 | 0.3543 | **0.3486** |
| Precision@10 | 0.2686 | 0.3086 | 0.3143 | **0.3029** |
| Recall@5 | 0.2729 | 0.3163 | 0.2878 | **0.2949** |
| Recall@10 | 0.3483 | 0.3731 | 0.3946 | **0.3731** |
| MRR (Mean Reciprocal Rank) | 0.4779 | 0.4639 | 0.5066 | **0.4827** |
| nDCG@5 | 0.4372 | 0.4492 | 0.4508 | **0.4614** |
| nDCG@10 | 0.4496 | 0.4706 | 0.4921 | **0.4904** |

### 4.3 Book Domain (Total Queries = 37)

| Metric | Dense Retrieval | BM25 Retrieval | RRF Hybrid | Cross-Encoder Reranked |
| :--- | :---: | :---: | :---: | :---: |
| Hit Rate@5 | 0.7273 | 0.7576 | 0.7576 | **0.7273** |
| Hit Rate@10 | 0.7576 | 0.7576 | 0.7879 | **0.7576** |
| Precision@5 | 0.3333 | 0.3394 | 0.3394 | **0.3333** |
| Precision@10 | 0.2515 | 0.2576 | 0.2606 | **0.2606** |
| Recall@5 | 0.4822 | 0.5125 | 0.5125 | **0.5075** |
| Recall@10 | 0.5410 | 0.5622 | 0.5697 | **0.5799** |
| MRR (Mean Reciprocal Rank) | 0.6765 | 0.6601 | 0.7079 | **0.6384** |
| nDCG@5 | 0.6123 | 0.6192 | 0.6468 | **0.6195** |
| nDCG@10 | 0.6143 | 0.6192 | 0.6504 | **0.6298** |

### 4.4 Music Domain (Total Queries = 37)

| Metric | Dense Retrieval | BM25 Retrieval | RRF Hybrid | Cross-Encoder Reranked |
| :--- | :---: | :---: | :---: | :---: |
| Hit Rate@5 | 0.3333 | 0.3333 | 0.3030 | **0.3333** |
| Hit Rate@10 | 0.3333 | 0.3333 | 0.3333 | **0.3333** |
| Precision@5 | 0.2424 | 0.2485 | 0.2424 | **0.2485** |
| Precision@10 | 0.2212 | 0.2242 | 0.2242 | **0.2182** |
| Recall@5 | 0.1071 | 0.1147 | 0.1071 | **0.1147** |
| Recall@10 | 0.1713 | 0.1788 | 0.1788 | **0.1637** |
| MRR (Mean Reciprocal Rank) | 0.2904 | 0.2848 | 0.2854 | **0.3333** |
| nDCG@5 | 0.2543 | 0.2599 | 0.2543 | **0.2691** |
| nDCG@10 | 0.2622 | 0.2672 | 0.2666 | **0.2691** |

---

## 5. Candidate Overlap, Reranker Shifts & Latency Profiling

### Candidate Overlap & Reranker Dynamics

- **Mean Dense vs. BM25 Candidate Overlap (Jaccard Index):** `0.3082`
- **Reranker MRR Improvements vs. RRF:** `18` queries
- **Reranker MRR Regressions vs. RRF:** `13` queries
- **Reranker MRR Neutrals vs. RRF:** `104` queries

### Latency Profile Across Pipelines (Milliseconds)

| Pipeline | Mean Latency (ms) | P50 Median (ms) | P95 Latency (ms) | Speed vs. Reranked |
| :--- | :---: | :---: | :---: | :---: |
| `dense_only` | 149.21 | 119.48 | 332.02 | 5.5x faster |
| `bm25_only` | 125.40 | 102.56 | 292.77 | 6.5x faster |
| `rrf_hybrid` | 274.63 | 228.77 | 639.39 | 3.0x faster |
| `reranked_hybrid` | 819.93 | 594.45 | 2018.27 | 1.0x faster |

---

## 6. Complete Per-Query Results Table (All 150 Queries)

| Query ID | Domain | Category | Query Text | Rel Count | Dense Hit@10 | BM25 Hit@10 | RRF Hit@10 | Cross-Enc Hit@10 | Cross-Enc MRR | Cross-Enc nDCG@10 | Latency (ms) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `KI_001` | movie | known_item | Find the movie The Dark Knight. | 1 | 1 | 1 | 1 | **1** | 0.50 | 0.63 | 16633.5 |
| `KI_002` | movie | known_item | Find Inception directed by Christopher Nolan. | 1 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 109.6 |
| `KI_003` | movie | known_item | Show me the movie Pulp Fiction. | 1 | 1 | 0 | 1 | **1** | 1.00 | 1.00 | 90.2 |
| `KI_004` | movie | known_item | Find the film Titanic. | 1 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 131.5 |
| `KI_005` | movie | known_item | Find the movie The Godfather. | 1 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 107.4 |
| `KI_006` | movie | known_item | Find the movie Gladiator. | 1 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 105.4 |
| `KI_007` | movie | known_item | Find Mad Max: Fury Road. | 1 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 91.7 |
| `KI_008` | movie | known_item | Find the movie The Matrix. | 1 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 137.0 |
| `KI_009` | movie | known_item | Find the movie Interstellar. | 1 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 81.2 |
| `KI_010` | movie | known_item | Find the film Jurassic Park. | 1 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 100.4 |
| `KI_011` | anime | known_item | Find the anime Death Note. | 2 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 1126.0 |
| `KI_012` | anime | known_item | Find Cowboy Bebop. | 2 | 1 | 1 | 1 | **1** | 0.50 | 0.69 | 305.1 |
| `KI_013` | anime | known_item | Find Steins;Gate. | 2 | 1 | 1 | 1 | **1** | 0.14 | 0.40 | 453.7 |
| `KI_014` | anime | known_item | Find the anime One Punch Man. | 2 | 1 | 1 | 1 | **1** | 0.17 | 0.42 | 356.6 |
| `KI_015` | anime | known_item | Find Neon Genesis Evangelion. | 2 | 1 | 1 | 1 | **1** | 0.33 | 0.57 | 264.1 |
| `KI_016` | anime | known_item | Find Code Geass: Hangyaku no Lelouch. | 2 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 638.8 |
| `KI_017` | anime | known_item | Find Hunter x Hunter. | 2 | 1 | 1 | 1 | **1** | 0.33 | 0.57 | 408.3 |
| `KI_018` | anime | known_item | Find Shingeki no Kyojin. | 2 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 799.0 |
| `KI_019` | anime | known_item | Find Kimi no Na wa. | 2 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 195.1 |
| `KI_020` | anime | known_item | Find Mob Psycho 100. | 2 | 1 | 1 | 1 | **1** | 0.50 | 0.69 | 253.4 |
| `KI_021` | book | known_item | Find The Way of Kings by Brandon Sanderson. | 2 | 1 | 1 | 1 | **1** | 0.50 | 0.65 | 1410.0 |
| `KI_022` | book | known_item | Find The Hobbit by J.R.R. Tolkien. | 2 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 219.3 |
| `KI_023` | book | known_item | Find Mansfield Park by Jane Austen. | 1 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 221.1 |
| `KI_024` | book | known_item | Find Brave New World by Aldous Huxley. | 1 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 201.8 |
| `KI_025` | book | known_item | Find The Hunger Games by Suzanne Collins. | 1 | 1 | 1 | 1 | **1** | 0.50 | 0.63 | 193.0 |
| `KI_026` | book | known_item | Find To Kill a Mockingbird by Harper Lee. | 1 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 197.4 |
| `KI_027` | book | known_item | Find Murder on the Orient Express by Agatha Christie. | 1 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 189.4 |
| `KI_028` | book | known_item | Find Frankenstein by Mary Shelley. | 1 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 151.6 |
| `KI_029` | book | known_item | Find The Final Empire by Brandon Sanderson. | 1 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 179.0 |
| `KI_030` | book | known_item | Find The Outsider by Stephen King. | 1 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 143.8 |
| `KI_031` | music | known_item | Find the song Shape of You by Ed Sheeran. | 2 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 222.9 |
| `KI_032` | music | known_item | Find the song Bad Guy by Billie Eilish. | 2 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 118.9 |
| `KI_033` | music | known_item | Find Someone Like You by Adele. | 2 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 119.3 |
| `KI_034` | music | known_item | Find the song Uptown Funk by Mark Ronson. | 2 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 118.5 |
| `KI_035` | music | known_item | Find Godzilla by Eminem. | 2 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 118.2 |
| `KI_036` | music | known_item | Find Rolling in the Deep by Adele. | 2 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 118.1 |
| `KI_037` | music | known_item | Find the song Radioactive by Imagine Dragons. | 2 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 117.2 |
| `KI_038` | music | known_item | Find Blank Space by Taylor Swift. | 2 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 119.3 |
| `KI_039` | music | known_item | Find Despacito by Luis Fonsi. | 2 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 119.2 |
| `KI_040` | music | known_item | Find the song Old Town Road by Lil Nas X. | 2 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 118.9 |
| `DE_001` | movie | descriptive | A man relives the same day over and over in a small town. | 1 | 0 | 1 | 1 | **1** | 1.00 | 1.00 | 561.2 |
| `DE_002` | movie | descriptive | A team enters people's dreams to plant an idea in someone's mind. | 1 | 1 | 0 | 1 | **1** | 1.00 | 1.00 | 521.1 |
| `DE_003` | movie | descriptive | Toys that come to life when humans leave the room. | 3 | 1 | 1 | 1 | **1** | 0.50 | 0.53 | 501.9 |
| `DE_004` | movie | descriptive | A shark terrorizes a beach town and the police chief tries to stop it. | 2 | 1 | 1 | 1 | **1** | 0.50 | 0.39 | 501.3 |
| `DE_005` | movie | descriptive | Friends wake up after a bachelor party with no memory of the night before. | 2 | 0 | 1 | 1 | **1** | 0.50 | 0.61 | 701.5 |
| `DE_006` | movie | descriptive | A computer hacker learns from mysterious rebels about the true nature of his reality. | 1 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 730.4 |
| `DE_007` | movie | descriptive | A clownfish crosses the ocean to find his lost son. | 1 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 541.9 |
| `DE_008` | movie | descriptive | Scientists bring dinosaurs back to life in an island theme park. | 3 | 1 | 1 | 1 | **1** | 1.00 | 0.91 | 595.0 |
| `DE_009` | anime | descriptive | A boy who can stretch like rubber wants to become king of the pirates. | 2 | 1 | 1 | 1 | **1** | 0.50 | 0.39 | 1454.1 |
| `DE_010` | anime | descriptive | A high school student finds a notebook that kills anyone whose name is written in it. | 2 | 1 | 1 | 1 | **1** | 1.00 | 0.61 | 838.3 |
| `DE_011` | anime | descriptive | Teenagers pilot giant robots to fight mysterious monsters called Angels. | 2 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 911.9 |
| `DE_012` | anime | descriptive | A boy and a girl randomly swap bodies and live each other's lives. | 2 | 0 | 1 | 1 | **1** | 1.00 | 1.00 | 821.3 |
| `DE_013` | anime | descriptive | A corporate worker dies and is reincarnated as a slime in a fantasy world. | 2 | 1 | 1 | 1 | **1** | 0.50 | 0.39 | 954.8 |
| `DE_014` | anime | descriptive | An underdog high school volleyball team aims for nationals. | 2 | 1 | 0 | 1 | **1** | 0.33 | 0.50 | 1042.9 |
| `DE_015` | anime | descriptive | Bounty hunters travel through space on their ship with a jazz soundtrack. | 2 | 0 | 1 | 1 | **1** | 0.25 | 0.26 | 792.9 |
| `DE_016` | anime | descriptive | Humanity hides behind giant walls from man-eating humanoid giants. | 3 | 1 | 1 | 1 | **1** | 1.00 | 0.47 | 1374.5 |
| `DE_017` | book | descriptive | A young surgeon turned slave fights to survive on the shattered plains. | 2 | 0 | 0 | 0 | **1** | 0.17 | 0.22 | 1230.3 |
| `DE_018` | book | descriptive | A dystopian society forces teenagers to fight to the death on television. | 2 | 1 | 0 | 0 | **1** | 1.00 | 0.61 | 1401.5 |
| `DE_019` | book | descriptive | A hobbit goes on an adventure with dwarves to reclaim treasure from a dragon. | 2 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 1115.7 |
| `DE_020` | book | descriptive | A Belgian detective investigates a murder on a snowbound luxury train. | 1 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 1088.0 |
| `DE_021` | book | descriptive | A detective and his doctor friend investigate a legendary hound on the Devon moors. | 1 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 1412.9 |
| `DE_022` | book | descriptive | A dystopian future where citizens are genetically engineered into social castes. | 1 | 0 | 1 | 1 | **1** | 1.00 | 1.00 | 1405.6 |
| `DE_023` | book | descriptive | A street thief with magical allomantic powers joins a rebellion against an immortal emperor. | 1 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 1393.9 |
| `DE_024` | music | descriptive | Upbeat pop dance hits for high intensity workout sessions. | 4 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 1145.0 |
| `DE_025` | music | descriptive | Calm acoustic and gentle indie songs for quiet study sessions. | 4 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 462.5 |
| `DE_026` | music | descriptive | Slow melancholic heartbreak ballads about lost love. | 3 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 429.8 |
| `DE_027` | music | descriptive | High energy electronic festival dance tracks with heavy synth drops. | 4 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 465.1 |
| `DE_028` | music | descriptive | Classic rock anthems featuring electrifying guitar riffs and solos. | 3 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 512.7 |
| `DE_029` | music | descriptive | Relaxing chill hip hop beats with smooth rhythmic grooves. | 3 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 465.8 |
| `DE_030` | music | descriptive | Latin dance party songs with infectious reggaeton rhythms. | 3 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 425.8 |
| `CO_001` | movie | constraint | Movies directed by Christopher Nolan. | 8 | 1 | 1 | 1 | **1** | 1.00 | 0.75 | 125.9 |
| `CO_002` | movie | constraint | Sci-fi movies released after 2010 with a runtime under 150 minutes. | 136 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 629.0 |
| `CO_003` | movie | constraint | Comedy movies shorter than 100 minutes. | 938 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 598.9 |
| `CO_004` | movie | constraint | Action movies starring Tom Cruise. | 12 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 270.4 |
| `CO_005` | movie | constraint | Horror movies released between 1980 and 1989. | 59 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 489.1 |
| `CO_006` | movie | constraint | Movies with revenue over 500 million dollars. | 190 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 495.6 |
| `CO_007` | movie | constraint | Drama movies starring Meryl Streep released before 2000. | 4 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 134.9 |
| `CO_008` | movie | constraint | Thriller movies longer than 150 minutes, excluding horror. | 32 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 639.6 |
| `CO_009` | anime | constraint | Romance anime with fewer than 15 episodes. | 1661 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 689.2 |
| `CO_010` | anime | constraint | Anime ranked in the top 50. | 100 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 792.6 |
| `CO_011` | anime | constraint | Comedy anime released after 2015 with more than 24 episodes. | 98 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 905.7 |
| `CO_012` | anime | constraint | Mecha anime from the 1990s. | 221 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 775.7 |
| `CO_013` | anime | constraint | Fantasy anime excluding ecchi. | 3494 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 808.6 |
| `CO_014` | anime | constraint | Sports anime with a popularity rank under 300. | 66 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 1081.2 |
| `CO_015` | anime | constraint | Drama anime movies with exactly 1 episode. | 1348 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 568.9 |
| `CO_016` | anime | constraint | Horror anime released between 2000 and 2010. | 162 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 743.2 |
| `CO_017` | book | constraint | Books by Stephen King with rating above 4.0. | 10 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 593.9 |
| `CO_018` | book | constraint | Fantasy books with more than 800 pages. | 92 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 1609.1 |
| `CO_019` | book | constraint | Books by Agatha Christie with rating above 4.0. | 10 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 328.7 |
| `CO_020` | book | constraint | Science fiction books shorter than 250 pages. | 458 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 1281.9 |
| `CO_021` | book | constraint | Books by Neil Gaiman with more than 300 pages. | 7 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 414.1 |
| `CO_022` | book | constraint | Non-fiction books with rating above 4.2. | 2203 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 1651.5 |
| `CO_023` | book | constraint | Mystery books by Arthur Conan Doyle. | 7 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 377.4 |
| `CO_024` | music | constraint | Songs by Taylor Swift. | 27 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 423.5 |
| `CO_025` | music | constraint | Songs by Queen shorter than 3 minutes. | 38 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 705.6 |
| `CO_026` | music | constraint | Tracks by The Beatles. | 19 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 920.8 |
| `CO_027` | music | constraint | Songs by Ed Sheeran longer than 4 minutes. | 13 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 911.5 |
| `CO_028` | music | constraint | Tracks from the album Thriller by Michael Jackson. | 6 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 354.6 |
| `CO_029` | music | constraint | Rock songs by Led Zeppelin longer than 5 minutes. | 17 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 360.9 |
| `CO_030` | music | constraint | Pop songs by Ariana Grande shorter than 3.5 minutes. | 26 | 1 | 1 | 1 | **1** | 1.00 | 1.00 | 438.3 |
| `SI_001` | movie | similar_to | Recommend movies similar to Inception. | 4 | 1 | 1 | 1 | **0** | 0.00 | 0.00 | 811.1 |
| `SI_002` | movie | similar_to | Recommend movies similar to The Godfather. | 3 | 1 | 0 | 0 | **0** | 0.00 | 0.00 | 1061.9 |
| `SI_003` | movie | similar_to | Recommend movies similar to Toy Story. | 4 | 0 | 1 | 1 | **1** | 1.00 | 0.64 | 949.6 |
| `SI_004` | movie | similar_to | Recommend movies similar to The Dark Knight. | 4 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 1070.0 |
| `SI_005` | movie | similar_to | Recommend movies similar to Fight Club. | 4 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 906.6 |
| `SI_006` | anime | similar_to | Recommend anime similar to Death Note. | 4 | 0 | 1 | 1 | **0** | 0.00 | 0.00 | 2129.1 |
| `SI_007` | anime | similar_to | Recommend anime similar to Naruto. | 4 | 1 | 1 | 1 | **0** | 0.00 | 0.00 | 1985.0 |
| `SI_008` | anime | similar_to | Recommend anime similar to Cowboy Bebop. | 4 | 1 | 1 | 1 | **1** | 0.33 | 0.20 | 2119.1 |
| `SI_009` | anime | similar_to | Recommend anime similar to Shingeki no Kyojin. | 4 | 1 | 0 | 1 | **0** | 0.00 | 0.00 | 2150.7 |
| `SI_010` | anime | similar_to | Recommend anime similar to Steins;Gate. | 4 | 0 | 1 | 1 | **0** | 0.00 | 0.00 | 2013.7 |
| `SI_011` | book | similar_to | Recommend books similar to The Way of Kings. | 4 | 1 | 1 | 1 | **0** | 0.00 | 0.00 | 2222.2 |
| `SI_012` | book | similar_to | Recommend books similar to The Hunger Games. | 3 | 1 | 1 | 1 | **0** | 0.00 | 0.00 | 2078.2 |
| `SI_013` | book | similar_to | Recommend books similar to Murder on the Orient Express. | 4 | 1 | 1 | 1 | **1** | 0.20 | 0.15 | 1763.4 |
| `SI_014` | book | similar_to | Recommend books similar to The Final Empire. | 4 | 1 | 0 | 1 | **1** | 0.50 | 0.37 | 2210.0 |
| `SI_015` | book | similar_to | Recommend books similar to Brave New World. | 3 | 1 | 1 | 1 | **0** | 0.00 | 0.00 | 1787.0 |
| `SI_016` | music | similar_to | Recommend songs similar to Shape of You by Ed Sheeran. | 4 | 1 | 1 | 1 | **1** | 1.00 | 0.39 | 702.8 |
| `SI_017` | music | similar_to | Recommend songs similar to Bad Guy by Billie Eilish. | 4 | 1 | 1 | 1 | **1** | 1.00 | 0.39 | 709.7 |
| `SI_018` | music | similar_to | Recommend songs similar to Someone Like You by Adele. | 4 | 1 | 1 | 1 | **1** | 1.00 | 0.71 | 606.2 |
| `SI_019` | music | similar_to | Recommend songs similar to Blinding Lights by The Weeknd. | 4 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 608.0 |
| `SI_020` | music | similar_to | Recommend songs similar to Uptown Funk by Mark Ronson. | 4 | 1 | 1 | 1 | **1** | 1.00 | 0.39 | 695.0 |
| `AB_001` | movie | absence | Find the movie Oppenheimer. | 0 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 22.3 |
| `AB_002` | movie | absence | Find the movie Barbie. | 0 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 21.3 |
| `AB_003` | movie | absence | Find the movie Top Gun: Maverick. | 0 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 22.2 |
| `AB_004` | movie | absence | Find the movie The Crimson Lighthouse Protocol. | 0 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 22.8 |
| `AB_005` | anime | absence | Find the anime Frieren: Beyond Journey's End. | 0 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 82.3 |
| `AB_006` | anime | absence | Find the anime Solo Leveling. | 0 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 69.5 |
| `AB_007` | anime | absence | Find the anime Bocchi the Rock!. | 0 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 72.3 |
| `AB_008` | book | absence | Find The Alchemist by Paulo Coelho. | 0 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 56.0 |
| `AB_009` | book | absence | Find Fourth Wing by Rebecca Yarros. | 0 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 54.9 |
| `AB_010` | book | absence | Find Atomic Habits by James Clear. | 0 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 55.7 |
| `AB_011` | book | absence | Find The Last Cartographer of Vell by Ian Marrow. | 0 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 59.1 |
| `AB_012` | music | absence | Find the song As It Was by Harry Styles. | 0 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 119.4 |
| `AB_013` | music | absence | Find the song Espresso by Sabrina Carpenter. | 0 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 116.2 |
| `AB_014` | music | absence | Find the song Anti-Hero by Taylor Swift. | 0 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 122.2 |
| `AB_015` | music | absence | Find the song Glass Harbor Nights by The Velvet Orchids. | 0 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 117.1 |
| `MD_001` | movie | multi_domain | Find movies and books about Sherlock Holmes. | 4 | 0 | 0 | 1 | **1** | 0.50 | 0.39 | 1987.1 |
| `MD_002` | movie | multi_domain | Find sci-fi movies and anime about time travel. | 5 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 1105.1 |
| `MD_003` | movie | multi_domain | Find movies and books by Stephen King. | 6 | 0 | 0 | 0 | **1** | 0.33 | 0.15 | 2022.0 |
| `MD_004` | anime | multi_domain | Find anime and movies about samurai. | 4 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 1020.6 |
| `MD_005` | anime | multi_domain | Find movies and anime directed by Hayao Miyazaki. | 4 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 1141.7 |
| `MD_006` | anime | multi_domain | Find horror anime and horror movies. | 4 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 1037.8 |
| `MD_007` | anime | multi_domain | Find romance anime and romantic comedy movies. | 4 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 1123.3 |
| `MD_008` | book | multi_domain | Find books and movies about vampires. | 3 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 1946.2 |
| `MD_009` | book | multi_domain | Find fantasy books and movies about high fantasy quests. | 5 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 1583.2 |
| `MD_010` | book | multi_domain | Find fantasy books and fantasy anime with magic systems. | 4 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 1981.8 |
| `MD_011` | book | multi_domain | Find dystopian books and dystopian movies. | 4 | 0 | 1 | 1 | **1** | 0.20 | 0.15 | 1990.6 |
| `MD_012` | music | multi_domain | Find epic space orchestral soundtracks and sci-fi movies about space. | 4 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 922.0 |
| `MD_013` | music | multi_domain | Find Christmas holiday songs and family holiday movies. | 3 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 868.4 |
| `MD_014` | music | multi_domain | Find energetic rock songs and anime about rock bands. | 4 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 1066.2 |
| `MD_015` | music | multi_domain | Find hip-hop tracks and movies about urban street culture. | 4 | 0 | 0 | 0 | **0** | 0.00 | 0.00 | 895.9 |
