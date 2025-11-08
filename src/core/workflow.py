"""
LangGraph Workflow Definition for Property Listing System - Iteration 1

This module defines the workflow graph structure that orchestrates the
property listing generation pipeline. The workflow consists of 7 sequential nodes:

1. input_guardrail_node - Safety checks on raw input (FIRST - prevents malicious content)
2. validate_input_node - Validates input fields (business logic validation)
3. normalize_text_node - Normalizes and cleans text inputs
4. enrich_data_node - Performs web search enrichment (Tavily)
5. generate_content_node - Generates listing content using LLM
6. output_guardrail_node - Validates LLM output (safety, compliance, quality)
7. format_output_node - Formats final output

The workflow is linear (sequential) - each node processes the state and passes
it to the next node.

Observability:
- Integrated with Opik for tracing and observability
- Tracks web search calls, LLM calls, and node execution times
- Captures time-to-first-token (TTFT) and total generation time
"""

from typing import Any, Tuple
from langgraph.graph import StateGraph, START, END
from core.state import PropertyListingState
from core.nodes import (
    input_guardrail_node,
    validate_input_node,
    normalize_text_node,
    enrich_data_node,
    generate_content_node,
    output_guardrail_node,
    format_output_node,
)
try:
    from utils.tracing import initialize_tracer, set_tracer, get_tracer
except ImportError:
    # Fallback for relative import
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.tracing import initialize_tracer, set_tracer, get_tracer


def should_continue_workflow(state: PropertyListingState) -> str:
    """
    Conditional routing function to check if workflow should continue.
    
    Checks if there are any errors in the state. If errors exist, workflow
    should stop immediately and return errors to the user.
    
    Args:
        state: Current workflow state
        
    Returns:
        "stop" if errors exist (route to END)
        "continue" if no errors (route to next node)
    """
    errors = state.get("errors", [])
    if errors:
        print(f"[DEBUG] Workflow stopping early due to {len(errors)} error(s)")
        return "stop"
    return "continue"


def create_workflow(enable_tracing: bool = True) -> Tuple[Any, Any]:
    """
    Create and compile the property listing workflow graph with Opik tracing.
    
    Steps:
    1. Create StateGraph with PropertyListingState schema
    2. Add all workflow nodes
    3. Add edges connecting nodes sequentially with conditional routing
    4. Compile the graph
    5. Initialize Opik tracer for observability
    
    Args:
        enable_tracing: Whether to enable Opik tracing (default: True)
        
    Returns:
        Tuple of (compiled_workflow, tracer)
        - compiled_workflow: Compiled LangGraph workflow ready for execution
        - tracer: OpikTracer instance (None if tracing disabled or unavailable)
        
    Workflow Flow:
        START → input_guardrail → [check errors] → validate_input → [check errors] → 
        normalize_text → enrich_data → generate_content → output_guardrail → format_output → END
        
    If errors are detected at input_guardrail or validate_input, workflow stops immediately.
    
    Observability:
        - Opik tracer is initialized and attached to the workflow
        - All node executions, web searches, and LLM calls are traced
        - Metrics include execution times, TTFT, and total generation time
    """
    # Step 1: Create StateGraph with state schema
    workflow = StateGraph(PropertyListingState)
    
    # Step 2: Add all nodes to the graph
    workflow.add_node("input_guardrail", input_guardrail_node)
    workflow.add_node("validate_input", validate_input_node)
    workflow.add_node("normalize_text", normalize_text_node)
    workflow.add_node("enrich_data", enrich_data_node)
    workflow.add_node("generate_content", generate_content_node)
    workflow.add_node("output_guardrail", output_guardrail_node)
    workflow.add_node("format_output", format_output_node)
    
    # Step 3: Add edges to connect nodes sequentially
    # Start with input_guardrail (FIRST - safety checks on raw input)
    workflow.add_edge(START, "input_guardrail")
    
    # After input_guardrail: check for errors, stop if any found
    workflow.add_conditional_edges(
        "input_guardrail",
        should_continue_workflow,
        {
            "stop": END,  # Stop immediately if errors found
            "continue": "validate_input"  # Continue to validation if no errors
        }
    )
    
    # After validate_input: check for errors, stop if any found
    workflow.add_conditional_edges(
        "validate_input",
        should_continue_workflow,
        {
            "stop": END,  # Stop immediately if errors found
            "continue": "normalize_text"  # Continue to normalization if no errors
        }
    )
    
    # Continue with remaining nodes (no conditional checks needed after validation)
    workflow.add_edge("normalize_text", "enrich_data")
    workflow.add_edge("enrich_data", "generate_content")
    workflow.add_edge("generate_content", "output_guardrail")
    workflow.add_edge("output_guardrail", "format_output")
    
    # End after format_output
    workflow.add_edge("format_output", END)
    
    # Step 4: Compile the graph
    compiled_workflow = workflow.compile()
    
    # Step 5: Initialize Opik tracer for observability
    tracer = None
    if enable_tracing:
        try:
            tracer = initialize_tracer(project_name="property-listing-system")
            if tracer:
                set_tracer(tracer)
                print("[TRACE] Opik tracer initialized successfully")
            else:
                print("[TRACE] Opik tracer initialization failed (tracing disabled)")
        except Exception as e:
            print(f"[TRACE] Failed to initialize Opik tracer: {e}")
            print("[TRACE] Continuing without tracing")
    
    return compiled_workflow, tracer

