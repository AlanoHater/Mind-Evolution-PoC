"""
Deterministic fitness evaluator v4 (NO LLM).
2-Day Meeting Planner: 10 participants, 8 locations, 11 constraints.
"""

import json
from typing import Tuple

# ── Participants ──
PARTICIPANTS = {
    # Day 1
    "Ana":    {"location": "Cafe Central",       "day": 1, "avail_start": 540,  "avail_end": 720,  "duration": 45},
    "Bruno":  {"location": "Parque Norte",       "day": 1, "avail_start": 600,  "avail_end": 780,  "duration": 30, "prereq": "Ana"},
    "Carla":  {"location": "Biblioteca Sur",     "day": 1, "avail_start": 480,  "avail_end": 660,  "duration": 60},
    "Diego":  {"location": "Oficina Este",       "day": 1, "avail_start": 840,  "avail_end": 1020, "duration": 45},
    "Elena":  {"location": "Centro Comercial",   "day": 0, "avail_start": 900,  "avail_end": 1140, "duration": 30},  # day 0 = both days
    "Felipe": {"location": "Restaurante Oeste",  "day": 1, "avail_start": 660,  "avail_end": 840,  "duration": 60},
    # Day 2
    "Gaby":   {"location": "Hotel Plaza",        "day": 2, "avail_start": 540,  "avail_end": 720,  "duration": 45},
    "Hugo":   {"location": "Museo Central",      "day": 2, "avail_start": 600,  "avail_end": 840,  "duration": 30, "prereq": "Gaby"},
    "Isabel": {"location": "Parque Norte",       "day": 2, "avail_start": 780,  "avail_end": 960,  "duration": 60},
    "Javier": {"location": "Estacion Sur",       "day": 2, "avail_start": 960,  "avail_end": 1140, "duration": 45, "prereq": "Isabel"},
}

LOCATIONS = [
    "Cafe Central", "Parque Norte", "Biblioteca Sur", "Oficina Este",
    "Centro Comercial", "Restaurante Oeste", "Hotel Plaza", "Museo Central",
    "Estacion Sur",
]

# ── Travel times (minutes) ──
_TRAVEL = {
    ("Cafe Central", "Parque Norte"): 20,
    ("Cafe Central", "Biblioteca Sur"): 30,
    ("Cafe Central", "Oficina Este"): 25,
    ("Cafe Central", "Centro Comercial"): 35,
    ("Cafe Central", "Restaurante Oeste"): 15,
    ("Cafe Central", "Hotel Plaza"): 10,
    ("Cafe Central", "Museo Central"): 20,
    ("Cafe Central", "Estacion Sur"): 40,
    ("Parque Norte", "Biblioteca Sur"): 40,
    ("Parque Norte", "Oficina Este"): 15,
    ("Parque Norte", "Centro Comercial"): 25,
    ("Parque Norte", "Restaurante Oeste"): 30,
    ("Parque Norte", "Hotel Plaza"): 25,
    ("Parque Norte", "Museo Central"): 15,
    ("Parque Norte", "Estacion Sur"): 35,
    ("Biblioteca Sur", "Oficina Este"): 35,
    ("Biblioteca Sur", "Centro Comercial"): 45,
    ("Biblioteca Sur", "Restaurante Oeste"): 25,
    ("Biblioteca Sur", "Hotel Plaza"): 35,
    ("Biblioteca Sur", "Museo Central"): 30,
    ("Biblioteca Sur", "Estacion Sur"): 20,
    ("Oficina Este", "Centro Comercial"): 20,
    ("Oficina Este", "Restaurante Oeste"): 30,
    ("Oficina Este", "Hotel Plaza"): 30,
    ("Oficina Este", "Museo Central"): 25,
    ("Oficina Este", "Estacion Sur"): 35,
    ("Centro Comercial", "Restaurante Oeste"): 40,
    ("Centro Comercial", "Hotel Plaza"): 30,
    ("Centro Comercial", "Museo Central"): 20,
    ("Centro Comercial", "Estacion Sur"): 25,
    ("Restaurante Oeste", "Hotel Plaza"): 20,
    ("Restaurante Oeste", "Museo Central"): 25,
    ("Restaurante Oeste", "Estacion Sur"): 30,
    ("Hotel Plaza", "Museo Central"): 15,
    ("Hotel Plaza", "Estacion Sur"): 35,
    ("Museo Central", "Estacion Sur"): 30,
}

# Make symmetric + self
TRAVEL_TIMES = {}
for (a, b), t in _TRAVEL.items():
    TRAVEL_TIMES[(a, b)] = t
    TRAVEL_TIMES[(b, a)] = t
for loc in LOCATIONS:
    TRAVEL_TIMES[(loc, loc)] = 0

DAY_START = 480   # 08:00
DAY_END = 1200    # 20:00
LUNCH_START = 720  # 12:00
LUNCH_END = 780    # 13:00


