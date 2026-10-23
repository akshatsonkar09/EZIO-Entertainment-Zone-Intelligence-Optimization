import os
import re
import pandas as pd
from pathlib import Path

existing_queries = set()
query_sources = {}

files_to_check = [
    "evaluation/black_knight_eval_queries_113_audited.csv",
    "evaluation/black_knight_eval_queries_150.csv",
    "evaluation/black_knight_eval_queries_150_audited.csv",
    "evaluation/black_knight_eval_queries_v2_150.csv",
    "evaluation/search_retrieval_benchmark_87.csv",
    "evaluation/retrieval_benchmark.jsonl",
    "evaluation/benchmark.jsonl",
]

for filepath in files_to_check:
    if os.path.exists(filepath):
        if filepath.endswith(".csv"):
            df = pd.read_csv(filepath)
            q_cols = [c for c in ["query", "query_text", "user_query"] if c in df.columns]
            if q_cols:
                col = q_cols[0]
                for q in df[col].dropna():
                    q_str = str(q).strip().lower()
                    existing_queries.add(q_str)
                    query_sources.setdefault(q_str, []).append(filepath)
        elif filepath.endswith(".jsonl"):
            import json
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        for key in ["query", "query_text", "user_query"]:
                            if key in data:
                                q_str = str(data[key]).strip().lower()
                                existing_queries.add(q_str)
                                query_sources.setdefault(q_str, []).append(filepath)
                    except:
                        pass

# Check test files
test_dir = Path("tests")
for p in test_dir.glob("*.py"):
    text = p.read_text(encoding="utf-8")
    # find string literals in test cases
    matches = re.findall(r'["\']([A-Z][a-zA-Z0-9\s,.-?!\']{10,80})["\']', text)
    for m in matches:
        # only keep things that look like search queries
        if any(w in m.lower() for w in ["find", "movie", "anime", "book", "directed", "about", "like", "by"]):
            q_str = m.strip().lower()
            existing_queries.add(q_str)
            query_sources.setdefault(q_str, []).append(str(p))

print(f"Total unique existing query strings tracked: {len(existing_queries)}")
with open("scratch/all_known_queries.json", "w", encoding="utf-8") as f:
    json.dump({q: sources for q, sources in query_sources.items()}, f, indent=2)
print("Saved scratch/all_known_queries.json")
