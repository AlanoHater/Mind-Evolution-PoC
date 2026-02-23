# Mind Evolution PoC: Meeting Planner

This project implements an evolutionary pipeline using **LangGraph** and **GPT-4.1 nano** (v4) to solve a complex Scheduling/Meeting Planner problem.

## Overview

The system uses an "Islands" topology where multiple populations evolve in parallel with migration. Each generation involves:
1. **Initiation**: Generating starting meeting plans.
2. **Evaluation**: A Python-based evaluator checks 11 complex constraints (travel times, prerequisites, day windows, etc.) and assigns a score.
3. **Evolution**: 
   - **LLM Crossover**: Combines two high-scoring parents into a child.
   - **RCC (Reflective Critic-author Correction)**: An LLM "Critic" identifies flaws and an "Author" fixes them.
4. **Migration**: High-performing solutions migrate between islands to maintain diversity.

## Requirements

- Python 3.10+
- OpenAI API Key (with access to `gpt-4.1-nano`)
- LangChain / LangGraph

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure environment:
   - Rename `.env.example` to `.env`
   - Add your `OPENAI_API_KEY` and optional LangSmith keys.

## Running

Launch the evolution pipeline:
```bash
python main.py <islands> <population> <generations> <run_id>
```
Example:
```bash
python main.py 3 4 6 my_first_run
```

## Metrics
The project logs detailed metrics in `metrics.csv` and generates an evolution chart `metrics_chart.png` after each run.
