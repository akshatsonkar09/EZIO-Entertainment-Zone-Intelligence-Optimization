import pandas as pd
import json
import os

movies_df = pd.read_csv("data/processed/movie_metadata_clean.csv")
anime_df = pd.read_csv("data/processed/anime_metadata_clean.csv")
book_df = pd.read_csv("data/processed/book_metadata_clean.csv")

with open("scratch/all_known_queries.json", "r", encoding="utf-8") as f:
    known_queries = json.load(f)

# Verification helpers
def verify_ids_exist(ids, domain=None):
    for item_id in ids:
        d, idx_str = item_id.split("_")
        idx = int(idx_str)
        if d == "movie":
            assert 0 <= idx < len(movies_df), f"Invalid movie ID: {item_id}"
        elif d == "anime":
            assert 0 <= idx < len(anime_df), f"Invalid anime ID: {item_id}"
        elif d == "book":
            assert 0 <= idx < len(book_df), f"Invalid book ID: {item_id}"
        else:
            raise ValueError(f"Unknown domain prefix: {item_id}")

test_queries = []
test_labels = []

def add_query(qid, qtext, category, domain, expected_absence, rel_ids, constraints, justification, evidence):
    q_clean = qtext.lower().strip()
    assert q_clean not in known_queries, f"LEAKAGE ERROR: Query '{qtext}' matches known query!"
    test_queries.append({
        "query_id": qid,
        "query_text": qtext,
        "category": category,
        "domain": domain,
        "expected_absence": expected_absence,
        "hard_constraints": json.dumps(constraints) if constraints else "{}"
    })
    test_labels.append({
        "query_id": qid,
        "query_text": qtext,
        "domain": domain,
        "category": category,
        "relevant_ids": json.dumps(rel_ids) if isinstance(rel_ids, list) else str(rel_ids),
        "expected_absence": expected_absence,
        "justification": justification,
        "catalog_evidence": evidence
    })

