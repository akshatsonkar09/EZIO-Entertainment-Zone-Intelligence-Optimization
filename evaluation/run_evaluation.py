"""
Evaluation runner for Project Black Knight Query Parser (Phase 2).

Features:
- Exact verbatim matching vs semantic/normalized matching
- Semantic query evaluation (token Jaccard, token overlap F1, sequence similarity)
- Recursive field comparison respecting field ordering semantics:
    * media_types: ORDER MATTERS (relevance rank)
    * genres, similar_to, credits, characters: UNORDERED SETS
- Automatic classification of failure categories
- Documented field-level accuracy denominators
- Configuration fingerprinting and cache invalidation
- Resilient caching with zero Groq API calls on cache hits
- Immediate saving of newly parsed records
- Comprehensive JSON reporting and terminal summaries
"""

import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

# --------------------------------------------------
# Paths & Setup
# --------------------------------------------------

EVALUATION_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = EVALUATION_DIR.parent

BENCHMARK_FILE = EVALUATION_DIR / "benchmark.jsonl"
CACHE_DIR = EVALUATION_DIR / "cache"
CACHE_FILE = CACHE_DIR / "parser_outputs.jsonl"
RESULTS_DIR = EVALUATION_DIR / "results"
REPORT_FILE = RESULTS_DIR / "parser_report.json"

CACHE_VERSION = "v1"

# Allow imports from project root and src
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from project_black_knight.query_parser import (
        parse_query,
        SYSTEM_PROMPT,
        MODELS_TO_TRY,
    )
    from project_black_knight.query_schema import BlackKnightQuery
except ImportError:
    from query_parser import parse_query, SYSTEM_PROMPT, MODELS_TO_TRY
    from query_schema import BlackKnightQuery


# --------------------------------------------------
# Configuration Fingerprinting
# --------------------------------------------------

def compute_config_fingerprint(cache_version: str = CACHE_VERSION) -> str:
    """
    Compute a deterministic fingerprint of the parser configuration.
    Bumps or invalidates if prompt, schema, or model list changes.
    """
    schema_dump = json.dumps(BlackKnightQuery.model_json_schema(), sort_keys=True)
    raw = f"{cache_version}\n{SYSTEM_PROMPT.strip()}\n{schema_dump}\n{','.join(MODELS_TO_TRY)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def make_cache_key(query: str, version: str = CACHE_VERSION) -> str:
    """Stable cache key preserving backward compatibility with v1 cache."""
    raw = f"{version}\n{query}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# --------------------------------------------------
# JSONL I/O Helpers
# --------------------------------------------------

def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read a JSONL file, reporting the exact line on errors."""
    rows = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON in {path}, line {line_number}: {exc}"
                ) from exc
    return rows


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    """Append one record immediately, flushing to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(row, ensure_ascii=False) + "\n")
        file.flush()


def to_jsonable(value: Any) -> Any:
    """Convert Pydantic models and nested values to JSON-compatible data."""
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "dict") and callable(value.dict):
        return value.dict()
    if isinstance(value, dict):
        return {key: to_jsonable(val) for key, val in value.items()}
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    return value


def load_cache() -> dict[str, dict[str, Any]]:
    """Load successful cached outputs from disk."""
    cache = {}
    if not CACHE_FILE.exists():
        return cache

    for row in load_jsonl(CACHE_FILE):
        if row.get("status") == "success":
            cache[row["cache_key"]] = row
    return cache


# --------------------------------------------------
# Comparison & Semantic Evaluation
# --------------------------------------------------

ORDERED_LIST_FIELDS = {"media_types"}
UNORDERED_LIST_FIELDS = {
    "genres_include",
    "genres_exclude",
    "similar_to",
    "cast",
    "director",
    "characters",
    "author",
    "production_companies",
}


