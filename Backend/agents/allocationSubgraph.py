"""
agents/allocationSubgraph.py
─────────────────────────────
Allocation sub-graph — runs after contextSubgraph.

Nodes (in order):
  1. planner          — deterministic: picks strategy from anomaly ratio
  2. core_allocator   — deterministic: runs algorithm with LLM-tuned weights
  3. llm_swap_agent   — LLM: proposes up to 3 validated cluster swaps
  4. fairness_scorer  — deterministic: computes 0–1 workload equity score
"""

import copy
import json
import numpy as np
from typing import TypedDict, Dict, Any, List

from langchain_groq import ChatGroq

# Same package — direct import
from agents.optimized_allocation import (
    allocateDrivers_optimized,
    flatten_effort_vector,
    DIM_WEIGHTS,
    HEAVY_PERCENTILE,
)


# ─── State ───────────────────────────────────────────────────────────────────

class AllocationState(TypedDict):
    effort_vectors:   Dict[str, Any]
    drivers:          Dict[str, Any]
    tuned_weights:    Dict[str, float]
    soft_constraints: List[Dict]
    anomalies:        List[str]
    context_notes:    str
    strategy:         str
    allocation:       Dict[str, str]   # cluster → driver
    swap_log:         List[Dict]
    fairness_score:   float
    fairness_report:  Dict[str, Any]


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


def _driver_workloads(allocation: Dict[str, str],
                      effort_vectors: Dict[str, Any]) -> Dict[str, float]:
    totals: Dict[str, float] = {}
    for cluster, driver in allocation.items():
        vec = flatten_effort_vector(effort_vectors.get(cluster, {}))
        totals[driver] = totals.get(driver, 0.0) + float(np.sum(vec))
    return totals


def _equity_score(totals: Dict[str, float]) -> float:
    """Inverted coefficient of variation → 1.0 = perfect balance."""
    vals = list(totals.values())
    if not vals:
        return 1.0
    mean = float(np.mean(vals))
    if mean == 0:
        return 1.0
    cv = float(np.std(vals) / mean)
    return float(max(0.0, 1.0 - cv))


def _identify_heavy_clusters(effort_vectors: Dict[str, Any]) -> set:
    """
    Returns the set of cluster names classified as 'heavy' using the same
    75th-percentile logic as allocateDrivers_optimized.  Used by the swap
    validator so it can enforce the consecutive_heavy_days constraint.
    """
    names    = list(effort_vectors.keys())
    vecs     = np.array([flatten_effort_vector(v) for v in effort_vectors.values()])
    weights  = vecs[:, 0]
    durs     = vecs[:, 10]
    w_thresh = np.percentile(weights, HEAVY_PERCENTILE * 100)
    d_thresh = np.percentile(durs,    HEAVY_PERCENTILE * 100)
    return {
        names[i]
        for i in range(len(names))
        if weights[i] >= w_thresh or durs[i] >= d_thresh
    }


# ─── Node 1: Planner (deterministic) ─────────────────────────────────────────

def planner_node(state: AllocationState) -> dict:
    n_total   = len(state["effort_vectors"])
    n_anomaly = len(state["anomalies"])
    ratio     = n_anomaly / max(n_total, 1)
    strategy  = "conservative" if ratio > 0.3 else "balanced"

    print(f"[Planner] strategy={strategy}  anomalies={n_anomaly}/{n_total}")
    return {"strategy": strategy}


# ─── Node 2: Core Allocator (deterministic + LLM weight injection) ────────────

def core_allocator_node(state: AllocationState) -> dict:
    """
    Temporarily patches the module-level DIM_WEIGHTS with LLM-tuned
    values, runs the algorithm, then restores the originals.

    FIX Bug 4: drivers are deep-copied before being passed to
    allocateDrivers_optimized, which mutates its argument in-place.
    Without this, each retry compounds effort vectors from the
    previous attempt instead of starting from the original state.
    """
    import agents.optimized_allocation as _oa

    original = _oa.DIM_WEIGHTS.copy()

    if state.get("tuned_weights"):
        _oa.DIM_WEIGHTS.update(state["tuned_weights"])
        print(f"[CoreAllocator] tuned weights: {state['tuned_weights']}")
    drivers_copy = copy.deepcopy(state["drivers"])
    for c in state.get("soft_constraints", []):
        if c.get("type") == "cap_heavy":
            driver = c.get("driver", "")
            cap    = int(c.get("max_consecutive", 2))
            if driver in drivers_copy:
                drivers_copy[driver]["consecutive_heavy_days"] = min(
                    drivers_copy[driver].get("consecutive_heavy_days", 0), cap
                )

    allocation = allocateDrivers_optimized(state["effort_vectors"], drivers_copy)

    # Restore original weights
    _oa.DIM_WEIGHTS.update(original)

    return {"allocation": allocation, "drivers": drivers_copy}


