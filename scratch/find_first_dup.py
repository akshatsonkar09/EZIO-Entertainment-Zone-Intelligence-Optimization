import pandas as pd
pkl = pd.read_pickle('data/processed/anime.pkl')
is_dup = pkl.duplicated(subset=['uid'], keep='first').tolist()
first_dups = []
for i, d in enumerate(is_dup):
    if d:
        first_dups.append((i, pkl.iloc[i]['uid'], pkl.iloc[i]['title']))
        if len(first_dups) >= 10:
            break

for r, u, t in first_dups:
    print(f"Row {r}: UID={u}, Title='{t}'")
