# Project Black Knight — Phase 5 Known Issues and Diagnostics Analysis

## 1. Verified Defect & Demotion Patterns

1. **Cross-Encoder Domain Gap on Books:**
   - The MS-MARCO MiniLM cross-encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`) was trained on web search query-passage pairs. When applied to books, it occasionally demotes high-consensus title/author matches below generic topical books.
   - *Evidence:* Architecture B (RRF-only for books) avoids these demotions and yields faster execution (228ms vs 858ms median latency).

2. **Lexical BM25 Misses on Abstract Semantic Queries:**
   - Queries describing abstract moods, philosophical themes, or vibe without specific plot keywords frequently miss BM25 retrieval (BM25 score = 0), relying entirely on Dense ChromaDB embeddings.
   - *Evidence:* In thematic categories, dense retrieval recovered 100% of the surviving candidates.

3. **Candidate Truncation at Cutoff (Ranks 6–10 vs Top 5):**
   - The largest single category of 'misses' at Hit@5 is `rank_cutoff_top5`: the relevant item was correctly retrieved in the top 10 (ranks 6–9), but fell just outside the top-5 window.
   - *Evidence:* Hit@10 is consistently 3–4% higher than Hit@5 across all architectures.

## 2. Unresolved Limitations

- **Catalog Sparsity in Anime Character Lists:** Anime character filters rely on comma-delimited strings in `anime_metadata_clean.csv`. Minor secondary characters absent from the top 5 listed characters in the catalog cannot be matched.
- **Book ISBN Formatting Inconsistencies:** Some historical book records have unpadded 10-digit ISBNs without leading zeros. While `clean_isbn_str` normalizes floats and hyphens, unpadded 9-character entries require length-aware padding.