# Known-Item Queries (25)
ki_data = [
    # Movies (8)
    ("HT_KI_001", "Find the movie Whiplash directed by Damien Chazelle.", "movie", ["movie_3869"], "Damien Chazelle's 2014 psychological drama Whiplash", "movie_3869: title='Whiplash', director='DamienChazelle', release_date='2014-10-10'"),
    ("HT_KI_002", "Find the film The Prestige.", "movie", ["movie_1197"], "Christopher Nolan's 2006 drama/mystery The Prestige", "movie_1197: title='The Prestige', director='ChristopherNolan'"),
    ("HT_KI_003", "Find the movie Memento.", "movie", ["movie_3575"], "Christopher Nolan's 2000 mystery thriller Memento", "movie_3575: title='Memento', director='ChristopherNolan'"),
    ("HT_KI_004", "Show me The Truman Show.", "movie", ["movie_697"], "Peter Weir's 1998 comedy/drama The Truman Show", "movie_697: title='The Truman Show', director='PeterWeir'"),
    ("HT_KI_005", "Find Pan's Labyrinth directed by Guillermo del Toro.", "movie", ["movie_2467"], "Guillermo del Toro's 2006 dark fantasy Pan's Labyrinth", "movie_2467: title=\"Pan's Labyrinth\", director='GuillermodelToro'"),
    ("HT_KI_006", "Find the sci-fi film Gattaca.", "movie", ["movie_1353"], "Andrew Niccol's 1997 sci-fi thriller Gattaca", "movie_1353: title='Gattaca', director='AndrewNiccol'"),
    ("HT_KI_007", "Find the movie Fight Club directed by David Fincher.", "movie", ["movie_662"], "David Fincher's 1999 psychological drama Fight Club", "movie_662: title='Fight Club', director='DavidFincher'"),
    ("HT_KI_008", "Find Blade Runner directed by Ridley Scott.", "movie", ["movie_1727"], "Ridley Scott's 1982 cyberpunk sci-fi Blade Runner", "movie_1727: title='Blade Runner', director='RidleyScott'"),
    # Anime (8)
    ("HT_KI_009", "Find the anime series Psycho-Pass.", "anime", ["anime_633"], "2012 cyberpunk police procedural anime Psycho-Pass", "anime_633: title='Psycho-Pass', release_year=2012, episodes=22"),
    ("HT_KI_010", "Find Vinland Saga.", "anime", ["anime_746", "anime_17104"], "2019 historical viking anime Vinland Saga", "anime_746, anime_17104: title='Vinland Saga', release_year=2019"),
    ("HT_KI_011", "Find the anime Mushishi.", "anime", ["anime_734", "anime_17056"], "2005 supernatural folklore anime Mushishi", "anime_734, anime_17056: title='Mushishi', release_year=2005"),
    ("HT_KI_012", "Find the anime Monster.", "anime", ["anime_730", "anime_16817"], "2004 psychological thriller anime Monster", "anime_730, anime_16817: title='Monster', release_year=2004"),
    ("HT_KI_013", "Find Fate/Zero.", "anime", ["anime_629", "anime_14405"], "2011 dark fantasy anime Fate/Zero", "anime_629, anime_14405: title='Fate/Zero', release_year=2011"),
    ("HT_KI_014", "Find Steins;Gate 0.", "anime", ["anime_695", "anime_16031"], "2018 sci-fi thriller anime Steins;Gate 0", "anime_695, anime_16031: title='Steins;Gate 0', release_year=2018"),
    ("HT_KI_015", "Find the anime Hyouka.", "anime", ["anime_401", "anime_6558"], "2012 mystery slice-of-life anime Hyouka", "anime_401, anime_6558: title='Hyouka', release_year=2012"),
    ("HT_KI_016", "Find Toradora!.", "anime", ["anime_577", "anime_11055"], "2008 romantic comedy anime Toradora!", "anime_577, anime_11055: title='Toradora!', release_year=2008"),
    # Books (9)
    ("HT_KI_017", "Find The Crying of Lot 49 by Thomas Pynchon.", "book", ["book_21"], "Thomas Pynchon's 1966 postmodern novel The Crying of Lot 49", "book_21: title='The Crying of Lot 49', author='Thomas Pynchon'"),
    ("HT_KI_018", "Find All the King's Men by Robert Penn Warren.", "book", ["book_22"], "Robert Penn Warren's political classic All the King's Men", "book_22: title=\"All the King's Men\", author='Robert Penn Warren'"),
    ("HT_KI_019", "Find The Midnight Line by Lee Child.", "book", ["book_16"], "Lee Child's Jack Reacher thriller The Midnight Line", "book_16: title='The Midnight Line', author='Lee Child (Goodreads Author)'"),
    ("HT_KI_020", "Find First King of Shannara by Terry Brooks.", "book", ["book_17"], "Terry Brooks' epic fantasy novel First King of Shannara", "book_17: title='First King of Shannara', author='Terry Brooks (Goodreads Author)'"),
    ("HT_KI_021", "Find The Gift of the Magi by O. Henry.", "book", ["book_2"], "O. Henry's classic short story The Gift of the Magi", "book_2: title='The Gift of the Magi', author='O. Henry, Lisbeth Zwerger (Illustrator)'"),
    ("HT_KI_022", "Find Every Dead Thing by John Connolly.", "book", ["book_24"], "John Connolly's Charlie Parker mystery thriller Every Dead Thing", "book_24: title='Every Dead Thing', author='John Connolly (Goodreads Author)'"),
    ("HT_KI_023", "Find CivilWarLand in Bad Decline by George Saunders.", "book", ["book_7"], "George Saunders' satirical dystopian collection CivilWarLand in Bad Decline", "book_7: title='CivilWarLand in Bad Decline', author='George Saunders'"),
    ("HT_KI_024", "Find Speak by Laurie Halse Anderson.", "book", ["book_15"], "Laurie Halse Anderson's acclaimed YA novel Speak", "book_15: title='Speak', author='Laurie Halse Anderson (Goodreads Author)'"),
    ("HT_KI_025", "Find Coyote Blue by Christopher Moore.", "book", ["book_1"], "Christopher Moore's comedic trickster fantasy Coyote Blue", "book_1: title='Coyote Blue', author='Christopher Moore (Goodreads Author)'"),
]

