import datetime
from typing import List, Dict, Set, Tuple

# Different strategies (weight combinations)
WEIGHTS = {
    "fastest_wins": {
        "urgency": 0.2,
        "importance": 0.2,
        "effort": 0.5,
        "dependency": 0.1,
    },
    "high_impact": {
        "urgency": 0.2,
        "importance": 0.6,
        "effort": 0.1,
        "dependency": 0.1,
    },
    "deadline_driven": {
        "urgency": 0.6,
        "importance": 0.2,
        "effort": 0.1,
        "dependency": 0.1,
    },
    "smart_balance": {  # default
        "urgency": 0.35,
        "importance": 0.35,
        "effort": 0.15,
        "dependency": 0.15,
    },
}


def parse_date(date_str: str):
    """Convert 'YYYY-MM-DD' to date object, or return None if invalid."""
    if not date_str:
        return None
    try:
        return datetime.date.fromisoformat(date_str)
    except Exception:
        return None


def compute_dependents(tasks: List[Dict]) -> Dict:
    """
    Count how many tasks depend on each task.
    Returns: {task_id: dependents_count}
    """
    dependents = {}

    # Ensure every id exists in the dict
    for task in tasks:
        tid = task.get("id")
        if tid is not None:
            dependents.setdefault(tid, 0)

    # Count dependents
    for task in tasks:
        for dep_id in task.get("dependencies", []) or []:
            dependents[dep_id] = dependents.get(dep_id, 0) + 1

    return dependents


def detect_cycles(tasks_by_id: Dict) -> Set:
    """
    Detect circular dependencies using DFS.
    Returns: set of task IDs involved in a cycle.
    """
    visited = set()
    stack = set()
    in_cycle = set()

    def dfs(task_id):
        if task_id in stack:
            in_cycle.add(task_id)
            return
        if task_id in visited:
            return

        visited.add(task_id)
        stack.add(task_id)

        task = tasks_by_id.get(task_id)
        if task:
            for dep_id in task.get("dependencies", []) or []:
                dfs(dep_id)

        stack.remove(task_id)

    for tid in tasks_by_id.keys():
        if tid not in visited:
            dfs(tid)

    return in_cycle


def normalize_effort_scores(tasks: List[Dict]) -> Dict:
    """
    Convert estimated_hours into scores between 0 and 1.
    Smaller tasks => higher score.
    Returns: {task_id: effort_score}
    """
    hours_list = []
    for t in tasks:
        h = t.get("estimated_hours")
        if isinstance(h, (int, float)) and h > 0:
            hours_list.append(h)

    max_hours = max(hours_list) if hours_list else 4.0
    max_hours = max(max_hours, 4.0)  # at least 4 hours baseline

    result = {}
    for t in tasks:
        tid = t.get("id")
        h = t.get("estimated_hours") or 4.0
        if not isinstance(h, (int, float)) or h <= 0:
            h = 4.0

        # smaller -> closer to 1, larger -> closer to 0
        effort_score = 1.0 - min(h / max_hours, 1.0)
        result[tid] = effort_score

    return result


def score_single_task(
    task: Dict,
    today: datetime.date,
    dependents_count: Dict,
    effort_scores: Dict,
    weights: Dict,
    in_cycle: bool,
) -> Tuple[float, str]:
    """
    Compute score and explanation for one task.
    """

    # 1. Urgency
    due_date = parse_date(task.get("due_date"))
    if due_date is None:
        urgency = 0.5
        urgency_reason = "No due date provided"
    else:
        delta_days = (due_date - today).days
        if delta_days < 0:
            urgency = 1.0 + min(5, abs(delta_days)) / 20.0
            urgency_reason = f"Past due by {abs(delta_days)} day(s)"
        else:
            urgency = max(0.0, 1.0 - delta_days / 30.0)
            urgency_reason = f"Due in {delta_days} day(s)"
    urgency = max(0.0, min(urgency, 1.0))  # clamp between 0 and 1

    # 2. Importance
    importance_raw = task.get("importance") or 5
    try:
        importance_raw = float(importance_raw)
    except Exception:
        importance_raw = 5
    importance_raw = max(1.0, min(10.0, importance_raw))
    importance = importance_raw / 10.0
    importance_reason = f"Importance rated {int(importance_raw)}/10"

    # 3. Effort (quick win)
    tid = task.get("id")
    effort = effort_scores.get(tid, 0.5)
    est_h = task.get("estimated_hours") or "unknown"
    effort_reason = f"Estimated effort: {est_h} hour(s)"

    # 4. Dependency impact
    dep_count = dependents_count.get(tid, 0)
    max_dep = max(dependents_count.values()) if dependents_count else 0
    dependency_score = (dep_count / max_dep) if max_dep > 0 else 0.0

    if dep_count > 0:
        dep_reason = f"Blocks {dep_count} other task(s)"
    else:
        dep_reason = "Does not directly block other tasks"

    # Final weighted score
    score = (
        weights["urgency"] * urgency
        + weights["importance"] * importance
        + weights["effort"] * effort
        + weights["dependency"] * dependency_score
    )

    # Penalize circular dependencies a bit
    if in_cycle:
        score *= 0.8

    reasons = [urgency_reason, importance_reason, effort_reason, dep_reason]
    if in_cycle:
        reasons.append("Involved in circular dependency")

    explanation = "; ".join(reasons)
    return score, explanation


def analyze_tasks(tasks: List[Dict], strategy: str = "smart_balance") -> List[Dict]:
    """
    Main function: takes a list of tasks and returns them scored + sorted.
    """
    if strategy not in WEIGHTS:
        strategy = "smart_balance"
    weights = WEIGHTS[strategy]

    # Ensure each task has an ID
    for idx, t in enumerate(tasks):
        if "id" not in t or t["id"] is None:
            t["id"] = idx + 1

    dependents_count = compute_dependents(tasks)
    effort_scores = normalize_effort_scores(tasks)
    tasks_by_id = {t["id"]: t for t in tasks}
    cycles = detect_cycles(tasks_by_id)

    today = datetime.date.today()
    output = []

    for t in tasks:
        tid = t["id"]
        in_cycle = tid in cycles
        score, explanation = score_single_task(
            t, today, dependents_count, effort_scores, weights, in_cycle
        )
        t_out = dict(t)
        t_out["score"] = round(score, 4)
        t_out["explanation"] = explanation
        output.append(t_out)

    # Sort highest score first
    output.sort(key=lambda x: x["score"], reverse=True)
    return output