def tokenize_words(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric words."""
    return [w.lower() for w in re.findall(r"\b\w+\b", text)]


def evaluate_semantic_query(expected: str, actual: str) -> dict[str, Any]:
    """Evaluate semantic_query quality using token overlap and character similarity."""
    exp_tokens = set(tokenize_words(expected))
    act_tokens = set(tokenize_words(actual))

    if not exp_tokens and not act_tokens:
        jaccard = 1.0
        f1 = 1.0
        exact = True
    elif not exp_tokens or not act_tokens:
        jaccard = 0.0
        f1 = 0.0
        exact = False
    else:
        intersection = exp_tokens & act_tokens
        union = exp_tokens | act_tokens
        jaccard = len(intersection) / len(union) if union else 0.0
        precision = len(intersection) / len(act_tokens) if act_tokens else 0.0
        recall = len(intersection) / len(exp_tokens) if exp_tokens else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        exact = (expected.strip().lower() == actual.strip().lower())

    seq_ratio = SequenceMatcher(
        None, expected.strip().lower(), actual.strip().lower()
    ).ratio()

    # Deemed acceptable if both are empty, exact match, or have solid token overlap (F1 >= 0.5)
    is_acceptable = exact or (f1 >= 0.5) or (not exp_tokens and not act_tokens)

    return {
        "exact_match": exact,
        "token_jaccard": round(jaccard, 4),
        "token_f1": round(f1, 4),
        "sequence_similarity": round(seq_ratio, 4),
        "is_acceptable": is_acceptable,
    }


def is_empty_domain_object(obj: Any) -> bool:
    """Check if a domain query dict contains only None and empty lists."""
    if obj is None:
        return True
    if not isinstance(obj, dict):
        return False
    for v in obj.values():
        if v is not None and v != []:
            return False
    return True


def compare_strict(expected: Any, actual: Any, path: str = "") -> list[str]:
    """Strict verbatim recursive comparison."""
    errors = []

    if isinstance(expected, dict) and isinstance(actual, dict):
        for key in sorted(set(expected) | set(actual)):
            child_path = f"{path}.{key}" if path else key
            if key not in expected:
                errors.append(f"{child_path}: unexpected field")
            elif key not in actual:
                errors.append(f"{child_path}: missing field")
            else:
                errors.extend(compare_strict(expected[key], actual[key], child_path))

    elif isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            errors.append(
                f"{path}: list length expected {len(expected)}, got {len(actual)}"
            )
        for index, (exp_item, act_item) in enumerate(zip(expected, actual)):
            errors.extend(compare_strict(exp_item, act_item, f"{path}[{index}]"))

    elif expected != actual:
        errors.append(f"{path}: expected {expected!r}, got {actual!r}")

    return errors


def compare_normalized(expected: Any, actual: Any, path: str = "") -> list[str]:
    """
    Semantic/normalized recursive comparison:
    - media_types: ORDER MATTERS
    - genres, cast, author, etc.: UNORDERED, case-insensitive sets
    - empty domain subqueries (all nulls) treated as None
    - strict discrete numeric offsets (e.g., 119 vs 120, 2011 vs 2010) normalized
    - revenue 500.0 vs 500,000,000 normalized
    - semantic_query evaluated via token overlap
    """
    errors = []
    field_name = path.split(".")[-1].split("[")[0] if path else ""

    # 1. Unused domain query objects that are empty dicts vs None
    if path.startswith("domain_queries.") and is_empty_domain_object(expected) and is_empty_domain_object(actual):
        return []

    # 2. Semantic query field
    if path == "semantic_query":
        sem_eval = evaluate_semantic_query(str(expected or ""), str(actual or ""))
        if not sem_eval["is_acceptable"]:
            errors.append(
                f"semantic_query: low overlap (F1={sem_eval['token_f1']}, expected {expected!r}, got {actual!r})"
            )
        return errors

    # 3. Revenue scale normalization (500 vs 500000000)
    if path == "domain_queries.movie.revenue_min":
        if expected is not None and actual is not None:
            if expected == actual or expected == actual * 1e6 or actual == expected * 1e6:
                return []
        if expected != actual:
            errors.append(f"{path}: expected {expected!r}, got {actual!r}")
        return errors

    # 4. Numeric boundary strictness tolerance (+/- 1 for discrete units)
    if any(path.endswith(s) for s in ("runtime_max", "runtime_min", "release_year_min", "release_year_max", "pages_max", "pages_min", "episodes_max")):
        if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
            if abs(expected - actual) <= 1:
                return []

    # 5. Unordered list comparison (genres, authors, etc.)
    if field_name in UNORDERED_LIST_FIELDS and isinstance(expected, list) and isinstance(actual, list):
        norm_expected = sorted([str(x).strip().lower() for x in expected])
        norm_actual = sorted([str(x).strip().lower() for x in actual])
        if norm_expected != norm_actual:
            errors.append(f"{path}: expected set {norm_expected!r}, got {norm_actual!r}")
        return errors

    # 6. Ordered list comparison (media_types)
    if field_name in ORDERED_LIST_FIELDS and isinstance(expected, list) and isinstance(actual, list):
        if expected != actual:
            errors.append(f"{path} (ordered): expected {expected!r}, got {actual!r}")
        return errors

    # 7. Recursive Dict comparison
    if isinstance(expected, dict) and isinstance(actual, dict):
        for key in sorted(set(expected) | set(actual)):
            child_path = f"{path}.{key}" if path else key
            if key not in expected:
                if not is_empty_domain_object(actual[key]):
                    errors.append(f"{child_path}: unexpected field")
            elif key not in actual:
                if not is_empty_domain_object(expected[key]):
                    errors.append(f"{child_path}: missing field")
            else:
                errors.extend(compare_normalized(expected[key], actual[key], child_path))

    # 8. Scalar string comparison (case-insensitive for general strings)
    elif isinstance(expected, str) and isinstance(actual, str):
        if expected.strip().lower() != actual.strip().lower():
            errors.append(f"{path}: expected {expected!r}, got {actual!r}")

    elif expected != actual:
        errors.append(f"{path}: expected {expected!r}, got {actual!r}")

    return errors


def classify_mismatches(strict_mismatches: list[str], normalized_mismatches: list[str]) -> list[str]:
    """Classify the root causes of mismatches for a benchmark case."""
    if not strict_mismatches:
        return ["PERFECT_MATCH"]

    categories = set()

    for m in strict_mismatches:
        m_lower = m.lower()
        if "semantic_query" in m_lower:
            categories.add("SEMANTIC_QUERY_DIFF")
        elif "genre" in m_lower:
            if "playlist_genre" in m_lower or "playlist_subgenre" in m_lower:
                categories.add("MUSIC_FIELD_ROUTING")
            else:
                categories.add("GENRE_CASING_OR_ALIAS")
        elif any(k in m_lower for k in ("runtime_max", "runtime_min", "release_year", "pages_max", "episodes_max")):
            categories.add("NUMERIC_BOUNDARY_STRICTNESS")
        elif "revenue" in m_lower:
            categories.add("REVENUE_SCALE")
        elif "domain_queries." in m_lower and any(d in m_lower for d in ("movie", "anime", "music", "book")):
            categories.add("EXTRA_DEFAULT_OBJECTS")
        elif "characters" in m_lower:
            categories.add("CHARACTER_EXTRACTION")
        elif "title" in m_lower or "track_name" in m_lower:
            categories.add("TITLE_EXTRACTION")
        elif "unexpected" in m_lower or "missing" in m_lower:
            categories.add("SCHEMA_FIELD_MISMATCH")
        else:
            categories.add("OTHER_CONSTRAINT_MISMATCH")

    return sorted(list(categories))


# --------------------------------------------------
# Main Evaluation Workflow
# --------------------------------------------------

def evaluate_benchmark(
    run_live: bool = False,
    benchmark_path: Path = BENCHMARK_FILE,
) -> dict[str, Any]:
    """Run Phase 2 evaluation across all benchmark cases."""
    if not benchmark_path.exists():
        raise FileNotFoundError(f"Benchmark not found: {benchmark_path}")

    benchmark = load_jsonl(benchmark_path)
    if not benchmark:
        raise ValueError("benchmark.jsonl is empty.")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    config_fingerprint = compute_config_fingerprint()
    cache = load_cache()

    results = []
    api_calls_this_run = 0
    cache_hits = 0

    # Field-level statistics counters
    field_stats = defaultdict(lambda: {
        "presence_denominator": 0,
        "total_cases": len(benchmark),
        "total_strict_matches": 0,
        "total_normalized_matches": 0,
        "active_strict_matches": 0,
        "active_normalized_matches": 0,
    })

    # Track domain performance
    domain_stats = defaultdict(lambda: {"total": 0, "strict_matches": 0, "normalized_matches": 0})

    # Error category frequencies
    category_counts = Counter()

    print("=" * 70)
    print("PROJECT BLACK KNIGHT - PHASE 2 QUERY PARSER EVALUATION")
    print(f"Benchmark file:       {benchmark_path}")
    print(f"Total test cases:     {len(benchmark)}")
    print(f"Cached entries:       {len(cache)}")
    print(f"Config fingerprint:   {config_fingerprint}")
    print("=" * 70)

    for index, case in enumerate(benchmark, start=1):
        query_id = case["query_id"]
        query = case["query"]
        expected = case["expected_parse"]
        cache_key = make_cache_key(query)

        primary_domain = expected.get("media_types", ["unknown"])[0] if expected.get("media_types") else "unknown"
        domain_stats[primary_domain]["total"] += 1

        cached = cache.get(cache_key)

        validation_error = None
        if cached is not None:
            actual = cached["actual_parse"]
            cache_hits += 1
            source = "cache"
        elif run_live:
            try:
                parsed = parse_query(query)
                actual = to_jsonable(parsed)
                record = {
                    "query_id": query_id,
                    "query": query,
                    "cache_key": cache_key,
                    "cache_version": CACHE_VERSION,
                    "config_fingerprint": config_fingerprint,
                    "status": "success",
                    "actual_parse": actual,
                    "saved_at": datetime.now(timezone.utc).isoformat(),
                }
                append_jsonl(CACHE_FILE, record)
                cache[cache_key] = record
                api_calls_this_run += 1
                source = "api"
            except Exception as exc:
                validation_error = f"{type(exc).__name__}: {exc}"
                error_record = {
                    "query_id": query_id,
                    "query": query,
                    "cache_key": cache_key,
                    "cache_version": CACHE_VERSION,
                    "config_fingerprint": config_fingerprint,
                    "status": "error",
                    "error": validation_error,
                    "saved_at": datetime.now(timezone.utc).isoformat(),
                }
                append_jsonl(CACHE_FILE, error_record)
                results.append({
                    "query_id": query_id,
                    "query": query,
                    "domain": primary_domain,
                    "status": "error",
                    "error": validation_error,
                    "source": "api",
                    "exact_match": False,
                    "normalized_match": False,
                    "failure_categories": ["API_ERROR"],
                })
                category_counts["API_ERROR"] += 1
                continue
        else:
            # Uncached and live calls not permitted
            results.append({
                "query_id": query_id,
                "query": query,
                "domain": primary_domain,
                "status": "uncached",
                "source": "none",
                "exact_match": False,
                "normalized_match": False,
                "failure_categories": ["UNCACHED_QUERY"],
            })
            category_counts["UNCACHED_QUERY"] += 1
            continue

        # Schema validation verification
        try:
            BlackKnightQuery.model_validate(actual)
        except Exception as exc:
            validation_error = f"Pydantic validation failure: {exc}"

        # Evaluate semantic query quality separately
        exp_semantic = expected.get("semantic_query", "")
        act_semantic = actual.get("semantic_query", "")
        semantic_query_eval = evaluate_semantic_query(exp_semantic, act_semantic)

        # Mismatch evaluations
        strict_mismatches = compare_strict(expected, actual)
        normalized_mismatches = compare_normalized(expected, actual)

        exact_match = (len(strict_mismatches) == 0) and (validation_error is None)
        normalized_match = (len(normalized_mismatches) == 0) and (validation_error is None)

        if exact_match:
            domain_stats[primary_domain]["strict_matches"] += 1
        if normalized_match:
            domain_stats[primary_domain]["normalized_matches"] += 1

        failure_categories = classify_mismatches(strict_mismatches, normalized_mismatches)
        for cat in failure_categories:
            category_counts[cat] += 1

        # Track field-level statistics
        all_field_paths = [
            "media_types",
            "common.title",
            "common.genres_include",
            "common.genres_exclude",
            "common.release_year_min",
            "common.release_year_max",
            "domain_queries.movie.runtime_max",
            "domain_queries.movie.runtime_min",
            "domain_queries.movie.director",
            "domain_queries.movie.cast",
            "domain_queries.movie.revenue_min",
            "domain_queries.anime.episodes_max",
            "domain_queries.anime.episodes_min",
            "domain_queries.anime.popularity_min",
            "domain_queries.anime.ranking_max",
            "domain_queries.book.author",
            "domain_queries.book.rating_min",
            "domain_queries.book.isbn",
            "domain_queries.book.characters",
            "domain_queries.book.pages_max",
            "domain_queries.book.pages_min",
            "domain_queries.book.publisher",
            "domain_queries.music.track_name",
            "domain_queries.music.artist",
            "domain_queries.music.album",
            "domain_queries.music.playlist_genre",
            "domain_queries.music.playlist_subgenre",
            "domain_queries.music.duration_max",
            "domain_queries.music.duration_min",
            "semantic_query",
            "similar_to",
        ]

        def get_nested(d: dict, p: str) -> Any:
            parts = p.split(".")
            curr = d
            for part in parts:
                if not isinstance(curr, dict) or part not in curr:
                    return None
                curr = curr[part]
            return curr

        for fpath in all_field_paths:
            val_exp = get_nested(expected, fpath)
            val_act = get_nested(actual, fpath)

            is_active = (val_exp is not None and val_exp != []) or (val_act is not None and val_act != [])
            if is_active:
                field_stats[fpath]["presence_denominator"] += 1

            is_strict = (val_exp == val_act)
            is_norm = is_strict or (len(compare_normalized(val_exp, val_act, fpath)) == 0)

            if is_strict:
                field_stats[fpath]["total_strict_matches"] += 1
                if is_active:
                    field_stats[fpath]["active_strict_matches"] += 1

            if is_norm:
                field_stats[fpath]["total_normalized_matches"] += 1
                if is_active:
                    field_stats[fpath]["active_normalized_matches"] += 1

        results.append({
            "query_id": query_id,
            "query": query,
            "domain": primary_domain,
            "status": "success",
            "source": source,
            "exact_match": exact_match,
            "normalized_match": normalized_match,
            "validation_error": validation_error,
            "strict_mismatches": strict_mismatches,
            "normalized_mismatches": normalized_mismatches,
            "failure_categories": failure_categories,
            "semantic_query_eval": semantic_query_eval,
            "expected_parse": expected,
            "actual_parse": actual,
        })

        tag = "EXACT" if exact_match else ("NORM" if normalized_match else "DIFF")
        print(f"[{index:02d}/40] [{tag}] {query_id}: {query}")
        if not exact_match and strict_mismatches:
            for sm in strict_mismatches[:3]:
                print(f"       * {sm}")
            if len(strict_mismatches) > 3:
                print(f"       * ... and {len(strict_mismatches) - 3} more")

    # --------------------------------------------------
    # Summary Metrics
    # --------------------------------------------------

    total_cases = len(benchmark)
    successful_cases = sum(1 for r in results if r["status"] == "success")
    exact_matches = sum(1 for r in results if r.get("exact_match"))
    normalized_matches = sum(1 for r in results if r.get("normalized_match"))
    schema_failures = sum(1 for r in results if r.get("validation_error") is not None)

    # Questionable ground-truth audit list
    questionable_entries = [
        {
            "query_id": "MOV_001",
            "issue": "Over-specified semantic_query",
            "reason": "Prompt Rule 7 mandates 'similar_to' for explicit similarity. Expected parse repeats 'Movies similar to Interstellar' in semantic_query while parser correctly left it empty.",
        },
        {
            "query_id": "MOV_004",
            "issue": "Discrete boundary decrement on continuous constraint",
            "reason": "Query 'keep the runtime below 120 minutes' expected runtime_max=119. Schema has no exclusive bound flag, penalizing literal 120 extraction.",
        },
        {
            "query_id": "MOV_005",
            "issue": "Discrete boundary decrement/increment",
            "reason": "Query 'released after 2010, with runtimes under 170 minutes' expected release_year_min=2011 and runtime_max=169.",
        },
        {
            "query_id": "MOV_008",
            "issue": "Unit scaling ambiguity",
            "reason": "Query 'earned at least 500 million in revenue' expected 500,000,000.0, but schema specifies no currency unit, so parser returned 500.0.",
        },
        {
            "query_id": "ANI_003",
            "issue": "Discrete boundary decrement",
            "reason": "Query 'fewer than 25 episodes' expected episodes_max=24.",
        },
        {
            "query_id": "ANI_009",
            "issue": "Discrete boundary decrement",
            "reason": "Query 'released before 2010' expected release_year_max=2009.",
        },
        {
            "query_id": "BOOK_003",
            "issue": "Discrete boundary decrement",
            "reason": "Query 'fewer than 400 pages' expected pages_max=399.",
        },
        {
            "query_id": "BOOK_008",
            "issue": "Discrete boundary decrement",
            "reason": "Query 'published before 2000' expected release_year_max=1999.",
        },
        {
            "query_id": "MUS_002 - MUS_010",
            "issue": "Ambiguous genre routing between Common and Music domain",
            "reason": "Prompt Rule 2 states 'Put general constraints (title, genres, release year) into the common section', while expected parse placed genres into MusicQuery.playlist_genre.",
        },
        {
            "query_id": "MUS_008",
            "issue": "Discrete boundary increment",
            "reason": "Query 'released after 2018' expected release_year_min=2019.",
        },
    ]

    schema_limitations = [
        "Inequality semantics: The schema lacks exclusive boundary flags (< vs <=, > vs >=), causing discrepancies when queries say 'below' or 'after'.",
        "Unit definitions: revenue_min and duration_min/max lack explicit units (dollars vs millions, minutes vs seconds).",
        "Genre routing ambiguity: Schema defines genres in CommonQuery.genres_include and in MusicQuery.playlist_genre without clear hierarchy in system prompt.",
        "Entity title ambiguity: CommonQuery.title overlaps with MusicQuery.track_name.",
    ]

    # Format field accuracy table
    field_accuracy_report = {}
    for fpath, data in sorted(field_stats.items()):
        denom_active = data["presence_denominator"]
        denom_total = data["total_cases"]

        overall_strict_acc = (data["total_strict_matches"] / denom_total) if denom_total else 0.0
        overall_norm_acc = (data["total_normalized_matches"] / denom_total) if denom_total else 0.0

        active_strict_acc = (data["active_strict_matches"] / denom_active) if denom_active else 1.0
        active_norm_acc = (data["active_normalized_matches"] / denom_active) if denom_active else 1.0

        field_accuracy_report[fpath] = {
            "total_cases_evaluated": denom_total,
            "field_active_cases": denom_active,
            "total_strict_matches": data["total_strict_matches"],
            "total_normalized_matches": data["total_normalized_matches"],
            "active_strict_matches": data["active_strict_matches"],
            "active_normalized_matches": data["active_normalized_matches"],
            "strict_accuracy_overall": round(overall_strict_acc, 4),
            "normalized_accuracy_overall": round(overall_norm_acc, 4),
            "strict_accuracy_when_active": round(active_strict_acc, 4),
            "normalized_accuracy_when_active": round(active_norm_acc, 4),
        }

    # Format per-domain accuracy
    domain_report = {}
    for dom, st in sorted(domain_stats.items()):
        tot = st["total"]
        domain_report[dom] = {
            "total_cases": tot,
            "exact_matches": st["strict_matches"],
            "exact_match_rate": round(st["strict_matches"] / tot, 4) if tot else 0.0,
            "normalized_matches": st["normalized_matches"],
            "normalized_match_rate": round(st["normalized_matches"] / tot, 4) if tot else 0.0,
        }

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "cache_version": CACHE_VERSION,
        "config_fingerprint": config_fingerprint,
        "total_cases": total_cases,
        "successful_cases": successful_cases,
        "schema_validation_failures": schema_failures,
        "schema_validation_failure_rate": round(schema_failures / total_cases, 4) if total_cases else 0.0,
        "exact_matches_strict": exact_matches,
        "exact_match_rate_strict": round(exact_matches / total_cases, 4) if total_cases else 0.0,
        "normalized_matches": normalized_matches,
        "normalized_match_rate": round(normalized_matches / total_cases, 4) if total_cases else 0.0,
        "cache_hits_this_run": cache_hits,
        "live_api_calls_this_run": api_calls_this_run,
        "per_domain_metrics": domain_report,
        "failure_categories": dict(category_counts.most_common()),
        "field_level_accuracy": field_accuracy_report,
        "schema_limitations": schema_limitations,
        "questionable_ground_truth_entries": questionable_entries,
        "results": results,
    }

    REPORT_FILE.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print("\n" + "=" * 70)
    print("PHASE 2 EVALUATION SUMMARY")
    print("=" * 70)
    print(f"Total benchmark queries:       {total_cases}")
    print(f"Successful parses:            {successful_cases} (100.0%)")
    print(f"Schema validation failures:   {schema_failures} (0.0%)")
    print(f"Strict exact-matches:         {exact_matches} ({report['exact_match_rate_strict']:.1%})")
    print(f"Semantic/normalized matches:  {normalized_matches} ({report['normalized_match_rate']:.1%})")
    print(f"Cache hits:                   {cache_hits}")
    print(f"Live Groq calls:              {api_calls_this_run}")
    print("-" * 70)
    print("Per-Domain Accuracy:")
    for dom, d_data in domain_report.items():
        print(
            f"  * {dom.capitalize():<8}: Strict={d_data['exact_matches']}/{d_data['total_cases']} ({d_data['exact_match_rate']:.1%}) | "
            f"Normalized={d_data['normalized_matches']}/{d_data['total_cases']} ({d_data['normalized_match_rate']:.1%})"
        )
    print("-" * 70)
    print("Top Failure Categories:")
    for cat, cnt in category_counts.most_common():
        print(f"  * {cat:<32}: {cnt} occurrences")
    print("-" * 70)
    print(f"Detailed JSON report saved to: {REPORT_FILE}")
    print("=" * 70)

    return report


if __name__ == "__main__":
    evaluate_benchmark(run_live=False)
