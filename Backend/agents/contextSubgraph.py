"""
agents/contextSubgraph.py
─────────────────────────
Context sub-graph — runs before allocation.

Nodes (in order):
  1. history_loader     — deterministic: summarises driver fatigue
  2. anomaly_detector   — LLM: flags outlier clusters
  3. llm_weight_tuner   — LLM: rewrites DIM_WEIGHTS for today
  4. constraint_gen     — LLM: emits soft avoid/prefer/cap rules
"""

import json
from typing import TypedDict, Dict, Any, List

from langchain_groq import ChatGroq


# ─── State ───────────────────────────────────────────────────────────────────

class ContextState(TypedDict):
    effort_vectors:   Dict[str, Any]
    drivers:          Dict[str, Any]
    anomalies:        List[str]
    tuned_weights:    Dict[str, float]
    soft_constraints: List[Dict]
    context_notes:    str


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


DEFAULT_WEIGHTS = {
    "physical_load":     1.5,
    "stair_load":        1.3,
    "traffic_stress":    1.0,
    "route_distance":    1.2,
    "cognitive_density": 0.8,
}


# ─── Node 1: History Loader (deterministic) ───────────────────────────────────

def history_loader_node(state: ContextState) -> dict:
    """
    Reads cumulative effort + consecutive_heavy_days from each driver
    and produces a plain-text snapshot that LLM nodes can consume.
    """
    lines = []
    for name, data in state["drivers"].items():
        ev  = data.get("cumulative_effort_vector", {})
        pl  = ev.get("physical_load", {})
        rd  = ev.get("route_distance", {})
        chd = data.get("consecutive_heavy_days", 0)
        lines.append(
            f"{name}: weight={pl.get('total_weight', 0):.1f}  "
            f"distance={rd.get('total_distance', 0):.1f}  "
            f"consecutive_heavy={chd}"
        )

    note = "Driver workload snapshot:\n" + "\n".join(lines)
    return {"context_notes": note}


# ─── Node 2: Anomaly Detector (LLM) ──────────────────────────────────────────

def anomaly_detector_node(state: ContextState, llm: ChatGroq) -> dict:
    """
    LLM flags clusters whose values are outliers (>1.5× median)
    in any dimension so the allocator can treat them carefully.
    """
    summary = {
        k: {
            "physical_weight":  v.get("physical_load",  {}).get("total_weight",     0),
            "stair_load_index": v.get("stair_load",     {}).get("stair_load_index", 0),
            "total_distance":   v.get("route_distance", {}).get("total_distance",   0),
            "cognitive_density": v.get("cognitive_density", 0),
        }
        for k, v in state["effort_vectors"].items()
    }

    prompt = f"""
You are a logistics anomaly detector.

Cluster effort data:
{json.dumps(summary, indent=2)}

Driver context:
{state["context_notes"]}

Flag clusters that are outliers (>1.5x the median) in ANY dimension.

Return ONLY valid JSON. No markdown. No explanations.
{{
  "anomaly_clusters": ["cluster_name_1"],
  "reasoning": "one short sentence"
}}
"""
    resp   = llm.invoke(prompt)
    parsed = _parse_json(resp.content, {"anomaly_clusters": [], "reasoning": "parse failed"})

    updated_notes = (
        state["context_notes"]
        + f"\nAnomalies: {parsed.get('reasoning', '')}"
    )
    return {
        "anomalies":     parsed.get("anomaly_clusters", []),
        "context_notes": updated_notes,
    }


# ─── Node 3: LLM Weight Tuner ────────────────────────────────────────────────

def llm_weight_tuner_node(state: ContextState, llm: ChatGroq) -> dict:
    """
    LLM adjusts DIM_WEIGHTS based on today's anomaly profile and
    driver fatigue. Values are clamped to ±40% of defaults so the
    algorithm remains stable.
    """
    prompt = f"""
You are a logistics weight tuner.

Default dimension weights:
{json.dumps(DEFAULT_WEIGHTS, indent=2)}

Context today:
{state["context_notes"]}

Anomaly clusters (need careful handling): {state["anomalies"]}

Adjust weights to reflect today's conditions. For example, if anomalies
are mostly stair-related, increase stair_load weight.

Rules:
- Adjust each weight by at most ±40% from its default.
- If no change is needed, return the default.

Return ONLY valid JSON. No markdown.
{{
  "tuned_weights": {{
    "physical_load": <float>,
    "stair_load": <float>,
    "traffic_stress": <float>,
    "route_distance": <float>,
    "cognitive_density": <float>
  }},
  "reasons": {{ "<dim>": "one sentence", ... }}
}}
"""
    resp   = llm.invoke(prompt)
    parsed = _parse_json(resp.content, {"tuned_weights": DEFAULT_WEIGHTS, "reasons": {}})

    raw     = parsed.get("tuned_weights", DEFAULT_WEIGHTS)
    clamped = {
        dim: max(default * 0.60, min(default * 1.40, float(raw.get(dim, default))))
        for dim, default in DEFAULT_WEIGHTS.items()
    }

    reason_str = "; ".join(
        f"{k}: {v}" for k, v in parsed.get("reasons", {}).items()
    )
    return {
        "tuned_weights": clamped,
        "context_notes": state["context_notes"] + f"\nWeight tuning: {reason_str}",
    }


# ─── Node 4: Constraint Generator (LLM) ──────────────────────────────────────

def constraint_generator_node(state: ContextState, llm: ChatGroq) -> dict:
    """
    LLM generates soft rules for the allocator:
      avoid     — driver should skip a cluster today
      prefer    — driver should take a cluster if possible
      cap_heavy — limit consecutive_heavy_days for a driver
    """
    prompt = f"""
You are a logistics constraint generator.

Driver context:
{state["context_notes"]}

Anomaly clusters: {state["anomalies"]}

Generate soft constraints the scheduler should respect today.

Valid types:
  {{"type": "avoid",     "driver": "<n>", "cluster": "<n>", "reason": "..."}}
  {{"type": "prefer",    "driver": "<n>", "cluster": "<n>", "reason": "..."}}
  {{"type": "cap_heavy", "driver": "<n>", "max_consecutive": <int>, "reason": "..."}}

Return ONLY valid JSON. No markdown.
{{
  "constraints": [ <list> ]
}}
"""
    resp   = llm.invoke(prompt)
    parsed = _parse_json(resp.content, {"constraints": []})
    return {"soft_constraints": parsed.get("constraints", [])}


# ─── Sub-graph builder ────────────────────────────────────────────────────────

from langgraph.graph import StateGraph, END as LGEND


def build_context_subgraph(llm: ChatGroq):
    builder = StateGraph(ContextState)

    builder.add_node("history_loader",   history_loader_node)
    builder.add_node("anomaly_detector", lambda s: anomaly_detector_node(s, llm))
    builder.add_node("llm_weight_tuner", lambda s: llm_weight_tuner_node(s, llm))
    builder.add_node("constraint_gen",   lambda s: constraint_generator_node(s, llm))

    builder.set_entry_point("history_loader")
    builder.add_edge("history_loader",   "anomaly_detector")
    builder.add_edge("anomaly_detector", "llm_weight_tuner")
    builder.add_edge("llm_weight_tuner", "constraint_gen")
    builder.add_edge("constraint_gen",   LGEND)

    return builder.compile()