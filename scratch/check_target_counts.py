import pandas as pd
import json

for f in ["evaluation/black_knight_eval_queries_113_audited.csv", "evaluation/black_knight_eval_queries_150_audited.csv"]:
    df = pd.read_csv(f)
    items = set()
    for r_ids in df["relevant_ids"].dropna():
        s = str(r_ids).strip()
        if s.startswith("[") and s.endswith("]"):
            try:
                for x in json.loads(s):
                    items.add(str(x))
            except:
                pass
        else:
            for x in s.split(";"):
                if x.strip():
                    items.add(x.strip())
    print(f"{f}: {len(items)} unique item IDs referenced")
