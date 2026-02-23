"""
Mind Evolution v4 -- Entry Point
2-Day Meeting Planner (10 participants, 11 constraints)
Configurable islands / pop / generations via CLI args.
"""

import json
import sys
import os
from dotenv import load_dotenv

load_dotenv()


def main():
    # --- Config (override via CLI: python main.py <islands> <pop> <gens> <run_id>) ---
    num_islands = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    pop_size = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    max_gens = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    run_id = sys.argv[4] if len(sys.argv) > 4 else f"run_{num_islands}isl_{max_gens}gen"

    # Patch nodes config before importing
    import nodes
    nodes.NUM_ISLANDS = num_islands
    nodes.POP_SIZE = pop_size
    nodes.MAX_GENERATIONS = max_gens

    from graph import build_graph
    from metrics import init_csv, generate_chart

    print("=" * 70)
    print(f"  MIND EVOLUTION v4 - 2-Day Meeting Planner")
    print(f"  Model: GPT-4.1 nano | Islands: {num_islands} | Pop: {pop_size} | Gen: {max_gens}")
    print(f"  Run ID: {run_id}")
    print("=" * 70)

    init_csv(run_id=run_id)
    app = build_graph()

    # Build initial state dynamically
    initial_state = {
        "generation": 0,
        "max_generations": max_gens,
        "llm_call_count": 0,
        "best_solution": "",
        "best_score": 0.0,
    }
    for i in range(1, num_islands + 1):
        initial_state[f"island_{i}"] = []
        initial_state[f"scores_{i}"] = []
        initial_state[f"feedback_{i}"] = []

    print(f"\n>> Starting evolution...\n")
    result = app.invoke(initial_state)

    # --- Results ---
    print("\n" + "=" * 70)
    print("  RESULTS")
    print("=" * 70)

    best_json = result["best_solution"]
    best_score = result["best_score"]
    total_calls = result["llm_call_count"]

    print(f"\n[SCORE] Best Score: {best_score:.3f}")
    print(f"[CALLS] Total LLM Calls: {total_calls}")

    try:
        parsed = json.loads(best_json)
        print(f"\n[PLAN] Best Meeting Plan:")
        print(json.dumps(parsed, indent=2, ensure_ascii=False))
    except (json.JSONDecodeError, TypeError):
        print(f"\n[PLAN] Best Solution (raw): {best_json[:500]}")

    from evaluator import evaluate
    final_score, final_feedback = evaluate(best_json)
    print(f"\n[VERIFY] Final: score={final_score:.3f}")
    print(f"         Feedback: {final_feedback}")

    if final_score == 1.0:
        print("\n>>> PERFECT PLAN! <<<")

    print(f"[COST] {total_calls} LLM calls | Run: {run_id}")

    print("\n[CHART] Generating metrics chart...")
    generate_chart()
    print("=" * 70)


if __name__ == "__main__":
    main()
