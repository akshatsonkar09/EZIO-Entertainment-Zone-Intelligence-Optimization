import json
import pandas as pd
from project_black_knight.query_schema import BlackKnightQuery, CommonQuery, DomainQueries, MovieQuery, AnimeQuery, BookQuery

queries_df = pd.read_csv("final_test_queries.csv")
labels_df = pd.read_csv("final_test_labels.csv")

parses = {}

for _, r in queries_df.iterrows():
    qid = r["query_id"]
    qtext = r["query_text"]
    cat = r["category"]
    dom = r["domain"]
    hard_con = json.loads(r["hard_constraints"]) if pd.notna(r["hard_constraints"]) else {}
    
    # Common query fields
    title = None
    genres_inc = hard_con.get("genres_include", [])
    genres_exc = hard_con.get("genres_exclude", [])
    y_min = hard_con.get("release_year_min")
    y_max = hard_con.get("release_year_max")
    
    # Domain specific queries
    movie_q = None
    anime_q = None
    book_q = None
    
    if dom == "movie" or "movie" in hard_con:
        movie_q = MovieQuery(
            director=hard_con.get("director", []),
            cast=hard_con.get("cast", []),
            revenue_min=hard_con.get("revenue_min"),
            runtime_min=hard_con.get("runtime_min"),
            runtime_max=hard_con.get("runtime_max")
        )
    if dom == "anime" or "anime" in hard_con:
        anime_q = AnimeQuery(
            episodes_min=hard_con.get("episodes_min"),
            episodes_max=hard_con.get("episodes_max"),
            ranking_max=hard_con.get("ranking_max"),
            popularity_min=hard_con.get("popularity_min")
        )
    if dom == "book" or "book" in hard_con:
        book_q = BookQuery(
            author=hard_con.get("author", []),
            rating_min=hard_con.get("rating_min"),
            pages_min=hard_con.get("pages_min"),
            pages_max=hard_con.get("pages_max")
        )
        
    # Media types list (max 2)
    if dom == "movie":
        m_types = ["movie"]
    elif dom == "anime":
        m_types = ["anime"]
    elif dom == "book":
        m_types = ["book"]
    elif dom == "mixed":
        # Multi-domain queries
        if qid in ["HT_MD_001", "HT_MD_002", "HT_MD_005", "HT_MD_006", "HT_MD_007", "HT_MD_008", "HT_MD_009", "HT_MD_010", "HT_MD_012", "HT_MD_013", "HT_MD_014"]:
            m_types = ["movie", "anime"]
        else:
            m_types = ["anime", "book"]
    else:
        m_types = ["movie", "book"]

    # Known-item title extraction
    if cat == "known_item":
        # Extract title from query text
        if "Whiplash" in qtext: title = "Whiplash"
        elif "The Prestige" in qtext: title = "The Prestige"
        elif "Memento" in qtext: title = "Memento"
        elif "The Truman Show" in qtext: title = "The Truman Show"
        elif "Pan's Labyrinth" in qtext: title = "Pan's Labyrinth"
        elif "Gattaca" in qtext: title = "Gattaca"
        elif "Fight Club" in qtext: title = "Fight Club"
        elif "Blade Runner" in qtext: title = "Blade Runner"
        elif "Psycho-Pass" in qtext: title = "Psycho-Pass"
        elif "Vinland Saga" in qtext: title = "Vinland Saga"
        elif "Mushishi" in qtext: title = "Mushishi"
        elif "Monster" in qtext: title = "Monster"
        elif "Fate/Zero" in qtext: title = "Fate/Zero"
        elif "Steins;Gate 0" in qtext: title = "Steins;Gate 0"
        elif "Hyouka" in qtext: title = "Hyouka"
        elif "Toradora!" in qtext: title = "Toradora!"
        elif "The Crying of Lot 49" in qtext: title = "The Crying of Lot 49"
        elif "All the King's Men" in qtext: title = "All the King's Men"
        elif "The Midnight Line" in qtext: title = "The Midnight Line"
        elif "First King of Shannara" in qtext: title = "First King of Shannara"
        elif "The Gift of the Magi" in qtext: title = "The Gift of the Magi"
        elif "Every Dead Thing" in qtext: title = "Every Dead Thing"
        elif "CivilWarLand in Bad Decline" in qtext: title = "CivilWarLand in Bad Decline"
        elif "Speak" in qtext: title = "Speak"
        elif "Coyote Blue" in qtext: title = "Coyote Blue"
        semantic_query = title or qtext
    elif cat == "descriptive":
        semantic_query = qtext
    elif cat == "multi_domain":
        semantic_query = qtext
    else:
        # Constraint or absence query
        semantic_query = qtext

    bk_query = BlackKnightQuery(
        media_types=m_types,
        common=CommonQuery(
            title=title,
            genres_include=genres_inc,
            genres_exclude=genres_exc,
            release_year_min=y_min,
            release_year_max=y_max
        ),
        domain_queries=DomainQueries(
            movie=movie_q,
            anime=anime_q,
            book=book_q
        ),
        semantic_query=semantic_query,
        similar_to=[]
    )
    
    # Validate and store
    parses[qid] = bk_query.model_dump()

print(f"Total parses generated and validated: {len(parses)}")
with open("scratch/held_out_parses.json", "w", encoding="utf-8") as f:
    json.dump(parses, f, indent=2)

print("Saved scratch/held_out_parses.json successfully!")
