"""
State definition for Mind Evolution v4 pipeline.
"""

from typing import TypedDict


class MindEvolutionState(TypedDict, total=False):
    # Population (JSON strings) - up to 5 islands
    island_1: list[str]
    island_2: list[str]
    island_3: list[str]
    island_4: list[str]
    island_5: list[str]

    # Fitness
    scores_1: list[float]
    scores_2: list[float]
    scores_3: list[float]
    scores_4: list[float]
    scores_5: list[float]

    # Feedback
    feedback_1: list[str]
    feedback_2: list[str]
    feedback_3: list[str]
    feedback_4: list[str]
    feedback_5: list[str]

    # Control
    generation: int
    max_generations: int
    llm_call_count: int

    # Best
    best_solution: str
    best_score: float
