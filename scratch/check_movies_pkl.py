"""
Check movies.pkl columns and contents
"""
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
df_movies = pd.read_pickle(PROJECT_ROOT / "data" / "processed" / "movies.pkl")
print("movies.pkl columns:", df_movies.columns.tolist())
print("movies.pkl row 0:")
print(df_movies.iloc[0])
print("\nmovies.pkl row 65:")
print(df_movies.iloc[65])
