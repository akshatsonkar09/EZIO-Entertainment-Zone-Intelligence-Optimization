"""
Test full proposed retrieval pipeline changes on the 113-query benchmark.
"""

import json
import math
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from project_black_knight.query_schema import BlackKnightQuery
from project_black_knight.retrieval import (
    RetrievalRepository,
    dense_retrieve,
    bm25_retrieve,
    reciprocal_rank_fusion,
    TITLE_FIELDS,
)
from project_black_knight.metadata_filter import get_valid_ids

def custom_rerank_candidates(
    query_text: str,
    candidate_ids: list[str],
    media_type: str,
    candidate_scores: dict[str, float] | None = None,
    top_k: int = 10,
    repo: RetrievalRepository = None,
    alpha: float = 0.7,
):
    if not candidate_ids or not query_text:
        return [(cid, 0.0) for cid in candidate_ids[:top_k]]

    reranker = repo.get_reranker_model()
    docs, _ = repo.get_documents_and_ids(media_type)
    id_to_idx = repo._id_to_index[media_type]

    df_meta = None
    if media_type == "movie":
        df_meta = repo.get_metadata_df(media_type)
        title_col = TITLE_FIELDS[media_type]

    pairs = []
    valid_cids = []
    for cid in candidate_ids:
        if cid in id_to_idx:
            row_idx = id_to_idx[cid]
            doc_text = docs[row_idx]
            if df_meta is not None and not doc_text.lower().startswith("title:"):
                t_val = str(df_meta.iloc[row_idx][title_col])
                doc_text = f"title: {t_val} {doc_text}"
            pairs.append([query_text, doc_text])
            valid_cids.append(cid)

    if not pairs:
        return []

    scores = reranker.predict(pairs)

    if candidate_scores and len(scores) > 0:
        min_ce = float(min(scores))
        max_ce = float(max(scores))
        ce_range = (max_ce - min_ce) if max_ce > min_ce else 1.0

        rrf_vals = [candidate_scores.get(cid, 0.0) for cid in valid_cids]
        min_r = min(rrf_vals)
        max_r = max(rrf_vals)
        r_range = (max_r - min_r) if max_r > min_r else 1.0

        combined_scores = []
        for cid, raw_ce in zip(valid_cids, scores):
            norm_ce = (float(raw_ce) - min_ce) / ce_range
            norm_r = (candidate_scores.get(cid, 0.0) - min_r) / r_range
            final_s = alpha * norm_ce + (1.0 - alpha) * norm_r
            combined_scores.append(final_s)

        ranked = sorted(
            zip(valid_cids, combined_scores),
            key=lambda x: (-x[1], str(x[0])),
        )
    else:
        ranked = sorted(
            zip(valid_cids, [float(s) for s in scores]),
            key=lambda x: (-x[1], str(x[0])),
        )

    return ranked[:top_k]

def custom_hybrid_retrieve(
    query: str,
    media_type: str,
    filters: dict = None,
    similar_to: list = None,
    top_k: int = 10,
    candidate_k: int = 60,
    repo: RetrievalRepository = None,
):
    df_meta = repo.get_metadata_df(media_type)
    _, item_ids = repo.get_documents_and_ids(media_type)

    valid_ids = get_valid_ids(
        dataframe=df_meta,
        current_ids=item_ids,
        filters=filters or {},
        media_type=media_type,
    )
    if not valid_ids:
        return []

    effective_query = query.strip() if query else ""
    excluded_seed_ids = set()

    if similar_to:
        for seed_title in similar_to:
            from project_black_knight.retrieval import resolve_similar_seed
            resolved = resolve_similar_seed(seed_title, target_domain=media_type, repo=repo)
            if resolved:
                if resolved["domain"] == media_type:
                    excluded_seed_ids.add(resolved["item_id"])
                seed_doc = resolved["doc_text"]
                if not effective_query:
                    effective_query = seed_doc
                else:
                    effective_query = f"{effective_query} {seed_doc}"

    effective_valid_ids = valid_ids - excluded_seed_ids
    if not effective_valid_ids:
        return []

    if not effective_query:
        if filters.get("title"):
            effective_query = str(filters["title"])
        else:
            effective_query = "popular recommended entertainment"

    dense_results = dense_retrieve(
        query_text=effective_query,
        media_type=media_type,
        valid_ids=effective_valid_ids,
        top_k=candidate_k,
        repo=repo,
    )

    bm25_results = bm25_retrieve(
        query_text=effective_query,
        media_type=media_type,
        valid_ids=effective_valid_ids,
        top_k=candidate_k,
        repo=repo,
    )

    rrf_fused = reciprocal_rank_fusion(
        result_lists=[
            [c["id"] for c in dense_results],
            [c["id"] for c in bm25_results],
        ],
        k=60,
        top_k=candidate_k,
    )

    if not rrf_fused:
        candidate_ids = list(effective_valid_ids)[:candidate_k]
        candidate_scores = None
    else:
        candidate_ids = [cid for cid, s in rrf_fused]
        candidate_scores = dict(rrf_fused)

    reranked = custom_rerank_candidates(
        query_text=effective_query,
        candidate_ids=candidate_ids,
        media_type=media_type,
        candidate_scores=candidate_scores,
        top_k=top_k,
        repo=repo,
        alpha=0.7,
    )

    id_to_idx = repo._id_to_index[media_type]
    title_col = TITLE_FIELDS[media_type]

    final_results = []
    for item_id, score in reranked:
        row_idx = id_to_idx[item_id]
        row_data = df_meta.iloc[row_idx]
        final_results.append({
            "id": item_id,
            "title": str(row_data[title_col]),
            "media_type": media_type,
            "score": round(float(score), 4),
        })

    return final_results

