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
import os
from typing import Optional, Dict, Any, Callable, Tuple
from functools import wraps
import uuid


# Global tracer instance (initialized in workflow.py)
_tracer: Optional[Any] = None
_trace_metadata: Dict[str, Any] = {}


def get_opik_config() -> Tuple[bool, Optional[str]]:
    """
    Get Opik configuration from environment variables.
    
    Environment variables:
    - OPIK_USE_LOCAL: Set to "true" or "1" to use local mode, "false" or "0" for cloud (default: cloud)
    - OPIK_URL: URL for local Opik server (only used when OPIK_USE_LOCAL=true, default: http://localhost:5173/api/)
    - COMET_API_KEY: Required for cloud mode (Opik will prompt if not set)
    
    Returns:
        Tuple of (use_local: bool, url: Optional[str])
        - use_local: True for local mode, False for cloud mode
        - url: Local Opik URL if use_local=True, None otherwise
        
    Example:
        To use local mode, set in .env:
            OPIK_USE_LOCAL=true
            OPIK_URL=http://localhost:5173/api/
        
        To use cloud mode (default), set in .env:
            OPIK_USE_LOCAL=false
            COMET_API_KEY=your-api-key-here
    """
    # Load .env file if available
    try:
        from utils.env_loader import load_iteration1_env
        load_iteration1_env()
    except ImportError:
        pass  # env_loader not available, continue with system env vars
    
    # Get OPIK_USE_LOCAL from environment (default to False/cloud mode)
    use_local_str = os.getenv("OPIK_USE_LOCAL", "false").strip().lower()
    use_local = use_local_str in ("true", "1", "yes", "on")
    
    # Get OPIK_URL for local mode (only used if use_local=True)
    url = None
    if use_local:
        url = os.getenv("OPIK_URL", "http://localhost:5173/api/").strip()
        if not url:
            url = "http://localhost:5173/api/"
    
    return use_local, url


def _normalize_local_opik_url(url: Optional[str]) -> str:
    """
    Ensure the provided URL points to the Opik REST API root.
    
    Opik's API expects the base URL to include the `/api/` prefix.
    Users commonly provide `http://localhost:5173`, which results in 404s
    when the SDK attempts to call `/v1/...` endpoints. This helper makes sure
    the suffix is present and that the URL always ends with a trailing slash.
    """
    default_base = "http://localhost:5173/api/"
    if not url:
        return default_base
    
    normalized = url.strip()
    if not normalized:
        return default_base
    
    # Guarantee trailing slash
    if not normalized.endswith("/"):
        normalized += "/"
    
    # Ensure `/api/` suffix is present (before trailing slash)
    if not normalized.rstrip("/").endswith("/api"):
        normalized = normalized.rstrip("/") + "/api/"
    else:
        # Already ends with /api or /api/, normalize to /api/
        normalized = normalized.rstrip("/") + "/"
    
    return normalized


def initialize_tracer(
    graph: Any,
    project_name: str = "property-listing-system",
    use_local: bool = True,
    url: Optional[str] = None
) -> Any:
    """
    Initialize Opik tracer for LangGraph workflow.
    
    Args:
        graph: The compiled LangGraph workflow (use graph.get_graph(xray=True))
        project_name: Name of the project for Opik dashboard
        use_local: Whether to use local Opik server (default: True)
                   Set to False to use Opik Cloud (requires API key)
        url: URL of the local Opik instance (optional, defaults to http://localhost:5173/api/)
             Only used when use_local=True
             Make sure you are running the Opik local server (see https://www.comet.com/docs/opik/)
             so that the API is reachable at the URL provided here.
        
    Returns:
        OpikTracer instance
    """
    try:
        # For local mode, just set the environment variable - no need to call configure()
        # OpikTracer will automatically pick up OPIK_URL_OVERRIDE
        if use_local:
            normalized_url = _normalize_local_opik_url(url)
            os.environ["OPIK_URL_OVERRIDE"] = normalized_url
            print(f"[TRACE] Opik configured for LOCAL mode: api_root={normalized_url}")
            print(f"[TRACE] ⚠️  Start the Opik local server (see Opik docs) so the API is reachable.")
            print(f"[TRACE]    Expected health check: {normalized_url}is-alive/ping")
            print(f"[TRACE]    UI will be served at {normalized_url.replace('/api/', '/')}")
            url = normalized_url
        
        # Import after setting environment variables
        import opik
        from opik.integrations.langchain import OpikTracer
        
        # Only configure for cloud mode (local mode uses environment variable)
        if not use_local:
            # Cloud mode - remove local URL override if it exists
            if "OPIK_URL_OVERRIDE" in os.environ:
                del os.environ["OPIK_URL_OVERRIDE"]
            
            # Configure Opik for cloud mode
            # Opik will use COMET_API_KEY from environment if available
            # Otherwise, it will prompt for API key or use automatic approvals
            try:
                opik.configure(use_local=False, automatic_approvals=True)
                api_key = os.environ.get("COMET_API_KEY", "Not set (will prompt if needed)")
                print(f"[TRACE] Opik configured for CLOUD mode")
                print(f"[TRACE] COMET_API_KEY: {'Set' if api_key != 'Not set (will prompt if needed)' else 'Not set - Opik will prompt for API key'}")
                print(f"[TRACE] View traces at: https://www.comet.com/opik")
            except Exception as e:
                print(f"[TRACE] Warning: Could not configure Opik cloud mode: {e}")
                print(f"[TRACE] Make sure COMET_API_KEY is set in your environment")
        
        # Initialize OpikTracer with the graph
        # Note: graph is already the result of compiled_workflow.get_graph(xray=True)
        # Opik will handle connection errors gracefully - traces will be queued
        tracer = OpikTracer(
            graph=graph,
            project_name=project_name
        )
        
        # Note: Connection errors are expected if proxy server isn't running
        # Opik will retry sending traces when the server becomes available
        return tracer

    except ImportError:
        print("[WARNING] Opik not installed. Tracing will be disabled.")
        return None
    except Exception as e:
        print(f"[WARNING] Failed to initialize Opik tracer: {e}")
        print("[WARNING] Tracing will be disabled.")
        print("[WARNING] Note: Connection errors are normal if Opik proxy server isn't running.")
        print("[WARNING] Ensure the Opik local server is running and reachable at the configured URL.")
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