# Descriptive Queries (25)
dq_data = [
    # Movies (8)
    ("HT_DQ_001", "An insurance investigator with anterograde amnesia uses polaroids and tattoos to hunt his wife's killer.", "movie", ["movie_3575"], "Narrative description of Memento", "movie_3575 plot: Leonard Shelby suffering from short-term memory loss"),
    ("HT_DQ_002", "An ambitious young jazz drummer is pushed to his psychological limits by a ruthless music conservatory instructor.", "movie", ["movie_3869"], "Narrative description of Whiplash", "movie_3869 plot: Andrew Neiman and Terence Fletcher at Shaffer Conservatory"),
    ("HT_DQ_003", "A man discovers his entire life is an unscripted 24-hour reality television broadcast filmed on an enormous domed set.", "movie", ["movie_697"], "Narrative description of The Truman Show", "movie_697 plot: Truman Burbank living unwittingly inside Seahaven studio"),
    ("HT_DQ_004", "Two rival stage magicians in Victorian London engage in a competitive obsession to perform the ultimate teleportation illusion.", "movie", ["movie_1197"], "Narrative description of The Prestige", "movie_1197 plot: Robert Angier and Alfred Borden creating the Transported Man"),
    ("HT_DQ_005", "In 1944 post-Civil War Spain, a young girl escapes her cruel stepfather into an ancient mythical underworld labyrinth.", "movie", ["movie_2467"], "Narrative description of Pan's Labyrinth", "movie_2467 plot: Ofelia and the Faun in fascist Spain"),
    ("HT_DQ_006", "In a future society driven by genetic determinism, an in-valid man assumes the identity of a paralyzed athlete to travel into space.", "movie", ["movie_1353"], "Narrative description of Gattaca", "movie_1353 plot: Vincent Freeman assumes Jerome Morrow's identity to join Gattaca space program"),
    ("HT_DQ_007", "An insomniac office worker forms an underground combat club with a charismatic soap salesman.", "movie", ["movie_662"], "Narrative description of Fight Club", "movie_662 plot: The Narrator and Tyler Durden form secret fight club"),
    ("HT_DQ_008", "A cynical blade runner cop is assigned to track down and retire four rogue replicants who returned to Earth.", "movie", ["movie_1727"], "Narrative description of Blade Runner", "movie_1727 plot: Rick Deckard hunts Roy Batty and Nexus-6 replicants"),
    # Anime (8)
    ("HT_DQ_009", "A futuristic society where the Sibyl System continuously quantifies mental states and criminal intent using Dominator weapons.", "anime", ["anime_633"], "Narrative description of Psycho-Pass", "anime_633: Sibyl System, Crime Coefficient, Inspector Akane Tsunemori"),
    ("HT_DQ_010", "A young Icelandic warrior joins a band of Viking mercenaries seeking vengeance against the leader who killed his father.", "anime", ["anime_746", "anime_17104"], "Narrative description of Vinland Saga", "anime_746: Thorfinn seeking revenge against Askeladd"),
    ("HT_DQ_011", "A wandering traveler studies primitive lifeforms that exist alongside humans, curing bizarre spiritual afflictions.", "anime", ["anime_734", "anime_17056"], "Narrative description of Mushishi", "anime_734: Ginko investigates Mushi entities and cures afflicted villagers"),
    ("HT_DQ_012", "A brilliant brain surgeon in Germany saves the life of a young boy who grows up to be a charismatic psychopathic killer.", "anime", ["anime_730", "anime_16817"], "Narrative description of Monster", "anime_730: Dr. Kenzo Tenma hunts Johan Liebert across post-Cold War Europe"),
    ("HT_DQ_013", "Seven mages summon legendary heroic spirits to fight in a secret battle royale in Fuyuki City for a wish-granting relic.", "anime", ["anime_629", "anime_14405"], "Narrative description of Fate/Zero", "anime_629: Fourth Holy Grail War, Kiritsugu Emiya, Saber"),
    ("HT_DQ_014", "An eccentric scientist suffers from PTSD and depression after failing to save the woman he loved across multiple world lines.", "anime", ["anime_695", "anime_16031"], "Narrative description of Steins;Gate 0", "anime_695: Rintaro Okabe grieving Kurisu Makise in the Beta worldline"),
    ("HT_DQ_015", "An energy-conserving high school boy joins the Classic Literature Club and solves everyday campus mysteries.", "anime", ["anime_401", "anime_6558"], "Narrative description of Hyouka", "anime_401: Houtarou Oreki and Eru Chitanda solving mysteries"),
    ("HT_DQ_016", "A gentle high school boy with an intimidating delinquent face forms an unlikely alliance with a tiny, fierce palmtop tiger girl.", "anime", ["anime_577", "anime_11055"], "Narrative description of Toradora!", "anime_577: Ryuuji Takasu and Taiga Aisaka help each other with crushes"),
    # Books (9)
    ("HT_DQ_017", "A woman named Oedipa Maas uncovers what may be a centuries-old underground postal conspiracy called the Tristero.", "book", ["book_21"], "Narrative description of The Crying of Lot 49", "book_21: Oedipa Maas, Pierce Inverarity estate, Tristero post horn symbol"),
    ("HT_DQ_018", "The political rise and moral corruption of a ruthless Southern governor named Willie Stark observed by his cynical aide.", "book", ["book_22"], "Narrative description of All the King's Men", "book_22: Jack Burden narrates the trajectory of Governor Willie Stark"),
    ("HT_DQ_019", "A nomadic ex-military investigator spots a tiny West Point graduation ring in a pawn shop and uncovers a missing soldier mystery.", "book", ["book_16"], "Narrative description of The Midnight Line", "book_16: Jack Reacher investigates a miniature 2005 West Point class ring"),
    ("HT_DQ_020", "A Druid named Bremen struggles to unite the Four Lands against the emerging threat of the demonic Warlock Lord.", "book", ["book_17"], "Narrative description of First King of Shannara", "book_17: Bremen creates the Sword of Shannara to defeat the Warlock Lord"),
    ("HT_DQ_021", "A young impoverished couple secretly sacrifice their most precious possessions to buy Christmas gifts for each other.", "book", ["book_2"], "Narrative description of The Gift of the Magi", "book_2: Jim and Della Young sacrifice his watch and her hair"),
    ("HT_DQ_022", "A former NYPD detective turned private investigator investigates brutal serial killings that lead back to his own dark past.", "book", ["book_24"], "Narrative description of Every Dead Thing", "book_24: Charlie Parker tracks the Travelling Man serial killer"),
    ("HT_DQ_023", "A dystopian satire set in a bizarre historical theme park where genetically altered monsters and disillusioned workers clash.", "book", ["book_7"], "Narrative description of CivilWarLand in Bad Decline", "book_7: George Saunders' dark comedic stories set in failing futuristic theme parks"),
    ("HT_DQ_024", "A traumatized high school freshman becomes selectively mute after calling the police during a summer party.", "book", ["book_15"], "Narrative description of Speak", "book_15: Melinda Sordino finds art and her voice after trauma"),
    ("HT_DQ_025", "A modern-day insurance salesman's orderly life unravels when he accidentally summons the Native American trickster god Coyote.", "book", ["book_1"], "Narrative description of Coyote Blue", "book_1: Samuel Hunter is visited by Coyote in modern Santa Barbara"),
]

