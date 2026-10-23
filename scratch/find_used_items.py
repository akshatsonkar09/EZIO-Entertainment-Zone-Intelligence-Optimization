import pandas as pd
import json

existing_files = [
    "evaluation/black_knight_eval_queries_113_audited.csv",
    "evaluation/black_knight_eval_queries_150_audited.csv",
    "evaluation/black_knight_eval_queries_v2_150.csv",
    "evaluation/search_retrieval_benchmark_87.csv"
]

used_item_ids = set()
used_queries = set()

for f in existing_files:
    df = pd.read_csv(f)
    q_col = "query" if "query" in df.columns else "query_text"
    for q in df[q_col].dropna():
        used_queries.add(str(q).strip().lower())
    if "relevant_ids" in df.columns:
        for r_ids in df["relevant_ids"].dropna():
            # could be json string or semicolon separated
            s = str(r_ids).strip()
            if s.startswith("[") and s.endswith("]"):
                try:
                    parsed = json.loads(s)
                    for item in parsed:
                        used_item_ids.add(str(item).strip())
                except:
                    pass
            else:
                for item in s.split(";"):
                    if item.strip():
                        used_item_ids.add(item.strip())

print(f"Total used query strings across past eval files: {len(used_queries)}")
print(f"Total item IDs already referenced as relevant targets: {len(used_item_ids)}")

with open("scratch/used_item_ids.json", "w", encoding="utf-8") as f:
    json.dump(list(used_item_ids), f, indent=2)
