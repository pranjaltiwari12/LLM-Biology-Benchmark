"""
LLM Biology Benchmark — Groq Pipeline
======================================
Evaluated model : llama-3.3-70b-versatile  (answers the biology questions)
Judge model     : llama-3.1-70b-versatile   (scores responses 0-3 on 4 dimensions)

Usage:
    export GROQ_API_KEY="your_groq_key_here"
    python benchmark/runner/run_benchmark_groq.py

Outputs:
    results/raw_responses/groq_<timestamp>.json   — raw model responses
    results/scores/groq_<timestamp>_scores.csv    — auto-scored by Groq judge
    results/scores/summary.txt                    — aggregated statistics
"""

import json
import os
import csv
import time
import re
from datetime import datetime
from groq import Groq

# ── CONFIG ────────────────────────────────────────────────────────────────────
GROQ_API_KEY      = os.environ.get("GROQ_API_KEY")
EVAL_MODEL        = "llama-3.3-70b-versatile"   # model being benchmarked
JUDGE_MODEL       = "llama-3.1-70b-versatile"   # model doing the scoring

BASE_DIR          = os.path.dirname(os.path.abspath(__file__))
DATA_DIR          = os.path.join(BASE_DIR, "..", "data")
RAW_DIR           = os.path.join(BASE_DIR, "..", "results", "raw_responses")
SCORES_DIR        = os.path.join(BASE_DIR, "..", "results", "scores")

DOMAIN_FILES = {
    "molecular_biology" : "molecular_biology.json",
    "bioinformatics"    : "bioinformatics.json",
    "pathway_analysis"  : "pathway_analysis.json",
}

EVAL_SYSTEM_PROMPT = """You are an expert biologist and bioinformatician with deep knowledge
of molecular biology, genomics, and systems biology. Answer the following question as precisely
and thoroughly as possible. If you are uncertain about any part of your answer, explicitly state
your uncertainty. Do not hallucinate facts. If a question is outside your confident knowledge,
say so clearly."""

JUDGE_SYSTEM_PROMPT = """You are an expert scientific evaluator assessing LLM responses to
advanced biology questions. You must score the response strictly and objectively.

Scoring scale for each dimension (integer 0-3 only):
  0 = completely wrong / absent
  1 = partially correct / minor gaps
  2 = correct and sound
  3 = exceptionally precise, expert-level

Dimensions:
  factual_accuracy      : Is the answer scientifically correct?
  reasoning_consistency : Are intermediate steps logically sound and complete?
  confidence_calibration: Does the model express appropriate uncertainty where needed?
  domain_depth          : Does the answer reflect niche specialist knowledge?

You MUST respond with ONLY a JSON object in this exact format, nothing else:
{
  "factual_accuracy": <0-3>,
  "reasoning_consistency": <0-3>,
  "confidence_calibration": <0-3>,
  "domain_depth": <0-3>,
  "reasoning": "<one sentence explaining your scores>"
}"""

# ── SETUP ─────────────────────────────────────────────────────────────────────
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable not set.\nRun: export GROQ_API_KEY='your_key'")

client = Groq(api_key=GROQ_API_KEY)


# ── HELPERS ───────────────────────────────────────────────────────────────────
def load_all_questions():
    all_questions = []
    for domain, filename in DOMAIN_FILES.items():
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            print(f"  WARNING: {filepath} not found — skipping.")
            continue
        with open(filepath, "r", encoding="utf-8") as f:
            questions = json.load(f)
        for q in questions:
            q["domain"] = domain
        all_questions.extend(questions)
        print(f"  Loaded {len(questions)} questions from {filename}")
    return all_questions


def query_eval_model(question_text):
    response = client.chat.completions.create(
        model=EVAL_MODEL,
        messages=[
            {"role": "system", "content": EVAL_SYSTEM_PROMPT},
            {"role": "user",   "content": question_text},
        ],
        temperature=0.2,
        max_tokens=1024,
    )
    return response.choices[0].message.content.strip()


