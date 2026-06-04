"""
LLM Biology Benchmark — Evaluation Runner
==========================================
Evaluates frontier LLMs on domain-specific biology reasoning problems,
with focus on context-dependent sensitivity and multi-step inference.

Author: Pranjal Tiwari
"""

import json
import argparse
import os
import time
from pathlib import Path
from datetime import datetime
import anthropic

# ── Configuration ──────────────────────────────────────────────────────────────

MODELS = {
    "claude-sonnet": "claude-sonnet-4-5",
    "claude-opus":   "claude-opus-4-5",
}

DOMAINS = {
    "molecular_biology": "benchmark/problems/molecular_biology.json",
    "pathway_analysis":  "benchmark/problems/pathway_analysis.json",
    "bioinformatics":    "benchmark/problems/bioinformatics.json",
}

SYSTEM_PROMPT = """You are a domain expert in molecular biology, bioinformatics, and systems biology.
Answer the following question with scientific rigour.
Show your reasoning step by step.
Acknowledge uncertainty where it exists.
Do not oversimplify biological systems — explicitly consider context-dependent effects,
feedback mechanisms, and non-linear dynamics where relevant."""

# ── Scoring Rubric ─────────────────────────────────────────────────────────────

SCORING_CRITERIA = {
    "factual_accuracy": {
        "weight": 0.30,
        "description": "Scientific correctness of core claims"
    },
    "reasoning_consistency": {
        "weight": 0.30,
        "description": "Logical coherence of multi-step inference chains"
    },
    "confidence_calibration": {
        "weight": 0.20,
        "description": "Appropriate expression of uncertainty on niche topics"
    },
    "domain_depth": {
        "weight": 0.20,
        "description": "Use of domain-specific terminology and niche knowledge"
    },
}

SENSITIVITY_RUBRIC = {
    "missed_cascade":      "Model failed to identify downstream cascade effects",
    "linear_assumption":   "Model assumed linear/proportional biological response",
    "context_ignored":     "Model ignored context-dependency of biological mechanism",
    "overconfident":       "Model gave confident answer on niche topic without hedging",
    "correct_sensitivity": "Model correctly identified non-linear or context-dependent behaviour",
}

# ── Core Functions ─────────────────────────────────────────────────────────────

def load_problems(domain: str) -> list:
    """Load benchmark problems for a given domain."""
    path = DOMAINS.get(domain)
    if not path:
        raise ValueError(f"Unknown domain: {domain}. Choose from {list(DOMAINS.keys())}")
    with open(path) as f:
        data = json.load(f)
    return data["problems"]


def query_model(client: anthropic.Anthropic, model_key: str, question: str) -> dict:
    """Send a problem to a model and return response with metadata."""
    model_id = MODELS[model_key]
    start = time.time()

    message = client.messages.create(
        model=model_id,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": question}]
    )

    elapsed = time.time() - start
    response_text = message.content[0].text

    return {
        "model": model_key,
        "model_id": model_id,
        "response": response_text,
        "input_tokens": message.usage.input_tokens,
        "output_tokens": message.usage.output_tokens,
        "response_time_seconds": round(elapsed, 2),
    }


def evaluate_sensitivity(response: str, problem: dict) -> dict:
    """
    Heuristic evaluation of whether the model correctly handled
    context-dependent sensitivity in its response.
    """
    response_lower = response.lower()
    expected_steps = problem.get("expected_reasoning_steps", [])
    sensitivity_trap = problem.get("sensitivity_trap", "")

    steps_covered = []
    for step in expected_steps:
        key_words = [w.lower() for w in step.split() if len(w) > 5]
        coverage = sum(1 for w in key_words if w in response_lower) / max(len(key_words), 1)
        steps_covered.append({
            "step": step,
            "coverage_score": round(coverage, 2),
            "likely_addressed": coverage > 0.4
        })

    steps_addressed = sum(1 for s in steps_covered if s["likely_addressed"])
    sensitivity_score = round(steps_addressed / max(len(expected_steps), 1), 2)

    failure_flags = []
    if any(w in response_lower for w in ["proportional", "linearly", "directly proportional"]):
        failure_flags.append("linear_assumption")
    if any(w in response_lower for w in ["simply", "just", "only affects", "straightforward"]):
        failure_flags.append("oversimplification_language")
    if sensitivity_score < 0.4:
        failure_flags.append("missed_cascade")

    return {
        "sensitivity_score": sensitivity_score,
        "steps_addressed": steps_addressed,
        "total_steps": len(expected_steps),
        "step_coverage": steps_covered,
        "failure_flags": failure_flags,
        "sensitivity_trap_description": sensitivity_trap,
    }


