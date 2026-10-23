# Stage 2 Report — Better Item Representations

## 1. Executive Summary & Status
- **Status:** `PASS`
- **Objective:** Upgrade catalog document representations from unstructured keyword bags to domain-aware, structured text representations containing catalog facts (director, cast, genres, themes, synopsis, episodes, author, characters) while maintaining strict versioning and backward compatibility.
- **Key Empirical Result:**
  - In **Movies**, BM25 Recall@100 surged from **44.77% to 56.46% (+11.69 percentage points)** because titles, directors, and cast were previously absent from raw keyword tags.
  - Overall BM25 Recall@100 increased from **53.06% to 56.96% (+3.90 percentage points)** across all 102 evaluated benchmark queries with ground truth.
  - Overall BM25 Recall@50 increased from **49.67% to 54.36% (+4.69 percentage points)**.
  - Overall RRF candidate Recall@100 improved to **57.71%**.
  - All 9 new Stage 2 unit/integration tests and all 128 existing system tests pass (137 total passing tests).

---

## 2. Original Behavior & Problem Diagnosis
1. **Unstructured Legacy Representations (`v1_legacy`):**
   - The original pipeline relied on `movies1234.pkl["tag"]`, `anime_tag2.pkl["tag2"]`, and `books_tag2.pkl["tag2"]`.
   - In movies, `tag` was a mashed-up lowercase token string omitting the movie's title, director, and leading cast in the text body (forcing a runtime hack `if not doc_text.startswith("title:"): doc_text = f"title: {t_val} {doc_text}"` in reranking).
   - In anime and books, unstructured blobs mixed keywords, raw synopsis, and arbitrary tokens without field semantics, preventing BM25 from distinguishing author/director queries from plot words.
2. **Missing Token-Budget & Context Control:**
   - Books contained lengthy synopsis text without structured tags for author, characters, or page-length indicators.
   - Anime lacked format, episode count, or ranking status signals.

---

## 3. Implementation Details

### Files Modified & Created
1. **`src/project_black_knight/item_representations.py` (New Module):**
   - Implemented `build_movie_representation`: Formats `title: {title} director: {director} cast: {top 4 cast} genres: {genres} year: {year} themes: {keywords} synopsis: {overview}`.
   - Implemented `build_anime_representation`: Formats `title: {title} genres: {genres} year: {year} episodes: {count} status: {tier} synopsis: {synopsis}`.
   - Implemented `build_book_representation`: Formats `title: {title} author: {author} genres: {genres} characters: {characters} length: {tier} synopsis: {description}`.
   - Robust `clean_str` function safely handling lists, tuples, numpy floats, NaNs, and missing values.
   - Multi-space and comma normalization (`' '.join(val.replace(',', ' ').split())`).
   - Zero hallucination or invented attributes: only verified catalog facts from metadata CSVs and processed pickles are included.
2. **`src/project_black_knight/retrieval.py`:**
   - Updated `RetrievalRepository.get_documents_and_ids(domain, version="v2")` to support representation versioning (`v1_legacy` vs `v2_structured_semantic`).
   - Updated `RetrievalRepository.get_bm25_index(domain, version="v2")` to index domain representations with lazy loading and version-specific caching.
   - Added `representation_version` parameter across `bm25_retrieve`, `rerank_candidates`, `hybrid_retrieve`, and `search_black_knight`, defaulting to `"v2"`.
3. **`tests/test_stage_02_item_representations.py` (New Tests):**
   - 9 dedicated unit and integration tests covering field extraction, missing value safety, determinism, cross-domain isolation, versioning, and repository indexing.
4. **`evaluation/evaluate_stage_02_representations.py` (Evaluation Script):**
   - Full ablation evaluation across 102 benchmark queries with ground truth comparing v1 vs v2 across BM25, Dense ChromaDB, and RRF.

---

## 4. Empirical Evaluation Results

### Candidate Retrieval Recall by Domain (102 Benchmark Queries)
| Domain | Query Count | v1 BM25 Rec@50 | v2 BM25 Rec@50 | v1 BM25 Rec@100 | v2 BM25 Rec@100 | Dense Rec@100 | v1 RRF Rec@100 | v2 RRF Rec@100 | BM25 Rec@100 Delta |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Movie** | 34 | 0.3895 | **0.5445** | 0.4477 | **0.5646** | 0.5983 | 0.6094 | **0.6116** | **+0.1169 (+11.69%)** |
| **Anime** | 35 | 0.4686 | **0.4692** | 0.4852 | **0.4881** | 0.4383 | 0.4726 | **0.4733** | **+0.0029 (+0.29%)** |
| **Book** | 33 | **0.6368** | 0.6217 | **0.6642** | 0.6612 | 0.5877 | 0.6518 | 0.6518 | -0.0030 (-0.30%) |
| **Overall** | **102** | 0.4967 | **0.5436** | 0.5306 | **0.5696** | 0.5400 | 0.5762 | **0.5771** | **+0.0390 (+3.90%)** |

