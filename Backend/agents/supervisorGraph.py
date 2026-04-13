"""
agents/supervisorGraph.py
──────────────────────────
Supervisor graph — called from main.py after preprocessing.

Public API:
    from agents.supervisorGraph import run_dispatch

    result = run_dispatch(effort_vectors, driver_data)
    # result keys: allocation, fairness_report, critique, explanation

Internal flow:
    context_phase → allocation_phase → critique_phase
                                            ↓
                          score < 0.60 → reallocator → allocation_phase (retry)
                          score ≥ 0.60 → explainer → END

LLM-influenced nodes (★):
    ★ anomaly_detector   — flags outlier clusters
    ★ llm_weight_tuner   — adjusts DIM_WEIGHTS dynamically
    ★ constraint_gen     — injects soft avoid/prefer/cap rules
    ★ llm_swap_agent     — post-allocation cluster swaps
    ★ critic_agent       — holistic fairness scoring
    ★ explainer          — plain-English daily briefing
"""

import copy
import os
import json
from typing import TypedDict, Dict, Any, List

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END

from Backend.agents.contextSubgraph    import build_context_subgraph,    ContextState
from Backend.agents.allocationSubgraph import build_allocation_subgraph, AllocationState
from Backend.agents.critiqueSubgraph   import build_critique_subgraph,   CritiqueState

load_dotenv()

# ─── LLM setup ───────────────────────────────────────────────────────────────

def _make_llm() -> ChatGroq:
    return ChatGroq(
        model="openai/gpt-oss-120b",
        api_key=os.getenv("groqAPI2"),
    )

MAX_REALLOCATION_ATTEMPTS = 2


# ─── Master state ─────────────────────────────────────────────────────────────

class DispatchState(TypedDict):
    # ── Inputs (set by main.py) ──────────────────────────────────────────────
    effort_vectors:          Dict[str, Any]
    drivers:                 Dict[str, Any]

    # ── Context sub-graph outputs ────────────────────────────────────────────
    anomalies:               List[str]
    tuned_weights:           Dict[str, float]
    soft_constraints:        List[Dict]
    context_notes:           str

    # ── Allocation sub-graph outputs ─────────────────────────────────────────
    strategy:                str
    allocation:              Dict[str, str]
    swap_log:                List[Dict]
    fairness_score:          float
    fairness_report:         Dict[str, Any]

    # ── Critique sub-graph outputs ───────────────────────────────────────────
    critique:                Dict[str, Any]
    policy_violations:       List[str]

    # ── Supervisor bookkeeping ───────────────────────────────────────────────
    reallocation_attempts:   int

    # ── Terminal output ──────────────────────────────────────────────────────
    explanation:             str


# ─── Phase wrappers ───────────────────────────────────────────────────────────

def _run_context(state: DispatchState, graphs: dict) -> dict:
    print("\n══ [Supervisor] Context phase ══")
    result = graphs["context"].invoke({
        "effort_vectors":   state["effort_vectors"],
        "drivers":          state["drivers"],
        "anomalies":        [],
        "tuned_weights":    {},
        "soft_constraints": [],
        "context_notes":    "",
    })
    return {
        "anomalies":        result["anomalies"],
        "tuned_weights":    result["tuned_weights"],
        "soft_constraints": result["soft_constraints"],
        "context_notes":    result["context_notes"],
    }


def _run_allocation(state: DispatchState, graphs: dict) -> dict:
    print("\n══ [Supervisor] Allocation phase ══")
    drivers_snapshot = copy.deepcopy(state["drivers"])

    result = graphs["allocation"].invoke({
        "effort_vectors":   state["effort_vectors"],
        "drivers":          drivers_snapshot,
        "tuned_weights":    state.get("tuned_weights",    {}),
        "soft_constraints": state.get("soft_constraints", []),
        "anomalies":        state.get("anomalies",        []),
        "context_notes":    state.get("context_notes",    ""),
        "strategy":         "",
        "allocation":       {},
        "swap_log":         [],
        "fairness_score":   0.0,
        "fairness_report":  {},
    })
    return {
        "strategy":        result["strategy"],
        "allocation":      result["allocation"],
        "swap_log":        result.get("swap_log", []),
        "fairness_score":  result["fairness_score"],
        "fairness_report": result["fairness_report"],
        "drivers":         result["drivers"],   # updated cumulative effort
    }


def _run_critique(state: DispatchState, graphs: dict) -> dict:
    print("\n══ [Supervisor] Critique phase ══")
    result = graphs["critique"].invoke({
        "allocation":        state["allocation"],
        "drivers":           state["drivers"],
        "fairness_report":   state["fairness_report"],
        "soft_constraints":  state.get("soft_constraints", []),
        "anomalies":         state.get("anomalies",        []),
        "context_notes":     state.get("context_notes",    ""),
        "critique":          {},
        "policy_violations": [],
    })
    return {
        "critique":          result["critique"],
        "policy_violations": result.get("policy_violations", []),
    }


