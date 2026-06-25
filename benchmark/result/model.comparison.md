# Model Comparison: Sensitivity to Biological Complexity
## LLM Biology Benchmark — Full Results

## Overview

This document reports findings from benchmarking **Llama-3.3-70B-Versatile** (via Groq) on 60 biology problems designed to test context-dependent sensitivity — the ability to recognise that small, localised biological changes can produce disproportionately large system-wide effects.

Scoring was performed using **Llama-3.3-70B-Versatile as LLM judge**, evaluating each response against expert-written reference answers across four dimensions.

---

## Model Evaluated

| Role | Model | Provider |
|------|-------|----------|
| Evaluated model | llama-3.3-70b-versatile | Groq |
| Judge model | llama-3.3-70b-versatile | Groq |

---

## Scoring Methodology

Each of 60 questions was scored 0–3 on four dimensions:

| Dimension | 0 | 1 | 2 | 3 |
|-----------|---|---|---|---|
| Factual Accuracy | Wrong | Partially correct | Correct | Exceptionally precise |
| Reasoning Consistency | Incoherent | Minor gaps | Sound | Rigorous |
| Confidence Calibration | Overconfident + wrong | Overconfident | Appropriate | Well-calibrated |
| Domain Depth | Superficial | Textbook | Specialist | Expert niche |

Max per question: 12. Max total: 720 (60 × 12).

---

## Overall Results

| Domain | Total | Avg/12 | Percentage | n |
|--------|-------|--------|------------|---|
| Molecular Biology | 193 | 9.65 | 80.4% | 20 |
| Bioinformatics | 207 | 10.35 | 86.2% | 20 |
| Pathway Analysis | 179 | 8.95 | 74.6% | 20 |
| **Overall** | **579** | **9.65** | **80.4%** | **60** |

---

## Key Finding — Performance Gradient Across Domains

Contrary to the initial hypothesis that bioinformatics (computational/pipeline reasoning) would be the weakest domain, **bioinformatics scored highest (86.2%)**, followed by molecular biology (80.4%), with **pathway analysis scoring lowest (74.6%)**.

This suggests the model's weakest area is not computational/statistical reasoning but **systems-level, multi-step cascade reasoning** — exactly the kind of reasoning pathway analysis questions are designed to probe (feedback loops, network bottlenecks, non-linear threshold dynamics, cross-pathway compensation).

---

## Failure Pattern Analysis

### Pattern 1 — Confidence Calibration Is the Weakest Dimension Across All Domains

Across nearly every question, `confidence_calibration` scored at or below `factual_accuracy`/`reasoning_consistency`. The model rarely hedges, even on incomplete answers. Of 60 responses, the large majority scored CC=2 (appropriate) only when FA/RC were also high (3); whenever FA/RC dropped to 2, CC dropped to 1 in most cases — indicating the model does not independently signal uncertainty, it only "looks uncertain" when it actually performs worse.

### Pattern 2 — Cascade and Multi-Step Reasoning Is the Most Common Failure Mode

Lowest-scoring questions cluster heavily around cascade/multi-step mechanism tracing:
- **MB_003** (MEK1/ERK bistability) — 7/12 — missed ultrasensitivity specifically
- **MB_009** (CYLD/NF-κB cascade) — 8/12
- **MB_011** (RB1 threshold) — 7/12
- **MB_012** (lncRNA traps) — 7/12
- **MB_015** (ATF4 uORF) — 7/12 — misidentified PERK instead of GCN2
- **PA_003** (NSP1 selective translation) — 7/12
- **PA_005** (gene regulatory feedback) — 7/12
- **PA_008** (APC/Wnt threshold) — 7/12
- **PA_011** (Notch lateral inhibition) — 7/12
- **PA_012** (reverse TCA flux) — 7/12
- **PA_014** (circadian period sensitivity) — 7/12

The pattern: the model correctly identifies the *first-order* mechanism but fails to trace the *specific* non-obvious downstream step that the reference answer requires (e.g., missing the precise kinase, the precise feedback loop, or the precise threshold mechanism), substituting a plausible but imprecise adjacent explanation instead.

### Pattern 3 — Near-Perfect Scores Cluster on Context-Dependency Questions

Highest-scoring questions (11–12/12) are concentrated in `context_dependent_sensitivity` reasoning type across all three domains — questions asking "why does X behave differently in context A vs context B" rather than "trace the exact mechanism step by step." This is consistent with the model having strong associative/explanatory knowledge but weaker precise causal-chain reasoning.

---

## Results by Reasoning Type (approximate, pooled across domains)

| Reasoning Type | Performance Tier |
|----------------|-------------------|
| context_dependent_sensitivity | Strong (most 11-12/12) |
| non_linear_biological_threshold | Mixed (7-11/12) |
| cascade_reasoning | Weakest (7-8/12 typical) |
| systems_reasoning / network_feedback_sensitivity | Weakest (7-8/12 typical) |
| statistical_sensitivity / quantitative_reasoning (bioinformatics) | Strong (8-12/12) |

---

## Core Research Finding

Llama-3.3-70B shows **structured, non-random failure** when reasoning about biological complexity. Failures concentrate specifically in:

1. **Multi-step cascade tracing** — the model identifies the first downstream effect correctly but loses precision tracing beyond 2-3 mechanistic steps
2. **Non-linear threshold mechanisms** — bistability, ultrasensitivity, and feedback-driven switches are frequently described qualitatively but the specific molecular threshold mechanism is often missed or substituted with an adjacent but incorrect mechanism
3. **Confidence calibration** — the model does not proactively signal uncertainty; its expressed confidence does not reliably track its actual correctness

Notably, **computational/statistical bioinformatics reasoning was not a weak point** — this contradicts a common assumption that LLMs struggle more with quantitative/pipeline reasoning than with conceptual biology. The data instead points to **systems-level cascade reasoning** as the primary bottleneck, regardless of domain.

---

## Implications

**Scientific reliability:** A researcher relying on this model for systems biology reasoning (e.g., predicting downstream effects of a perturbation) should expect first-order effects to be reliable but should independently verify any claim involving 3+ sequential mechanistic steps.

**Alignment relevance:** The model's confidence does not drop proportionally when its reasoning chain weakens — this is the central calibration risk for deployment in scientific advisory contexts.

**Structured failure = tractable failure:** Because the weak point is specifically multi-step causal-chain reasoning rather than knowledge breadth, targeted interventions (chain-of-thought prompting, retrieval augmentation with explicit mechanism databases, or step-verification scaffolding) are plausible mitigations worth testing in follow-up work.

---

## Limitations

- Single model evaluated (Llama-3.3-70B via Groq); results may not generalise to other frontier models (Claude, GPT, Gemini)
- LLM-as-judge using the same model family for evaluation and judging introduces potential self-evaluation bias — an independent judge model would strengthen these conclusions
- 60 questions is sufficient to identify failure patterns but insufficient for strong quantitative claims about exact performance percentages
- Reference answers were authored by the benchmark creator with reasoning-step checklists, not independently peer-reviewed

---

*Benchmark version 1.0 | Questions: 60 | Domains: 3 | Evaluated: llama-3.3-70b-versatile | Judge: llama-3.3-70b-versatile (Groq)*
