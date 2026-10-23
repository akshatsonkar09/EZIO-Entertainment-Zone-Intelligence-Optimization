"""
Detailed Diagnostic 2: Inspect Candidate Pools and Ranking Failures
"""

import json
import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from project_black_knight.query_schema import BlackKnightQuery
from project_black_knight.retrieval import RetrievalRepository, hybrid_retrieve, search_black_knight

def main():
    repo = RetrievalRepository()
    df_eval = pd.read_csv(PROJECT_ROOT / "evaluation" / "black_knight_eval_queries_113_audited.csv")
    
    # We want to check all queries where reranked Hit@10 is 0 or less than 1.0 (for single target) or has missed targets
    baseline_json = PROJECT_ROOT / "evaluation" / "results" / "retrieval_113_baseline_report.json"
    with open(baseline_json, "r", encoding="utf-8") as f:
        baseline_data = json.load(f)
        
    per_query = {q["query_id"]: q for q in baseline_data["per_query_results"]}
    
    # Group queries by domain
    domain_queries = {"movie": [], "anime": [], "book": []}
    for _, row in df_eval.iterrows():
        domain_queries[row["domain"]].append(row)
        
    print("=== SUMMARY OF MISSED QUERIES (Hit@10 == 0) IN RERANKED HYBRID ===")
    for dom in ["movie", "anime", "book"]:
        missed = []
        for row in domain_queries[dom]:
            qid = row["query_id"]
            q_res = per_query[qid]
            if not q_res["is_absence_query"] and q_res["reranked"]["hit_rate_at_10"] == 0:
                missed.append((qid, row["category"], row["query_text"], q_res["relevant_ids"]))
        print(f"\nDomain: {dom} - Missed in Reranked Top 10: {len(missed)} queries")
        for qid, cat, text, rel in missed:
            print(f"  [{qid}] ({cat}) '{text}' -> targets: {rel}")

    # Now let's trace: For each missed query, at what stage is the target lost?
    # Stage A: In DB (valid_ids)?
    # Stage B: In Dense Top 30?
    # Stage C: In BM25 Top 30?
    # Stage D: In RRF Top 30?
    # Stage E: In RRF Top 30 but ranked > 10 by Cross-Encoder?
    print("\n=== FAILURE STAGE ATTRIBUTION FOR MISSED QUERIES ===")
    stage_counts = {
        "movie": {"not_in_valid_ids": 0, "not_in_dense_or_bm25_30": 0, "in_dense_or_bm25_not_in_rrf_30": 0, "in_rrf_30_demoted_by_ce": 0},
        "anime": {"not_in_valid_ids": 0, "not_in_dense_or_bm25_30": 0, "in_dense_or_bm25_not_in_rrf_30": 0, "in_rrf_30_demoted_by_ce": 0},
        "book": {"not_in_valid_ids": 0, "not_in_dense_or_bm25_30": 0, "in_dense_or_bm25_not_in_rrf_30": 0, "in_rrf_30_demoted_by_ce": 0},
    }

    for _, row in df_eval.iterrows():
        qid = row["query_id"]
        dom = row["domain"]
        q_res = per_query[qid]
        if q_res["is_absence_query"]:
            continue
        
        parsed_dict = json.loads(row["expected_parse"])
        q_obj = BlackKnightQuery.model_validate(parsed_dict)
        rel_ids = set(q_res["relevant_ids"])
        
        # Execute hybrid retrieve with diagnostics
        common = q_obj.common
        domain_queries_obj = q_obj.domain_queries
        dom_q = getattr(domain_queries_obj, dom, None)
        filters = {
            "title": common.title,
            "genres_include": common.genres_include,
            "genres_exclude": common.genres_exclude,
            "release_year_min": common.release_year_min,
            "release_year_max": common.release_year_max,
        }
        if dom_q is not None:
            filters.update(dom_q.model_dump(exclude_none=True))
            
        final_results, diag = hybrid_retrieve(
            query=q_obj.semantic_query,
            media_type=dom,
            filters=filters,
            similar_to=q_obj.similar_to,
            top_k=10,
            candidate_k=30,
            repo=repo,
            collect_diagnostics=True,
        )
        
        retrieved_ids = [r["id"] for r in final_results]
        hits_10 = [x for x in retrieved_ids if x in rel_ids]
        
        if len(hits_10) == 0:
            # Diagnose failure stage
            df_meta = repo.get_metadata_df(dom)
            docs, ids = repo.get_documents_and_ids(dom)
            
            # Check valid_ids
            from project_black_knight.metadata_filter import get_valid_ids
            valid_ids = get_valid_ids(df_meta, ids, filters, dom)
            if q_obj.similar_to:
                # seeds
                from project_black_knight.retrieval import resolve_similar_seed
                for s in q_obj.similar_to:
                    res_s = resolve_similar_seed(s, dom, repo)
                    if res_s and res_s["domain"] == dom:
                        valid_ids.discard(res_s["item_id"])
                        
            missing_targets = rel_ids - set(retrieved_ids)
            # Check if any target was in valid_ids
            in_valid = missing_targets.intersection(valid_ids)
            if not in_valid:
                stage_counts[dom]["not_in_valid_ids"] += 1
                print(f"[{qid}] ({dom}) Targets {rel_ids} NOT in valid_ids! (Filter or seed excluded)")
                continue
                
            # Check dense & bm25
            eff_q = diag.get("effective_retrieval_query", q_obj.semantic_query or "")
            from project_black_knight.retrieval import dense_retrieve, bm25_retrieve, reciprocal_rank_fusion
            d_res = dense_retrieve(eff_q, dom, valid_ids=valid_ids, top_k=30, repo=repo)
            b_res = bm25_retrieve(eff_q, dom, valid_ids=valid_ids, top_k=30, repo=repo)
            d_ids = [c["id"] for c in d_res]
            b_ids = [c["id"] for c in b_res]
            
            in_d_or_b = in_valid.intersection(set(d_ids) | set(b_ids))
            if not in_d_or_b:
                stage_counts[dom]["not_in_dense_or_bm25_30"] += 1
                print(f"[{qid}] ({dom}) Targets {in_valid} in DB but NOT in Dense(30) or BM25(30). Dense top 3: {d_ids[:3]}, BM25 top 3: {b_ids[:3]}")
                continue
                
            # Check RRF
            rrf_res = reciprocal_rank_fusion([d_ids, b_ids], k=60, top_k=30)
            rrf_ids = [cid for cid, s in rrf_res]
            in_rrf = in_valid.intersection(set(rrf_ids))
            if not in_rrf:
                stage_counts[dom]["in_dense_or_bm25_not_in_rrf_30"] += 1
                print(f"[{qid}] ({dom}) Targets {in_d_or_b} in Dense/BM25 but DROPPED by RRF top 30!")
                continue
                
            # If in RRF top 30, then Cross-Encoder demoted it past rank 10!
            stage_counts[dom]["in_rrf_30_demoted_by_ce"] += 1
            print(f"[{qid}] ({dom}) Targets {in_rrf} in RRF top 30 (RRF ranks: {[rrf_ids.index(t)+1 for t in in_rrf]}), but DEMOTED by Cross-Encoder below top 10!")

    print("\nStage breakdown counts:")
    print(json.dumps(stage_counts, indent=2))

if __name__ == "__main__":
    main()