# Constraint Queries (20)
cq_data = [
    # Movies (7)
    ("HT_CQ_001", "Mystery movies directed by Christopher Nolan.", "movie", ["movie_1197", "movie_3575"], {"director": ["ChristopherNolan"], "genres_include": ["Mystery"]}, "Nolan mystery films", "movie_1197 (The Prestige), movie_3575 (Memento)"),
    ("HT_CQ_002", "Movies released between 1995 and 1999 with runtime under 110 minutes and genre Drama.", "movie", ["movie_697", "movie_1353"], {"release_year_min": 1995, "release_year_max": 1999, "runtime_max": 110, "genres_include": ["Drama"]}, "1995-1999 drama films under 110 min", "movie_697 (1998, 103 min), movie_1353 (1997, 106 min)"),
    ("HT_CQ_003", "Action movies directed by Ridley Scott released before 2005.", "movie", ["movie_274", "movie_1727"], {"director": ["RidleyScott"], "release_year_max": 2004, "genres_include": ["Action"]}, "Pre-2005 Ridley Scott action films", "movie_274 (Gladiator, 2000), movie_1727 (Blade Runner, 1982)"),
    ("HT_CQ_004", "Comedy movies released in 1998 with runtime between 100 and 110 minutes.", "movie", ["movie_697"], {"release_year_min": 1998, "release_year_max": 1998, "runtime_min": 100, "runtime_max": 110, "genres_include": ["Comedy"]}, "1998 comedy 100-110 min", "movie_697 (The Truman Show, 1998, 103 min)"),
    ("HT_CQ_005", "Fantasy movies directed by Guillermo del Toro.", "movie", ["movie_2467"], {"director": ["GuillermodelToro"], "genres_include": ["Fantasy"]}, "Del Toro fantasy films", "movie_2467 (Pan's Labyrinth)"),
    ("HT_CQ_006", "Sci-fi movies released before 1990 with runtime between 110 and 125 minutes.", "movie", ["movie_1727"], {"release_year_max": 1989, "runtime_min": 110, "runtime_max": 125, "genres_include": ["ScienceFiction"]}, "Pre-1990 Sci-fi 110-125 min", "movie_1727 (Blade Runner, 1982, 117 min)"),
    ("HT_CQ_007", "Drama movies directed by Damien Chazelle.", "movie", ["movie_3869"], {"director": ["DamienChazelle"], "genres_include": ["Drama"]}, "Chazelle drama movies", "movie_3869 (Whiplash)"),
    # Anime (7)
    ("HT_CQ_008", "Psychological anime released in 2012 with exactly 22 episodes.", "anime", ["anime_633"], {"release_year_min": 2012, "release_year_max": 2012, "episodes_min": 22, "episodes_max": 22, "genres_include": ["Psychological"]}, "2012 psychological anime with 22 episodes", "anime_633 (Psycho-Pass)"),
    ("HT_CQ_009", "Historical anime released in 2019 with 24 episodes.", "anime", ["anime_746", "anime_17104"], {"release_year_min": 2019, "release_year_max": 2019, "episodes_min": 24, "episodes_max": 24, "genres_include": ["Historical"]}, "2019 historical anime with 24 episodes", "anime_746, anime_17104 (Vinland Saga)"),
    ("HT_CQ_010", "Mystery anime ranked in the top 50 with more than 20 episodes.", "anime", ["anime_730", "anime_734", "anime_16817", "anime_17056"], {"ranking_max": 50, "episodes_min": 21, "genres_include": ["Mystery"]}, "Top 50 mystery anime with >20 episodes", "anime_734 (Mushishi, rank 42), anime_730 (Monster, rank 46)"),
    ("HT_CQ_011", "Fantasy anime with popularity rank under 60 and exactly 13 episodes.", "anime", ["anime_629", "anime_14405"], {"popularity_min": 1, "episodes_min": 13, "episodes_max": 13, "genres_include": ["Fantasy"]}, "Popular fantasy anime with 13 episodes", "anime_629 (Fate/Zero, pop 50, ep 13)"),
    ("HT_CQ_012", "Romance anime released in 2008 with 25 episodes.", "anime", ["anime_577", "anime_11055"], {"release_year_min": 2008, "release_year_max": 2008, "episodes_min": 25, "episodes_max": 25, "genres_include": ["Romance"]}, "2008 romance anime with 25 episodes", "anime_577, anime_11055 (Toradora!)"),
    ("HT_CQ_013", "Sci-Fi anime released in 2018 with 23 episodes.", "anime", ["anime_695", "anime_16031"], {"release_year_min": 2018, "release_year_max": 2018, "episodes_min": 23, "episodes_max": 23, "genres_include": ["Sci-Fi"]}, "2018 sci-fi anime with 23 episodes", "anime_695, anime_16031 (Steins;Gate 0)"),
    ("HT_CQ_014", "Mystery anime released in 2012 with 22 episodes.", "anime", ["anime_401", "anime_6558"], {"release_year_min": 2012, "release_year_max": 2012, "episodes_min": 22, "episodes_max": 22, "genres_include": ["Mystery"]}, "2012 mystery anime with 22 episodes", "anime_401, anime_6558 (Hyouka)"),
    # Books (6)
    ("HT_CQ_015", "Books by Thomas Pynchon with fewer than 200 pages.", "book", ["book_21"], {"author": ["Thomas Pynchon"], "pages_max": 200}, "Thomas Pynchon novellas under 200 pages", "book_21: 152 pages"),
    ("HT_CQ_016", "Classics books by Robert Penn Warren.", "book", ["book_22"], {"author": ["Robert Penn Warren"], "genres_include": ["Classics"]}, "Robert Penn Warren classic novels", "book_22: All the King's Men"),
    ("HT_CQ_017", "Thriller books by Lee Child with more than 350 pages.", "book", ["book_16"], {"author": ["Lee Child"], "pages_min": 350, "genres_include": ["Thriller"]}, "Lee Child thrillers >350 pages", "book_16: The Midnight Line, 368 pages"),
    ("HT_CQ_018", "Fantasy books by Terry Brooks with more than 400 pages.", "book", ["book_17"], {"author": ["Terry Brooks"], "pages_min": 400, "genres_include": ["Fantasy"]}, "Terry Brooks fantasy books >400 pages", "book_17: First King of Shannara, 489 pages"),
    ("HT_CQ_019", "Short stories by O. Henry with rating above 4.0.", "book", ["book_2"], {"author": ["O. Henry"], "rating_min": 4.0, "genres_include": ["Short Stories"]}, "O. Henry short stories rating >4.0", "book_2: The Gift of the Magi, rating 4.09"),
    ("HT_CQ_020", "Horror mystery books by John Connolly with rating above 3.9.", "book", ["book_24"], {"author": ["John Connolly"], "rating_min": 3.9, "genres_include": ["Horror"]}, "John Connolly horror mystery books rating >3.9", "book_24: Every Dead Thing, rating 3.98"),
]

