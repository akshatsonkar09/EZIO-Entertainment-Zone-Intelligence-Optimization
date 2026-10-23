import pandas as pd
import json

movies_df = pd.read_csv("data/processed/movie_metadata_clean.csv")
anime_df = pd.read_csv("data/processed/anime_metadata_clean.csv")
book_df = pd.read_csv("data/processed/book_metadata_clean.csv")

queries_df = pd.read_csv("final_test_queries.csv")
abs_queries = queries_df[queries_df["expected_absence"] == True]

print(f"Total absence queries to verify: {len(abs_queries)}")

for _, r in abs_queries.iterrows():
    qid = r["query_id"]
    con = json.loads(r["hard_constraints"])
    dom = r["domain"]
    
    if dom == "movie":
        df = movies_df
        if "director" in con:
            dirs = [d.lower() for d in con["director"]]
            df = df[df["director"].str.lower().isin(dirs)]
        if "release_year_min" in con:
            df = df[df["release_date"].str[:4].astype(float) >= con["release_year_min"]]
        if "release_year_max" in con:
            df = df[df["release_date"].str[:4].astype(float) <= con["release_year_max"]]
        if "runtime_min" in con:
            df = df[df["runtime"] >= con["runtime_min"]]
        if "revenue_min" in con:
            df = df[df["revenue"] >= con["revenue_min"]]
        if "cast" in con:
            cast = [c.lower() for c in con["cast"]]
            df = df[df["cast"].fillna("").str.lower().apply(lambda s: any(c in s for c in cast))]
        if "genres_include" in con:
            for g in con["genres_include"]:
                df = df[df["genres"].fillna("").str.lower().str.contains(g.lower())]
                
    elif dom == "anime":
        df = anime_df
        if "release_year_min" in con:
            df = df[df["release_year"] >= con["release_year_min"]]
        if "release_year_max" in con:
            df = df[df["release_year"] <= con["release_year_max"]]
        if "episodes_min" in con:
            df = df[df["episodes"] >= con["episodes_min"]]
        if "episodes_max" in con:
            df = df[df["episodes"] <= con["episodes_max"]]
        if "ranking_max" in con:
            df = df[df["ranking"] <= con["ranking_max"]]
        if "popularity_min" in con:
            df = df[df["popularity"] <= con["popularity_min"]]
        if "genres_include" in con:
            for g in con["genres_include"]:
                df = df[df["genres"].fillna("").str.lower().str.contains(g.lower())]
                
    elif dom == "book":
        df = book_df
        if "author" in con:
            authors = [a.lower() for a in con["author"]]
            df = df[df["author"].fillna("").str.lower().apply(lambda s: any(a in s for a in authors))]
        if "pages_min" in con:
            df = df[df["pages"] >= con["pages_min"]]
        if "pages_max" in con:
            df = df[df["pages"] <= con["pages_max"]]
        if "rating_min" in con:
            df = df[df["rating"] >= con["rating_min"]]
        if "genres_include" in con:
            for g in con["genres_include"]:
                df = df[df["genres"].fillna("").str.lower().str.contains(g.lower())]
                
    print(f"Query {qid} ({dom}): matching catalog records = {len(df)}")
    assert len(df) == 0, f"Error: Query {qid} matched {len(df)} records!"

print("ALL 15 ABSENCE QUERIES VERIFIED TO HAVE ZERO MATCHES IN CATALOG!")
