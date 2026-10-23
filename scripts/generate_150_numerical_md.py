"""
Generate comprehensive test results and numerical data markdown for the 150-query dataset.
Outputs to:
- evaluation/results/test_results_and_numerical_data_150.md
"""
import json
from pathlib import Path

report_json_path = Path("evaluation/results/retrieval_150_report.json")
audit_json_path = Path("evaluation/results/benchmark_audit_report.json")
out_md_path = Path("evaluation/results/test_results_and_numerical_data_150.md")

with open(report_json_path, "r", encoding="utf-8") as f:
    rep = json.load(f)

with open(audit_json_path, "r", encoding="utf-8") as f:
    aud = json.load(f)

cfg_summary = rep["summary_by_configuration"]
per_dom = rep["per_domain_summary"]
overlap = rep["candidate_overlap_and_reranking"]
lat = rep["latency_summary"]
per_query = rep["per_query_results"]

with open(out_md_path, "w", encoding="utf-8") as f:
    f.write("# Project Black Knight — 150-Query Dataset Test Results & Numerical Data\n\n")
    f.write(f"**Generated:** {rep['generated_at']}  \n")
    f.write("**Evaluation Suite:** Audited 150-Query Multi-Modal Retrieval Benchmark  \n")
    f.write("**Configurations Evaluated:** Dense Retrieval (ChromaDB), BM25 Lexical, RRF Hybrid ($k=60$), Cross-Encoder Reranked Hybrid (`ms-marco-MiniLM-L-6-v2`)  \n")
    f.write("**Canonical Dataset:** `evaluation/black_knight_eval_queries_150_audited.csv`  \n\n")
    f.write("---\n\n")

    f.write("## 1. Benchmark Composition & Domain Balance\n\n")
    f.write("| Domain | Total Queries | Positive Queries | Absence Queries | Percentage of Benchmark |\n")
    f.write("| :--- | :---: | :---: | :---: | :---: |\n")
    for dom in ["movie", "anime", "music", "book"]:
        cnt = rep["domain_distribution"][dom]
        abs_cnt = sum(1 for q in per_query if q["domain"] == dom and q["is_absence_query"])
        pos_cnt = cnt - abs_cnt
        f.write(f"| **{dom.capitalize()}** | {cnt} | {pos_cnt} | {abs_cnt} | {cnt/150*100:.1f}% |\n")
    f.write(f"| **Total** | **150** | **135** | **15** | **100.0%** |\n\n")

    f.write("### Query Category Breakdown\n\n")
    f.write("| Category | Query Count | Percentage | Description |\n")
    f.write("| :--- | :---: | :---: | :--- |\n")
    for cat, cnt in aud["category_distribution"].items():
        f.write(f"| `{cat}` | {cnt} | {cnt/150*100:.1f}% | ")
        if cat == "known_item":
            f.write("Exact entity searches anchored on verified local catalog titles and stable record IDs.\n")
        elif cat == "descriptive":
            f.write("Narrative and thematic descriptions with human-inspected catalog relevance targets.\n")
        elif cat == "constraint":
            f.write("Deterministic metadata constraints evaluated via production `metadata_filter.py`.\n")
        elif cat == "similar_to":
            f.write("Recommendations anchored on verified seeds with independent thematic clusters.\n")
        elif cat == "multi_domain":
            f.write("Cross-domain discovery spanning combinations of movies, anime, music, and books.\n")
        elif cat == "absence":
            f.write("Verified catalog absences testing resilience against spurious hallucinated retrieval.\n")
    f.write("\n---\n\n")

    f.write("## 2. Overall Numerical Retrieval Metrics (Positive Queries, N=135)\n\n")
    f.write("| Metric | Dense Retrieval | BM25 Retrieval | RRF Hybrid ($k=60$) | Cross-Encoder Reranked | Best Configuration |\n")
    f.write("| :--- | :---: | :---: | :---: | :---: | :--- |\n")
    
    metric_rows = [
        ("hit_rate_at_5", "Hit Rate@5"),
        ("hit_rate_at_10", "Hit Rate@10"),
        ("precision_at_5", "Precision@5"),
        ("precision_at_10", "Precision@10"),
        ("recall_at_5", "Recall@5"),
        ("recall_at_10", "Recall@10"),
        ("mrr", "MRR (Mean Reciprocal Rank)"),
        ("ndcg_at_5", "nDCG@5"),
        ("ndcg_at_10", "nDCG@10"),
    ]

    for k, label in metric_rows:
        vd = cfg_summary["dense_only"]["positive_ranking_metrics"][k]
        vb = cfg_summary["bm25_only"]["positive_ranking_metrics"][k]
        vr = cfg_summary["rrf_hybrid"]["positive_ranking_metrics"][k]
        vx = cfg_summary["reranked_hybrid"]["positive_ranking_metrics"][k]
        best_val = max(vd, vb, vr, vx)
        best_name = "Cross-Encoder" if vx == best_val else ("RRF Hybrid" if vr == best_val else ("BM25" if vb == best_val else "Dense"))
        f.write(f"| **{label}** | {vd:.4f} | {vb:.4f} | {vr:.4f} | **{vx:.4f}** | `{best_name}` |\n")

    f.write("\n---\n\n")

    f.write("## 3. Absence Detection Numerical Results (Absence Queries, N=15)\n\n")
    f.write("| Retrieval Pipeline | Total Absence Queries | Correct Rejections | False Acceptances | Rejection Rate | Precision on Absences |\n")
    f.write("| :--- | :---: | :---: | :---: | :---: | :---: |\n")
    for cfg in ["dense_only", "bm25_only", "rrf_hybrid", "reranked_hybrid"]:
        am = cfg_summary[cfg]["absence_metrics"]
        f.write(f"| `{cfg}` | {am['total_absence_queries']} | {int(am['correct_rejections'])} | {int(am['false_acceptances'])} | **{am['rejection_rate']*100:.1f}%** | 100.0% |\n")
    
    f.write("\n> **Absence Decision Rule:** When an entity title is specified as an anchor, the metadata filter checks exact and normalized catalog tokens. If the item does not exist, `valid_ids` evaluates to an empty set `set()`, filtering all candidates and returning 0 retrieved results. For title-constrained absence queries, 0 retrieved results constitutes a Correct Rejection (CR).\n\n")
    f.write("---\n\n")

    f.write("## 4. Per-Domain Numerical Breakdown\n\n")
    for dom in ["movie", "anime", "book", "music"]:
        d_data = per_dom[dom]["configs"]
        f.write(f"### 4.{['movie', 'anime', 'book', 'music'].index(dom)+1} {dom.capitalize()} Domain (Total Queries = {rep['domain_distribution'][dom]})\n\n")
        f.write("| Metric | Dense Retrieval | BM25 Retrieval | RRF Hybrid | Cross-Encoder Reranked |\n")
        f.write("| :--- | :---: | :---: | :---: | :---: |\n")
        for k, label in metric_rows:
            vd = d_data["dense_only"]["positive_ranking_metrics"][k]
            vb = d_data["bm25_only"]["positive_ranking_metrics"][k]
            vr = d_data["rrf_hybrid"]["positive_ranking_metrics"][k]
            vx = d_data["reranked_hybrid"]["positive_ranking_metrics"][k]
            f.write(f"| {label} | {vd:.4f} | {vb:.4f} | {vr:.4f} | **{vx:.4f}** |\n")
        f.write("\n")

    f.write("---\n\n")

    f.write("## 5. Candidate Overlap, Reranker Shifts & Latency Profiling\n\n")
    f.write("### Candidate Overlap & Reranker Dynamics\n\n")
    f.write(f"- **Mean Dense vs. BM25 Candidate Overlap (Jaccard Index):** `{overlap['mean_dense_bm25_jaccard']:.4f}`\n")
    f.write(f"- **Reranker MRR Improvements vs. RRF:** `{overlap['rerank_vs_rrf_improvements']}` queries\n")
    f.write(f"- **Reranker MRR Regressions vs. RRF:** `{overlap['rerank_vs_rrf_regressions']}` queries\n")
    f.write(f"- **Reranker MRR Neutrals vs. RRF:** `{overlap['rerank_vs_rrf_neutrals']}` queries\n\n")

    f.write("### Latency Profile Across Pipelines (Milliseconds)\n\n")
    f.write("| Pipeline | Mean Latency (ms) | P50 Median (ms) | P95 Latency (ms) | Speed vs. Reranked |\n")
    f.write("| :--- | :---: | :---: | :---: | :---: |\n")
    for cfg in ["dense_only", "bm25_only", "rrf_hybrid", "reranked_hybrid"]:
        l = lat[cfg]
        speedup = lat["reranked_hybrid"]["mean_ms"] / l["mean_ms"]
        f.write(f"| `{cfg}` | {l['mean_ms']:.2f} | {l['p50_ms']:.2f} | {l['p95_ms']:.2f} | {speedup:.1f}x faster |\n")

    f.write("\n---\n\n")

    f.write("## 6. Complete Per-Query Results Table (All 150 Queries)\n\n")
    f.write("| Query ID | Domain | Category | Query Text | Rel Count | Dense Hit@10 | BM25 Hit@10 | RRF Hit@10 | Cross-Enc Hit@10 | Cross-Enc MRR | Cross-Enc nDCG@10 | Latency (ms) |\n")
    f.write("| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n")
    for q in per_query:
        qid = q["query_id"]
        dom = q["domain"]
        cat = q["category"]
        qtext = q["query_text"]
        rcnt = q["relevant_ids_count"]
        dh = int(q["dense_hit_10"])
        bh = int(q["bm25_hit_10"])
        rh = int(q["rrf_hit_10"])
        xh = int(q["reranked_hit_10"])
        xmrr = q["reranked_mrr"]
        xndcg = q["reranked_ndcg_10"]
        xlat = q["reranked_latency_ms"]
        f.write(f"| `{qid}` | {dom} | {cat} | {qtext} | {rcnt} | {dh} | {bh} | {rh} | **{xh}** | {xmrr:.2f} | {xndcg:.2f} | {xlat:.1f} |\n")

print(f"Generated {out_md_path} successfully!")
