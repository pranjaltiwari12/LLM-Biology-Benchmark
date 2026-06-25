# LLM Biology Benchmark

A domain-specific benchmark for evaluating scientific reasoning reliability in large language models across molecular biology, bioinformatics, and pathway analysis.

## Motivation

While working with frontier LLMs on original biology problems, two consistent failure patterns emerged:

- Models giving confidently wrong answers on niche biological topics
- Multi-step reasoning breaking down on complex, cascade-driven mechanisms

These aren't just accuracy problems — they are **reliability** problems. In scientific domains, confident wrong answers are more dangerous than acknowledged uncertainty. This benchmark is designed to systematically probe and document these failure modes, rather than just produce a single leaderboard score.

## Benchmark Structure

| Domain | Questions | Reasoning Focus |
|--------|-----------|------------------|
| Molecular Biology | 20 | Context-dependent sensitivity, non-linear thresholds, cascade mechanisms |
| Bioinformatics | 20 | Statistical/pipeline sensitivity, quantitative interpretation, methodological caveats |
| Pathway Analysis | 20 | Systems-level reasoning, network feedback, multi-step cascade tracing |

All 60 questions are hard-difficulty, free-response, and paired with an expert-written reference answer plus an explicit reasoning checklist used during scoring.

## Evaluation Dimensions

Each response is scored 0–3 on four dimensions:

| Dimension | What it measures |
|-----------|-------------------|
| Factual Accuracy | Is the answer scientifically correct? |
| Reasoning Consistency | Are intermediate steps logically sound and complete? |
| Confidence Calibration | Does the model express appropriate uncertainty? |
| Domain Depth | Does the answer reflect specialist-level knowledge? |

Max score per question: 12. Max total: 720.

## Model Evaluated

| Role | Model | Provider |
|------|-------|----------|
| Evaluated model | `llama-3.3-70b-versatile` | Groq |
| Judge model | `llama-3.3-70b-versatile` | Groq |

Scoring is performed automatically using an LLM-as-judge methodology: the judge model receives the question, the reference answer, and the model's response, and returns structured 0–3 scores plus a one-line justification for each dimension.

## Key Findings

- **Overall score: 80.4%** (579/720) across all 60 questions
- **Bioinformatics scored highest (86.2%)** — computational/statistical reasoning was not the weak point, contrary to a common assumption about LLM limitations
- **Pathway analysis scored lowest (74.6%)** — multi-step cascade and systems-level reasoning is the primary bottleneck, not domain category
- **Confidence calibration is the weakest dimension across every domain** — the model rarely expresses uncertainty even when its reasoning chain breaks down, the most safety-relevant finding in this benchmark
- Failures concentrate specifically on questions requiring precise tracing of 3+ sequential mechanistic steps; first-order effects are usually identified correctly, but the model frequently substitutes a plausible *adjacent* mechanism for the precise correct one (e.g., misidentifying the specific kinase or feedback loop involved)

Full results, per-question scores, and methodology notes: [`results/model_comparison.md`](results/model_comparison.md)

## Repository Structure

```
LLM-Biology-Benchmark/
├── benchmark/
│   ├── data/
│   │   ├── molecular_biology.json
│   │   ├── bioinformatics.json
│   │   └── pathway_analysis.json
│   ├── runner/
│   │   ├── run_benchmark_groq.py       # full pipeline: query model + judge, run from scratch
│   │   └── run_benchmark_resume.py     # resumable runner, skips already-scored questions
│   ├── scoring/
│   │   ├── score_sheet.py              # generates manual scoring CSV (legacy/manual path)
│   │   └── aggregate_scores.py         # computes summary stats from a scored CSV
│   └── results/
│       ├── raw_responses/              # raw model outputs per run (gitignored)
│       ├── scores/                     # scored CSVs (gitignored)
│       └── model_comparison.md         # full written results and analysis
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

## Question Schema

Each question in `benchmark/data/*.json` follows this structure:

```json
{
  "id": "MB_001",
  "domain": "molecular_biology",
  "difficulty": "hard",
  "reasoning_type": "context_dependent_sensitivity",
  "question": "...",
  "reference_answer": "...",
  "expected_reasoning_steps": ["...", "...", "...", "..."],
  "sensitivity_trap": "Describes the specific failure mode this question is designed to surface",
  "scoring_dimensions": {
    "factual_accuracy": "...",
    "reasoning_consistency": "...",
    "confidence_calibration": "...",
    "domain_depth": "..."
  }
}
```

## Running the Benchmark

**Setup:**
```bash
pip install groq
export GROQ_API_KEY="your_groq_key_here"
```

**Run from scratch:**
```bash
python benchmark/runner/run_benchmark_groq.py
```

**Resume an interrupted run** (e.g. after hitting a rate/token limit):
```bash
python benchmark/runner/run_benchmark_resume.py benchmark/results/scores/<your_scores_file>.csv
```

The resumable runner reads the existing scores CSV, detects which question IDs already have valid scores, and only processes the remaining ones — appending new rows without disturbing completed ones.

**Aggregate results** (if using the manual scoring path):
```bash
python benchmark/scoring/aggregate_scores.py benchmark/results/scores/<your_scores_file>.csv
```

## Methodology Notes

- **LLM-as-judge caveat:** The same model (`llama-3.3-70b-versatile`) is used both as the evaluated model and the judge. This is a known limitation — self-family evaluation can introduce bias. An independent judge model (e.g. a different model provider) is a planned improvement.
- **Sample size:** 60 questions is sufficient to surface qualitative failure patterns but is not large enough to support strong quantitative claims about exact performance percentages. Treat percentages as indicative, not precise.
- **Reference answers** were written by the benchmark author with explicit reasoning-step checklists for each question, designed to make scoring auditable rather than purely subjective.

## Limitations and Future Work

- Extend to additional frontier models (Claude, GPT, Gemini) for cross-model comparison
- Use an independent judge model to remove self-evaluation bias
- Expand to 150–200 questions per domain for stronger statistical power
- Add a difficulty tier (easy/medium/hard) within each domain to study how failure rate scales with reasoning depth
- Add human-expert baseline scores for direct comparison against model performance

## License

See [LICENSE](LICENSE).
