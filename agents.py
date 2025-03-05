"""
Agent implementations for the multi-agent question answering system.

This module contains the core agent implementations that handle different types of questions
and provide specialized responses using the Claude 3 Sonnet model.
"""

from langchain_anthropic import ChatAnthropic
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
import time
from anthropic._exceptions import OverloadedError, AuthenticationError
from typing import Callable, Any, Dict

def create_llm() -> ChatAnthropic:
    """
    Create and configure the Claude 3 Sonnet language model instance.
    
    Returns:
        ChatAnthropic: Configured Claude 3 Sonnet model instance
    """
    return ChatAnthropic(model="claude-3-sonnet-20240229")

def retry_with_backoff(func: Callable[[], Any], max_retries: int = 3, initial_delay: int = 1) -> Any:
    """
    Execute a function with exponential backoff retry logic.
    
    Args:
        func (Callable[[], Any]): The function to execute
        max_retries (int, optional): Maximum number of retry attempts. Defaults to 3.
        initial_delay (int, optional): Initial delay between retries in seconds. Defaults to 1.
    
    Returns:
        Any: The result of the function execution
    
    Raises:
        OverloadedError: If the API is overloaded and max retries are exceeded
        AuthenticationError: If there's an authentication issue
        Exception: For any other unexpected errors
    """
    for attempt in range(max_retries):
        try:
            return func()
        except OverloadedError as e:
            if attempt == max_retries - 1:
                raise e
            delay = initial_delay * (2 ** attempt)  # Exponential backoff
            print(f"\n⚠️ API is overloaded. Retrying in {delay} seconds...")
            time.sleep(delay)
        except AuthenticationError as e:
            print("\n❌ Authentication Error: Please check your API key in the .env file")
            raise e
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            raise e

# Creating the first analysis agent to check the prompt structure
def analyze_question(state: Dict[str, str]) -> Dict[str, str]:
    """
    Analyze the input question to determine if it's technical or general.
    
    This agent uses Claude 3 Sonnet to classify the question type and route it
    to the appropriate specialized agent.
    
    Args:
        state (Dict[str, str]): Current state containing the input question
        
    Returns:
        Dict[str, str]: Updated state with the decision and input
    """
    print("\nAnalyzing question type...")
    llm = create_llm()
    prompt = PromptTemplate.from_template("""
    You are an agent that needs to define if a question is a technical code one or a general one.

    Question: {input}

    Analyze the question. Only answer with "code" if the question is about technical development. If not just answer "general".

    Your answer (code/general):
    """)
    chain = prompt | llm
    
    def invoke_chain():
        return chain.invoke({"input": state["input"]})
    
    response = retry_with_backoff(invoke_chain)
    decision = response.content.strip().lower()
    print(f"Decision: {decision.upper()}")
    return {"decision": decision, "input": state["input"]}

# Creating the code agent that could be way more technical
def answer_code_question(state: Dict[str, str]) -> Dict[str, Any]:
    """
    Process technical questions using a specialized code expert agent.
    
    This agent provides detailed, step-by-step technical answers with code examples
    and implementation details.
    
    Args:
        state (Dict[str, str]): Current state containing the input question
        
    Returns:
        Dict[str, Any]: Updated state with the formatted response
    """
    print("\nUsing Code Expert Agent...")
    llm = create_llm()
    prompt = PromptTemplate.from_template("""
    You are a software engineer. Answer this question with step-by-step details.

    Question: {input}

    Please format your response as follows:
    MAIN_ANSWER: [Your brief overview]
    SUPPORTING_DETAILS:
    - [Step 1]
    - [Step 2]
    - [Step 3]
    [Add more steps as needed]

    Your response:
    """)
    chain = prompt | llm
    
    def invoke_chain():
        return chain.invoke({"input": state["input"]})
    
    response = retry_with_backoff(invoke_chain)
    return {"output": response}

# Creating the generic agent
def answer_generic_question(state: Dict[str, str]) -> Dict[str, Any]:
    """
    Process general questions using a knowledge agent.
    
    This agent provides clear and concise answers to non-technical questions
    with supporting details and explanations.
    
    Args:
        state (Dict[str, str]): Current state containing the input question
        
    Returns:
        Dict[str, Any]: Updated state with the formatted response
    """
    print("\nUsing General Knowledge Agent...")
    llm = create_llm()
    prompt = PromptTemplate.from_template("""
    Give a clear and concise answer to the question.

    Question: {input}

    Please format your response as follows:
    MAIN_ANSWER: [Your direct answer]
    SUPPORTING_DETAILS:
    - [Supporting detail 1]
    - [Supporting detail 2]
    [Add more details as needed]

    Your response:
    """)
    chain = prompt | llm
    
    def invoke_chain():
        return chain.invoke({"input": state["input"]})
    
    response = retry_with_backoff(invoke_chain)
    return {"output": response}