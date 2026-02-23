"""
Metrics logger for Mind Evolution v4 pipeline.
Supports N islands. Writes CSV + generates matplotlib chart.
"""

import csv
import os
from datetime import datetime

METRICS_FILE = os.path.join(os.path.dirname(__file__), "metrics.csv")
CHART_FILE = os.path.join(os.path.dirname(__file__), "metrics_chart.png")

_HEADERS = [
    "timestamp", "run_id", "generation", "island", "individual",
    "score", "violations", "llm_calls_total", "phase",
]

_initialized = False
_run_id = "default"


def init_csv(run_id: str = "default"):
    """Initialize CSV. Only writes headers if file doesn't exist. Appends otherwise."""
    global _initialized, _run_id
    _run_id = run_id
    if not os.path.exists(METRICS_FILE) or os.path.getsize(METRICS_FILE) == 0:
        with open(METRICS_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(_HEADERS)
    _initialized = True


def log_row(generation, island, individual, score, violations, llm_calls_total, phase):
    global _initialized
    if not _initialized:
        init_csv()
    with open(METRICS_FILE, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([
            datetime.now().isoformat(timespec="seconds"),
            _run_id, generation, island, individual,
            round(score, 3), violations, llm_calls_total, phase,
        ])


def _count_violations(feedback: str) -> int:
    if not feedback or "perfecto" in feedback.lower():
        return 0
    return len(feedback.split(";"))


def log_population(
    generation, scores_1, scores_2, feedback_1, feedback_2,
    llm_calls, phase,
    scores_3=None, feedback_3=None,
):
    """Log all individuals from islands."""
    for i, (s, f) in enumerate(zip(scores_1, feedback_1)):
        log_row(generation, 1, i, s, _count_violations(f), llm_calls, phase)
    for i, (s, f) in enumerate(zip(scores_2, feedback_2)):
        log_row(generation, 2, i, s, _count_violations(f), llm_calls, phase)
    if scores_3 and feedback_3:
        for i, (s, f) in enumerate(zip(scores_3, feedback_3)):
            log_row(generation, 3, i, s, _count_violations(f), llm_calls, phase)


def generate_chart():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("[metrics] matplotlib not installed")
        return

    if not os.path.exists(METRICS_FILE):
        return

    rows = []
    with open(METRICS_FILE, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)

    if not rows:
        return

    # Group by generation
    gens = {}
    for row in rows:
        gen = int(row["generation"])
        score = float(row["score"])
        gens.setdefault(gen, []).append(score)

    gen_nums = sorted(gens.keys())
    if not gen_nums: return
    
    best_scores = [max(gens[g]) for g in gen_nums]
    avg_scores = [sum(gens[g]) / len(gens[g]) for g in gen_nums]
    worst_scores = [min(gens[g]) for g in gen_nums]

    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Chart: Score evolution
    ax1.plot(gen_nums, best_scores, "g-o", label="Best", linewidth=2)
    ax1.plot(gen_nums, avg_scores, "b-s", label="Average", linewidth=1.5)
    ax1.plot(gen_nums, worst_scores, "r-^", label="Worst", linewidth=1)
    ax1.fill_between(gen_nums, worst_scores, best_scores, alpha=0.1, color="blue")
    
    ax1.set_xlabel("Generation")
    ax1.set_ylabel("Score")
    ax1.set_title("Mind Evolution - Score Progress")
    ax1.legend()
    ax1.set_ylim(0, 1.05)
    ax1.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(CHART_FILE, dpi=150)
    plt.close()
    print(f"[metrics] Chart saved to {CHART_FILE}")