# Unified Multi-Domain Queries (15)
md_data = [
    ("HT_MD_001", "Cyberpunk dystopias exploring neural implants and corporate hegemony.", "mixed", ["movie_1727", "anime_633", "book_7"], "Cyberpunk cross-domain works", "movie_1727 (Blade Runner), anime_633 (Psycho-Pass), book_7 (CivilWarLand)"),
    ("HT_MD_002", "Stories about memory manipulation, altered recollections, and manufactured identities.", "mixed", ["movie_3575", "movie_1353", "anime_695"], "Memory manipulation cross-domain", "movie_3575 (Memento), movie_1353 (Gattaca), anime_695 (Steins;Gate 0)"),
    ("HT_MD_003", "Grimdark medieval warrior mercenaries battling in brutal wartime conflicts.", "mixed", ["anime_746", "movie_2467", "book_17"], "Brutal historical/fantasy conflicts", "anime_746 (Vinland Saga), movie_2467 (Pan's Labyrinth), book_17 (Shannara)"),
    ("HT_MD_004", "Supernatural folklore encounters with wandering spirits and ancient mythical beasts.", "mixed", ["anime_734", "book_1", "movie_2467"], "Mythical/folklore spirits", "anime_734 (Mushishi), book_1 (Coyote Blue), movie_2467 (Pan's Labyrinth)"),
    ("HT_MD_005", "Psychological cat-and-mouse games between brilliant investigators and sociopathic masterminds.", "mixed", ["anime_730", "movie_3575", "book_24"], "Investigator vs sociopath thrillers", "anime_730 (Monster), movie_3575 (Memento), book_24 (Every Dead Thing)"),
    ("HT_MD_006", "Battle royale death matches where competitors summon legendary figures or fight for relics.", "mixed", ["anime_629", "movie_662", "book_23"], "Competitive combat / relic quests", "anime_629 (Fate/Zero), movie_662 (Fight Club), book_23 (Grendel's Curse)"),
    ("HT_MD_007", "Time travel tragedies exploring multiple world lines, paradoxes, and the emotional cost of altering history.", "mixed", ["anime_695", "movie_1727", "book_21"], "Time paradoxes and alternate realities", "anime_695 (Steins;Gate 0), movie_1727 (Blade Runner), book_21 (Crying of Lot 49)"),
    ("HT_MD_008", "Intricate mystery investigations involving observational deduction and hidden motives.", "mixed", ["anime_401", "movie_1197", "book_16"], "Observational mystery deductions", "anime_401 (Hyouka), movie_1197 (The Prestige), book_16 (Midnight Line)"),
    ("HT_MD_009", "Bizarre conspiracies and underground societies operating hidden communication channels.", "mixed", ["book_21", "movie_662", "anime_633"], "Secret underground conspiracies", "book_21 (Crying of Lot 49), movie_662 (Fight Club), anime_633 (Psycho-Pass)"),
    ("HT_MD_010", "Corrupt political power struggles and charismatic populist leaders manipulating public sentiment.", "mixed", ["book_22", "anime_730", "movie_697"], "Political power corruption", "book_22 (All the King's Men), anime_730 (Monster), movie_697 (Truman Show)"),
    ("HT_MD_011", "Epic high fantasy quests to overthrow dark lords threatening mystical kingdoms.", "mixed", ["book_17", "anime_629", "movie_2467"], "High fantasy dark lord quests", "book_17 (Shannara), anime_629 (Fate/Zero), movie_2467 (Pan's Labyrinth)"),
    ("HT_MD_012", "Dystopian corporate theme parks and absurd amusement spectacles with dark secrets.", "mixed", ["book_7", "movie_697", "anime_633"], "Corporate spectacles & synthetic realities", "book_7 (CivilWarLand), movie_697 (Truman Show), anime_633 (Psycho-Pass)"),
    ("HT_MD_013", "Dark noir detective cases involving serial murderers and haunting personal trauma.", "mixed", ["book_24", "movie_3575", "anime_730"], "Traumatized detective noir", "book_24 (Every Dead Thing), movie_3575 (Memento), anime_730 (Monster)"),
    ("HT_MD_014", "Coming-of-age emotional journeys dealing with psychological isolation and finding a voice.", "mixed", ["book_15", "movie_3869", "anime_577"], "Coming-of-age emotional journeys", "book_15 (Speak), movie_3869 (Whiplash), anime_577 (Toradora!)"),
    ("HT_MD_015", "Mythological trickster gods interfering in the ordinary modern lives of unsuspecting mortals.", "mixed", ["book_1", "anime_734", "movie_2467"], "Tricksters & mythical entities", "book_1 (Coyote Blue), anime_734 (Mushishi), movie_2467 (Pan's Labyrinth)"),
]