def judge_response(question, reference_answer, model_response):
    judge_prompt = f"""Question:
{question}

Reference Answer (gold standard):
{reference_answer}

Model Response to evaluate:
{model_response}

Score the Model Response against the Reference Answer on all four dimensions.
Return ONLY the JSON object, no other text."""

    response = client.chat.completions.create(
        model=JUDGE_MODEL,
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user",   "content": judge_prompt},
        ],
        temperature=0.0,
        max_tokens=256,
    )
    raw = response.choices[0].message.content.strip()

    # parse JSON safely
    try:
        # strip markdown fences if present
        clean = re.sub(r"```(?:json)?|```", "", raw).strip()
        scores = json.loads(clean)
        # validate all keys present and values in range
        for key in ["factual_accuracy", "reasoning_consistency",
                    "confidence_calibration", "domain_depth"]:
            if key not in scores:
                scores[key] = 0
            scores[key] = max(0, min(3, int(scores[key])))
        if "reasoning" not in scores:
            scores["reasoning"] = ""
    except Exception as e:
        print(f"    Judge parse error: {e} | raw: {raw[:100]}")
        scores = {
            "factual_accuracy": 0,
            "reasoning_consistency": 0,
            "confidence_calibration": 0,
            "domain_depth": 0,
            "reasoning": f"PARSE_ERROR: {raw[:80]}"
        }
    return scores


