"""
LangGraph nodes for Mind Evolution v4 pipeline.
"""

import json
import re
import time
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from state import MindEvolutionState
from evaluator import evaluate
from prompts import INIT_PROMPT, CRITIC_PROMPT, AUTHOR_PROMPT, CROSSOVER_PROMPT
from metrics import log_population, log_row, _count_violations

# ── Config (patched from main) ──
POP_SIZE = 4
NUM_ISLANDS = 3
MAX_GENERATIONS = 6

# ── LLM singleton ──
_llm = None


def get_llm() -> ChatOpenAI:
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model="gpt-4.1-nano",
            temperature=0.9,
            max_tokens=1200,
        )
    return _llm


def _call_llm(prompt: str, temperature: float = None) -> str:
    """Single LLM call with retry on rate limit."""
    llm = get_llm()
    if temperature is not None:
        llm = llm.bind(temperature=temperature)

    max_retries = 4
    for attempt in range(max_retries):
        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            return response.content.strip()
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "rate" in error_str.lower():
                wait = 35 + attempt * 15
                print(f"    [rate-limit] Waiting {wait}s (retry {attempt+1}/{max_retries})...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("Max retries exceeded for LLM call")

def _extract_json(text: str) -> str:
    """Extract JSON from LLM response, stripping comments and markdown."""
    text = re.sub(r'```(?:json)?\s*', '', text)
    text = re.sub(r'```', '', text)
    text = re.sub(r'//[^\n]*', '', text)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    
    depth = 0
    start_idx = None
    for i, ch in enumerate(text):
        if ch == '{':
            if depth == 0: start_idx = i
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0 and start_idx is not None:
                return text[start_idx:i+1].strip()
    match = re.search(r'\{.*\}', text, re.DOTALL)
    return match.group(0).strip() if match else text


def init_node(state: MindEvolutionState) -> dict:
    """Generate initial population."""
    islands = {i: [] for i in range(1, NUM_ISLANDS + 1)}
    call_count = 0
    temps = [0.7, 0.8, 0.9, 1.0]

    for island_num in range(1, NUM_ISLANDS + 1):
        for i in range(POP_SIZE):
            t = temps[i % len(temps)]
            raw = _call_llm(INIT_PROMPT, temperature=t)
            islands[island_num].append(_extract_json(raw))
            call_count += 1

    result = {
        "generation": 0,
        "max_generations": MAX_GENERATIONS,
        "llm_call_count": call_count,
        "best_solution": "",
        "best_score": 0.0,
    }
    for i in range(1, NUM_ISLANDS + 1):
        result[f"island_{i}"] = islands[i]
        result[f"scores_{i}"] = [0.0] * POP_SIZE
        result[f"feedback_{i}"] = [""] * POP_SIZE
    return result


def eval_node(state: MindEvolutionState) -> dict:
    """Evaluate all individuals across all islands."""
    all_scores = {}
    all_feedback = {}

    for island_num in range(1, NUM_ISLANDS + 1):
        key_island = f"island_{island_num}"
        key_scores = f"scores_{island_num}"
        key_fb = f"feedback_{island_num}"
        scores, feedbacks = [], []

        for sol in state[key_island]:
            s, f = evaluate(sol)
            scores.append(s)
            feedbacks.append(f)

        all_scores[key_scores] = scores
        all_feedback[key_fb] = feedbacks

    combined_scores = []
    combined_sols = []
    for i in range(1, NUM_ISLANDS + 1):
        combined_scores += all_scores[f"scores_{i}"]
        combined_sols += state[f"island_{i}"]
    
    best_idx = max(range(len(combined_scores)), key=lambda i: combined_scores[i])
    best_score = combined_scores[best_idx]
    best_solution = combined_sols[best_idx]
    
    if state.get("best_score", 0.0) > best_score:
        best_score = state["best_score"]
        best_solution = state["best_solution"]

    parts = [f"I{i}:{[f'{s:.2f}' for s in all_scores[f'scores_{i}']]}" for i in range(1, NUM_ISLANDS + 1)]
    print(f"  [eval] Gen {state['generation']} | {' | '.join(parts)} | Best:{best_score:.2f}")

    # Metrics
    for i in range(1, NUM_ISLANDS + 1):
        for j, (s, f) in enumerate(zip(all_scores[f"scores_{i}"], all_feedback[f"feedback_{i}"])):
            log_row(state["generation"], i, j, s, _count_violations(f), state.get("llm_call_count", 0), "eval")

    result = {**all_scores, **all_feedback, "best_solution": best_solution, "best_score": best_score}
    return result


def evolution_node(state: MindEvolutionState) -> dict:
    """LLM crossover + RCC refinement per island."""
    call_count = state["llm_call_count"]
    new_islands = {}

    for island_num in range(1, NUM_ISLANDS + 1):
        key = f"island_{island_num}"
        scores = state[f"scores_{island_num}"]
        island = list(state[key])
        label = f"I{island_num}"

        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        best_idx, second_idx, worst_idx = ranked[0], ranked[1], ranked[-1]

        # Crossover
        crossover_prompt = (CROSSOVER_PROMPT.replace("<<parent_a>>", island[best_idx])
                            .replace("<<score_a>>", f"{scores[best_idx]:.2f}")
                            .replace("<<parent_b>>", island[second_idx])
                            .replace("<<score_b>>", f"{scores[second_idx]:.2f}"))
        child_raw = _call_llm(crossover_prompt, temperature=0.5)
        child_json = _extract_json(child_raw)
        call_count += 1
        child_score, child_feedback = evaluate(child_json)

        # RCC
        if child_score < 1.0:
            critique = _call_llm(CRITIC_PROMPT.replace("<<solution>>", child_json).replace("<<feedback>>", child_feedback), temperature=0.3)
            call_count += 1
            fixed_raw = _call_llm(AUTHOR_PROMPT.replace("<<solution>>", child_json).replace("<<critique>>", critique), temperature=0.4)
            child_json = _extract_json(fixed_raw)
            call_count += 1

        island[worst_idx] = child_json
        new_islands[key] = island

    return {**new_islands, "generation": state["generation"] + 1, "llm_call_count": call_count}


def migration_node(state: MindEvolutionState) -> dict:
    """Ring migration."""
    islands = [list(state[f"island_{i}"]) for i in range(1, NUM_ISLANDS + 1)]
    scores = [state[f"scores_{i}"] for i in range(1, NUM_ISLANDS + 1)]
    bests = [max(range(len(s)), key=lambda i: s[i]) for s in scores]
    worsts = [min(range(len(s)), key=lambda i: s[i]) for s in scores]

    migrants = [islands[i][bests[i]] for i in range(NUM_ISLANDS)]
    for i in range(NUM_ISLANDS):
        target = (i + 1) % NUM_ISLANDS
        islands[target][worsts[target]] = migrants[i]

    result = {f"island_{i+1}": islands[i] for i in range(NUM_ISLANDS)}
    return result


def select_best_node(state: MindEvolutionState) -> dict:
    """Pick final best."""
    all_sols = []
    all_scores = []
    for i in range(1, NUM_ISLANDS + 1):
        all_sols += state[f"island_{i}"]
        all_scores += state[f"scores_{i}"]
    best_idx = max(range(len(all_scores)), key=lambda i: all_scores[i])
    best = all_sols[best_idx]
    best_score = all_scores[best_idx]

    if state.get("best_score", 0.0) > best_score:
        best = state["best_solution"]
        best_score = state["best_score"]

    print(f"\n  [select] Final best score: {best_score:.3f}")
    return {"best_solution": best, "best_score": best_score}