# ─── Supervisor nodes ─────────────────────────────────────────────────────────

def make_context_node(graphs):
    def node(state): return _run_context(state, graphs)
    return node

def make_allocation_node(graphs):
    def node(state): return _run_allocation(state, graphs)
    return node

def make_critique_node(graphs):
    def node(state): return _run_critique(state, graphs)
    return node


def reallocator_node(state: DispatchState) -> dict:

    attempt = state.get("reallocation_attempts", 0) + 1
    print(f"\n══ [Supervisor] Reallocation attempt {attempt} ══")

    assigned_today = set(state.get("allocation", {}).values())

    drivers_reset = copy.deepcopy(state["drivers"])
    for name, data in drivers_reset.items():
        if name in assigned_today:
            data["consecutive_heavy_days"] = min(
                data.get("consecutive_heavy_days", 0), 3
            )

    return {
        "drivers":               drivers_reset,
        "reallocation_attempts": attempt,
    }


def make_explainer_node(llm: ChatGroq):
    def explainer_node(state: DispatchState) -> dict:
        print("\n══ [Supervisor] Explainer ══")
        prompt = f"""
You are a logistics dispatch coordinator writing a daily briefing.

Final allocation (cluster → driver):
{json.dumps(state["allocation"], indent=2)}

Fairness report:
{json.dumps(state["fairness_report"], indent=2)}

Critique score: {state["critique"].get("score", "N/A")}
Critique issues: {state["critique"].get("issues", [])}

AI-suggested swaps applied: {state.get("swap_log", [])}
Policy violations found: {state.get("policy_violations", [])}

Write a clear 3–5 paragraph briefing:
  1. Who is assigned where and why
  2. Special considerations (anomalies, fatigued drivers)
  3. Overall fairness assessment
  4. Any remaining concerns or suggestions for tomorrow

Plain English only. No JSON. No markdown headers.
"""
        resp = llm.invoke(prompt)
        return {"explanation": resp.content}
    return explainer_node


# ─── Routing ──────────────────────────────────────────────────────────────────

def _should_reallocate(state: DispatchState) -> str:
    score    = float(state["critique"].get("score", 1.0))
    attempts = state.get("reallocation_attempts", 0)
    if score < 0.60 and attempts < MAX_REALLOCATION_ATTEMPTS:
        print(f"[Supervisor] score={score:.3f} < 0.60 → reallocation")
        return "reallocate"
    print(f"[Supervisor] score={score:.3f} → explain")
    return "explain"


# ─── Graph builder ────────────────────────────────────────────────────────────

def _build_graph(llm: ChatGroq) -> "CompiledGraph":
    graphs = {
        "context":    build_context_subgraph(llm),
        "allocation": build_allocation_subgraph(llm),
        "critique":   build_critique_subgraph(llm),
    }

    builder = StateGraph(DispatchState)

    builder.add_node("context_phase",    make_context_node(graphs))
    builder.add_node("allocation_phase", make_allocation_node(graphs))
    builder.add_node("critique_phase",   make_critique_node(graphs))
    builder.add_node("reallocator",      reallocator_node)
    builder.add_node("explainer",        make_explainer_node(llm))

    builder.set_entry_point("context_phase")
    builder.add_edge("context_phase",    "allocation_phase")
    builder.add_edge("allocation_phase", "critique_phase")

    builder.add_conditional_edges(
        "critique_phase",
        _should_reallocate,
        {"reallocate": "reallocator", "explain": "explainer"},
    )

    builder.add_edge("reallocator", "allocation_phase")   # retry loop
    builder.add_edge("explainer",   END)

    return builder.compile()


# ─── Public API — called from main.py ────────────────────────────────────────

def run_dispatch(effort_vectors: Dict[str, Any],
                 driver_data:    Dict[str, Any]) -> Dict[str, Any]:
    """
    Entry point for main.py.

    Args:
        effort_vectors: cluster-level effort feature vectors
        driver_data:    per-driver cumulative effort + metadata

    Returns:
        dict with keys: allocation, fairness_report, critique, explanation
    """
    llm   = _make_llm()
    graph = _build_graph(llm)

    initial: DispatchState = {
        "effort_vectors":        effort_vectors,
        "drivers":               driver_data,
        "anomalies":             [],
        "tuned_weights":         {},
        "soft_constraints":      [],
        "context_notes":         "",
        "strategy":              "",
        "allocation":            {},
        "swap_log":              [],
        "fairness_score":        0.0,
        "fairness_report":       {},
        "critique":              {},
        "policy_violations":     [],
        "reallocation_attempts": 0,
        "explanation":           "",
    }

    result = graph.invoke(initial)

    return {
        "allocation":      result["allocation"],
        "fairness_report": result["fairness_report"],
        "critique":        result["critique"],
        "explanation":     result["explanation"],
    }