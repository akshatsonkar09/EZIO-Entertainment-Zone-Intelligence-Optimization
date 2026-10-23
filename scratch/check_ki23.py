"""
Inspect KI_023 (Mansfield Park)
"""
import sys, json
from pathlib import Path
import pandas as pd
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from project_black_knight.query_schema import BlackKnightQuery
from project_black_knight.retrieval import RetrievalRepository
from project_black_knight.metadata_filter import get_valid_ids

def main():
    repo = RetrievalRepository()
    df_eval = pd.read_csv(PROJECT_ROOT / "evaluation" / "black_knight_eval_queries_113_audited.csv").set_index("query_id")
    row = df_eval.loc["KI_023"]
    print(row.to_dict())
    
    parsed = json.loads(row["expected_parse"])
    df_meta = repo.get_metadata_df("book")
    docs, ids = repo.get_documents_and_ids("book")
    
    q_obj = BlackKnightQuery.model_validate(parsed)
    common = q_obj.common
    dom_q = q_obj.domain_queries.book
    filters = {"title": common.title}
    if dom_q:
        filters.update(dom_q.model_dump(exclude_none=True))
    print(f"Filters: {filters}")
    v_ids = get_valid_ids(df_meta, ids, filters, "book")
    print(f"Valid IDs count: {len(v_ids)}")
    print(f"Is book_10435 in valid_ids? {'book_10435' in v_ids}")
    
    # Let's search df_meta for Mansfield Park
    mp_rows = df_meta[df_meta["title"].str.contains("Mansfield Park", case=False, na=False)]
    print("\nMansfield Park rows in book_metadata_clean:")
    for idx, r in mp_rows.iterrows():
        print(f"  book_{idx}: title='{r['title']}', author='{r['author']}'")

if __name__ == "__main__":
    main()