def compute_summary(rows, scores_path):
    from collections import defaultdict

    score_cols = ["factual_accuracy", "reasoning_consistency",
                  "confidence_calibration", "domain_depth"]

    n = len(rows)
    overall_total = sum(r["total"] for r in rows)
    overall_pct   = round(overall_total / (n * 12) * 100, 1)

    lines = []
    lines.append("=" * 55)
    lines.append(f"  BENCHMARK RESULTS — {n} questions")
    lines.append(f"  Evaluated model : {EVAL_MODEL}")
    lines.append(f"  Judge model     : {JUDGE_MODEL}")
    lines.append("=" * 55)

    for col in score_cols:
        vals = [r[col] for r in rows]
        pct  = round(sum(vals) / (n * 3) * 100, 1)
        lines.append(f"  {col:30s}: {sum(vals)}/{n*3}  ({pct}%)")

    lines.append(f"  {'overall_score':30s}: {overall_total}/{n*12}  ({overall_pct}%)")

    lines.append("\n--- By Domain ---")
    domains = defaultdict(list)
    for r in rows:
        domains[r["domain"]].append(r["total"])
    for domain, sc in sorted(domains.items()):
        avg = round(sum(sc) / len(sc), 2)
        pct = round(avg / 12 * 100, 1)
        lines.append(f"  {domain:25s}: {avg}/12  ({pct}%)  n={len(sc)}")

    lines.append("\n--- By Reasoning Type ---")
    rtypes = defaultdict(list)
    for r in rows:
        rtypes[r["reasoning_type"]].append(r["total"])
    for rtype, sc in sorted(rtypes.items()):
        avg = round(sum(sc) / len(sc), 2)
        pct = round(avg / 12 * 100, 1)
        lines.append(f"  {rtype:35s}: {avg}/12  ({pct}%)  n={len(sc)}")

    overconfident = [r["id"] for r in rows
                     if r["factual_accuracy"] == 0 and r["confidence_calibration"] <= 1]
    lines.append(f"\n--- Overconfidence Failures ---")
    lines.append(f"  Wrong + overconfident: {len(overconfident)} questions")
    if overconfident:
        lines.append(f"  IDs: {', '.join(overconfident)}")

    cascade_fail = [r["id"] for r in rows
                    if r["reasoning_type"] in ["multi_step_inference", "cascade_reasoning",
                                                "systems_reasoning"]
                    and r["reasoning_consistency"] <= 1]
    lines.append(f"\n--- Multi-step / Cascade Failures ---")
    lines.append(f"  Broken reasoning on cascade questions: {len(cascade_fail)}")
    if cascade_fail:
        lines.append(f"  IDs: {', '.join(cascade_fail)}")

    summary_text = "\n".join(lines)
    print(summary_text)

    summary_path = os.path.join(os.path.dirname(scores_path), "summary.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary_text)
    print(f"\n  Summary saved to: {summary_path}")


# ── MAIN ──────────────────────────────────────────────────────────────────────
def run_benchmark():
    os.makedirs(RAW_DIR,    exist_ok=True)
    os.makedirs(SCORES_DIR, exist_ok=True)

    print("\nLoading questions...")
    questions = load_all_questions()
    if not questions:
        print("No questions found. Check benchmark/data/ folder.")
        return

    timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_path    = os.path.join(RAW_DIR,    f"groq_{timestamp}.json")
    scores_path = os.path.join(SCORES_DIR, f"groq_{timestamp}_scores.csv")

    total    = len(questions)
    results  = []
    scored   = []

    fieldnames = [
        "id", "domain", "difficulty", "reasoning_type",
        "question", "reference_answer", "model_response",
        "factual_accuracy", "reasoning_consistency",
        "confidence_calibration", "domain_depth",
        "total", "judge_reasoning"
    ]

    print(f"\nRunning benchmark: {total} questions")
    print(f"  Eval model  : {EVAL_MODEL}")
    print(f"  Judge model : {JUDGE_MODEL}\n")

    with open(scores_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for i, q in enumerate(questions):
            qid = q.get("id", f"Q{i+1}")
            print(f"[{i+1:02d}/{total}] {qid} — {q['domain']}")

            # Step 1: get model response
            try:
                model_response = query_eval_model(q["question"])
            except Exception as e:
                model_response = f"ERROR: {str(e)}"
                print(f"  Eval error: {e}")

            # Step 2: judge the response
            try:
                scores = judge_response(
                    q["question"],
                    q.get("reference_answer", ""),
                    model_response
                )
            except Exception as e:
                scores = {
                    "factual_accuracy": 0,
                    "reasoning_consistency": 0,
                    "confidence_calibration": 0,
                    "domain_depth": 0,
                    "reasoning": f"JUDGE_ERROR: {str(e)}"
                }
                print(f"  Judge error: {e}")

            total_score = (scores["factual_accuracy"] +
                           scores["reasoning_consistency"] +
                           scores["confidence_calibration"] +
                           scores["domain_depth"])

            fa  = scores["factual_accuracy"]
            rc  = scores["reasoning_consistency"]
            cc  = scores["confidence_calibration"]
            dd  = scores["domain_depth"]
            print(f"  Scores → FA:{fa} RC:{rc} CC:{cc} DD:{dd} Total:{total_score}/12")

            row = {
                "id"                    : qid,
                "domain"                : q.get("domain", ""),
                "difficulty"            : q.get("difficulty", ""),
                "reasoning_type"        : q.get("reasoning_type", ""),
                "question"              : q["question"],
                "reference_answer"      : q.get("reference_answer", ""),
                "model_response"        : model_response,
                "factual_accuracy"      : scores["factual_accuracy"],
                "reasoning_consistency" : scores["reasoning_consistency"],
                "confidence_calibration": scores["confidence_calibration"],
                "domain_depth"          : scores["domain_depth"],
                "total"                 : total_score,
                "judge_reasoning"       : scores.get("reasoning", ""),
            }

            writer.writerow(row)
            csvfile.flush()
            scored.append(row)

            results.append({
                "id"            : qid,
                "domain"        : q.get("domain", ""),
                "model"         : EVAL_MODEL,
                "model_response": model_response,
                "scores"        : scores,
                "total"         : total_score,
                "timestamp"     : timestamp,
            })

            time.sleep(0.5)  # Groq rate limit buffer

    # save raw responses
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n  Raw responses saved to : {raw_path}")
    print(f"  Scores CSV saved to    : {scores_path}")

    # compute and print summary
    print("\n")
    compute_summary(scored, scores_path)


if __name__ == "__main__":
    run_benchmark()
