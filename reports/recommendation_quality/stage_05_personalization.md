# Stage 5 Report — Taste-Aware Personalization

## 1. Executive Summary & Status
- **Status:** `PASS` (Implementation and Functional Testing: `PASS`; Production Personalization Quality: `NOT VALIDATED` per instruction requirements).
- **Objective:** Allow a user's explicit preferences (liked/disliked items, preferred/disliked genres, preferred creators) to influence recommendation ranking while guaranteeing that the current non-personalized system remains a bit-for-bit identical, reliable fallback.
- **Key Empirical Results:**
  - **Zero-Profile Baseline Identity:** When `user_profile=None` or an empty profile is passed, recommendations match the non-personalized baseline bit-for-bit (0 rank shift, 100% ID and score parity).
  - **Inviolable Constraints:** Hard metadata filters (release year, genre exclusions) cannot be bypassed by strong personal preferences; 0 constraint violations across all tests.
  - **Demonstrated Taste Shift:** Evaluated across 6 clearly labeled synthetic user profiles; confirmed that disliked genres and creators demote unwanted candidates (e.g. demoting horror movie *Lake Placid* from top 3 when user dislikes horror) while elevating preferred attributes.
  - **Validation Status:** Marked as **`NOT VALIDATED`** for real human recommendation quality because repository datasets lack multi-turn human session logs and individualized relevance ground truth.
  - **All 8 Stage 5 unit/integration tests passed**; full regression suite passing (157 total passing tests).

---

## 2. Preference Representation Schema

Implemented in `src/project_black_knight/personalization.py`:

```python
class UserPreferences(BaseModel):
    user_id: str | None = None
    liked_item_ids: list[str] = Field(default_factory=list)
    disliked_item_ids: list[str] = Field(default_factory=list)
    preferred_genres: list[str] = Field(default_factory=list)
    disliked_genres: list[str] = Field(default_factory=list)
    reference_titles: list[str] = Field(default_factory=list)
    preferred_creators: list[str] = Field(default_factory=list)  # Directors, authors
    disliked_creators: list[str] = Field(default_factory=list)
```

### Key Architectural Safeguards
1. **Stateless & Privacy-Preserving:** Zero silent database persistence, cookies, or tracking. The profile is passed ephemerally per request.
2. **Modular Scoring Contribution:**
   $$S_{\text{final}} = S_{\text{base}} + (\beta \cdot S_{\text{personalization}})$$
   where $\beta = 0.35$ and $S_{\text{personalization}} \in [-1.0, 1.0]$.
3. **Deterministic Conflict Resolution:** If a user specifies a genre or creator in both preferred and disliked lists, the negative preference takes precedence for safety.
4. **Hard Filter Protection:** Hard filters (`get_valid_ids`) execute before candidate generation. Personalization only re-weights valid candidates that already satisfy all user constraints.

---

## 3. Functional Evaluation on Synthetic Profiles

Evaluated across 6 clearly labeled synthetic profiles:

| Profile ID | Description | Domain | Test Query | Observed Top-3 Change | Top-10 Mean Shift |
| :--- | :--- | :---: | :--- | :--- | :---: |
| `syn_user_01_nolan_scifi` | Hard sci-fi fan, prefers Christopher Nolan | Movie | *Mind-bending space exploration adventure* | Maintained high-affinity sci-fi (*Avatar*, *Interstellar*, *2001*) | 0.00 |
| `syn_user_02_anti_horror` | Action fan, strictly avoids horror | Movie | *Intense action thriller* | **Demoted horror-hybrid *Lake Placid* out of top 3; elevated *Invasion U.S.A.*** | **1.40** |
| `syn_user_03_cyberpunk_anime` | Cyberpunk & dark anime fan | Anime | *Dystopian future detective* | Maintained *UN-GO*, *Hurricane Polymar* | 0.00 |
| `syn_user_04_shounen_purist` | Classic shounen action fan | Anime | *Martial arts tournaments and battles* | Re-ordered shounen fighting titles | 0.20 |
| `syn_user_05_epic_fantasy_books` | Epic high fantasy reader | Book | *Ancient magic war and kingdom rebellion* | Re-ordered high fantasy epics | 0.20 |
| `syn_user_06_cozy_detective_books` | Cozy mystery reader avoiding violence | Book | *Clever detective murder mystery* | Boosted classic mystery titles | 0.40 |

### Validation Limitation Statement
> [!IMPORTANT]
> The above profiles are synthetic and used strictly for functional testing. Because the repository catalog does not contain real human user interaction histories or personalized test sets, personalization quality is officially marked **`NOT VALIDATED`** for real users.

---

## 4. Implementation Details

### Files Modified & Created
1. **`src/project_black_knight/personalization.py` (New Module):**
   - Implemented `UserPreferences` schema.
   - Implemented `compute_personalization_delta` and `apply_taste_personalization`.
2. **`src/project_black_knight/retrieval.py`:**
   - Added `user_profile` parameter to `hybrid_retrieve` and `search_black_knight`.
   - Inserted Step 6c (Taste-Aware Personalization) prior to candidate sorting.
3. **`tests/test_stage_05_personalization.py` (New Tests):**
   - 8 unit and integration tests verifying baseline identity, positive boosting, negative demotion, explicit item penalties, conflict safety, hard filter inviolability, and session isolation.
4. **`evaluation/evaluate_stage_05_personalization.py`:**
   - Functional benchmark runner on synthetic profiles.

---

## 5. Artifacts Persisted
- `reports/recommendation_quality/artifacts/stage_05/stage_05_metrics.json`
- `reports/recommendation_quality/artifacts/stage_05/stage_05_profile_tests.json`
- `reports/recommendation_quality/artifacts/stage_05/stage_05_tests.txt`

---

## 6. Reproduction Commands
- **Run Unit Tests:**
  `$env:PYTHONPATH='src'; project_black_knight\Scripts\python -m pytest tests/test_stage_05_personalization.py -v`
- **Run Evaluation:**
  `$env:PYTHONPATH='src'; project_black_knight\Scripts\python evaluation/evaluate_stage_05_personalization.py`

---

## 7. Next Stage Starting Point
- **Stage 5 Status:** `PASS` (Implemented & Functionally Tested; Quality `NOT VALIDATED`)
- **Stage 6 Starting Point:** Stage 6 focuses on **Building a Stronger Relevance Evaluation Framework** (creating a multi-domain, versioned reference-query evaluation benchmark with graded relevance 0-3, human-verified and audited ground truth, end-to-end ablation across all 6 stages, and benchmark manifest).
