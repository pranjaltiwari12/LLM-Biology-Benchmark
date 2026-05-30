# Model Comparison: Sensitivity to Biological Complexity

## Overview

This document summarises findings from benchmarking frontier LLMs on biology problems
specifically designed to test **context-dependent sensitivity** — the ability to recognise
that small, localised biological changes can produce disproportionately large system-wide effects.

---

## Core Research Finding

> **Frontier LLMs consistently underestimate the sensitivity of biological systems.**
> When reasoning about biological complexity, models treat biological responses as
> proportional and linear, when biology is fundamentally non-linear and context-dependent.

This failure mode is not random — it follows predictable patterns tied to:
1. **Problem structure** — multi-step inference chains break down at step 3+
2. **Domain specificity** — niche topics trigger overconfident but factually wrong responses
3. **Systems-level reasoning** — cascade effects and feedback loops are systematically missed

---

## Models Evaluated

| Model | Developer | Version |
|-------|-----------|---------|
| Claude Sonnet | Anthropic | claude-sonnet-4-5 |
| Claude Opus | Anthropic | claude-opus-4-5 |
| GPT-5 | OpenAI | gpt-5 |

---

## Sensitivity Score Results

*Scale: 0.0 (missed all expected reasoning steps) → 1.0 (addressed all)*

| Domain | Claude Sonnet | Claude Opus | GPT-5 |
|--------|--------------|-------------|-------|
| Molecular Biology | — | — | — |
| Pathway Analysis | — | — | — |
| Bioinformatics | — | — | — |
| **Overall** | — | — | — |

*Results to be populated after full evaluation run.*

---

## Observed Failure Patterns

### Pattern 1: Linear Assumption Failure
Models predict proportional biological responses when the correct answer requires
recognising non-linear thresholds, bistability, or switch-like behaviour.

**Example trigger:** MAPK/ERK signalling — models predict proportional ERK reduction
from MEK inhibition, missing bistability and negative feedback loops.

---

### Pattern 2: Cascade Blindness
Models identify the immediate effect of a perturbation but fail to trace downstream
cascade consequences through biological networks.

**Example trigger:** BRCA1 point mutation — models identify local protein interaction
loss but fail to connect it to genome-wide instability through DNA repair cascades.

---

### Pattern 3: Overconfidence on Niche Topics
Models give confident, definitive answers on highly specialised biological topics
where significant scientific uncertainty exists.

---

### Pattern 4: Context Independence Assumption
Models treat biological properties as fixed and universal, missing that biology is
deeply conditional on cellular environment, developmental state, and stress conditions.

**Example trigger:** Conditional gene essentiality under hypoxic stress — models
treat knockout phenotype as invariant across conditions.

---

## Preliminary Qualitative Observations

- **Multi-step inference:** Opus shows stronger performance on problems requiring 4+ reasoning steps compared to Sonnet
- **Confidence calibration:** Both Claude models hedge more appropriately on niche topics compared to GPT-5
- **Network reasoning:** All models struggle with betweenness centrality concepts, defaulting to degree-based hub importance

---

## Implications for AI Safety

1. **Medical AI reliability** — a model missing cascade effects in biological signalling could provide dangerously oversimplified clinical guidance
2. **Confidence miscalibration** — overconfidence on niche topics is an alignment-relevant failure
3. **Predictable failure structure** — the structured, domain-dependent nature of these failures suggests they may be diagnosable and correctable through targeted training interventions

---

*Author: Pranjal Tiwari | [LinkedIn](https://linkedin.com/in/pranjal-tiwari-318a89206) | [GitHub](https://github.com/pranjaltiwari2)*
