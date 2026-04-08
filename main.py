import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from typing import TypedDict, Dict, Any
from optimized_allocation import allocateDrivers_optimized
import json

load_dotenv()
groqAPI = os.getenv("groqAPI")
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=groqAPI
)

class DispatchState(TypedDict):
    effort_vectors: Dict
    drivers: Dict
    plan: Dict
    allocation: Dict
    critique: Dict
    explanation: Dict

def allocateDrivers(effortVectors, driverData):
    return allocateDrivers_optimized(effortVectors, driverData)

def openJson(filePath):
    with open(filePath, 'r') as file:
        return json.load(file)

def planner_agent(state: DispatchState):

    effort_vectors = state["effort_vectors"]

    # simple rule-based (can upgrade to LLM later)
    plan = {
        "strategy": "fairness_strict",
        "num_clusters": len(effort_vectors),
        "notes": "Prioritize fairness over efficiency"
    }

    return {"plan": plan}

def allocation_agent(state: DispatchState):

    effort_vectors = state["effort_vectors"]
    drivers = state["drivers"]

    allocation = allocateDrivers(effort_vectors, drivers)

    return {"allocation": allocation, "drivers": drivers}

def critic_agent(state: DispatchState):

    allocation = state["allocation"]

    prompt = f"""
You are an expert in logistics fairness systems.

Analyze this allocation:
{allocation}

IMPORTANT:
- Return ONLY valid JSON
- Do NOT include explanations
- Do NOT include <think> or reasoning

Strict format:
{{
  "score": 0.0,
  "issues": [],
  "suggestion": ""
}}
"""

    response = llm.invoke(prompt)

    import json
    try:
        critique_json = json.loads(response.content)
    except:
        critique_json = {
            "score": 0.5,
            "issues": ["invalid_json_response"],
            "suggestion": "LLM output not structured properly"
        }

    return {"critique": critique_json}

def reallocation_agent(state: DispatchState):

    critique = state["critique"]
    score = critique.get("score", 1)

    if score > 0.75:
        return {}
    print("Reallocation triggered")
    for d in state["drivers"].values():
        d["consecutive_heavy_days"] = max(0, d["consecutive_heavy_days"] - 1)

    new_allocation = allocateDrivers(
        state["effort_vectors"],
        state["drivers"]
    )

    return {"allocation": new_allocation}

def explainer_agent(state: DispatchState):

    allocation = state["allocation"]

    prompt = f"""
    Explain this driver allocation in simple terms.

    {allocation}

    For each cluster:
    - Why that driver was chosen
    - Mention fairness and constraints

    Keep it clear and concise.
    """

    response = llm.invoke(prompt)

    return {"explanation": response.content}

from langgraph.graph import StateGraph, END

builder = StateGraph(DispatchState)

builder.add_node("planner", planner_agent)
builder.add_node("allocator", allocation_agent)
builder.add_node("critic", critic_agent)
builder.add_node("reallocator", reallocation_agent)
builder.add_node("explainer", explainer_agent)
def should_reallocate(state: DispatchState):

    critique = state["critique"]

    return critique.get("score", 1) < 0.60

builder.set_entry_point("planner")

builder.add_edge("planner", "allocator")
builder.add_edge("allocator", "critic")

builder.add_conditional_edges(
    "critic",
    should_reallocate,
    {
        True: "reallocator",
        False: "explainer"
    }
)

builder.add_edge("reallocator", "explainer")
builder.add_edge("explainer", END)

graph = builder.compile()

with open("data/jsonFiles/finalFeatures.json", "r") as f:
    effortVectors = json.load(f)

with open("data/jsonFiles/driversdata.json", "r") as f:
    driverData = json.load(f)


result = graph.invoke({
    "effort_vectors": effortVectors,
    "drivers": driverData
})

print(result["allocation"])
print(result["critique"])
print(result["explanation"])