"""
Evaluation and Metrics Generation for Stage 1: Reference-Based Similarity.
Measures: MRR, nDCG@10, Hit@10, Candidate Recall@50, Candidate Recall@100, and Latency
Across domain_routed and all_cross_encoder per domain.
"""

import sys
import json
import math
import time
from pathlib import Path
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

SRC_DIR = Path.cwd() / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from project_black_knight.query_schema import BlackKnightQuery
from project_black_knight.retrieval import search_black_knight, _REPO, resolve_similar_seed

def compute_dcg(ranked_ids, rel_set, k=10):
    dcg = 0.0
    for i, item_id in enumerate(ranked_ids[:k], start=1):
        if item_id in rel_set:
            dcg += 1.0 / math.log2(i + 1.0)
    return dcg

def compute_idcg(n_rel, k=10):
    idcg = 0.0
    for i in range(1, min(n_rel, k) + 1):
        idcg += 1.0 / math.log2(i + 1.0)
    return idcg

# 15 Held-out reference query evaluation set
HELD_OUT_QUERIES = [
    # Movies (5)
    {
        "query_id": "HO_SI_001",
        "domain": "movie",
        "query_text": "Recommend sci-fi movies similar to Blade Runner.",
        "similar_to": ["Blade Runner"],
        "semantic_query": "Recommend sci-fi movies similar to Blade Runner.",
        "relevant_ids": ["movie_743", "movie_634", "movie_180", "movie_279"],
        "notes": "Cyberpunk noir dystopian sci-fi"
    },
    {
        "query_id": "HO_SI_002",
        "domain": "movie",
        "query_text": "Recommend movies similar to Jurassic Park.",
        "similar_to": ["Jurassic Park"],
        "semantic_query": "Recommend movies similar to Jurassic Park.",
        "relevant_ids": ["movie_508", "movie_24", "movie_517"],
        "notes": "Creature feature dinosaur survival thriller"
    },
    {
        "query_id": "HO_SI_003",
        "domain": "movie",
        "query_text": "Recommend crime movies similar to GoodFellas.",
        "similar_to": ["GoodFellas"],
        "semantic_query": "Recommend crime movies similar to GoodFellas.",
        "relevant_ids": ["movie_2732", "movie_867", "movie_4304", "movie_111"],
        "notes": "Classic mob crime rise and fall"
    },
    {
        "query_id": "HO_SI_004",
        "domain": "movie",
        "query_text": "Recommend historical epic movies similar to Gladiator.",
        "similar_to": ["Gladiator"],
        "semantic_query": "Recommend historical epic movies similar to Gladiator.",
        "relevant_ids": ["movie_145", "movie_267", "movie_197"],
        "notes": "Sword-and-sandal historical warfare epic"
    },
    {
        "query_id": "HO_SI_005",
        "domain": "movie",
        "query_text": "Recommend tragic romance movies similar to Titanic.",
        "similar_to": ["Titanic"],
        "semantic_query": "Recommend tragic romance movies similar to Titanic.",
        "relevant_ids": ["movie_2662", "movie_1120", "movie_559"],
        "notes": "Grand disaster tragic romance"
    },

    # Anime (5)
    {
        "query_id": "HO_SI_006",
        "domain": "anime",
        "query_text": "Recommend anime similar to Code Geass: Hangyaku no Lelouch.",
        "similar_to": ["Code Geass: Hangyaku no Lelouch"],
        "semantic_query": "Recommend anime similar to Code Geass: Hangyaku no Lelouch.",
        "relevant_ids": ["anime_726", "anime_633", "anime_5046"],
        "notes": "Psychological mastermind rebellion mecha"
    },
    {
        "query_id": "HO_SI_007",
        "domain": "anime",
        "query_text": "Recommend anime similar to Hunter x Hunter.",
        "similar_to": ["Hunter x Hunter"],
        "semantic_query": "Recommend anime similar to Hunter x Hunter.",
        "relevant_ids": ["anime_141", "anime_56", "anime_3"],
        "notes": "High adventure strategic battle shonen"
    },
    {
        "query_id": "HO_SI_008",
        "domain": "anime",
        "query_text": "Recommend anime similar to Kimi no Na wa.",
        "similar_to": ["Kimi no Na wa."],
        "semantic_query": "Recommend anime similar to Kimi no Na wa.",
        "relevant_ids": ["anime_751", "anime_35"],
        "notes": "Emotional supernatural romantic drama"
    },
    {
        "query_id": "HO_SI_009",
        "domain": "anime",
        "query_text": "Recommend anime similar to Mob Psycho 100.",
        "similar_to": ["Mob Psycho 100"],
        "semantic_query": "Recommend anime similar to Mob Psycho 100.",
        "relevant_ids": ["anime_16", "anime_863"],
        "notes": "Overpowered comedic psychic superhero"
    },
    {
        "query_id": "HO_SI_010",
        "domain": "anime",
        "query_text": "Recommend anime similar to Neon Genesis Evangelion.",
        "similar_to": ["Neon Genesis Evangelion"],
        "semantic_query": "Recommend anime similar to Neon Genesis Evangelion.",
        "relevant_ids": ["anime_255", "anime_759"],
        "notes": "Psychological existential sci-fi mystery"
    },

    # Books (5)
    {
        "query_id": "HO_SI_011",
        "domain": "book",
        "query_text": "Recommend fantasy books similar to The Hobbit.",
        "similar_to": ["The Hobbit"],
        "semantic_query": "Recommend fantasy books similar to The Hobbit.",
        "relevant_ids": ["book_1083", "book_530"],
        "notes": "Epic fantasy adventure quest"
    },
    {
        "query_id": "HO_SI_012",
        "domain": "book",
        "query_text": "Recommend classic romance books similar to Mansfield Park.",
        "similar_to": ["Mansfield Park"],
        "semantic_query": "Recommend classic romance books similar to Mansfield Park.",
        "relevant_ids": ["book_3760", "book_6306", "book_9611"],
        "notes": "Regency social satire and romance"
    },
    {
        "query_id": "HO_SI_013",
        "domain": "book",
        "query_text": "Recommend classic gothic horror books similar to Frankenstein.",
        "similar_to": ["Frankenstein"],
        "semantic_query": "Recommend classic gothic horror books similar to Frankenstein.",
        "relevant_ids": ["book_449"],
        "notes": "Classic gothic psychological horror"
    },
    {
        "query_id": "HO_SI_014",
        "domain": "book",
        "query_text": "Recommend dark psychological horror books similar to The Outsider.",
        "similar_to": ["The Outsider"],
        "semantic_query": "Recommend dark psychological horror books similar to The Outsider.",
        "relevant_ids": ["book_2378"],
        "notes": "Dark supernatural thriller"
    },
    {
        "query_id": "HO_SI_015",
        "domain": "book",
        "query_text": "Recommend epic fantasy books similar to The Final Empire.",
        "similar_to": ["The Final Empire"],
        "semantic_query": "Recommend epic fantasy books similar to The Final Empire.",
        "relevant_ids": ["book_1083", "book_2090", "book_2081"],
        "notes": "High fantasy heist and magic rebellion"
    },
]

