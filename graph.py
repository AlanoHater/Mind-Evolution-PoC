"""
LangGraph StateGraph definition for the Mind Evolution pipeline.
Topology: init → eval → [evolve ↔ eval loop] → migrate → eval → select_best
"""

from langgraph.graph import StateGraph, START, END

from state import MindEvolutionState
from nodes import (
    init_node,
    eval_node,
    evolution_node,
    migration_node,
    select_best_node,
)


def should_evolve_or_migrate(state: MindEvolutionState) -> str:
    """
    Conditional edge after evaluation:
    - If generation < max_generations → evolve
    - Else → migrate (final phase)
    """
    if state["generation"] < state["max_generations"]:
        return "evolve"
    return "migrate"


def build_graph():
    """Build and compile the Mind Evolution LangGraph pipeline."""
    graph = StateGraph(MindEvolutionState)

    # --- Add Nodes ---
    graph.add_node("init", init_node)
    graph.add_node("evaluate", eval_node)
    graph.add_node("evolve", evolution_node)
    graph.add_node("migrate", migration_node)
    graph.add_node("select_best", select_best_node)

    # --- Add Edges ---
    # START → init → evaluate
    graph.add_edge(START, "init")
    graph.add_edge("init", "evaluate")

    # evaluate → (evolve OR migrate) based on generation count
    graph.add_conditional_edges(
        "evaluate",
        should_evolve_or_migrate,
        {
            "evolve": "evolve",
            "migrate": "migrate",
        }
    )

    # evolve → evaluate (loop back for re-evaluation)
    graph.add_edge("evolve", "evaluate")

    # migrate → select_best → END
    graph.add_edge("migrate", "select_best")
    graph.add_edge("select_best", END)

    return graph.compile()
