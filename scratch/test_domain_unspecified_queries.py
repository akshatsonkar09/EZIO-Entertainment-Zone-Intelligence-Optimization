from project_black_knight.retrieval import search_black_knight
from project_black_knight.query_parser import parse_query

test_queries = [
    "Find works about artificial intelligence.",
    "A story about a detective solving murders.",
    "Books or films about time travel.",
    "Find the work directed by Christopher Nolan about dreams."
]

for q in test_queries:
    parsed = parse_query(q)
    print("=" * 60)
    print(f"QUERY: '{q}'")
    print(f"Parsed media_types: {parsed.media_types}")
    print(f"Semantic query: '{parsed.semantic_query}'")
    
    res = search_black_knight(q, architecture="domain_routed", top_k=6)
    results = res["results"]
    domains_present = set(r["media_type"] for r in results)
    print(f"Total results: {len(results)} | Domains represented: {domains_present}")
    for idx, r in enumerate(results, start=1):
        print(f"  {idx}. [{r['media_type']}] {r['title']} ({r['id']}) - score: {r['score']:.4f}")