def run_evaluation(domain: str, model_keys: list, output_dir: str = "results"):
    """Run full evaluation for given domain and models."""
    client = anthropic.Anthropic()
    problems = load_problems(domain)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = []

    print(f"\n{'='*60}")
    print(f"LLM Biology Benchmark — {domain.replace('_', ' ').title()}")
    print(f"Models: {', '.join(model_keys)}")
    print(f"Problems: {len(problems)}")
    print(f"{'='*60}\n")

    for problem in problems:
        print(f"Problem {problem['id']}: {problem['question'][:80]}...")
        problem_results = {"problem_id": problem["id"], "domain": domain, "models": {}}

        for model_key in model_keys:
            if model_key not in MODELS:
                print(f"  ⚠ Unknown model: {model_key}, skipping")
                continue

            print(f"  Querying {model_key}...", end=" ", flush=True)
            try:
                response_data = query_model(client, model_key, question=problem["question"])
                sensitivity = evaluate_sensitivity(response_data["response"], problem)

                problem_results["models"][model_key] = {
                    **response_data,
                    "sensitivity_evaluation": sensitivity,
                    "reasoning_type": problem.get("reasoning_type"),
                    "complexity": problem.get("complexity"),
                }
                print(f"✓ (sensitivity score: {sensitivity['sensitivity_score']})")

            except Exception as e:
                print(f"✗ Error: {e}")
                problem_results["models"][model_key] = {"error": str(e)}

        results.append(problem_results)
        time.sleep(1)

    os.makedirs(output_dir, exist_ok=True)
    output_path = f"{output_dir}/{domain}_{timestamp}.json"
    with open(output_path, "w") as f:
        json.dump({
            "benchmark_version": "1.0",
            "domain": domain,
            "timestamp": timestamp,
            "models_evaluated": model_keys,
            "scoring_criteria": SCORING_CRITERIA,
            "results": results
        }, f, indent=2)

    print(f"\n✓ Results saved to {output_path}")
    print_summary(results, model_keys)
    return results


def print_summary(results: list, model_keys: list):
    """Print a summary comparison across models."""
    print(f"\n{'='*60}")
    print("SENSITIVITY SCORE SUMMARY")
    print(f"{'='*60}")

    for model_key in model_keys:
        scores = []
        for r in results:
            if model_key in r["models"] and "sensitivity_evaluation" in r["models"][model_key]:
                scores.append(r["models"][model_key]["sensitivity_evaluation"]["sensitivity_score"])

        if scores:
            avg = round(sum(scores) / len(scores), 3)
            print(f"{model_key:20s} | Avg sensitivity score: {avg} | Problems: {len(scores)}")

    print(f"{'='*60}\n")


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="LLM Biology Benchmark Evaluation Runner"
    )
    parser.add_argument(
        "--domain",
        choices=list(DOMAINS.keys()),
        default="molecular_biology",
        help="Domain to evaluate"
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=["claude-sonnet", "claude-opus"],
        help="Models to evaluate"
    )
    parser.add_argument(
        "--output",
        default="results",
        help="Output directory for results"
    )

    args = parser.parse_args()
    run_evaluation(args.domain, args.models, args.output)
