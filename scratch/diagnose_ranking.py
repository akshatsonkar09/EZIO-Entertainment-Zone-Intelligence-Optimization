"""
Targeted Diagnostic Script for Phase 2: RRF & Cross-Encoder Retrieval Quality
"""

import json
import sys
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from project_black_knight.query_schema import BlackKnightQuery
from project_black_knight.retrieval import (
    RetrievalRepository,
    dense_retrieve,
    bm25_retrieve,
    reciprocal_rank_fusion,
    rerank_candidates,
    search_black_knight,
)
from project_black_knight.metadata_filter import get_valid_ids

def main():
    repo = RetrievalRepository()
    baseline_json = PROJECT_ROOT / "evaluation" / "results" / "retrieval_113_baseline_report.json"
    with open(baseline_json, "r", encoding="utf-8") as f:
        baseline_data = json.load(f)

    per_query = baseline_data["per_query_results"]

    print("=== 1. CROSS-ENCODER REGRESSIONS VS RRF ===")
    regressions = []
    for q in per_query:
        if q["is_absence_query"]:
            continue
        rrf_hit10 = q["rrf"]["hit_rate_at_10"]
        rerank_hit10 = q["reranked"]["hit_rate_at_10"]
        rrf_mrr = q["rrf"]["mrr"]
        rerank_mrr = q["reranked"]["mrr"]

        if rerank_hit10 < rrf_hit10 or rerank_mrr < rrf_mrr:
            regressions.append(q)

    print(f"Total positive queries with Cross-Encoder regression: {len(regressions)} / 102")
    by_dom = {}
    for r in regressions:
        by_dom[r["domain"]] = by_dom.get(r["domain"], 0) + 1
    print(f"Regressions by domain: {by_dom}")

    print("\nDetailed list of regressions where Hit@10 dropped:")
    hit10_drops = [r for r in regressions if r["reranked"]["hit_rate_at_10"] < r["rrf"]["hit_rate_at_10"]]
    print(f"Total Hit@10 drops: {len(hit10_drops)}")
    for r in hit10_drops:
        print(f"[{r['query_id']}] ({r['domain']}) '{r['query_text']}'")
        print(f"   Relevant IDs: {r['relevant_ids']}")
        print(f"   RRF top 10: {r['rrf']['ranked_ids']}")
        print(f"   Rerank top 10: {r['reranked']['ranked_ids']}")
        print(f"   RRF hits@10: {r['rrf']['hits_at_10']}, Rerank hits@10: {r['reranked']['hits_at_10']}")

    print("\n=== 2. DOCUMENT TEXT ANALYSIS ===")
    for dom in ["movie", "anime", "book"]:
        docs, ids = repo.get_documents_and_ids(dom)
        meta = repo.get_metadata_df(dom)
        print(f"\nDomain: {dom} (Total docs: {len(docs)})")
        print(f"Columns in metadata: {list(meta.columns)}")
        print(f"Sample doc_text[0] (length {len(docs[0])}):\n{docs[0][:300]}...")
        if len(docs) > 1:
            print(f"Sample doc_text[1] (length {len(docs[1])}):\n{docs[1][:300]}...")

    print("\n=== 3. DEEP DIVE INTO ANIME REGRESSIONS ===")
    for r in hit10_drops:
        if r["domain"] == "anime":
            qid = r["query_id"]
            print(f"\nAnalyzing {qid}: '{r['query_text']}'")
            # Let's inspect the RRF candidate pool and cross-encoder scores
            parsed_dict = json.loads(pd.read_csv(PROJECT_ROOT / "evaluation" / "black_knight_eval_queries_113_audited.csv").set_index("query_id").loc[qid, "expected_parse"])
            q_obj = BlackKnightQuery.model_validate(parsed_dict)
            
            # Run hybrid_retrieve step by step
            df_meta = repo.get_metadata_df("anime")
            docs, ids = repo.get_documents_and_ids("anime")
            id_to_idx = repo._id_to_index["anime"]
            
            eff_q = q_obj.semantic_query or ""
            d_res = dense_retrieve(eff_q, "anime", top_k=30, repo=repo)
            b_res = bm25_retrieve(eff_q, "anime", top_k=30, repo=repo)
            rrf_res = reciprocal_rank_fusion([[c["id"] for c in d_res], [c["id"] for c in b_res]], k=60, top_k=30)
            
            rel_ids = set(r["relevant_ids"])
            print(f"Relevant IDs: {rel_ids}")
            for item in rel_ids:
                idx = id_to_idx.get(item)
                title = df_meta.iloc[idx]["title"] if idx is not None else "UNKNOWN"
                d_rank = next((c["rank"] for c in d_res if c["id"] == item), "NOT IN TOP 30")
                b_rank = next((c["rank"] for c in b_res if c["id"] == item), "NOT IN TOP 30")
                rrf_rank = next((i+1 for i, (cid, s) in enumerate(rrf_res) if cid == item), "NOT IN TOP 30")
                print(f"  Target '{title}' ({item}): Dense rank={d_rank}, BM25 rank={b_rank}, RRF rank={rrf_rank}")
                if idx is not None:
                    print(f"  Doc text: {docs[idx][:200]}...")
            
            # Now let's see Cross-Encoder scoring on all 30 RRF candidates
            cand_ids = [cid for cid, s in rrf_res]
            pairs = [[eff_q, docs[id_to_idx[cid]]] for cid in cand_ids]
            ce_model = repo.get_reranker_model()
            ce_scores = ce_model.predict(pairs)
            ce_ranked = sorted(zip(cand_ids, ce_scores), key=lambda x: (x[1], x[0]), reverse=True)
            print("  Top 10 Cross-Encoder candidates:")
            for rank, (cid, score) in enumerate(ce_ranked[:10], start=1):
                is_hit = "*" if cid in rel_ids else " "
                c_title = df_meta.iloc[id_to_idx[cid]]["title"]
                print(f"    {is_hit} Rank {rank}: {cid} ({score:.4f}) - '{c_title}'")
            print("  Ranks of relevant IDs in Cross-Encoder:")
            for item in rel_ids:
                ce_rank = next((i+1 for i, (cid, s) in enumerate(ce_ranked) if cid == item), "NOT IN CANDIDATES")
                print(f"    Target {item}: Cross-Encoder rank={ce_rank}")

if __name__ == "__main__":
    main()
