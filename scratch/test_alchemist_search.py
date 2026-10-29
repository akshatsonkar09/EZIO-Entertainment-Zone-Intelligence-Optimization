import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from project_black_knight.retrieval import RetrievalRepository, search_black_knight
from project_black_knight.query_schema import BlackKnightQuery, DomainQueries, CommonQuery

repo = RetrievalRepository()

# 1. Search anime domain for 'alchemist'
query = BlackKnightQuery(
    media_types=['anime'],
    common=CommonQuery(),
    domain_queries=DomainQueries(),
    semantic_query='alchemist',
    similar_to=[]
)
res = search_black_knight('alchemist', top_k=15, parsed_query=query, repo=repo)
print('Search results for alchemist (anime):')
for r in res['results']:
    print(f"  {r['id']} | {r['media_type']} | {r['title']} | score: {r['score']}")

# Check if Fullmetal Alchemist appears multiple times
fma_titles = [r['title'] for r in res['results'] if r['title'] == 'Fullmetal Alchemist']
print(f"\nOccurrences of 'Fullmetal Alchemist (2003)': {len(fma_titles)}")

# 2. Search exact title for 'Fullmetal Alchemist'
query_exact = BlackKnightQuery(
    media_types=['anime'],
    common=CommonQuery(title='Fullmetal Alchemist'),
    domain_queries=DomainQueries(),
    semantic_query='Fullmetal Alchemist',
    similar_to=[]
)
res_exact = search_black_knight('Fullmetal Alchemist', top_k=5, parsed_query=query_exact, repo=repo)
print('\nExact title search for Fullmetal Alchemist:')
for r in res_exact['results']:
    print(f"  {r['id']} | {r['title']} | score: {r['score']}")

# 3. Search exact title for 'Cowboy Bebop'
query_cb = BlackKnightQuery(
    media_types=['anime'],
    common=CommonQuery(title='Cowboy Bebop'),
    domain_queries=DomainQueries(),
    semantic_query='Cowboy Bebop',
    similar_to=[]
)
res_cb = search_black_knight('Cowboy Bebop', top_k=5, parsed_query=query_cb, repo=repo)
print('\nExact title search for Cowboy Bebop:')
for r in res_cb['results']:
    print(f"  {r['id']} | {r['title']} | score: {r['score']}")