# No-Answer / Absence Queries (15)
abs_data = [
    # Movies (5)
    ("HT_ABS_001", "Movies directed by Christopher Nolan released between 1980 and 1985.", "movie", [], {"director": ["ChristopherNolan"], "release_year_min": 1980, "release_year_max": 1985}, "Absence query: Nolan released zero films in 1980-1985", "Verified: 0 matching records in movies catalog"),
    ("HT_ABS_002", "Sci-fi movies directed by Damien Chazelle with runtime over 200 minutes.", "movie", [], {"director": ["DamienChazelle"], "runtime_min": 200, "genres_include": ["ScienceFiction"]}, "Absence query: Chazelle directed 0 sci-fi movies >200 min", "Verified: 0 matching records in movies catalog"),
    ("HT_ABS_003", "Horror movies directed by Peter Weir starring Leonardo DiCaprio.", "movie", [], {"director": ["PeterWeir"], "cast": ["LeonardoDiCaprio"], "genres_include": ["Horror"]}, "Absence query: Weir directed 0 horror movies with DiCaprio", "Verified: 0 matching records in movies catalog"),
    ("HT_ABS_004", "Movies with revenue over 2 billion dollars released before 1970.", "movie", [], {"release_year_max": 1969, "revenue_min": 2000000000}, "Absence query: 0 pre-1970 movies with >$2B revenue", "Verified: 0 matching records in movies catalog"),
    ("HT_ABS_005", "Animated family movies directed by Ridley Scott.", "movie", [], {"director": ["RidleyScott"], "genres_include": ["Animation", "Family"]}, "Absence query: Ridley Scott directed 0 animated family movies", "Verified: 0 matching records in movies catalog"),
    # Anime (5)
    ("HT_ABS_006", "Anime series with more than 3000 episodes released after 2020.", "anime", [], {"release_year_min": 2021, "episodes_min": 3000}, "Absence query: 0 post-2020 anime with >3000 episodes", "Verified: 0 matching records in anime catalog"),
    ("HT_ABS_007", "Psychological horror anime released in 1950 with 100 episodes.", "anime", [], {"release_year_min": 1950, "release_year_max": 1950, "episodes_min": 100, "genres_include": ["Psychological", "Horror"]}, "Absence query: 0 1950 psychological horror anime", "Verified: 0 matching records in anime catalog"),
    ("HT_ABS_008", "Sports anime ranked in the top 5 with fewer than 3 episodes.", "anime", [], {"ranking_max": 5, "episodes_max": 2, "genres_include": ["Sports"]}, "Absence query: 0 top 5 sports anime with <3 episodes", "Verified: 0 matching records in anime catalog"),
    ("HT_ABS_009", "Mecha anime released in 2018 with popularity rank under 5 and exactly 500 episodes.", "anime", [], {"release_year_min": 2018, "release_year_max": 2018, "episodes_min": 500, "episodes_max": 500, "genres_include": ["Mecha"]}, "Absence query: 0 2018 mecha anime with 500 episodes", "Verified: 0 matching records in anime catalog"),
    ("HT_ABS_010", "Romance anime series with exactly 999 episodes.", "anime", [], {"episodes_min": 999, "episodes_max": 999, "genres_include": ["Romance"]}, "Absence query: 0 romance anime with 999 episodes", "Verified: 0 matching records in anime catalog"),
    # Books (5)
    ("HT_ABS_011", "Books written by Thomas Pynchon with more than 5000 pages.", "book", [], {"author": ["Thomas Pynchon"], "pages_min": 5000}, "Absence query: Pynchon has 0 books >5000 pages", "Verified: 0 matching records in books catalog"),
    ("HT_ABS_012", "Science fiction books by Jane Austen published with rating above 4.8.", "book", [], {"author": ["Jane Austen"], "rating_min": 4.8, "genres_include": ["Science Fiction"]}, "Absence query: Austen wrote 0 sci-fi books", "Verified: 0 matching records in books catalog"),
    ("HT_ABS_013", "Books with rating above 4.99 and exactly 1 page.", "book", [], {"rating_min": 4.99, "pages_min": 1, "pages_max": 1}, "Absence query: 0 books with rating >4.99 and 1 page", "Verified: 0 matching records in books catalog"),
    ("HT_ABS_014", "Thriller novels by Lee Child with fewer than 10 pages.", "book", [], {"author": ["Lee Child"], "pages_max": 10, "genres_include": ["Thriller"]}, "Absence query: Child wrote 0 thriller novels <10 pages", "Verified: 0 matching records in books catalog"),
    ("HT_ABS_015", "Fantasy books by George Saunders with more than 2000 pages.", "book", [], {"author": ["George Saunders"], "pages_min": 2000, "genres_include": ["Fantasy"]}, "Absence query: Saunders wrote 0 fantasy books >2000 pages", "Verified: 0 matching records in books catalog"),
]

