"""
Tracing and Observability Utilities for Property Listing System - Iteration 1

This module provides Opik-based tracing and observability for the LangGraph workflow.
It tracks:
- Web search calls (Tavily)
- LLM calls (OpenAI)
- Context preparation (prompt building)
- Time to first token (TTFT)
- Total response generation time
- Node execution times
"""

import time
from typing import Optional, Dict, Any, Callable, Tuple
from functools import wraps
import uuid


# Global tracer instance (initialized in workflow.py)
_tracer: Optional[Any] = None
_trace_metadata: Dict[str, Any] = {}


def initialize_tracer(project_name: str = "property-listing-system") -> Any:
    """
    Initialize Opik tracer for LangGraph workflow.
    
    Args:
        project_name: Name of the project for Opik dashboard
        
    Returns:
        OpikTracer instance
    """
    try:
        from opik.integrations.langchain import OpikTracer
        return OpikTracer(project_name=project_name)
    except ImportError:
        print("[WARNING] Opik not installed. Tracing will be disabled.")
        return None


def set_tracer(tracer: Any) -> None:
    """Set the global tracer instance."""
    global _tracer
    _tracer = tracer


def get_tracer() -> Optional[Any]:
    """Get the global tracer instance."""
    return _tracer


def set_trace_metadata(key: str, value: Any) -> None:
    """Set metadata for the current trace."""
    global _trace_metadata
    _trace_metadata[key] = value


def get_trace_metadata() -> Dict[str, Any]:
    """Get all trace metadata."""
    return _trace_metadata.copy()


def clear_trace_metadata() -> None:
    """Clear trace metadata (call at start of new request)."""
    global _trace_metadata
    _trace_metadata = {}


class TimingContext:
    """Context manager for timing operations and tracking metrics."""
    
    def __init__(self, operation_name: str, metadata: Optional[Dict[str, Any]] = None):
        self.operation_name = operation_name
        self.metadata = metadata or {}
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.duration: Optional[float] = None
        self.first_token_time: Optional[float] = None
        self.ttft: Optional[float] = None
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        if self.start_time:
            self.duration = self.end_time - self.start_time
        
        # Log timing information
        if self.duration is not None:
            print(f"[TRACE] {self.operation_name}: {self.duration:.3f}s")
            if self.metadata:
                print(f"[TRACE] Metadata: {self.metadata}")
        
        return False
    
    def mark_first_token(self):
        """Mark the time when first token is received (for TTFT calculation)."""
        if self.start_time:
            self.first_token_time = time.time()
            self.ttft = self.first_token_time - self.start_time
            print(f"[TRACE] {self.operation_name} - TTFT: {self.ttft:.3f}s")
            return self.ttft
        return None
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get timing metrics."""
        metrics = {
            "operation": self.operation_name,
            "duration": self.duration,
            "start_time": self.start_time,
            "end_time": self.end_time,
        }
        if self.ttft is not None:
            metrics["ttft"] = self.ttft
        if self.metadata:
            metrics["metadata"] = self.metadata
        return metrics


def trace_operation(operation_name: str, metadata: Optional[Dict[str, Any]] = None):
    """
    Decorator to trace an operation with timing.
    
    Usage:
        @trace_operation("web_search", {"query": "..."})
        def my_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_metadata = metadata or {}
            # Add function name and args info
            op_metadata["function"] = func.__name__
            
            with TimingContext(operation_name, op_metadata) as timer:
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    op_metadata["error"] = str(e)
                    raise
        return wrapper
    return decorator


def trace_llm_call(
    llm: Any,
    prompt: str,
    temperature: float = 0.7,
    model_name: Optional[str] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Call LLM with tracing for TTFT and total generation time.
    
    Args:
        llm: LLM instance
        prompt: Prompt string
        temperature: Temperature setting
        model_name: Model name for metadata
        
    Returns:
        Tuple of (response, metrics_dict)
    """
    from langchain_core.messages import HumanMessage
    
    metrics = {
        "operation": "llm_call",
        "model": model_name or "unknown",
        "temperature": temperature,
        "prompt_length": len(prompt),
    }
    
    with TimingContext("llm_call", metrics) as timer:
        try:
            # Create messages
            messages = [HumanMessage(content=prompt)]
            
            # For streaming LLMs, we can track TTFT
            # For now, we'll track the full call duration
            # If the LLM supports streaming, we can enhance this
            
            # Check if LLM supports streaming
            if hasattr(llm, "stream"):
                # Use streaming to track TTFT
                first_token_received = False
                response_parts = []
                
                for chunk in llm.stream(messages):
                    if not first_token_received:
                        timer.mark_first_token()
                        first_token_received = True
                    
                    if hasattr(chunk, 'content'):
                        response_parts.append(chunk.content)
                    elif isinstance(chunk, str):
                        response_parts.append(chunk)
                
                response = "".join(response_parts)
            else:
                # Non-streaming: invoke and track total time
                response = llm.invoke(messages)
                
                # Extract content
                if hasattr(response, 'content'):
                    response = response.content
                elif isinstance(response, str):
                    pass  # Already a string
                else:
                    response = str(response)
            
            # Update metrics
            metrics.update(timer.get_metrics())
            metrics["response_length"] = len(response)
            
            return response, metrics
            
        except Exception as e:
            metrics["error"] = str(e)
            raise


def trace_web_search(
    search_tool: Any,
    query: str,
    max_results: int = 3
) -> Tuple[list, Dict[str, Any]]:
    """
    Perform web search with tracing.
    
    Args:
        search_tool: TavilySearch tool instance
        query: Search query
        max_results: Maximum results to return
        
    Returns:
        Tuple of (results_list, metrics_dict)
    """
    metrics = {
        "operation": "web_search",
        "query": query,
        "max_results": max_results,
    }
    
    with TimingContext("web_search", metrics) as timer:
        try:
            # Perform search
            results = search_tool.invoke({"query": query})
            
            # Extract results
            if isinstance(results, dict) and "results" in results:
                results_list = results["results"][:max_results]
            elif isinstance(results, list):
                results_list = results[:max_results]
            else:
                results_list = []
            
            # Update metrics
            metrics.update(timer.get_metrics())
            metrics["results_count"] = len(results_list)
            metrics["success"] = True
            
            # Extract URLs for reference
            if results_list:
                metrics["urls"] = [
                    r.get("url", "") for r in results_list if isinstance(r, dict)
                ][:5]  # Limit to 5 URLs
            
            return results_list, metrics
            
        except Exception as e:
            metrics["error"] = str(e)
            metrics["success"] = False
            print(f"[TRACE] Web search failed: {e}")
            return [], metrics


def trace_prompt_building(
    prompt_builder: Callable,
    *args,
    **kwargs
) -> Tuple[str, Dict[str, Any]]:
    """
    Trace prompt building operation.
    
    Args:
        prompt_builder: Function that builds the prompt
        *args, **kwargs: Arguments to pass to prompt_builder
        
    Returns:
        Tuple of (prompt_string, metrics_dict)
    """
    metrics = {
        "operation": "prompt_building",
        "builder_function": prompt_builder.__name__,
    }
    
    with TimingContext("prompt_building", metrics) as timer:
        try:
            prompt = prompt_builder(*args, **kwargs)
            
            # Update metrics
            metrics.update(timer.get_metrics())
            metrics["prompt_length"] = len(prompt) if isinstance(prompt, str) else 0
            metrics["success"] = True
            
            return prompt, metrics
            
        except Exception as e:
            metrics["error"] = str(e)
            metrics["success"] = False
            raise