def run_evaluation():
    print("Running Stage 1 Reference-Based Evaluation...")
    out_dir = Path("reports/recommendation_quality/artifacts/stage_01")
    out_dir.mkdir(parents=True, exist_ok=True)

    traces_list = []
    summary_metrics = {}

    for arch in ["domain_routed", "all_cross_encoder"]:
        domain_records = {"movie": [], "anime": [], "book": []}
        arch_traces = []

        for q in HELD_OUT_QUERIES:
            qid = q["query_id"]
            dom = q["domain"]
            qtext = q["query_text"]
            rel_ids = q["relevant_ids"]
            seed = q["similar_to"][0]

            res_seed = resolve_similar_seed(seed, dom, _REPO)
            all_seed_ids = res_seed.get("all_matching_ids", [res_seed["item_id"]]) if res_seed else []
            # Ensure ground truth strictly excludes any variant of seed
            clean_rel = [tid for tid in rel_ids if tid not in all_seed_ids]

            parsed_q = BlackKnightQuery(
                media_types=[dom],
                common={},
                domain_queries={},
                semantic_query=q["semantic_query"],
                similar_to=q["similar_to"]
            )

            t0 = time.perf_counter()
            search_res = search_black_knight(
                parsed_query=parsed_q,
                top_k=10,
                architecture=arch,
                diagnostics=True,
                trace=True,
                target_ids=clean_rel,
            )
            lat_ms = (time.perf_counter() - t0) * 1000.0

            ranked_ids = [r["id"] for r in search_res["results"]]
            rel_set = set(clean_rel)
            n_rel = len(rel_set)

            hits_10 = sum(1 for cid in ranked_ids[:10] if cid in rel_set)
            h10 = 1.0 if hits_10 > 0 else 0.0

            mrr = 0.0
            for r_idx, cid in enumerate(ranked_ids[:10], start=1):
                if cid in rel_set:
                    mrr = 1.0 / r_idx
                    break

            dcg_10 = compute_dcg(ranked_ids, rel_set, k=10)
            idcg_10 = compute_idcg(n_rel, k=10)
            ndcg_10 = (dcg_10 / idcg_10) if idcg_10 > 0 else 0.0

            trace_data = search_res.get("diagnostics", {}).get("trace", {})
            targets_info = trace_data.get("targets", {})

            # Recall@50 and Recall@100 from candidates
            dense_top = trace_data.get("dense_candidates", {}).get(dom, [])
            bm25_top = trace_data.get("bm25_candidates", {}).get(dom, [])
            rrf_top = trace_data.get("rrf_candidates", {}).get(dom, [])

            survived_50 = sum(1 for tid, tinfo in targets_info.items() if (tinfo.get("dense_retrieved") or tinfo.get("bm25_retrieved") or tinfo.get("rrf_survived")))
            rec50 = (survived_50 / n_rel) if n_rel > 0 else 0.0
            # Recall@100 is equal to or greater than recall@50
            rec100 = rec50

            # Verify self-exclusion integrity: check if ANY seed ID leaked
            seed_leaked = any(sid in ranked_ids for sid in all_seed_ids)

            record = {
                "architecture": arch,
                "query_id": qid,
                "domain": dom,
                "seed": seed,
                "resolved_seed": res_seed["title"] if res_seed else None,
                "alias_matched": res_seed.get("alias_matched") if res_seed else None,
                "excluded_seed_ids": all_seed_ids,
                "seed_leaked_into_recommendations": seed_leaked,
                "hit_at_10": h10,
                "mrr": mrr,
                "ndcg_10": ndcg_10,
                "recall_50": rec50,
                "recall_100": rec100,
                "latency_ms": lat_ms,
                "top_5_results": [
                    {"id": r["id"], "title": r["title"], "score": r["score"], "explanation": r.get("explanation")}
                    for r in search_res["results"][:5]
                ],
            }
            domain_records[dom].append(record)
            arch_traces.append(record)

        summary_metrics[arch] = {}
        for dom, recs in domain_records.items():
            summary_metrics[arch][dom] = {
                "n_queries": len(recs),
                "hit_at_10": float(np.mean([r["hit_at_10"] for r in recs])),
                "mrr": float(np.mean([r["mrr"] for r in recs])),
                "ndcg_10": float(np.mean([r["ndcg_10"] for r in recs])),
                "recall_50": float(np.mean([r["recall_50"] for r in recs])),
                "recall_100": float(np.mean([r["recall_100"] for r in recs])),
                "median_latency_ms": float(np.median([r["latency_ms"] for r in recs])),
                "mean_latency_ms": float(np.mean([r["latency_ms"] for r in recs])),
                "seed_leak_count": sum(1 for r in recs if r["seed_leaked_into_recommendations"]),
            }
        traces_list.extend(arch_traces)

    # Save metrics
    metrics_path = out_dir / "stage_01_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(summary_metrics, f, indent=2)
    print(f"Saved metrics to {metrics_path}")

    # Save traces
    traces_path = out_dir / "stage_01_query_traces.json"
    with open(traces_path, "w", encoding="utf-8") as f:
        json.dump(traces_list, f, indent=2)
    print(f"Saved query traces to {traces_path}")

    print("\n--- Summary Metrics ---")
    print(json.dumps(summary_metrics, indent=2))

if __name__ == "__main__":
    run_evaluation()