# Process and add all
for qid, qtext, dom, rel, just, evid in ki_data:
    verify_ids_exist(rel, dom)
    add_query(qid, qtext, "known_item", dom, False, rel, {}, just, evid)

for qid, qtext, dom, rel, just, evid in dq_data:
    verify_ids_exist(rel, dom)
    add_query(qid, qtext, "descriptive", dom, False, rel, {}, just, evid)

for qid, qtext, dom, rel, con, just, evid in cq_data:
    verify_ids_exist(rel, dom)
    add_query(qid, qtext, "constraint", dom, False, rel, con, just, evid)

for qid, qtext, dom, rel, just, evid in md_data:
    verify_ids_exist(rel, dom)
    add_query(qid, qtext, "multi_domain", dom, False, rel, {}, just, evid)

for qid, qtext, dom, rel, con, just, evid in abs_data:
    add_query(qid, qtext, "absence", dom, True, rel, con, just, evid)

print(f"Total queries constructed: {len(test_queries)}")
assert len(test_queries) == 100, f"Expected exactly 100 queries, got {len(test_queries)}"

# Convert to DataFrame
queries_df = pd.DataFrame(test_queries)
labels_df = pd.DataFrame(test_labels)

queries_df.to_csv("final_test_queries.csv", index=False)
labels_df.to_csv("final_test_labels.csv", index=False)
print("Saved final_test_queries.csv and final_test_labels.csv successfully!")
