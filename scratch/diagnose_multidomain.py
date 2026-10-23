"""
Diagnostic 3: Cross-Encoder Score Distribution Across Domains & Multi-Domain Interleaving
"""

import json
import sys
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from project_black_knight.query_schema import BlackKnightQuery
from project_black_knight.retrieval import RetrievalRepository, search_black_knight

def main():
    repo = RetrievalRepository()
    df_eval = pd.read_csv(PROJECT_ROOT / "evaluation" / "black_knight_eval_queries_113_audited.csv")
    
    # Check all MD_* queries
    md_queries = df_eval[df_eval["query_id"].str.startswith("MD_")]
    print(f"Total Multi-Domain Queries: {len(md_queries)}")
    
    for _, row in md_queries.iterrows():
        qid = row["query_id"]
        qtext = row["query_text"]
        rel_ids = json.loads(row["relevant_ids"])
        parsed_dict = json.loads(row["expected_parse"])
        q_obj = BlackKnightQuery.model_validate(parsed_dict)
        
        res = search_black_knight(parsed_query=q_obj, top_k=10, repo=repo)
        top10 = res["results"]
        
        dom_counts = {}
        for r in top10:
            dom = r["media_type"]
            dom_counts[dom] = dom_counts.get(dom, 0) + 1
            
        hits = [r["id"] for r in top10 if r["id"] in rel_ids]
        print(f"\n[{qid}] '{qtext}'")
        print(f"  Target domains requested: {q_obj.media_types}")
        print(f"  Top 10 domain distribution: {dom_counts}")
        print(f"  Hits in top 10: {hits} / {rel_ids}")
        print(f"  Top 10 results:")
        for rank, r in enumerate(top10, 1):
            is_hit = "*" if r["id"] in rel_ids else " "
            print(f"    {is_hit} Rank {rank}: [{r['media_type']}] {r['id']} ({r['score']}) - '{r['title']}'")
        
        # Check per-domain results before combined sort
        per_dom = res["per_domain_results"]
        for d, d_list in per_dom.items():
            scores = [x["score"] for x in d_list]
            d_hits = [x["id"] for x in d_list if x["id"] in rel_ids]
            print(f"    Domain {d}: count={len(d_list)}, hits={d_hits}, score_range=[{min(scores) if scores else None}, {max(scores) if scores else None}]")

if __name__ == "__main__":
    main()
