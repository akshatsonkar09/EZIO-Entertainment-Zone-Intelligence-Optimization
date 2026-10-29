import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import pandas as pd
from project_black_knight.text_normalizer import normalize_title, normalize_title_key

raw = pd.read_csv('data/raw/anime/animes.csv')
clean = pd.read_csv('data/processed/anime_metadata_clean.csv')
pkl = pd.read_pickle('data/processed/anime.pkl')

print("--- Analysis of Duplicate Criteria ---")

# Let's inspect rows in pkl
# 1. Exact UID match
dup_uids = pkl[pkl.duplicated(subset=['uid'], keep=False)]
print(f"Rows with duplicated UID: {len(dup_uids)} in {dup_uids['uid'].nunique()} unique groups")

# In these duplicated UID rows, are they the same title?
same_title_in_dup_uids = 0
diff_title_in_dup_uids = 0
for uid, grp in pkl.groupby('uid'):
    if len(grp) > 1:
        norm_titles = grp['title'].astype(str).apply(normalize_title).unique()
        if len(norm_titles) == 1:
            same_title_in_dup_uids += 1
        else:
            diff_title_in_dup_uids += 1
            print(f"UID {uid} has different titles: {grp['title'].tolist()}")

print(f"Duplicate UID groups with identical normalized title: {same_title_in_dup_uids}")
print(f"Duplicate UID groups with different normalized title: {diff_title_in_dup_uids}")

# 2. What about records with the SAME normalized title, but DIFFERENT UIDs?
# We saw 40 such normalized titles earlier.
# Let's test if ANY of them have identical aired AND episodes AND synopsis
norm_map = {}
for idx, row in pkl.iterrows():
    nt = normalize_title(str(row['title']))
    norm_map.setdefault(nt, []).append((idx, row))

same_title_diff_uid_count = 0
same_work_diff_uid = []
flag_for_review = []

for nt, rows in norm_map.items():
    uids = {r['uid'] for _, r in rows}
    if len(uids) > 1:
        same_title_diff_uid_count += 1
        # Check if episodes and aired and synopsis match
        eps = {r['episodes'] for _, r in rows}
        aired = {r['aired'] for _, r in rows}
        syn = {r['synopsis'] for _, r in rows}
        if len(eps) == 1 and len(aired) == 1 and len(syn) == 1:
            same_work_diff_uid.append((nt, uids))
        else:
            flag_for_review.append((nt, [(idx, r['uid'], r['title'], r['aired'], r['episodes']) for idx, r in rows]))

print(f"\nGroups with same normalized title but different UIDs: {same_title_diff_uid_count}")
print(f"Confirmed same work with different UID (identical aired, episodes, synopsis): {len(same_work_diff_uid)}")
print(f"Distinct works/flagged for review (different seasons, episodes, specials, or air dates): {len(flag_for_review)}")
