import json
import pandas as pd
from project_black_knight.query_schema import BlackKnightQuery
from project_black_knight.retrieval import (
    RetrievalRepository,
    search_black_knight,
    TITLE_FIELDS,
    normalize_token_str,
)

repo = RetrievalRepository()
bench = pd.read_csv('evaluation/black_knight_eval_queries_113_audited.csv')

# Let's check KI_018 specifically
row_18 = bench[bench['query_id'] == 'KI_018'].iloc[0]
p_18 = json.loads(row_18['expected_parse'])
q_18 = BlackKnightQuery.model_validate(p_18)

df_anime = repo.get_metadata_df('anime')
_, anime_ids = repo.get_documents_and_ids('anime')
id_to_idx = repo._id_to_index['anime']

title = p_18['common']['title']
norm_title = normalize_token_str(title)
print(f"Query title: '{title}', normalized key: '{norm_title}'")

exact = [aid for aid in anime_ids if normalize_token_str(df_anime.iloc[id_to_idx[aid]]['title']) == norm_title]
print(f"Exact catalog matches for '{title}': {exact}")
for aid in exact:
    print(f"  {aid}: {df_anime.iloc[id_to_idx[aid]]['title']}")
