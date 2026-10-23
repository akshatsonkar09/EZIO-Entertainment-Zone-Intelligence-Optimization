import json
import pandas as pd
from project_black_knight.query_schema import BlackKnightQuery
from project_black_knight.retrieval import RetrievalRepository, search_black_knight

repo = RetrievalRepository()
bench = pd.read_csv('evaluation/black_knight_eval_queries_113_audited.csv')

with open('evaluation/results/experiment_1_report.json', 'r') as f:
    rep = json.load(f)

cases = rep['per_query_results']
failures = [c for c in cases if not c.get('is_absence_query') and c['architecture_b']['hit_rate_at_10'] == 0]

print(f"Total zero-hit queries at k=10 in Architecture B: {len(failures)}")
for f in failures:
    qid = f['query_id']
    cat = f['category']
    dom = f['domain']
    text = f['query_text']
    rel = f['relevant_ids']
    
    # Classify cause
    row = bench[bench['query_id'] == qid].iloc[0]
    p = json.loads(row['expected_parse'])
    sim = p.get('similar_to', [])
    
    cause = "Unknown"
    notes = ""
    
    if qid == 'KI_016':
        cause = "Benchmark-label issue"
        notes = "Expected anime_732 (Gurren Lagann), true entity is anime_745 (Code Geass)"
    elif qid == 'KI_023':
        cause = "Benchmark-label issue"
        notes = "Expected book_10435 ('Revealed' by Tamera Alexander), true entity is book_3338 ('Mansfield Park')"
    elif qid == 'MD_005':
        cause = "Benchmark-label issue"
        notes = "Expected movie_96 ('Inception' by Nolan) for query asking for Hayao Miyazaki films"
    elif cat == 'similar_to':
        # Check if seed item is in rel
        # Find resolved seed item ID
        if sim:
            from project_black_knight.retrieval import resolve_similar_seed
            res_s = resolve_similar_seed(sim[0], dom, repo)
            seed_id = res_s['item_id'] if res_s else None
            if seed_id in rel:
                cause = "Benchmark contract issue / Seed exclusion"
                notes = f"Ground truth expects seed entity itself ({seed_id}: {sim[0]}), which is correctly excluded by recommendation contract"
            else:
                cause = "Retrieval/candidate-generation failure"
                notes = f"Semantic/thematic disconnect between seed overview and labeled targets"
    elif cat == 'multi_domain':
        cause = "Benchmark-label / Cross-domain candidate generation"
        notes = "Cross-domain candidate balance and benchmark target subjectivity"
    elif qid == 'DE_011':
        cause = "Retrieval/candidate-generation failure"
        notes = "Vocabulary mismatch: query says 'robots' / 'Angels', anime_573 synopsis says 'giant machines' / 'Evangelions'"
    elif qid == 'DE_023':
        cause = "Retrieval/candidate-generation failure (RRF bypass cutoff)"
        notes = "book_530 in BM25 rank 28, but dense rank 113 pulls RRF rank to 54, truncated by top_k=10"
        
    print(f"[{qid}] ({dom} / {cat}): {text}")
    print(f"  Cause: {cause}")
    print(f"  Notes: {notes}")
    print(f"  Expected: {rel}\n")
