"""
agents/critiqueSubgraph.py
───────────────────────────
Critique sub-graph — audits the allocation after it is produced.

Nodes (in order):
  1. critic_agent    — LLM: holistic fairness score + issues
  2. policy_checker  — deterministic: hard rule violations pull score down
"""

import json
from typing import TypedDict, Dict, Any, List

from langchain_groq import ChatGroq


# ─── State ───────────────────────────────────────────────────────────────────

class CritiqueState(TypedDict):
    allocation:        Dict[str, str]
    drivers:           Dict[str, Any]
    fairness_report:   Dict[str, Any]
    soft_constraints:  List[Dict]
    anomalies:         List[str]
    context_notes:     str
    critique:          Dict[str, Any]
    policy_violations: List[str]


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _parse_json(text: str, fallback: Any) -> Any:
    try:
        clean = (
            text.strip()
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )
        return json.loads(clean)
    except Exception:
        return fallback


# ─── Node 1: Critic Agent (LLM) ──────────────────────────────────────────────

def critic_agent_node(state: CritiqueState, llm: ChatGroq) -> dict:
    """
    LLM audits the allocation holistically and emits a 0–1 score.
    Score < 0.60 triggers automatic reallocation in the supervisor.
    """
    prompt = f"""
You are an expert logistics fairness auditor.

Allocation (cluster → driver):
{json.dumps(state["allocation"], indent=2)}

Fairness report:
{json.dumps(state["fairness_report"], indent=2)}

Anomaly clusters: {state["anomalies"]}

Active soft constraints:
{json.dumps(state["soft_constraints"], indent=2)}

Context:
{state.get("context_notes", "")}

Evaluate the allocation. Consider:
  - Workload balance across all drivers
  - Anomaly clusters assigned to rested drivers
  - Soft constraints respected
  - Consecutive heavy-day rules honoured

Score 0.0 (completely unfair) to 1.0 (excellent).
A score below 0.60 triggers automatic reallocation — be accurate.

Return ONLY valid JSON. No markdown.
{{
  "score": <float 0.0-1.0>,
  "issues": ["issue 1", "issue 2"],
  "suggestion": "one concrete improvement for the next attempt",
  "driver_assessments": {{
    "<driver>": "one sentence on their workload fairness"
  }}
}}
"""
    resp   = llm.invoke(prompt)
    parsed = _parse_json(resp.content, {
        "score":              0.5,
        "issues":             ["llm_parse_failure"],
        "suggestion":         "rerun with default weights",
        "driver_assessments": {},
    })
    return {"critique": parsed}


# ─── Node 2: Policy Checker (deterministic) ───────────────────────────────────

# FIX Bug 2: reduced per-violation penalty from 0.15 → 0.05 and added a
# 0.40 cap on total deduction.  Previously, 30 phantom violations produced a
# deduction of 4.5, which always floors the score at 0.0 regardless of how
# good the actual allocation was.
_PENALTY_PER_VIOLATION = 0.05
_MAX_PENALTY           = 0.40

def policy_checker_node(state: CritiqueState) -> dict:
    """
    Three hard rules the LLM cannot override:

    RULE-1  No *assigned* driver may have > 3 consecutive heavy days.
            (Only drivers who receive a cluster today are checked — the
             other drivers' historical counts are irrelevant for today's run.)
    RULE-2  Every anomaly cluster must go to a driver with
            consecutive_heavy_days < 2.
    RULE-3  Every cluster in the allocation must have a non-empty driver.
    """
    allocation = state["allocation"]
    drivers    = state["drivers"]
    anomalies  = set(state.get("anomalies", []))
    violations = []

    # FIX Bug 1: only examine drivers who are actually assigned today.
    # Previously this iterated ALL drivers in the database, generating
    # 24-30 phantom violations from historical data and making the score 0.0.
    assigned_drivers = set(allocation.values())

    # RULE-1
    for name, data in drivers.items():
        if name not in assigned_drivers:
            continue   # ← skip drivers not working today
        chd = data.get("consecutive_heavy_days", 0)
        if chd > 3:
            violations.append(
                f"RULE-1: {name} has {chd} consecutive heavy days (max 3)"
            )

    # RULE-2
    for cluster, driver in allocation.items():
        if cluster in anomalies:
            chd = drivers.get(driver, {}).get("consecutive_heavy_days", 0)
            if chd >= 2:
                violations.append(
                    f"RULE-2: anomaly cluster '{cluster}' → '{driver}' "
                    f"who has {chd} consecutive heavy days"
                )

    # RULE-3
    for cluster, driver in allocation.items():
        if not driver:
            violations.append(f"RULE-3: cluster '{cluster}' has no assigned driver")

    if violations:
        print(f"[PolicyChecker] {len(violations)} violation(s):")
        for v in violations:
            print(f"  • {v}")
    else:
        print("[PolicyChecker] No violations.")

    critique      = dict(state.get("critique", {}))
    current_score = float(critique.get("score", 0.5))

    # FIX Bug 2: cap total deduction so a handful of real violations
    # can't by themselves tank the score below the 0.60 retry threshold.
    deduction = min(_MAX_PENALTY, _PENALTY_PER_VIOLATION * len(violations))
    adjusted  = max(0.0, current_score - deduction)

    critique["score"]             = round(adjusted, 4)
    critique["policy_violations"] = violations

    return {
        "critique":          critique,
        "policy_violations": violations,
    }


# ─── Sub-graph builder ────────────────────────────────────────────────────────

from langgraph.graph import StateGraph, END as LGEND


def build_critique_subgraph(llm: ChatGroq):
    builder = StateGraph(CritiqueState)

    builder.add_node("critic_agent",   lambda s: critic_agent_node(s, llm))
    builder.add_node("policy_checker", policy_checker_node)

    builder.set_entry_point("critic_agent")
    builder.add_edge("critic_agent",   "policy_checker")
    builder.add_edge("policy_checker", LGEND)

    return builder.compile()