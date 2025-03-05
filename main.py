"""
Main entry point for the multi-agent question answering system.

This module handles the user interaction, response parsing, and orchestration
of the question answering workflow.
"""

import os
import json
from dotenv import load_dotenv
from typing import Annotated, TypedDict, Dict, Any
from langgraph.graph import StateGraph, END

# Load environment variables from .env file
load_dotenv()

from graph import create_graph

class UserInput(TypedDict):
    """
    Type definition for user input state.
    
    Attributes:
        input (str): The user's question
        continue_conversation (bool): Flag indicating whether to continue the conversation
    """
    input: str
    continue_conversation: bool

def get_user_input(state: UserInput) -> UserInput:
    """
    Get user input from the command line.
    
    Args:
        state (UserInput): Current conversation state
        
    Returns:
        UserInput: Updated state with new user input
    """
    user_input = input("\nEnter your question (or 'q' to quit): ")
    return {
        "input": user_input,
        "continue_conversation": user_input.lower() != 'q'
    }

def parse_response(response_text: Any) -> Dict[str, Any]:
    """
    Parse the LLM response into a structured format.
    
    Args:
        response_text: The raw response from the LLM
        
    Returns:
        Dict[str, Any]: Structured response containing content and metadata
    """
    # Get the content from the AIMessage object
    content = response_text.content if hasattr(response_text, 'content') else str(response_text)
    
    # Split the response into lines
    lines = content.strip().split('\n')
    
    # Initialize the result structure
    result = {
        "content": {
            "main_answer": "",
            "supporting_details": []
        },
        "metadata": {
            "response_id": getattr(response_text, "id", ""),
            "model": getattr(response_text, "model", ""),
            "run_id": getattr(response_text, "run_id", ""),
            "stop_reason": getattr(response_text, "stop_reason", ""),
            "token_usage": getattr(response_text, "usage", {})
        }
    }
    
    # Parse the content
    current_section = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith("MAIN_ANSWER:"):
            current_section = "main_answer"
            result["content"]["main_answer"] = line.replace("MAIN_ANSWER:", "").strip()
        elif line.startswith("SUPPORTING_DETAILS:"):
            current_section = "supporting_details"
        elif line.startswith("-") and current_section == "supporting_details":
            result["content"]["supporting_details"].append(line[1:].strip())
    
    return result

def process_question(state: UserInput) -> UserInput:
    """
    Process a user question through the multi-agent workflow.
    
    This function:
    1. Creates the workflow graph
    2. Invokes the graph with the user's question
    3. Parses and formats the response
    4. Displays the result
    
    Args:
        state (UserInput): Current conversation state containing the question
        
    Returns:
        UserInput: Updated state after processing
    """
    print("\n" + "="*50)
    print("Processing your question...")
    print("-"*50)
    
    graph = create_graph()
    result = graph.invoke({"input": state["input"]})
    
    # Parse and format the response as JSON
    formatted_response = parse_response(result["output"])
    
    # Save to file
    #output_file = "outputs/formatted_output.json"
    #os.makedirs("outputs", exist_ok=True)
    #with open(output_file, "w") as f:
    #    json.dump(formatted_response, f, indent=2)
    
    print("\n" + "="*50)
    print("Response:")
    print("-"*50)
    print(json.dumps(formatted_response, indent=2))
    print("="*50 + "\n")
    
    return state

def create_conversation_graph() -> StateGraph:
    """
    Create and configure the main conversation workflow graph.
    
    The graph implements the following workflow:
    1. Get user input
    2. Process the question
    3. Return to input or end based on user choice
    
    Returns:
        StateGraph: Configured conversation workflow graph
    """
    workflow = StateGraph(UserInput)

    workflow.add_node("get_input", get_user_input)
    workflow.add_node("process_question", process_question)

    workflow.set_entry_point("get_input")

    workflow.add_conditional_edges(
        "get_input",
        lambda x: "continue" if x["continue_conversation"] else "end",
        {
            "continue": "process_question",
            "end": END
        }
    )

    workflow.add_edge("process_question", "get_input")

    return workflow.compile()

def main():
    """
    Main entry point for the application.
    
    Initializes and runs the conversation workflow graph.
    """
    conversation_graph = create_conversation_graph()
    conversation_graph.invoke({"input": "", "continue_conversation": True})

if __name__ == "__main__":
    main()