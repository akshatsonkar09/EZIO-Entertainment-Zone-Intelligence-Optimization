import pandas as pd
import json
import re

movies_df = pd.read_csv("data/processed/movie_metadata_clean.csv")
anime_df = pd.read_csv("data/processed/anime_metadata_clean.csv")
book_df = pd.read_csv("data/processed/book_metadata_clean.csv")

with open("scratch/all_known_queries.json", "r", encoding="utf-8") as f:
    known_queries = json.load(f)

# Load existing eval files to ensure no target leakage
with open("scratch/used_item_ids.json", "r", encoding="utf-8") as f:
    used_item_ids = set(json.load(f))

queries = []
labels = []

def add_query(qid, qtext, category, domain, expected_absence, rel_ids, constraints, justification, evidence):
    # Overlap check
    q_clean = qtext.lower().strip()
    assert q_clean not in known_queries, f"LEAKAGE ERROR: Query '{qtext}' matches known query!"
    
    queries.append({
        "query_id": qid,
        "query_text": qtext,
        "category": category,
        "domain": domain,
        "expected_absence": expected_absence,
        "hard_constraints": json.dumps(constraints) if constraints else "{}"
    })
    
    labels.append({
        "query_id": qid,
        "query_text": qtext,
        "domain": domain,
        "category": category,
        "relevant_ids": json.dumps(rel_ids) if isinstance(rel_ids, list) else str(rel_ids),
        "expected_absence": expected_absence,
        "justification": justification,
        "catalog_evidence": evidence
    })

print("Building 100 test queries...")
