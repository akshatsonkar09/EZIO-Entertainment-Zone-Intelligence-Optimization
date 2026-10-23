"""
Check anime_732 in anime_metadata_clean.csv
"""
import sys, json
from pathlib import Path
import pandas as pd
PROJECT_ROOT = Path(__file__).resolve().parent.parent

df_meta = pd.read_csv(PROJECT_ROOT / "data" / "processed" / "anime_metadata_clean.csv")
print(f"Row 732: {df_meta.iloc[732].to_dict()}")
