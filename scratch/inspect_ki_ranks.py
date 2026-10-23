import json
with open('evaluation/results/experiment_1_report.json', 'r') as f:
    rep = json.load(f)

ki_cases = [q for q in rep['per_query_results'] if q['category'] == 'known_item']
print(f"Total Known-Item queries: {len(ki_cases)}")
mrr_sum = sum(c['architecture_b']['mrr'] for c in ki_cases)
print(f"Overall Known-Item MRR: {mrr_sum / len(ki_cases):.4f}")
hit1_count = sum(1 for c in ki_cases if c['architecture_b']['mrr'] == 1.0)
print(f"Overall Known-Item Hit@1: {hit1_count / len(ki_cases):.4f} ({hit1_count}/{len(ki_cases)})")

for c in sorted(ki_cases, key=lambda x: x['query_id']):
    mrr_b = c['architecture_b']['mrr']
    rank_b = round(1.0/mrr_b) if mrr_b > 0 else "MISS"
    print(f"  {c['query_id']} ({c['domain']}): rank={rank_b} (MRR={mrr_b:.3f}) | '{c['query_text']}'")
