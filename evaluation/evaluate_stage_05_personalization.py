"""
Stage 5 Taste-Aware Personalization Functional Evaluation Script.

IMPORTANT METHODOLOGY NOTICE:
As required by the Project Black Knight quality protocol, because actual historical user click logs
and multi-turn personalized relevance judgments are not present in the catalog dataset, this script
evaluates taste-aware personalization using 6 clearly labeled SYNTHETIC PROFILES for functional validation only.
Personalization recommendation quality is explicitly marked as 'NOT VALIDATED' against real production users.
"""

import json
import math
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from project_black_knight.query_schema import BlackKnightQuery, CommonQuery, DomainQueries
from project_black_knight.personalization import UserPreferences
from project_black_knight.retrieval import RetrievalRepository, search_black_knight


SYNTHETIC_PROFILES = [
    {
        "profile_id": "syn_user_01_nolan_scifi",
        "description": "Hard sci-fi enthusiast with strong preference for Christopher Nolan",
        "profile": UserPreferences(
            user_id="syn_user_01_nolan_scifi",
            preferred_creators=["Christopher Nolan"],
            preferred_genres=["Science Fiction"],
        ),
        "test_query": "Mind-bending space exploration adventure",
        "domain": "movie",
    },
    {
        "profile_id": "syn_user_02_anti_horror",
        "description": "General action lover who strictly avoids horror and gore",
        "profile": UserPreferences(
            user_id="syn_user_02_anti_horror",
            disliked_genres=["Horror"],
            preferred_genres=["Action", "Adventure"],
        ),
        "test_query": "Intense action thriller",
        "domain": "movie",
    },
    {
        "profile_id": "syn_user_03_cyberpunk_anime",
        "description": "Cyberpunk and dark thriller anime fan",
        "profile": UserPreferences(
            user_id="syn_user_03_cyberpunk_anime",
            preferred_genres=["Sci-Fi", "Cyberpunk", "Psychological"],
            disliked_genres=["Romance", "Slice of Life"],
        ),
        "test_query": "Dystopian future detective",
        "domain": "anime",
    },
    {
        "profile_id": "syn_user_04_shounen_purist",
        "description": "Classic shounen action fan",
        "profile": UserPreferences(
            user_id="syn_user_04_shounen_purist",
            preferred_genres=["Shounen", "Action", "Supernatural"],
        ),
        "test_query": "Martial arts tournaments and superpower battles",
        "domain": "anime",
    },
    {
        "profile_id": "syn_user_05_epic_fantasy_books",
        "description": "Epic high fantasy reader",
        "profile": UserPreferences(
            user_id="syn_user_05_epic_fantasy_books",
            preferred_genres=["Fantasy", "High Fantasy"],
            preferred_creators=["Brandon Sanderson", "J.R.R. Tolkien"],
        ),
        "test_query": "Ancient magic war and kingdom rebellion",
        "domain": "book",
    },
    {
        "profile_id": "syn_user_06_cozy_detective_books",
        "description": "Cozy mystery reader avoiding violence",
        "profile": UserPreferences(
            user_id="syn_user_06_cozy_detective_books",
            preferred_genres=["Mystery", "Detective"],
            disliked_genres=["Horror", "Gore"],
        ),
        "test_query": "Clever detective murder mystery investigation",
        "domain": "book",
    },
]


def evaluate_personalization():
    repo = RetrievalRepository()

    profile_evaluations = []
    overall_rank_shifts = []

    for test_case in SYNTHETIC_PROFILES:
        prof = test_case["profile"]
        q_text = test_case["test_query"]
        domain = test_case["domain"]

        q_obj = BlackKnightQuery(
            media_types=[domain],
            common=CommonQuery(),
            domain_queries=DomainQueries(),
            semantic_query=q_text,
        )

        # 1. Unpersonalized baseline
        t0 = time.perf_counter()
        res_unpers = search_black_knight(parsed_query=q_obj, user_profile=None, top_k=10, repo=repo)
        lat_unpers = (time.perf_counter() - t0) * 1000

        # 2. Personalized
        t0 = time.perf_counter()
        res_pers = search_black_knight(parsed_query=q_obj, user_profile=prof, top_k=10, repo=repo)
        lat_pers = (time.perf_counter() - t0) * 1000

        unpers_ids = [r["id"] for r in res_unpers["results"]]
        pers_ids = [r["id"] for r in res_pers["results"]]

        # Calculate rank shifts for overlapping items
        rank_shifts = []
        for rank_pers, cid in enumerate(pers_ids, start=1):
            if cid in unpers_ids:
                rank_unpers = unpers_ids.index(cid) + 1
                rank_shifts.append(abs(rank_pers - rank_unpers))
            else:
                # Newly elevated into top 10
                rank_shifts.append(5)

        mean_shift = float(np.mean(rank_shifts)) if rank_shifts else 0.0
        overall_rank_shifts.append(mean_shift)

        profile_evaluations.append({
            "profile_id": test_case["profile_id"],
            "description": test_case["description"],
            "domain": domain,
            "query": q_text,
            "unpersonalized_top_3": [f"{r['title']} ({r.get('genres', '')[:30]})" for r in res_unpers["results"][:3]],
            "personalized_top_3": [f"{r['title']} ({r.get('genres', '')[:30]})" for r in res_pers["results"][:3]],
            "mean_top10_rank_shift": round(mean_shift, 2),
            "unpersonalized_latency_ms": round(lat_unpers, 2),
            "personalized_latency_ms": round(lat_pers, 2),
            "jaccard_top10": round(len(set(unpers_ids) & set(pers_ids)) / float(len(set(unpers_ids) | set(pers_ids))), 4),
        })

    summary = {
        "status": "IMPLEMENTED_AND_FUNCTIONALLY_TESTED",
        "validation_status": "NOT_VALIDATED",
        "validation_notice": "Personalization quality is marked NOT VALIDATED for real users because multi-turn human profile ground truth was not present in repository datasets. Evaluated on 6 synthetic profiles for functional correctness.",
        "profile_count": len(SYNTHETIC_PROFILES),
        "mean_top10_rank_shift": round(float(np.mean(overall_rank_shifts)), 2),
        "profiles": profile_evaluations,
    }

    # Save artifacts
    artifacts_dir = Path("reports/recommendation_quality/artifacts/stage_05")
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    metrics_path = artifacts_dir / "stage_05_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    profile_tests_path = artifacts_dir / "stage_05_profile_tests.json"
    with open(profile_tests_path, "w", encoding="utf-8") as f:
        json.dump(profile_evaluations, f, indent=2)

    print("Stage 5 Personalization Evaluation Completed Successfully.")
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    evaluate_personalization()