# ─── Node 3: LLM Swap Agent ───────────────────────────────────────────────────

def llm_swap_agent_node(state: AllocationState, llm: ChatGroq) -> dict:
    """
    LLM reviews the allocation and proposes swaps for anomaly clusters
    on fatigued drivers or soft-constraint violations.

    FIX Bug 5: before applying any LLM-proposed swap, the validator now
    checks whether the receiving driver would violate the consecutive_heavy
    constraint (>= 2 heavy days → ineligible for a heavy cluster).  This
    prevents the LLM from inadvertently creating RULE-1 violations that
    the PolicyChecker would then penalise.
    """
    driver_loads  = _driver_workloads(state["allocation"], state["effort_vectors"])
    heavy_clusters = _identify_heavy_clusters(state["effort_vectors"])

    prompt = f"""
You are a logistics allocation reviewer.

Current allocation (cluster → driver):
{json.dumps(state["allocation"], indent=2)}

Driver workload totals:
{json.dumps({k: round(v, 2) for k, v in driver_loads.items()}, indent=2)}

Anomaly clusters needing careful assignment: {state["anomalies"]}

Soft constraints:
{json.dumps(state.get("soft_constraints", []), indent=2)}

Context:
{state.get("context_notes", "")}

Propose at most 3 swaps that improve fairness or fix constraint violations.
A swap exchanges two clusters between two drivers.
Only propose a swap if it genuinely helps. If everything is fine, return [].

Return ONLY valid JSON. No markdown.
{{
  "swaps": [
    {{
      "cluster_a": "...", "driver_a": "...",
      "cluster_b": "...", "driver_b": "...",
      "reason": "one sentence"
    }}
  ]
}}
"""
    resp   = llm.invoke(prompt)
    parsed = _parse_json(resp.content, {"swaps": []})

    updated = dict(state["allocation"])
    applied = []

    for swap in parsed.get("swaps", []):
        ca, da = swap.get("cluster_a"), swap.get("driver_a")
        cb, db = swap.get("cluster_b"), swap.get("driver_b")

        # --- Existing structural validation ---
        if not (ca in updated and cb in updated
                and updated[ca] == da and updated[cb] == db):
            continue
        drivers = state["drivers"]
        if ca in heavy_clusters:
            if drivers.get(db, {}).get("consecutive_heavy_days", 0) >= 2:
                print(
                    f"[LLMSwap] REJECTED {ca}↔{cb}: {db} has "
                    f"{drivers.get(db, {}).get('consecutive_heavy_days', 0)} "
                    "consecutive heavy days (max 2 for heavy cluster)"
                )
                continue
        if cb in heavy_clusters:
            if drivers.get(da, {}).get("consecutive_heavy_days", 0) >= 2:
                print(
                    f"[LLMSwap] REJECTED {ca}↔{cb}: {da} has "
                    f"{drivers.get(da, {}).get('consecutive_heavy_days', 0)} "
                    "consecutive heavy days (max 2 for heavy cluster)"
                )
                continue

        # Swap is safe — apply it
        updated[ca] = db
        updated[cb] = da
        applied.append(swap)
        print(f"[LLMSwap] {ca}↔{cb} ({da}↔{db}) — {swap.get('reason')}")

    return {"allocation": updated, "swap_log": applied}


# ─── Node 4: Fairness Scorer (deterministic) ─────────────────────────────────

def fairness_scorer_node(state: AllocationState) -> dict:
    totals = _driver_workloads(state["allocation"], state["effort_vectors"])
    score  = _equity_score(totals)

    report = {
        "driver_workloads": {k: round(v, 3) for k, v in totals.items()},
        "fairness_score":   round(score, 4),
        "strategy_used":    state.get("strategy", "unknown"),
        "swaps_applied":    len(state.get("swap_log", [])),
    }

    print(f"[FairnessScorer] score={score:.4f}  workloads={totals}")
    return {"fairness_score": score, "fairness_report": report}


# ─── Sub-graph builder ────────────────────────────────────────────────────────

from langgraph.graph import StateGraph, END as LGEND


def build_allocation_subgraph(llm: ChatGroq):
    builder = StateGraph(AllocationState)

    builder.add_node("planner",         planner_node)
    builder.add_node("core_allocator",  core_allocator_node)
    builder.add_node("llm_swap_agent",  lambda s: llm_swap_agent_node(s, llm))
    builder.add_node("fairness_scorer", fairness_scorer_node)

    builder.set_entry_point("planner")
    builder.add_edge("planner",         "core_allocator")
    builder.add_edge("core_allocator",  "llm_swap_agent")
    builder.add_edge("llm_swap_agent",  "fairness_scorer")
    builder.add_edge("fairness_scorer", LGEND)

    return builder.compile()