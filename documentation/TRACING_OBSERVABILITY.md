# Tracing and Observability with Opik

This document describes the tracing and observability implementation for the Property Listing System using Opik.

## Overview

The system is now instrumented with comprehensive tracing that tracks the entire journey from query to response. All critical operations are traced, including:

- **Web search calls** (Tavily API)
- **LLM calls** (OpenAI)
- **Context preparation** (prompt building)
- **Time to first token (TTFT)** for LLM responses
- **Total response generation time**
- **Node execution times** (all 7 workflow nodes)

## Architecture

### Components

1. **Tracing Utilities** (`src/utils/tracing.py`)
   - Core tracing infrastructure
   - Timing context managers
   - Opik tracer initialization
   - Custom metrics tracking

2. **Workflow Integration** (`src/core/workflow.py`)
   - OpikTracer initialization
   - Tracer attachment to workflow execution

3. **LLM Client** (`src/utils/llm_client.py`)
   - LLM call tracing with TTFT tracking
   - Streaming support for real-time TTFT measurement

4. **Enrichment Module** (`src/utils/enrichment.py`)
   - Web search call tracing
   - Search result tracking

5. **Node Functions** (`src/core/nodes.py`)
   - Prompt building tracing
   - Context preparation metrics

6. **Main Entry Point** (`main.py`)
   - Workflow execution with tracer callbacks
   - Total execution time tracking
   - Trace metadata collection

## Installation

Add Opik to your dependencies:

```bash
pip install opik>=0.1.0
```

Or install from requirements:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Tracing is enabled by default when creating the workflow:

```python
from core import create_workflow

# Create workflow with tracing enabled (default)
workflow, tracer = create_workflow(enable_tracing=True)

# Execute workflow with tracer callback
config = {
    "configurable": {"thread_id": "unique_thread_id"},
    "callbacks": [tracer] if tracer else []
}

result = workflow.invoke(initial_state, config=config)
```

### Accessing Trace Metadata

Trace metadata is automatically collected and included in the response:

```python
result = process_listing_request(...)

# Access trace metadata
trace_metadata = result.get("trace_metadata", {})
print(f"Total execution time: {trace_metadata.get('total_execution_time')}")
print(f"LLM TTFT: {trace_metadata.get('llm_ttft')}")
print(f"LLM total time: {trace_metadata.get('llm_total_time')}")
print(f"Web searches: {trace_metadata.get('web_searches', [])}")
```

## Metrics Tracked

### 1. Workflow-Level Metrics

- **total_execution_time**: Total time from start to finish
- **workflow_completed**: Boolean indicating success/failure
- **request_id**: Unique identifier for the request
- **address**, **listing_type**, **price**: Request metadata

### 2. LLM Metrics

- **llm_ttft**: Time to first token (seconds)
- **llm_total_time**: Total LLM generation time (seconds)
- **llm_metrics**: Complete LLM call metrics including:
  - Model name
  - Temperature
  - Prompt length
  - Response length
  - Duration
  - TTFT (if streaming)

### 3. Web Search Metrics

- **web_searches**: List of all web search operations with:
  - Query string
  - Execution time
  - Result count
  - Success/failure status
  - URLs returned

### 4. Prompt Building Metrics

- **prompt_building_metrics**: Metrics for prompt construction:
  - Builder function name
  - Execution time
  - Prompt length
  - Success/failure status

### 5. Node Execution Metrics

All node executions are automatically traced by Opik:
- input_guardrail_node
- validate_input_node
- normalize_text_node
- enrich_data_node
- generate_content_node
- output_guardrail_node
- format_output_node

## Opik Dashboard

When Opik is properly configured, traces are automatically sent to the Opik dashboard where you can:

1. **Visualize the workflow graph** - See all nodes and their execution flow
2. **View execution times** - Identify bottlenecks
3. **Monitor LLM performance** - Track TTFT and total generation time
4. **Debug web searches** - See queries, results, and timing
5. **Analyze errors** - Track failures and exceptions

### Opik Configuration

Opik can be configured via environment variables or configuration files. Refer to the [Opik documentation](https://www.comet.com/docs/opik/) for setup instructions.

## Example Trace Output

When tracing is enabled, you'll see console output like:

```
[TRACE] Opik tracer initialized successfully
[TRACE] Opik tracer attached to workflow execution
[TRACE] prompt_building: 0.012s
[TRACE] llm_call - TTFT: 0.543s
[TRACE] llm_call: 2.145s
[TRACE] web_search: 1.234s
[TRACE] Total execution time: 4.567s
```

## Custom Metrics

You can add custom metrics using the tracing utilities:

```python
from utils.tracing import set_trace_metadata, TimingContext

# Add custom metadata
set_trace_metadata("custom_key", "custom_value")

# Time a custom operation
with TimingContext("my_operation", {"param": "value"}) as timer:
    # Your code here
    result = do_something()
    
    # Mark first token if applicable
    timer.mark_first_token()
    
# Access metrics
metrics = timer.get_metrics()
```

## Error Handling

Tracing gracefully handles errors:

- If Opik is not installed, tracing is disabled with a warning
- If tracer initialization fails, the workflow continues without tracing
- Individual operation failures are logged in trace metadata
- Errors don't break the workflow execution

## Performance Impact

Tracing has minimal performance impact:

- **Overhead**: < 1% for most operations
- **Memory**: Trace metadata is lightweight
- **Network**: Only if using Opik Cloud (can be disabled for local development)

## Disabling Tracing

To disable tracing:

```python
# Disable during workflow creation
workflow, tracer = create_workflow(enable_tracing=False)

# Or set environment variable
import os
os.environ["OPIK_DISABLED"] = "true"
```

## Troubleshooting

### Opik Not Installed

If you see:
```
[WARNING] Opik not installed. Tracing will be disabled.
```

Install Opik:
```bash
pip install opik
```

### Tracer Initialization Fails

If tracer initialization fails, the workflow continues without tracing. Check:
1. Opik is installed correctly
2. Opik configuration is valid
3. Network connectivity (if using Opik Cloud)

### Missing Metrics

If metrics are missing:
1. Check that tracing is enabled
2. Verify the operation is using tracing utilities
3. Check console output for trace logs

## Future Enhancements

Potential improvements:

1. **Distributed Tracing**: Support for multi-service architectures
2. **Custom Dashboards**: Build custom visualization dashboards
3. **Alerting**: Set up alerts for performance degradation
4. **Cost Tracking**: Track API costs per request
5. **A/B Testing**: Compare different prompt strategies

## References

- [Opik Documentation](https://www.comet.com/docs/opik/)
- [LangGraph Observability](https://langchain-ai.github.io/langgraph/how-tos/observability/)
- [LangChain Tracing](https://python.langchain.com/docs/observability/)