def _time_str(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _parse_time(time_str: str) -> int:
    try:
        parts = time_str.strip().split(":")
        return int(parts[0]) * 60 + int(parts[1])
    except (ValueError, IndexError):
        return -1


def get_travel_time(loc_a: str, loc_b: str) -> int:
    return TRAVEL_TIMES.get((loc_a, loc_b), 60)


def evaluate(solution_json: str) -> Tuple[float, str]:
    """
    Evaluate a 2-day meeting plan. 11 constraints.
    Score = people_met/10 - 0.06*violations
    """
    try:
        plan = json.loads(solution_json)
    except (json.JSONDecodeError, TypeError):
        return 0.0, "JSON invalido"

    if isinstance(plan, list):
        meetings = plan
    elif isinstance(plan, dict) and "meetings" in plan:
        meetings = plan["meetings"]
    else:
        return 0.0, "Formato invalido: se espera {\"meetings\": [...]}"

    if not meetings or not isinstance(meetings, list):
        return 0.0, "Lista de reuniones vacia"

    violations = []
    valid_meetings = []
    people_seen = set()

    for m in meetings:
        person = m.get("person", "")
        if person not in PARTICIPANTS:
            violations.append(f"Persona '{person}' no existe")
            continue

        # C10: No duplicates
        if person in people_seen:
            violations.append(f"C10: {person} duplicado")
            continue
        people_seen.add(person)

        day = m.get("day", 0)
        start = _parse_time(m.get("start", ""))
        end = _parse_time(m.get("end", ""))

        if start < 0 or end < 0:
            violations.append(f"Hora invalida para {person}")
            continue
        if day not in (1, 2):
            violations.append(f"C7: {person} dia {day} invalido (debe ser 1 o 2)")
            continue

        info = PARTICIPANTS[person]

        # C7: Correct day
        if info["day"] != 0 and info["day"] != day:
            violations.append(f"C7: {person} debe ser dia {info['day']}, no dia {day}")

        # C1: Within availability window
        if start < info["avail_start"]:
            violations.append(f"C1: {person} empieza {_time_str(start)}, disponible desde {_time_str(info['avail_start'])}")
        if end > info["avail_end"]:
            violations.append(f"C1: {person} termina {_time_str(end)}, disponible hasta {_time_str(info['avail_end'])}")

        # C4: Duration
        actual_dur = end - start
        if actual_dur < info["duration"]:
            violations.append(f"C4: {person} dura {actual_dur}min, necesita {info['duration']}min")

        # C5: Day bounds
        if start < DAY_START:
            violations.append(f"C5: {person} antes de 08:00")
        if end > DAY_END:
            violations.append(f"C5: {person} despues de 20:00")

        valid_meetings.append({
            "person": person,
            "day": day,
            "start": start,
            "end": end,
            "location": info["location"],
        })

    # Split by day
    day1 = sorted([m for m in valid_meetings if m["day"] == 1], key=lambda x: x["start"])
    day2 = sorted([m for m in valid_meetings if m["day"] == 2], key=lambda x: x["start"])

    # C3: No overlapping meetings (per day)
    for day_meetings, day_label in [(day1, "D1"), (day2, "D2")]:
        for i in range(len(day_meetings) - 1):
            curr = day_meetings[i]
            nxt = day_meetings[i + 1]
            if curr["end"] > nxt["start"]:
                violations.append(
                    f"C3: {day_label} {curr['person']}({_time_str(curr['end'])}) solapa {nxt['person']}({_time_str(nxt['start'])})"
                )

    # C2: Travel time (per day)
    # C8: Start from Cafe Central each day at 08:00
    for day_meetings, day_label in [(day1, "D1"), (day2, "D2")]:
        prev_loc = "Cafe Central"
        prev_end = DAY_START
        for m in day_meetings:
            travel = get_travel_time(prev_loc, m["location"])
            earliest = prev_end + travel
            if m["start"] < earliest:
                violations.append(
                    f"C2: {day_label} llegas a {m['location']} a {_time_str(earliest)} "
                    f"(travel {travel}min desde {prev_loc}), "
                    f"pero {m['person']} empieza {_time_str(m['start'])}"
                )
            prev_loc = m["location"]
            prev_end = m["end"]

    # C6: Meet at least 7 of 10
    people_met = len(people_seen)
    if people_met < 7:
        violations.append(f"C6: Solo {people_met} reuniones, minimo 7")

    # C9: Prerequisites
    meeting_order = {}
    for m in day1 + day2:
        meeting_order[m["person"]] = (m["day"], m["start"])

    for person, info in PARTICIPANTS.items():
        if "prereq" in info and person in meeting_order:
            prereq = info["prereq"]
            if prereq not in meeting_order:
                violations.append(f"C9: {person} requiere {prereq}, pero {prereq} no programado")
            else:
                p_day, p_start = meeting_order[prereq]
                m_day, m_start = meeting_order[person]
                # prereq must be earlier (same day before, or earlier day)
                if (p_day, p_start) >= (m_day, m_start):
                    violations.append(f"C9: {person} requiere {prereq} antes, pero {prereq} es D{p_day}/{_time_str(p_start)}")

    # C11: At least 4 meetings on day 1 AND at least 3 on day 2
    d1_count = len([m for m in valid_meetings if m["day"] == 1])
    d2_count = len([m for m in valid_meetings if m["day"] == 2])
    if d1_count < 4:
        violations.append(f"C11: Solo {d1_count} reuniones dia 1, minimo 4")
    if d2_count < 3:
        violations.append(f"C11: Solo {d2_count} reuniones dia 2, minimo 3")

    # ── Score ──
    if people_met == 0:
        return 0.0, "Ninguna reunion valida"

    coverage = people_met / 10.0
    penalty = len(violations) * 0.06
    score = max(0.0, coverage - penalty)

    if not violations and people_met == 10:
        score = 1.0

    feedback = "; ".join(violations) if violations else f"Plan perfecto: {people_met} reuniones sin violaciones"
    return round(score, 3), feedback
