import os
import pandas as pd
import json

# Check existing eval datasets
files = [
    "evaluation/black_knight_eval_queries_113_audited.csv",
    "evaluation/black_knight_eval_queries_150.csv",
    "evaluation/black_knight_eval_queries_150_audited.csv",
    "evaluation/black_knight_eval_queries_v2_150.csv",
    "evaluation/search_retrieval_benchmark_87.csv",
]

all_queries = {}
for f in files:
    if os.path.exists(f):
        df = pd.read_csv(f)
        q_col = "query" if "query" in df.columns else "query_text"
        all_queries[f] = {
            "count": len(df),
            "columns": list(df.columns),
            "queries": df[q_col].dropna().tolist() if q_col in df.columns else [],
            "has_relevant_ids": "relevant_ids" in df.columns and df["relevant_ids"].notna().sum()
        }

print("EXISTING DATASETS:")
for f, info in all_queries.items():
    print(f"  {f}: {info['count']} rows, {len(info['queries'])} queries, non-null relevant_ids: {info['has_relevant_ids']}")

# Check catalogs
movies_df = pd.read_csv("data/processed/movie_metadata_clean.csv")
anime_df = pd.read_csv("data/processed/anime_metadata_clean.csv")
book_df = pd.read_csv("data/processed/book_metadata_clean.csv")

print("\nCATALOGS:")
print(f"  Movies: {len(movies_df)} rows, columns: {list(movies_df.columns[:8])}")
print(f"  Anime:  {len(anime_df)} rows, columns: {list(anime_df.columns[:8])}")
print(f"  Books:  {len(book_df)} rows, columns: {list(book_df.columns[:8])}")
