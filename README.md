# LLM Biology Benchmark

A domain-specific benchmark for evaluating scientific reasoning in frontier large language models (LLMs) across molecular biology, bioinformatics, and pathway analysis.

## Motivation

While benchmarking frontier LLMs on original biology problems, I observed two consistent failure patterns:
- Models giving **confidently wrong answers** on niche biological topics
- **Multi-step reasoning breaking down** on complex pathway questions

These aren't just accuracy problems — they are reliability problems. In scientific domains, unreliable AI causes real harm. This benchmark is designed to systematically probe and document these failure modes.

## Benchmark Structure

| Domain | Problems | Reasoning Type |
|--------|----------|---------------|
| Molecular Biology | 20 | Conceptual, factual recall, niche topic depth |
| Bioinformatics | 20 | Quantitative, tool-based, pipeline reasoning |
| Pathway Analysis | 20 | Multi-step inference, systems-level reasoning |

## Evaluation Dimensions

Each problem is scored across four dimensions:

1. **Factual Accuracy** — Is the answer scientifically correct?
2. **Reasoning Consistency** — Are intermediate steps logically sound?
3. **Confidence Calibration** — Does the model express appropriate uncertainty?
4. **Domain Depth** — Does the answer reflect niche domain knowledge?

## Models Evaluated

- Claude Sonnet
- Claude Opus
- GPT 5.0
## Key Findings

- Sonnet and Opus show systematic reasoning divergences on multi-step pathway questions
- Both models exhibit overconfidence on niche biological topics outside training distribution
- Failure patterns are structured and domain-dependent, not random

*Full results in `/results/model_comparison.md`*

## Repository Structure