def custom_search_black_knight(parsed_query, top_k=10, repo=None):
    all_domain_results = []
    for media_type in parsed_query.media_types:
        common = parsed_query.common
        domain_queries = parsed_query.domain_queries
        semantic_query = parsed_query.semantic_query
        similar_to = parsed_query.similar_to

        filters = {
            "title": common.title,
            "genres_include": common.genres_include,
            "genres_exclude": common.genres_exclude,
            "release_year_min": common.release_year_min,
            "release_year_max": common.release_year_max,
        }
        domain_query = getattr(domain_queries, media_type, None)
        if domain_query is not None:
            filters.update(domain_query.model_dump(exclude_none=True))

        domain_results = custom_hybrid_retrieve(
            query=semantic_query,
            media_type=media_type,
            filters=filters,
            similar_to=similar_to,
            top_k=top_k,
            candidate_k=60,
            repo=repo,
        )
        all_domain_results.extend(domain_results)

    all_domain_results.sort(key=lambda x: x["score"], reverse=True)
    return all_domain_results[:top_k]

def compute_metrics(ranked_ids, relevant_ids):
    n_rel = len(relevant_ids)
    if n_rel == 0:
        return 0.0, 0.0, 0.0, 0.0
    hits_5 = sum(1 for x in ranked_ids[:5] if x in relevant_ids)
    hits_10 = sum(1 for x in ranked_ids[:10] if x in relevant_ids)
    hr5 = 1.0 if hits_5 > 0 else 0.0
    hr10 = 1.0 if hits_10 > 0 else 0.0
    mrr = 0.0
    for r, item in enumerate(ranked_ids[:10], 1):
        if item in relevant_ids:
            mrr = 1.0 / r
            break
    dcg_10 = sum((1.0 / math.log2(i + 1.0)) for i, item in enumerate(ranked_ids[:10], 1) if item in relevant_ids)
    idcg_10 = sum((1.0 / math.log2(i + 1.0)) for i in range(1, min(n_rel, 10) + 1))
    ndcg10 = (dcg_10 / idcg_10) if idcg_10 > 0 else 0.0
    return hr5, hr10, mrr, ndcg10

def main():
    repo = RetrievalRepository()
    df_eval = pd.read_csv(PROJECT_ROOT / "evaluation" / "black_knight_eval_queries_113_audited.csv")
    cases = df_eval.to_dict("records")

    print(f"Running full evaluation over all {len(cases)} benchmark queries...")
    pos_cases = [c for c in cases if json.loads(c["relevant_ids"]) != []]
    abs_cases = [c for c in cases if json.loads(c["relevant_ids"]) == []]

    hr5_list, hr10_list, mrr_list, ndcg_list = [], [], [], []
    dom_hr10 = {"movie": [], "anime": [], "book": []}
    dom_mrr = {"movie": [], "anime": [], "book": []}

    for case in pos_cases:
        dom = case["domain"]
        rel_ids = set(json.loads(case["relevant_ids"]))
        parsed = json.loads(case["expected_parse"])
        q_obj = BlackKnightQuery.model_validate(parsed)

        results = custom_search_black_knight(q_obj, top_k=10, repo=repo)
        ranked_ids = [r["id"] for r in results]

        hr5, hr10, mrr, ndcg10 = compute_metrics(ranked_ids, rel_ids)
        hr5_list.append(hr5)
        hr10_list.append(hr10)
        mrr_list.append(mrr)
        ndcg_list.append(ndcg10)
        dom_hr10[dom].append(hr10)
        dom_mrr[dom].append(mrr)

    correct_rejections = 0
    for case in abs_cases:
        parsed = json.loads(case["expected_parse"])
        q_obj = BlackKnightQuery.model_validate(parsed)
        results = custom_search_black_knight(q_obj, top_k=10, repo=repo)
        if len(results) == 0:
            correct_rejections += 1

    print("\n==================== EVALUATION OF PROPOSED PIPELINE ====================")
    print(f"Positive Queries (N={len(pos_cases)}):")
    print(f"  Hit Rate@5:  {np.mean(hr5_list):.4f} (Baseline: 0.7353)")
    print(f"  Hit Rate@10: {np.mean(hr10_list):.4f} (Baseline: 0.7647)")
    print(f"  MRR:         {np.mean(mrr_list):.4f} (Baseline: 0.6254)")
    print(f"  nDCG@10:     {np.mean(ndcg_list):.4f} (Baseline: 0.6169)")
    print(f"\nPer-Domain Hit Rate@10 & MRR:")
    for d in ["movie", "anime", "book"]:
        print(f"  {d.capitalize()}: HR@10={np.mean(dom_hr10[d]):.4f}, MRR={np.mean(dom_mrr[d]):.4f}")
    print(f"\nAbsence Queries (N={len(abs_cases)}):")
    print(f"  Correct Rejections: {correct_rejections}/{len(abs_cases)} ({correct_rejections/len(abs_cases)*100:.1f}%)")

if __name__ == "__main__":
    main()
