import pandas as pd
import json

df = pd.read_csv("evaluation/black_knight_eval_queries_113_audited.csv")
for _, row in df.iterrows():
    s = str(row["relevant_ids"])
    if len(s) > 100:
        count = len(s.split(";")) if ";" in s else len(json.loads(s))
        if count > 50:
            print(f"Query {row['query_id']} ({row['category']}): '{row['query_text']}' has {count} target IDs!")
