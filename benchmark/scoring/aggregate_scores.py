import csv
import sys
import os
from collections import defaultdict

SCORE_COLS = ["factual_accuracy", "reasoning_consistency",
              "confidence_calibration", "domain_depth"]

def aggregate(score_file):
    rows = []
    with open(score_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    # Check all rows are filled
    unfilled = [r["id"] for r in rows if not r["factual_accuracy"].strip()]
    if unfilled:
        print(f"WARNING: {len(unfilled)} rows not yet scored: {unfilled}")
        print("Fill in all score columns before running this script.")
        return

    # Convert scores to int
    for r in rows:
        for col in SCORE_COLS:
            r[col] = int(r[col])
        r["total"] = sum(r[col] for col in SCORE_COLS)

    n = len(rows)

    # --- Overall Results ---
    print(f"\n{'='*55}")
    print(f"  BENCHMARK RESULTS — {n} questions")
    print(f"{'='*55}")

    for col in SCORE_COLS:
        vals = [r[col] for r in rows]
        pct = round(sum(vals) / (n * 3) * 100, 1)
        print(f"  {col:30s}: {sum(vals)}/{n*3}  ({pct}%)")

    total_vals = [r["total"] for r in rows]
    total_pct = round(sum(total_vals) / (n * 12) * 100, 1)
    print(f"  {'overall_score':30s}: {sum(total_vals)}/{n*12}  ({total_pct}%)")

    # --- By Domain ---
    print(f"\n--- By Domain ---")
    domains = defaultdict(list)
    for r in rows:
        domains[r["domain"]].append(r["total"])
    for domain, scores in sorted(domains.items()):
        avg = round(sum(scores) / len(scores), 2)
        pct = round(avg / 12 * 100, 1)
        print(f"  {domain:25s}: {avg}/12  ({pct}%)  n={len(scores)}")

    # --- By Difficulty ---
    print(f"\n--- By Difficulty ---")
    diffs = defaultdict(list)
    for r in rows:
        diffs[r["difficulty"]].append(r["total"])
    for diff, scores in sorted(diffs.items()):
        avg = round(sum(scores) / len(scores), 2)
        pct = round(avg / 12 * 100, 1)
        print(f"  {diff:10s}: {avg}/12  ({pct}%)  n={len(scores)}")

    # --- By Reasoning Type ---
    print(f"\n--- By Reasoning Type ---")
    rtypes = defaultdict(list)
    for r in rows:
        rtypes[r["reasoning_type"]].append(r["total"])
    for rtype, scores in sorted(rtypes.items()):
        avg = round(sum(scores) / len(scores), 2)
        pct = round(avg / 12 * 100, 1)
        print(f"  {rtype:30s}: {avg}/12  ({pct}%)  n={len(scores)}")

    # --- Overconfidence Failures ---
    overconfident = [
        r["id"] for r in rows
        if r["factual_accuracy"] == 0 and r["confidence_calibration"] <= 1
    ]
    print(f"\n--- Overconfidence Failures ---")
    print(f"  Wrong answer + poor calibration: {len(overconfident)} questions")
    if overconfident:
        print(f"  IDs: {', '.join(overconfident)}")

    # --- Cascade/Multi-step Failures ---
    cascade_fail = [
        r["id"] for r in rows
        if r["reasoning_type"] in ["multi_step_inference", "systems_reasoning"]
        and r["reasoning_consistency"] <= 1
    ]
    print(f"\n--- Multi-step Reasoning Failures ---")
    print(f"  Cascade/systems questions with broken reasoning: {len(cascade_fail)}")
    if cascade_fail:
        print(f"  IDs: {', '.join(cascade_fail)}")

    # --- Save summary ---
    summary_dir = os.path.join(os.path.dirname(score_file))
    summary_path = os.path.join(summary_dir, "summary.txt")
    with open(summary_path, "w") as f:
        f.write(f"Benchmark Results — {n} questions\n")
        f.write(f"Overall: {sum(total_vals)}/{n*12} ({total_pct}%)\n\n")
        f.write("By Domain:\n")
        for domain, scores in sorted(domains.items()):
            avg = round(sum(scores)/len(scores), 2)
            f.write(f"  {domain}: {avg}/12\n")
        f.write(f"\nOverconfidence failures: {len(overconfident)}\n")
        f.write(f"Multi-step failures: {len(cascade_fail)}\n")

    print(f"\n✓ Summary saved to: {summary_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scoring/aggregate_scores.py results/scores/<filename>.csv")
        sys.exit(1)
    aggregate(sys.argv[1])