### Indexing & Latency Profile
- **Movie Catalog Indexing Time (4,805 items):** v1 legacy 21.8ms | v2 structured 49.3ms.
- **Anime Catalog Indexing Time (18,336 items):** v1 legacy 68.2ms | v2 structured 136.7ms.
- **Book Catalog Indexing Time (11,230 items):** v1 legacy 43.1ms | v2 structured 94.6ms.
- **BM25 Query Latency (Mean):** 2.2ms per query.
- **Dense ChromaDB Query Latency (Mean):** 11.8ms per query.
- **RRF Fusion Latency (Mean):** 0.1ms per query.

---

## 5. Representative Representation Samples

### Movie (`movie_0` - Avatar)
- **v1 Legacy:** `action adventure fantasy sciencefiction cultureclash future spacewar spacecolony society spacetravel futuristic romance space alien tribe alienplanet cgi marine soldier battle loveaffair antiwar powerrelations mindandsoul 3d in the 22nd century, a paraplegic marine is dispatched to the moon pandora on a unique mission, but becomes torn between following orders and protecting an alien civilization. samworthington zoesaldana sigourneyweaver jamescameron`
- **v2 Structured:** `title: avatar director: james cameron cast: sam worthington zoe saldana sigourney weaver genres: action adventure fantasy science fiction year: 2009 themes: cultureclash future spacewar spacecolony society spacetravel synopsis: in the 22nd century, a paraplegic marine is dispatched to the moon pandora on a unique mission, but becomes torn between following orders and protecting an alien civilization.`

### Anime (`anime_0` - Fullmetal Alchemist: Brotherhood)
- **v1 Legacy:** `military, shounen, action, magic, fantasy, drama, adventure after a horrific alchemy experiment goes wrong in the elric household, brothers edward and alphonse are left in a catastrophic new reality. ignoring the alchemical principle banning human ...`
- **v2 Structured:** `title: fullmetal alchemist: brotherhood genres: military, shounen, action, magic, fantasy, drama, adventure year: 2009 episodes: 64 status: top-tier acclaimed synopsis: after a horrific alchemy experiment goes wrong in the elric household, brothers edward and alphonse are left in a catastrophic new reality. ignoring the alchemical principle banning human ...`

### Book (`book_0` - The Hunger Games)
- **v1 Legacy:** `young adult, fiction, science fiction, dystopia, fantasy, science fiction, romance, adventure, teen, post apocalyptic, action, audio book, dystopian, survival, thriller, future fiction, audio, young adult fantasy, 21st century, literature, war, young adult, young adult romance, drama, american, novels, action adventure, romance, teenage, suspense, speculative fiction, contemporary, scholastic, apocalyptic, science fiction romance, high school, general, dark, fantastic could you survive on your own in the wild, with everyone out to make sure you don't live to see the morning? in the ruins of a place once known as north america lies the nation of panem, a shining capitol surrounded by twelve outlying districts ...`
- **v2 Structured:** `title: the hunger games author: suzanne collins genres: young adult fiction science fiction dystopia fantasy characters: katniss everdeen peeta mellark gale hawthorne length: novella short read synopsis: could you survive on your own in the wild, with everyone out to make sure you don't live to see the morning? in the ruins of a place once known as north america lies the nation of panem, a shining capitol surrounded by twelve outlying districts ...`

---

## 6. Verification and Reproduction
- **Run Unit Tests:**
  `$env:PYTHONPATH='src'; project_black_knight\Scripts\python -m pytest tests/test_stage_02_item_representations.py -v`
- **Run Full Regression Suite:**
  `$env:PYTHONPATH='src'; project_black_knight\Scripts\python -m pytest tests -q`
- **Run Evaluation:**
  `$env:PYTHONPATH='src'; project_black_knight\Scripts\python evaluation/evaluate_stage_02_representations.py`

---

## 7. Next Stage Handoff
- **Stage 2 Status:** `PASS`
- **Stage 3 Starting Point:** Stage 3 focuses on **Candidate Retrieval** (optimizing independent dense and lexical retrieval, tuning candidate pool depth $k$, measuring retriever overlap and incremental coverage, and improving candidate generation prior to reranking).
