import json
import pandas as pd
from project_black_knight.query_parser import parse_query
from project_black_knight.retrieval import search_black_knight

df = pd.read_csv("evaluation/black_knight_eval_queries_113_audited.csv")
md_df = df[df["query_id"].str.startswith("MD_")]

print(f"Total MD queries: {len(md_df)}")

for _, row in md_df.iterrows():
    qid = row["query_id"]
    qtext = row["query_text"]
    rel_ids = row["relevant_ids"]
    domain = row["domain"]
    print(f"\n=======================================================")
    print(f"Query ID: {qid} | Domain col: {domain}")
    print(f"Query: '{qtext}'")
    print(f"Relevant IDs in benchmark: {rel_ids}")
    
    parsed = parse_query(qtext)
    print(f"Parsed media_types: {parsed.media_types}")
    print(f"Parsed fields: {parsed.model_dump()}")
    
    # Run search
    res = search_black_knight(qtext, architecture="domain_routed", top_k=10)
    top_items = res["results"][:5]
    print(f"Top 5 results returned:")
    for idx, item in enumerate(top_items):
        is_hit = item["id"] in str(rel_ids)
        marker = "==> HIT" if is_hit else ""
        print(f"  {idx+1}. [{item['media_type']}] {item['title']} ({item['id']}) score={item['score']:.4f} {marker}")
