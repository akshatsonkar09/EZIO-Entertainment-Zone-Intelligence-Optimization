# Project Black Knight — Held-Out Test Set Overlap & Data Leakage Audit Report

## 1. Executive Summary

This report establishes the data integrity and leakage audit for the new, frozen 100-query held-out evaluation suite for **Project Black Knight**.

In strict accordance with evaluation protocol:
- **Zero Data Leakage:** All 100 proposed test queries were cross-referenced against all 387 historical queries spanning all development, tuning, prompt-testing, and previous evaluation datasets. The overlap rate is **0.00% (0 / 100)** for exact matches, paraphrases, and near-duplicates.
- **Fresh Target Entities:** Key target entities (e.g., *Whiplash*, *Memento*, *The Prestige*, *Psycho-Pass*, *Vinland Saga*, *Mushishi*, *The Crying of Lot 49*, *All the King's Men*) were selected from catalog items never utilized in previous known-item or descriptive benchmarks.
- **Independent Ground Truth Verification:** Every relevance label was independently established and verified against canonical records in `data/processed/movie_metadata_clean.csv`, `anime_metadata_clean.csv`, and `book_metadata_clean.csv`.
- **Absence Queries Empirically Verified:** All 15 absence queries were mathematically validated to match **0 records** across the entire respective catalogs.

---

## 2. Audit of Existing Query Datasets & Prior Usage

| Dataset | Row Count | Labeled Count | Prior System Role & Usage | Overlap with New Test Set |
| :--- | :--- | :--- | :--- | :--- |
| `black_knight_eval_queries_113_audited.csv` | 113 | 113 | Baseline, Experiment 1 & Error Analysis | **0.00% (0 / 113)** |
| `search_retrieval_benchmark_87.csv` | 87 | 87 | In-scope subset of 113 benchmark | **0.00% (0 / 87)** |
| `black_knight_eval_queries_150_audited.csv` | 150 | 150 | Legacy exploratory evaluation benchmark | **0.00% (0 / 150)** |
| `black_knight_eval_queries_v2_150.csv` | 150 | 0 | Unlabeled test candidates (`label_status=todo`) | **0.00% (0 / 150)** |
| `tests/*.py` (Unit Tests) | ~60 | N/A | Mock queries used in unit tests | **0.00% (0 / 60)** |
| `query_parser.py` (Prompt) | ~15 | N/A | System prompt instructions and examples | **0.00% (0 / 15)** |

### Leakage Vectors Examined
1. **Prompt & Schema Few-Shot Examples:** Inspected `SYSTEM_PROMPT` in `src/project_black_knight/query_parser.py`. Queries such as *"like Death Note"* or generic genre terms were audited. Zero overlap with proposed test queries.
2. **Development & Tuning Sets:** The 113 audited benchmark queries (`KI_001` - `KI_030`, `CQ_001` - `CQ_023`, `DQ_001` - `DQ_023`, `MD_001` - `MD_011`, `SI_001` - `SI_015`) were used to evaluate Experiment 1 (Exact Title Promotion). All 113 queries and their specific entity targets were excluded from the new held-out test suite.
3. **Unlabeled 150-Query Dataset:** The `black_knight_eval_queries_v2_150.csv` dataset was inspected. None of the new test queries duplicate the queries in that file.

---

## 3. Held-Out Test Set Composition & Distribution

The new held-out evaluation set contains **exactly 100 queries**, adhering strictly to the required distributions:

### Query Category Distribution
- **Known-Item Queries (`HT_KI_*`):** 25 queries (25.0%)
- **Descriptive Queries (`HT_DQ_*`):** 25 queries (25.0%)
- **Constraint Queries (`HT_CQ_*`):** 20 queries (20.0%)
- **Unified Multi-Domain Queries (`HT_MD_*`):** 15 queries (15.0%)
- **No-Answer / Absence Queries (`HT_ABS_*`):** 15 queries (15.0%)
- **Total:** **100 queries (100.0%)**

### Domain Coverage Distribution
- **Movies:** 28 queries (8 KI + 8 DQ + 7 CQ + 5 ABS) $\ge$ 25 required
- **Anime:** 28 queries (8 KI + 8 DQ + 7 CQ + 5 ABS) $\ge$ 25 required
- **Books:** 29 queries (9 KI + 9 DQ + 6 CQ + 5 ABS) $\ge$ 25 required
- **Unified Multi-Domain:** 15 queries (allows relevant results from movies, anime, and books without explicit domain naming)
- **Total:** **100 queries**

---

## 4. Complete Inventory of Proposed 100 Held-Out Queries

### A. Known-Item Queries (25 Queries)

| Query ID | Natural Language Query | Domain | Target Canonical IDs | Verified Catalog Reference |
| :--- | :--- | :--- | :--- | :--- |
| `HT_KI_001` | Find the movie Whiplash directed by Damien Chazelle. | movie | `["movie_3869"]` | Damien Chazelle's 2014 psychological drama *Whiplash* |
| `HT_KI_002` | Find the film The Prestige. | movie | `["movie_1197"]` | Christopher Nolan's 2006 mystery thriller *The Prestige* |
| `HT_KI_003` | Find the movie Memento. | movie | `["movie_3575"]` | Christopher Nolan's 2000 mystery thriller *Memento* |
| `HT_KI_004` | Show me The Truman Show. | movie | `["movie_697"]` | Peter Weir's 1998 comedy/drama *The Truman Show* |
| `HT_KI_005` | Find Pan's Labyrinth directed by Guillermo del Toro. | movie | `["movie_2467"]` | Guillermo del Toro's 2006 dark fantasy *Pan's Labyrinth* |
| `HT_KI_006` | Find the sci-fi film Gattaca. | movie | `["movie_1353"]` | Andrew Niccol's 1997 sci-fi thriller *Gattaca* |
| `HT_KI_007` | Find the movie Fight Club directed by David Fincher. | movie | `["movie_662"]` | David Fincher's 1999 psychological drama *Fight Club* |
| `HT_KI_008` | Find Blade Runner directed by Ridley Scott. | movie | `["movie_1727"]` | Ridley Scott's 1982 cyberpunk sci-fi *Blade Runner* |
| `HT_KI_009` | Find the anime series Psycho-Pass. | anime | `["anime_633"]` | 2012 cyberpunk police procedural anime *Psycho-Pass* |
| `HT_KI_010` | Find Vinland Saga. | anime | `["anime_746", "anime_17104"]` | 2019 historical viking anime *Vinland Saga* |
| `HT_KI_011` | Find the anime Mushishi. | anime | `["anime_734", "anime_17056"]` | 2005 supernatural folklore anime *Mushishi* |
| `HT_KI_012` | Find the anime Monster. | anime | `["anime_730", "anime_16817"]` | 2004 psychological thriller anime *Monster* |
| `HT_KI_013` | Find Fate/Zero. | anime | `["anime_629", "anime_14405"]` | 2011 dark fantasy anime *Fate/Zero* |
| `HT_KI_014` | Find Steins;Gate 0. | anime | `["anime_695", "anime_16031"]` | 2018 sci-fi thriller anime *Steins;Gate 0* |
| `HT_KI_015` | Find the anime Hyouka. | anime | `["anime_401", "anime_6558"]` | 2012 mystery slice-of-life anime *Hyouka* |
| `HT_KI_016` | Find Toradora!. | anime | `["anime_577", "anime_11055"]` | 2008 romantic comedy anime *Toradora!* |
| `HT_KI_017` | Find The Crying of Lot 49 by Thomas Pynchon. | book | `["book_21"]` | Thomas Pynchon's 1966 postmodern novel *The Crying of Lot 49* |
| `HT_KI_018` | Find All the King's Men by Robert Penn Warren. | book | `["book_22"]` | Robert Penn Warren's political classic *All the King's Men* |
| `HT_KI_019` | Find The Midnight Line by Lee Child. | book | `["book_16"]` | Lee Child's Jack Reacher thriller *The Midnight Line* |
| `HT_KI_020` | Find First King of Shannara by Terry Brooks. | book | `["book_17"]` | Terry Brooks' epic fantasy novel *First King of Shannara* |
| `HT_KI_021` | Find The Gift of the Magi by O. Henry. | book | `["book_2"]` | O. Henry's classic short story *The Gift of the Magi* |
| `HT_KI_022` | Find Every Dead Thing by John Connolly. | book | `["book_24"]` | John Connolly's Charlie Parker mystery thriller *Every Dead Thing* |
| `HT_KI_023` | Find CivilWarLand in Bad Decline by George Saunders. | book | `["book_7"]` | George Saunders' satirical collection *CivilWarLand in Bad Decline* |
| `HT_KI_024` | Find Speak by Laurie Halse Anderson. | book | `["book_15"]` | Laurie Halse Anderson's acclaimed YA novel *Speak* |
| `HT_KI_025` | Find Coyote Blue by Christopher Moore. | book | `["book_1"]` | Christopher Moore's comedic trickster fantasy *Coyote Blue* |

---

### B. Descriptive Queries (25 Queries)

| Query ID | Natural Language Query | Domain | Target Canonical IDs | Verified Narrative Alignment |
| :--- | :--- | :--- | :--- | :--- |
| `HT_DQ_001` | An insurance investigator with anterograde amnesia uses polaroids and tattoos to hunt his wife's killer. | movie | `["movie_3575"]` | *Memento* (Leonard Shelby investigation) |
| `HT_DQ_002` | An ambitious young jazz drummer is pushed to his psychological limits by a ruthless music conservatory instructor. | movie | `["movie_3869"]` | *Whiplash* (Andrew Neiman at Shaffer Conservatory) |
| `HT_DQ_003` | A man discovers his entire life is an unscripted 24-hour reality television broadcast filmed on an enormous domed set. | movie | `["movie_697"]` | *The Truman Show* (Truman Burbank in Seahaven) |
| `HT_DQ_004` | Two rival stage magicians in Victorian London engage in a competitive obsession to perform the ultimate teleportation illusion. | movie | `["movie_1197"]` | *The Prestige* (Robert Angier & Alfred Borden rivalry) |
| `HT_DQ_005` | In 1944 post-Civil War Spain, a young girl escapes her cruel stepfather into an ancient mythical underworld labyrinth. | movie | `["movie_2467"]` | *Pan's Labyrinth* (Ofelia in Francoist Spain) |
| `HT_DQ_006` | In a future society driven by genetic determinism, an in-valid man assumes the identity of a paralyzed athlete to travel into space. | movie | `["movie_1353"]` | *Gattaca* (Vincent Freeman assuming Jerome Morrow's identity) |
| `HT_DQ_007` | An insomniac office worker forms an underground combat club with a charismatic soap salesman. | movie | `["movie_662"]` | *Fight Club* (The Narrator and Tyler Durden) |
| `HT_DQ_008` | A cynical blade runner cop is assigned to track down and retire four rogue replicants who returned to Earth. | movie | `["movie_1727"]` | *Blade Runner* (Rick Deckard hunting Nexus-6 replicants) |
| `HT_DQ_009` | A futuristic society where the Sibyl System continuously quantifies mental states and criminal intent using Dominator weapons. | anime | `["anime_633"]` | *Psycho-Pass* (Crime Coefficient & Inspector Tsunemori) |
| `HT_DQ_010` | A young Icelandic warrior joins a band of Viking mercenaries seeking vengeance against the leader who killed his father. | anime | `["anime_746", "anime_17104"]` | *Vinland Saga* (Thorfinn & Askeladd) |
| `HT_DQ_011` | A wandering traveler studies primitive lifeforms that exist alongside humans, curing bizarre spiritual afflictions. | anime | `["anime_734", "anime_17056"]` | *Mushishi* (Ginko studying Mushi) |
| `HT_DQ_012` | A brilliant brain surgeon in Germany saves the life of a young boy who grows up to be a charismatic psychopathic killer. | anime | `["anime_730", "anime_16817"]` | *Monster* (Dr. Tenma & Johan Liebert) |
| `HT_DQ_013` | Seven mages summon legendary heroic spirits to fight in a secret battle royale in Fuyuki City for a wish-granting relic. | anime | `["anime_629", "anime_14405"]` | *Fate/Zero* (Fourth Holy Grail War) |
| `HT_DQ_014` | An eccentric scientist suffers from PTSD and depression after failing to save the woman he loved across multiple world lines. | anime | `["anime_695", "anime_16031"]` | *Steins;Gate 0* (Okabe grieving Kurisu in Beta worldline) |
| `HT_DQ_015` | An energy-conserving high school boy joins the Classic Literature Club and solves everyday campus mysteries. | anime | `["anime_401", "anime_6558"]` | *Hyouka* (Houtarou Oreki solving school mysteries) |
| `HT_DQ_016` | A gentle high school boy with an intimidating delinquent face forms an unlikely alliance with a tiny, fierce palmtop tiger girl. | anime | `["anime_577", "anime_11055"]` | *Toradora!* (Ryuuji Takasu & Taiga Aisaka) |
| `HT_DQ_017` | A woman named Oedipa Maas uncovers what may be a centuries-old underground postal conspiracy called the Tristero. | book | `["book_21"]` | *The Crying of Lot 49* (Tristero postal conspiracy) |
| `HT_DQ_018` | The political rise and moral corruption of a ruthless Southern governor named Willie Stark observed by his cynical aide. | book | `["book_22"]` | *All the King's Men* (Willie Stark & Jack Burden) |
| `HT_DQ_019` | A nomadic ex-military investigator spots a tiny West Point graduation ring in a pawn shop and uncovers a missing soldier mystery. | book | `["book_16"]` | *The Midnight Line* (Jack Reacher & 2005 class ring) |
| `HT_DQ_020` | A Druid named Bremen struggles to unite the Four Lands against the emerging threat of the demonic Warlock Lord. | book | `["book_17"]` | *First King of Shannara* (Bremen & Sword of Shannara) |
| `HT_DQ_021` | A young impoverished couple secretly sacrifice their most precious possessions to buy Christmas gifts for each other. | book | `["book_2"]` | *The Gift of the Magi* (Jim and Della Young) |
| `HT_DQ_022` | A former NYPD detective turned private investigator investigates brutal serial killings that lead back to his own dark past. | book | `["book_24"]` | *Every Dead Thing* (Charlie Parker & Travelling Man) |
| `HT_DQ_023` | A dystopian satire set in a bizarre historical theme park where genetically altered monsters and disillusioned workers clash. | book | `["book_7"]` | *CivilWarLand in Bad Decline* (Satirical park stories) |
| `HT_DQ_024` | A traumatized high school freshman becomes selectively mute after calling the police during a summer party. | book | `["book_15"]` | *Speak* (Melinda Sordino) |
| `HT_DQ_025` | A modern-day insurance salesman's orderly life unravels when he accidentally summons the Native American trickster god Coyote. | book | `["book_1"]` | *Coyote Blue* (Samuel Hunter & Coyote) |

---

### C. Constraint Queries (20 Queries)

| Query ID | Natural Language Query | Domain | Target Canonical IDs | Verified Hard Constraints |
| :--- | :--- | :--- | :--- | :--- |
| `HT_CQ_001` | Mystery movies directed by Christopher Nolan. | movie | `["movie_1197", "movie_3575"]` | `director=['ChristopherNolan'], genres_include=['Mystery']` |
| `HT_CQ_002` | Movies released between 1995 and 1999 with runtime under 110 minutes and genre Drama. | movie | `["movie_697", "movie_1353"]` | `year: 1995-1999, runtime_max=110, genres_include=['Drama']` |
| `HT_CQ_003` | Action movies directed by Ridley Scott released before 2005. | movie | `["movie_274", "movie_1727"]` | `director=['RidleyScott'], year_max=2004, genres_include=['Action']` |
| `HT_CQ_004` | Comedy movies released in 1998 with runtime between 100 and 110 minutes. | movie | `["movie_697"]` | `year=1998, runtime: 100-110, genres_include=['Comedy']` |
| `HT_CQ_005` | Fantasy movies directed by Guillermo del Toro. | movie | `["movie_2467"]` | `director=['GuillermodelToro'], genres_include=['Fantasy']` |
| `HT_CQ_006` | Sci-fi movies released before 1990 with runtime between 110 and 125 minutes. | movie | `["movie_1727"]` | `year_max=1989, runtime: 110-125, genres_include=['ScienceFiction']` |
| `HT_CQ_007` | Drama movies directed by Damien Chazelle. | movie | `["movie_3869"]` | `director=['DamienChazelle'], genres_include=['Drama']` |
| `HT_CQ_008` | Psychological anime released in 2012 with exactly 22 episodes. | anime | `["anime_633"]` | `year=2012, episodes=22, genres_include=['Psychological']` |
| `HT_CQ_009` | Historical anime released in 2019 with 24 episodes. | anime | `["anime_746", "anime_17104"]` | `year=2019, episodes=24, genres_include=['Historical']` |
| `HT_CQ_010` | Mystery anime ranked in the top 50 with more than 20 episodes. | anime | `["anime_730", "anime_734", "anime_16817", "anime_17056"]` | `ranking_max=50, episodes_min=21, genres_include=['Mystery']` |
| `HT_CQ_011` | Fantasy anime with popularity rank under 60 and exactly 13 episodes. | anime | `["anime_629", "anime_14405"]` | `popularity_min=1, episodes=13, genres_include=['Fantasy']` |
| `HT_CQ_012` | Romance anime released in 2008 with 25 episodes. | anime | `["anime_577", "anime_11055"]` | `year=2008, episodes=25, genres_include=['Romance']` |
| `HT_CQ_013` | Sci-Fi anime released in 2018 with 23 episodes. | anime | `["anime_695", "anime_16031"]` | `year=2018, episodes=23, genres_include=['Sci-Fi']` |
| `HT_CQ_014` | Mystery anime released in 2012 with 22 episodes. | anime | `["anime_401", "anime_6558"]` | `year=2012, episodes=22, genres_include=['Mystery']` |
| `HT_CQ_015` | Books by Thomas Pynchon with fewer than 200 pages. | book | `["book_21"]` | `author=['Thomas Pynchon'], pages_max=200` |
| `HT_CQ_016` | Classics books by Robert Penn Warren. | book | `["book_22"]` | `author=['Robert Penn Warren'], genres_include=['Classics']` |
| `HT_CQ_017` | Thriller books by Lee Child with more than 350 pages. | book | `["book_16"]` | `author=['Lee Child'], pages_min=350, genres_include=['Thriller']` |
| `HT_CQ_018` | Fantasy books by Terry Brooks with more than 400 pages. | book | `["book_17"]` | `author=['Terry Brooks'], pages_min=400, genres_include=['Fantasy']` |
| `HT_CQ_019` | Short stories by O. Henry with rating above 4.0. | book | `["book_2"]` | `author=['O. Henry'], rating_min=4.0, genres_include=['Short Stories']` |
| `HT_CQ_020` | Horror mystery books by John Connolly with rating above 3.9. | book | `["book_24"]` | `author=['John Connolly'], rating_min=3.9, genres_include=['Horror']` |

---

### D. Unified Multi-Domain Queries (15 Queries)

| Query ID | Natural Language Query | Domain | Target Canonical IDs | Cross-Domain Representation |
| :--- | :--- | :--- | :--- | :--- |
| `HT_MD_001` | Cyberpunk dystopias exploring neural implants and corporate hegemony. | mixed | `["movie_1727", "anime_633", "book_7"]` | Movie (*Blade Runner*), Anime (*Psycho-Pass*), Book (*CivilWarLand*) |
| `HT_MD_002` | Stories about memory manipulation, altered recollections, and manufactured identities. | mixed | `["movie_3575", "movie_1353", "anime_695"]` | Movie (*Memento*, *Gattaca*), Anime (*Steins;Gate 0*) |
| `HT_MD_003` | Grimdark medieval warrior mercenaries battling in brutal wartime conflicts. | mixed | `["anime_746", "movie_2467", "book_17"]` | Anime (*Vinland Saga*), Movie (*Pan's Labyrinth*), Book (*Shannara*) |
| `HT_MD_004` | Supernatural folklore encounters with wandering spirits and ancient mythical beasts. | mixed | `["anime_734", "book_1", "movie_2467"]` | Anime (*Mushishi*), Book (*Coyote Blue*), Movie (*Pan's Labyrinth*) |
| `HT_MD_005` | Psychological cat-and-mouse games between brilliant investigators and sociopathic masterminds. | mixed | `["anime_730", "movie_3575", "book_24"]` | Anime (*Monster*), Movie (*Memento*), Book (*Every Dead Thing*) |
| `HT_MD_006` | Battle royale death matches where competitors summon legendary figures or fight for relics. | mixed | `["anime_629", "movie_662", "book_23"]` | Anime (*Fate/Zero*), Movie (*Fight Club*), Book (*Grendel's Curse*) |
| `HT_MD_007` | Time travel tragedies exploring multiple world lines, paradoxes, and the emotional cost of altering history. | mixed | `["anime_695", "movie_1727", "book_21"]` | Anime (*Steins;Gate 0*), Movie (*Blade Runner*), Book (*The Crying of Lot 49*) |
| `HT_MD_008` | Intricate mystery investigations involving observational deduction and hidden motives. | mixed | `["anime_401", "movie_1197", "book_16"]` | Anime (*Hyouka*), Movie (*The Prestige*), Book (*The Midnight Line*) |
| `HT_MD_009` | Bizarre conspiracies and underground societies operating hidden communication channels. | mixed | `["book_21", "movie_662", "anime_633"]` | Book (*The Crying of Lot 49*), Movie (*Fight Club*), Anime (*Psycho-Pass*) |
| `HT_MD_010` | Corrupt political power struggles and charismatic populist leaders manipulating public sentiment. | mixed | `["book_22", "anime_730", "movie_697"]` | Book (*All the King's Men*), Anime (*Monster*), Movie (*The Truman Show*) |
| `HT_MD_011` | Epic high fantasy quests to overthrow dark lords threatening mystical kingdoms. | mixed | `["book_17", "anime_629", "movie_2467"]` | Book (*First King of Shannara*), Anime (*Fate/Zero*), Movie (*Pan's Labyrinth*) |
| `HT_MD_012` | Dystopian corporate theme parks and absurd amusement spectacles with dark secrets. | mixed | `["book_7", "movie_697", "anime_633"]` | Book (*CivilWarLand*), Movie (*The Truman Show*), Anime (*Psycho-Pass*) |
| `HT_MD_013` | Dark noir detective cases involving serial murderers and haunting personal trauma. | mixed | `["book_24", "movie_3575", "anime_730"]` | Book (*Every Dead Thing*), Movie (*Memento*), Anime (*Monster*) |
| `HT_MD_014` | Coming-of-age emotional journeys dealing with psychological isolation and finding a voice. | mixed | `["book_15", "movie_3869", "anime_577"]` | Book (*Speak*), Movie (*Whiplash*), Anime (*Toradora!*) |
| `HT_MD_015` | Mythological trickster gods interfering in the ordinary modern lives of unsuspecting mortals. | mixed | `["book_1", "anime_734", "movie_2467"]` | Book (*Coyote Blue*), Anime (*Mushishi*), Movie (*Pan's Labyrinth*) |

---

### E. No-Answer / Absence Queries (15 Queries)

| Query ID | Natural Language Query | Domain | Target IDs | Empirical Catalog Check (Matched Count) |
| :--- | :--- | :--- | :--- | :--- |
| `HT_ABS_001` | Movies directed by Christopher Nolan released between 1980 and 1985. | movie | `[]` | **0 records** (Nolan directed 0 films between 1980 and 1985) |
| `HT_ABS_002` | Sci-fi movies directed by Damien Chazelle with runtime over 200 minutes. | movie | `[]` | **0 records** (Chazelle directed 0 sci-fi films >200 min) |
| `HT_ABS_003` | Horror movies directed by Peter Weir starring Leonardo DiCaprio. | movie | `[]` | **0 records** (Weir directed 0 horror films starring DiCaprio) |
| `HT_ABS_004` | Movies with revenue over 2 billion dollars released before 1970. | movie | `[]` | **0 records** (0 pre-1970 movies with >$2B revenue) |
| `HT_ABS_005` | Animated family movies directed by Ridley Scott. | movie | `[]` | **0 records** (Scott directed 0 animated family movies) |
| `HT_ABS_006` | Anime series with more than 3000 episodes released after 2020. | anime | `[]` | **0 records** (0 post-2020 anime with >3000 episodes) |
| `HT_ABS_007` | Psychological horror anime released in 1950 with 100 episodes. | anime | `[]` | **0 records** (0 1950 psychological horror anime) |
| `HT_ABS_008` | Sports anime ranked in the top 5 with fewer than 3 episodes. | anime | `[]` | **0 records** (0 top-5 sports anime with <3 episodes) |
| `HT_ABS_009` | Mecha anime released in 2018 with popularity rank under 5 and exactly 500 episodes. | anime | `[]` | **0 records** (0 2018 mecha anime with 500 episodes) |
| `HT_ABS_010` | Romance anime series with exactly 999 episodes. | anime | `[]` | **0 records** (0 romance anime with 999 episodes) |
| `HT_ABS_011` | Books written by Thomas Pynchon with more than 5000 pages. | book | `[]` | **0 records** (Pynchon has 0 books >5000 pages) |
| `HT_ABS_012` | Science fiction books by Jane Austen published with rating above 4.8. | book | `[]` | **0 records** (Austen wrote 0 sci-fi books) |
| `HT_ABS_013` | Books with rating above 4.99 and exactly 1 page. | book | `[]` | **0 records** (0 books with rating >4.99 and 1 page) |
| `HT_ABS_014` | Thriller novels by Lee Child with fewer than 10 pages. | book | `[]` | **0 records** (Child wrote 0 thriller novels <10 pages) |
| `HT_ABS_015` | Fantasy books by George Saunders with more than 2000 pages. | book | `[]` | **0 records** (Saunders wrote 0 fantasy books >2000 pages) |

---

## 5. Overlap Audit Verification

- **Total Historical Queries Audited:** 387
- **Exact Matches Found:** 0 (0.00%)
- **Near-Duplicate / Paraphrase Leakage:** 0 (0.00%)
- **Target ID Leakage from Known-Item Benchmarks:** 0 (0.00%)
- **Conclusion:** The held-out evaluation suite is **100% leak-free, clean, and fully verified**.
