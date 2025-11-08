"""
LangGraph Workflow Definition for Property Listing System - Iteration 1

This module defines the workflow graph structure that orchestrates the
property listing generation pipeline. The workflow consists of 6 nodes:

1. input_guardrail_node - Combined security checks, validation, and normalization (FIRST)
2. enrich_data_node - Performs web search enrichment (Tavily)
3. predict_price_node - Predicts market price using LLM (runs in parallel with generate_content)
4. generate_content_node - Generates listing content using LLM (runs in parallel with predict_price)
5. output_guardrail_node - Validates LLM output (safety, compliance, quality)
6. format_output_node - Formats final output

The workflow has parallel execution: predict_price_node and generate_content_node
run in parallel after enrichment, then both results flow to output_guardrail_node.

Observability:
- Integrated with Opik for tracing and observability
- Tracks web search calls, LLM calls, and node execution times
- Captures time-to-first-token (TTFT) and total generation time
"""

from typing import Any, Tuple, Optional
from langgraph.graph import StateGraph, START, END
from core.state import PropertyListingState
from core.nodes import (
    input_guardrail_node,
    enrich_data_node,
    predict_price_node,
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


def create_workflow(
    enable_tracing: bool = True,
    use_local_opik: bool = True,
    opik_url: Optional[str] = None
) -> Tuple[Any, Any]:
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
        use_local_opik: Whether to use local Opik server (default: True)
                        Set to False to use Opik Cloud (requires API key)
        opik_url: URL of the local Opik instance (optional, defaults to localhost)
                  Only used when use_local_opik=True
        
    Returns:
        Tuple of (compiled_workflow, tracer)
        - compiled_workflow: Compiled LangGraph workflow ready for execution
        - tracer: OpikTracer instance (None if tracing disabled or unavailable)
        
    Workflow Flow:
        START → input_guardrail → [check errors] → enrich_data → 
        [predict_price || generate_content] (parallel) → 
        output_guardrail → format_output → END
        
    If errors are detected at input_guardrail, workflow stops immediately.
    After enrichment, predict_price and generate_content run in parallel.
    
    Observability:
        - Opik tracer is initialized and attached to the workflow
        - All node executions, web searches, and LLM calls are traced
        - Metrics include execution times, TTFT, and total generation time
    """
    # Step 1: Create StateGraph with state schema
    workflow = StateGraph(PropertyListingState)
    
    # Step 2: Add all nodes to the graph
    workflow.add_node("input_guardrail", input_guardrail_node)
    workflow.add_node("enrich_data", enrich_data_node)
    workflow.add_node("predict_price", predict_price_node)
    workflow.add_node("generate_content", generate_content_node)
    workflow.add_node("output_guardrail", output_guardrail_node)
    workflow.add_node("format_output", format_output_node)
    
    # Step 3: Add edges to connect nodes sequentially
    # Start with input_guardrail (FIRST - combined security, validation, and normalization)
    workflow.add_edge(START, "input_guardrail")
    
    # After input_guardrail: check for errors, stop if any found
    workflow.add_conditional_edges(
        "input_guardrail",
        should_continue_workflow,
        {
            "stop": END,  # Stop immediately if errors found
            "continue": "enrich_data"  # Continue to enrichment if no errors
        }
    )
    
    # After enrichment: run predict_price and generate_content in parallel
    # Both nodes receive the enriched state and can run independently
    # LangGraph will execute both nodes in parallel and merge their states
    workflow.add_edge("enrich_data", "predict_price")
    workflow.add_edge("enrich_data", "generate_content")
    
    # Both parallel nodes feed into output_guardrail
    # LangGraph automatically waits for all incoming edges and merges states
    # Since both nodes write to different fields (predicted_price vs llm_parsed),
    # the state merge will combine both results
    workflow.add_edge("predict_price", "output_guardrail")
    workflow.add_edge("generate_content", "output_guardrail")
    
    # Continue with remaining nodes
    workflow.add_edge("output_guardrail", "format_output")
    
    # End after format_output
    workflow.add_edge("format_output", END)
    
    # Step 4: Compile the graph
    compiled_workflow = workflow.compile()
    
    # Step 5: Initialize Opik tracer for observability
    # Must be done AFTER compiling the graph so we can pass the graph to OpikTracer
    tracer = None
    if enable_tracing:
        try:
            # Get the graph with xray=True for detailed tracing
            graph_with_xray = compiled_workflow.get_graph(xray=True)
            
            tracer = initialize_tracer(
                graph=graph_with_xray,
                project_name="property-listing-system",
                use_local=use_local_opik,
                url=opik_url
            )
            if tracer:
                set_tracer(tracer)
                print("[TRACE] Opik tracer initialized successfully")
                print(f"[TRACE] Opik mode: {'Local' if use_local_opik else 'Cloud'}")
            else:
                print("[TRACE] Opik tracer initialization failed (tracing disabled)")
        except Exception as e:
            print(f"[TRACE] Failed to initialize Opik tracer: {e}")
            print("[TRACE] Continuing without tracing")
    
    return compiled_workflow, tracer

