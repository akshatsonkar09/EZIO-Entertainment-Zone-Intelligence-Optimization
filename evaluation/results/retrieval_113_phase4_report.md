# Project Black Knight — Phase 4: Comprehensive Hard-Filter Correctness Audit Report

## 1. Executive Summary & Audit Matrix

During Phase 4, an exhaustive audit was performed across all supported hard-filter fields in Project Black Knight. Every filter was audited across catalog domains (`movie`, `anime`, `book`), examining:
- Boundary conditions (inclusive lower/upper bounds, single-sided bounds, zero-width bounds).
- Entity matching semantics (preventing false-positive substring leaks, supporting PascalCase tokens, handling compound names, diacritics, and role annotations).
- Non-conforming and missing metadata handling (`None`, `NaN`, empty strings, boolean coercion bugs, malformed numeric types, float-encoded ISBNs).
- Query representation parity (raw dictionary query, `BlackKnightQuery` schema objects, and production retrieval via `search_black_knight`).

### Hard-Filter Audit Matrix

| Filter Field | Applicable Domains | Input Type | Comparison Semantics | Missing / Invalid Metadata Policy | Parity Verified Across Layers |
|---|---|---|---|---|---|
| `year_min` | Movie, Anime, Book | Integer / Numeric | `item_year >= year_min` (inclusive lower bound) | Excluded if missing, `None`, `NaN`, or unparseable | Raw query, `BlackKnightQuery`, `search_black_knight` |
| `year_max` | Movie, Anime, Book | Integer / Numeric | `item_year <= year_max` (inclusive upper bound) | Excluded if missing, `None`, `NaN`, or unparseable | Raw query, `BlackKnightQuery`, `search_black_knight` |
| `runtime_min` | Movie | Float / Integer (minutes) | `runtime >= runtime_min` (inclusive) | Excluded if missing, `None`, `NaN`, or unparseable | Raw query, `BlackKnightQuery`, `search_black_knight` |
| `runtime_max` | Movie | Float / Integer (minutes) | `runtime <= runtime_max` (inclusive) | Excluded if missing, `None`, `NaN`, or unparseable | Raw query, `BlackKnightQuery`, `search_black_knight` |
| `episodes_min` | Anime | Integer | `episodes >= episodes_min` (inclusive) | Excluded if missing, `None`, `NaN`, or unparseable | Raw query, `BlackKnightQuery`, `search_black_knight` |
| `episodes_max` | Anime | Integer | `episodes <= episodes_max` (inclusive) | Excluded if missing, `None`, `NaN`, or unparseable | Raw query, `BlackKnightQuery`, `search_black_knight` |
| `pages_min` | Book | Integer | `num_pages >= pages_min` (inclusive) | Excluded if missing, `None`, `NaN`, or unparseable | Raw query, `BlackKnightQuery`, `search_black_knight` |
| `pages_max` | Book | Integer | `num_pages <= pages_max` (inclusive) | Excluded if missing, `None`, `NaN`, or unparseable | Raw query, `BlackKnightQuery`, `search_black_knight` |
| `rating_min` | Movie, Anime, Book | Float | `vote_average / score / average_rating >= rating_min` | Excluded if missing, `None`, `NaN`, or unparseable | Raw query, `BlackKnightQuery`, `search_black_knight` |
| `rating_max` | Movie, Anime, Book | Float | `vote_average / score / average_rating <= rating_max` | Excluded if missing, `None`, `NaN`, or unparseable | Raw query, `BlackKnightQuery`, `search_black_knight` |
| `revenue_min` | Movie | Float / Numeric | `revenue >= revenue_min` | Excluded if missing or invalid | Raw query, `BlackKnightQuery`, `search_black_knight` |
| `revenue_max` | Movie | Float / Numeric | `revenue <= revenue_max` | Excluded if missing or invalid | Raw query, `BlackKnightQuery`, `search_black_knight` |
| `popularity_min`| Movie | Float / Numeric | `popularity >= popularity_min` | Excluded if missing or invalid | Raw query, `BlackKnightQuery`, `search_black_knight` |
| `popularity_max`| Movie | Float / Numeric | `popularity <= popularity_max` | Excluded if missing or invalid | Raw query, `BlackKnightQuery`, `search_black_knight` |
| `ranking_min` | Anime | Integer / Numeric | `ranking >= ranking_min` | Excluded if missing or invalid | Raw query, `BlackKnightQuery`, `search_black_knight` |
| `ranking_max` | Anime | Integer / Numeric | `ranking <= ranking_max` | Excluded if missing or invalid | Raw query, `BlackKnightQuery`, `search_black_knight` |
| `director` | Movie | String / List[String] | Exact token-sequence or contiguous name match across discrete entity records | Excluded if empty, `None`, or missing | Raw query, `BlackKnightQuery`, `search_black_knight` |
| `cast` | Movie | String / List[String] | Exact token-sequence or contiguous name match across discrete entity records | Excluded if empty, `None`, or missing | Raw query, `BlackKnightQuery`, `search_black_knight` |
| `production_companies` | Movie | String / List[String] | Exact token-sequence or contiguous company match | Excluded if empty, `None`, or missing | Raw query, `BlackKnightQuery`, `search_black_knight` |
| `author` | Book | String / List[String] | Exact token-sequence / surname match, strips role qualifiers like `(Illustrator)` | Excluded if empty, `None`, or missing | Raw query, `BlackKnightQuery`, `search_black_knight` |
| `publisher` | Book | String / List[String] | Exact token-sequence or contiguous publisher match | Excluded if empty, `None`, or missing | Raw query, `BlackKnightQuery`, `search_black_knight` |
| `characters` | Anime | String / List[String] | Exact token-sequence or contiguous character name match | Excluded if empty, `None`, or missing | Raw query, `BlackKnightQuery`, `search_black_knight` |
| `genres` | Movie, Anime, Book | List[String] | Phase 3B canonicalized mapping, compound requirements, or unsupported bypass | Excluded if empty, unless unsupported genre triggers bypass | Raw query, `BlackKnightQuery`, `search_black_knight` |
| `genres_exclude` | Movie, Anime, Book | List[String] | Strict exclusion: item cannot contain any excluded canonical genre | Passes if field is empty (omission doesn't exclude) | Raw query, `BlackKnightQuery`, `search_black_knight` |
| `isbn` / `isbn13` | Book | String / Numeric | Exact token match after normalizing hyphens, whitespace, and `.0` float artifacts | Excluded if missing or empty | Raw query, `BlackKnightQuery`, `search_black_knight` |
| `media_type` | Anime | String | Exact case-insensitive token match (`TV`, `Movie`, `OVA`) | Excluded if missing or empty | Raw query, `BlackKnightQuery`, `search_black_knight` |

---

## 2. Findings: Confirmed Defects, Severity, Root Cause, and Affected Files

### Defect 1: Unbounded Substring Leaks in Entity Filtering
- **Severity:** High
- **Root Cause:** In `src/project_black_knight/metadata_filter.py`, entity matching previously used `q_norm in c_norm` via `normalize_text_match`. Because `normalize_text_match` stripped all whitespace and punctuation, arbitrary substrings matched inside longer names.
  - Querying cast `"Ian"` matched `"Christian Bale"` (`"ian"` inside `"christianbale"`).
  - Querying author `"Dan"` matched `"Robert Jordan"` (`"dan"` inside `"robertjordan"`).
  - Querying studio `"War"` matched `"Warner Bros."`.
- **Affected File:** `src/project_black_knight/metadata_filter.py`
- **Resolution:** Implemented `clean_entity_text`, `extract_entity_records`, and `match_entity`. Names are partitioned into discrete entity records (handling commas, semicolons, and bracketed roles) and tokenized with PascalCase boundary support (`ChristopherNolan` -> `['christopher', 'nolan']`). Matches require whole-token equality or contiguous multi-word subsequence equality, strictly forbidding substring substring matching.

### Defect 2: Type Fragility on Non-List Entity Inputs
- **Severity:** Medium
- **Root Cause:** Entity filters (`director`, `cast`, `production_companies`, `author`, `characters`) assumed `list[str]`. If a caller or schema passed a single string (e.g., `{"director": "Christopher Nolan"}`), the loop iterated over single characters (`'C'`, `'h'`, `'r'`, ...), causing failed matches or spurious token lookups.
- **Affected File:** `src/project_black_knight/metadata_filter.py`
- **Resolution:** Added defensive normalization for entity and genre fields in `row_matches_filters`: if `isinstance(val, str)`, coerce to `[val]`.

### Defect 3: Python Boolean Coercion Defect in Numeric Filtering
- **Severity:** Medium
- **Root Cause:** In Python, `isinstance(True, int)` is `True`. In `coerce_numeric(val)`, passing `True` yielded `1.0` and `False` yielded `0.0`. A boolean metadata value or flag in numeric columns could accidentally pass numeric filters (e.g., `year_min=1` or `episodes_min=1`).
- **Affected File:** `src/project_black_knight/metadata_filter.py`
- **Resolution:** Added explicit boolean guard in `coerce_numeric`: `if val is None or isinstance(val, bool): return None`.

### Defect 4: Trailing `.0` Float Corruption in ISBN Matching
- **Severity:** Medium
- **Root Cause:** Pandas converts nullable integer columns to `float64`, resulting in stringified values like `"9780887080180.0"`. The existing `normalize_token_str` stripped punctuation but retained the trailing zero, turning it into `"97808870801800"`, causing ISBN lookup failures against standard 10/13-digit ISBN strings.
- **Affected File:** `src/project_black_knight/metadata_filter.py`
- **Resolution:** Implemented `clean_isbn_str` which strips whitespace, hyphens, and any trailing `.0` before string comparison.

### Defect 5: Asymmetric Filter Bounds
- **Severity:** Low
- **Root Cause:** `row_matches_filters` supported `revenue_min` but omitted `revenue_max`; supported `popularity_min` but omitted `popularity_max`; supported `ranking_max` but omitted `ranking_min`; supported `rating_min` but omitted `rating_max`.
- **Affected File:** `src/project_black_knight/metadata_filter.py`
- **Resolution:** Added symmetric bounds for `revenue_max`, `popularity_max`, `ranking_min`, and `rating_max`.

---

## 3. Changes Made

### 1. `src/project_black_knight/metadata_filter.py`
- **`coerce_numeric(val: Any) -> float | None`**: Added guard `if val is None or isinstance(val, bool): return None`.
- **`clean_isbn_str(val: Any) -> str`**: Created dedicated ISBN cleaner that removes hyphens, whitespace, and pandas `.0` float artifacts.
- **`clean_entity_text(text: str) -> str`**: Decomposes Unicode diacritics via NFKD, normalizes smart quotes/apostrophes.
- **`extract_entity_records(candidate_field: str) -> list[str]`**: Splits multiple entities on delimiters `,` and `;`, strips role descriptions like `(Illustrator)` or `(Goodreads Author)`.
- **`match_entity(query_entity: str, candidate_field: str) -> bool`**: Implements exact token sequence and contiguous word-boundary matching with PascalCase boundary support. Prevents unconstrained substring leakage.
- **`row_matches_filters`**:
  - Entity filters (`director`, `cast`, `production_companies`, `author`, `publisher`, `characters`) use `match_entity`.
  - Added string-to-list coercion for all sequence filters.
  - Added symmetric bounds for `rating_max`, `ranking_min`, `popularity_max`, `revenue_max`.
  - ISBN filters use `clean_isbn_str`.

### 2. `src/project_black_knight/__init__.py`
- Exported `match_entity` and `clean_isbn_str` in public package API.

### 3. `tests/test_hard_filter_correctness.py`
- Created comprehensive regression suite containing 20 focused tests covering:
  - All numeric lower/upper boundary conditions (exact, $+1$, $-1$, lower-only, upper-only, zero-interval).
  - Missing, `None`, `NaN`, malformed, and boolean numeric values.
  - Entity token-boundary matching and prevention of substring leakage (`Ian` vs `Christian Bale`, `Dan` vs `Robert Jordan`, `War` vs `Warner Bros.`).
  - PascalCase movie metadata handling (`ChristopherNolan`, `ChristianBale`).
  - Author role annotation stripping (`O. Henry, Lisbeth Zwerger (Illustrator)`).
  - Diacritic normalization (`José` vs `Jose`).
  - ISBN float artifact stripping (`9780887080180.0` vs `9780887080180`).
  - Multi-filter conjunctions and exclusion logic.
  - End-to-end integration through `search_black_knight` for both Architecture A and Architecture B.

---

## 4. Test Suite Execution & Results

### 1. Focused Correctness Tests
```bash
& "project_black_knight\Scripts\python.exe" -m pytest tests\test_hard_filter_correctness.py
```
- **Result:** 20 passed in 18.11s.

### 2. Full Test Suite
```bash
& "project_black_knight\Scripts\python.exe" -m pytest
```
- **Result:** 111 passed in 35.84s:
  - `tests/test_datasets.py`: 4 passed
  - `tests/test_genre_canonicalization.py`: 21 passed
  - `tests/test_hard_filter_correctness.py`: 20 passed
  - `tests/test_hybrid_retrieval.py`: 22 passed
  - `tests/test_metadata_filtering.py`: 13 passed
  - `tests/test_music_removal.py`: 10 passed
  - `tests/test_parser_evaluation.py`: 10 passed
  - `tests/test_query_parser.py`: 2 passed
  - `tests/test_query_schema.py`: 4 passed
  - `tests/test_text_normalizer.py`: 5 passed

---

## 5. Benchmark Comparison: Phase 3B Baseline vs. Phase 4

Evaluated using the established 113-query audited benchmark (`evaluation/black_knight_eval_queries_113_audited.csv`) under full production parity (`candidate_k=60`, cross-encoder blend `0.45 * RRF + 0.55 * CE`).

### Overall Ranking Performance (Positive Queries, N=102)

| Metric | Phase 3B (Arch A) | Phase 4 (Arch A) | Delta (A) | Phase 3B (Arch B) | Phase 4 (Arch B) | Delta (B) |
|---|---:|---:|---:|---:|---:|---:|
| Hit Rate@5 | 0.7353 | 0.7353 | +0.0000 | 0.7353 | 0.7353 | +0.0000 |
| Hit Rate@10 | 0.7647 | 0.7647 | +0.0000 | 0.7549 | 0.7549 | +0.0000 |
| Precision@5 | 0.3549 | 0.3549 | +0.0000 | 0.3529 | 0.3529 | +0.0000 |
| Precision@10 | 0.2833 | 0.2833 | +0.0000 | 0.2814 | 0.2814 | +0.0000 |
| Recall@5 | 0.4690 | 0.4690 | +0.0000 | 0.4665 | 0.4665 | +0.0000 |
| Recall@10 | 0.5313 | 0.5313 | +0.0000 | 0.5239 | 0.5239 | +0.0000 |
| MRR | 0.6426 | 0.6426 | +0.0000 | 0.6287 | 0.6287 | +0.0000 |
| nDCG@5 | 0.6098 | 0.6098 | +0.0000 | 0.6015 | 0.6015 | +0.0000 |
| nDCG@10 | 0.6229 | 0.6229 | +0.0000 | 0.6126 | 0.6126 | +0.0000 |

### Correctness & Integrity Metrics

| Metric | Phase 3B (Arch A) | Phase 4 (Arch A) | Phase 3B (Arch B) | Phase 4 (Arch B) | Status |
|---|---:|---:|---:|---:|---|
| Duplicate-Result Rate | 0.00% | 0.00% | 0.00% | 0.00% | Zero duplicates preserved |
| Hard-Filter Violation Rate | 0.00% | 0.00% | 0.00% | 0.00% | Zero violations preserved |
| Absence Correct Rejection Rate | 100.0% | 100.0% | 100.0% | 100.0% | Perfect rejection preserved |

### Latency Comparison (Milliseconds)

| Metric | Phase 3B (Arch A) | Phase 4 (Arch A) | Phase 3B (Arch B) | Phase 4 (Arch B) |
|---|---:|---:|---:|---:|
| Median / P50 (ms) | 870.1 | 858.2 | 234.1 | 228.5 |
| Mean (ms) | 1167.9 | 1162.8 | 598.0 | 592.2 |
| P95 (ms) | 3280.7 | 3266.2 | 2644.4 | 2588.5 |
| Steady-State Mean (ms) | 1172.0 | 1167.2 | 602.3 | 596.4 |

---

## 6. Unresolved Limitations & Risk Analysis

1. **Catalog PascalCase Formatting in Movie Metadata:**
   The movie dataset (`movie_metadata_clean.csv`) stores directors and cast members concatenated in PascalCase (`ChristopherNolan`, `ChristianBale`). The PascalCase word-boundary tokenizer successfully separates standard names into distinct words (`['christopher', 'nolan']`), but names with internal lowercase/uppercase irregularities or abbreviations without camel casing require exact canonical casing to partition properly.
2. **Initials vs. Expanded Names:**
   In accordance with the prompt's explicit instructions, initials (e.g., `J.K. Rowling` vs `Joanne Rowling`) are not heuristically expanded to full names to avoid cross-person collisions. Only explicit aliases or identical token sequences match. Middle initials (e.g., `George R.R. Martin` vs `George Martin`) are permitted only when all query tokens match the candidate entity record tokens.
3. **Compound Foreign Surnames:**
   Multi-part surnames (e.g., `Gabriel García Márquez`, `Guillermo del Toro`) match either when the full sequence is specified or when the candidate's name tokens match the query's contiguous token sequence. Single short words like `del` alone are prevented from matching arbitrarily.

---

## 7. Final Verdict

**Verdict: PASS**

**Evidence:**
- Every supported numeric constraint (`year`, `runtime`, `episodes`, `pages`, `rating`, `revenue`, `popularity`, `ranking`) was proven inclusive on upper and lower bounds, and correctly excludes invalid/missing/boolean values.
- Entity matching was overhauled to eliminate false-positive substring leaks (`Ian` vs `Christian Bale`), while robustly supporting diacritics, role annotations, and catalog-specific PascalCase tokenization.
- Float-encoded ISBN strings with `.0` artifacts are cleanly handled.
- 100% of tests passed (111/111 across the full suite).
- 113-query benchmark confirms zero ranking regressions, 0.00% duplicate-result rate, 0.00% hard-filter violation rate, and 100.0% absence rejection rate across both Architecture A and Architecture B.
