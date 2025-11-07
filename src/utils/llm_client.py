"""
LLM Client Utilities for Property Listing System - Iteration 1

This module provides LLM client initialization and interaction utilities.
Uses LangChain for LLM integration.

Observability:
- Integrated with Opik tracing for LLM call tracking
- Tracks time-to-first-token (TTFT) and total generation time
"""

import json
from typing import Optional, Dict, Any, Tuple
from langchain_core.output_parsers import StrOutputParser
from utils.tracing import trace_llm_call, set_trace_metadata


def initialize_llm(model_name: str = "gpt-4o-mini", model_provider: str = "openai", **kwargs):
    """
    Initialize LLM client using LangChain.
    
    Args:
        model_name: Name of the model to use (e.g., "gpt-4o-mini", "gpt-4")
        model_provider: Provider name (e.g., "openai", "anthropic")
        **kwargs: Additional arguments to pass to init_chat_model
        
    Returns:
        Initialized LLM instance
        
    Raises:
        ImportError: If langchain.chat_models is not available
        Exception: If LLM initialization fails
    """
    try:
        from langchain.chat_models import init_chat_model
    except ImportError:
        try:
            # Try alternative import path for newer LangChain versions
            from langchain_core.language_models import init_chat_model
        except ImportError:
            raise ImportError(
                "LangChain chat models not available. "
                "Please install langchain: pip install langchain"
            )
    
    try:
        llm = init_chat_model(model_name, model_provider=model_provider, **kwargs)
        return llm
    except Exception as e:
        raise Exception(f"Failed to initialize LLM: {str(e)}")


def call_llm_with_prompt(
    llm: Any, 
    prompt: str, 
    temperature: float = 0.7,
    model_name: Optional[str] = None
) -> str:
    """
    Call LLM with a prompt and return the response.
    
    This function converts the string prompt to a message format that
    LangChain chat models expect, then invokes the LLM with tracing.
    
    Args:
        llm: Initialized LLM instance (chat model)
        prompt: Prompt string to send to LLM
        temperature: Temperature setting for LLM (0.0-1.0)
        model_name: Model name for tracing metadata (optional)
        
    Returns:
        LLM response as string
        
    Raises:
        Exception: If LLM call fails
    """
    try:
        # Get model name from LLM if not provided
        if not model_name:
            if hasattr(llm, 'model_name'):
                model_name = llm.model_name
            elif hasattr(llm, 'model'):
                model_name = str(llm.model)
            else:
                model_name = "unknown"
        
        # Use tracing wrapper to track TTFT and total generation time
        response, metrics = trace_llm_call(
            llm=llm,
            prompt=prompt,
            temperature=temperature,
            model_name=model_name
        )
        
        # Store LLM metrics in trace metadata
        set_trace_metadata("llm_metrics", metrics)
        if metrics.get("ttft"):
            set_trace_metadata("llm_ttft", metrics["ttft"])
        if metrics.get("duration"):
            set_trace_metadata("llm_total_time", metrics["duration"])
        
        return response
            
    except Exception as e:
        # Store error in trace metadata
        set_trace_metadata("llm_error", str(e))
        raise Exception(f"LLM call failed: {str(e)}")


def parse_json_response(response: str) -> Dict[str, Any]:
    """
    Parse JSON response from LLM.
    
    Handles cases where LLM might return:
    - Plain JSON: {"title": "...", "description": "...", "price_block": "..."}
    - JSON wrapped in markdown code blocks: ```json {...} ```
    - JSON with extra text before/after
    
    Args:
        response: Raw response string from LLM
        
    Returns:
        Parsed JSON dictionary with keys: title, description, price_block
        
    Raises:
        ValueError: If JSON cannot be parsed or required keys are missing
    """
    if not response or not response.strip():
        raise ValueError("Empty response from LLM")
    
    # Clean the response
    cleaned_response = response.strip()
    
    # Remove markdown code blocks if present
    if cleaned_response.startswith("```"):
        # Extract content between ```json and ```
        lines = cleaned_response.split("\n")
        # Find start and end of code block
        start_idx = None
        end_idx = None
        for i, line in enumerate(lines):
            if line.strip().startswith("```"):
                if start_idx is None:
                    start_idx = i + 1
                else:
                    end_idx = i
                    break
        if start_idx is not None and end_idx is not None:
            cleaned_response = "\n".join(lines[start_idx:end_idx])
        elif start_idx is not None:
            # No closing ```, take everything after opening
            cleaned_response = "\n".join(lines[start_idx:])
    
    # Try to find JSON object in the response
    # Look for { ... } pattern
    start_brace = cleaned_response.find("{")
    end_brace = cleaned_response.rfind("}")
    
    if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
        json_str = cleaned_response[start_brace:end_brace + 1]
    else:
        json_str = cleaned_response
    
    # Parse JSON
    try:
        parsed = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from LLM response: {str(e)}")
    
    # Validate required keys
    required_keys = ["title", "description", "price_block"]
    missing_keys = [key for key in required_keys if key not in parsed]
    if missing_keys:
        raise ValueError(f"Missing required keys in LLM response: {missing_keys}")
    
    # Validate that values are strings and not empty
    for key in required_keys:
        if not isinstance(parsed[key], str) or not parsed[key].strip():
            raise ValueError(f"Invalid value for '{key}': must be non-empty string")
    
    return parsed

