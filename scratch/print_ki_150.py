import pandas as pd

df = pd.read_csv("evaluation/black_knight_eval_queries_150_audited.csv")
ki_df = df[df["category"] == "known_item"]
print(f"Known item queries in 150 benchmark ({len(ki_df)}):")
for _, r in ki_df.iterrows():
    print(f"  {r['query_id']}: '{r['query_text']}'")
