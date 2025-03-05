"""
Workflow graph definition for the multi-agent question answering system.

This module defines the state management and workflow graph that orchestrates
the interaction between different specialized agents.
"""

from langgraph.graph import StateGraph, END
from typing import Annotated, TypedDict
from agents import analyze_question, answer_code_question, answer_generic_question

#You can precise the format here which could be helpfull for multimodal graphs
class AgentState(TypedDict):
    """
    Type definition for the state managed by the workflow graph.
    
    Attributes:
        input (str): The user's input question
        output (str): The agent's response
        decision (str): The classification of the question type ("code" or "general")
    """
    input: str
    output: str
    decision: str

#Here is a simple 3 steps graph that is going to be working in the bellow "decision" condition
def create_graph() -> StateGraph:
    """
    Create and configure the workflow graph for the multi-agent system.
    
    The graph implements the following workflow:
    1. Analyze the question type
    2. Route to appropriate specialized agent based on type
    3. Generate and return the response
    
    Returns:
        StateGraph: Configured workflow graph instance
    """
    workflow = StateGraph(AgentState)

    workflow.add_node("analyze", analyze_question)
    workflow.add_node("code_agent", answer_code_question)
    workflow.add_node("generic_agent", answer_generic_question)

    workflow.add_conditional_edges(
        "analyze",
        lambda x: x["decision"],
        {
            "code": "code_agent",
            "general": "generic_agent"
        }
    )

    workflow.set_entry_point("analyze")
    workflow.add_edge("code_agent", END)
    workflow.add_edge("generic_agent", END)

    return workflow.compile()