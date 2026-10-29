import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import pandas as pd
from project_black_knight.text_normalizer import normalize_title, normalize_title_key

pkl = pd.read_pickle('data/processed/anime.pkl')
clean = pd.read_csv('data/processed/anime_metadata_clean.csv')

print(f"pkl total rows: {len(pkl)}")
print(f"clean total rows: {len(clean)}")

# Let's add index as canonical id
pkl['id'] = [f"anime_{i}" for i in range(len(pkl))]
clean['id'] = [f"anime_{i}" for i in range(len(clean))]

# Group by uid in pkl
uid_groups = pkl.groupby('uid')
dup_uid_groups = {uid: grp for uid, grp in uid_groups if len(grp) > 1}
print(f"Total duplicate groups by UID: {len(dup_uid_groups)}")
total_dup_records = sum(len(grp) - 1 for grp in dup_uid_groups.values())
print(f"Total redundant duplicate records by UID: {total_dup_records}")

# Check if there are any duplicate records with DIFFERENT UIDs that might be duplicates
# Group by normalized title
clean['norm_title'] = clean['title'].astype(str).apply(normalize_title)
pkl['norm_title'] = clean['norm_title']

title_groups = pkl.groupby('norm_title')
diff_uid_title_dups = []
for title, grp in title_groups:
    uids = grp['uid'].unique()
    if len(uids) > 1:
        diff_uid_title_dups.append((title, grp))

print(f"Groups with same normalized title but different UIDs: {len(diff_uid_title_dups)}")

# Let's inspect these groups to see if ANY of them are true duplicates or distinct works
uncertain_count = 0
for title, grp in diff_uid_title_dups:
    uids = grp['uid'].unique()
    # Check if aired, episodes, etc. differ
    # print details
    ep_set = grp['episodes'].dropna().unique()
    aired_set = grp['aired'].dropna().unique()
    year_set = grp['release_year'].dropna().unique() if 'release_year' in grp.columns else []
    # If all metadata (aired, episodes, synopsis) are also identical across different UIDs:
    # let's check
    synopsis_unique = grp['synopsis'].dropna().nunique()
    if synopsis_unique == 1 and len(ep_set) <= 1 and len(aired_set) <= 1:
        print(f"SUSPECT SAME WORK DIFFERENT UID: '{title}' UIDs: {uids}")
        uncertain_count += 1

print(f"Total suspect same work with different UID: {uncertain_count}")
