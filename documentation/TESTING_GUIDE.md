# Testing Guide - Iteration 1

## Overview

This guide explains how to test the Property Listing System end-to-end.

## Files Created

1. **`main.py`** - Main entry point that processes listing requests
2. **`app.py`** - Gradio UI interface
3. **`test_main.py`** - Test script for main function
4. **`test_end_to_end.py`** - End-to-end workflow test

## Testing Methods

### Method 1: Command-Line Testing (main.py)

Test the main processing function directly:

```bash
cd iteration1
source ../.venv/bin/activate
python main.py
```

This will:
- Create a sample listing request
- Execute the full workflow
- Display results

### Method 2: Test Script (test_main.py)

Run multiple test scenarios:

```bash
cd iteration1
source ../.venv/bin/activate
python test_main.py
```

This tests:
- Sale listing with all fields
- Rental listing with all fields
- Minimal input (required fields only)

### Method 3: End-to-End Workflow Test (test_end_to_end.py)

Test the workflow structure:

```bash
cd iteration1
source ../.venv/bin/activate
python test_end_to_end.py
```

This verifies:
- All nodes execute in sequence
- State flows correctly
- Debug output shows execution path

### Method 4: Gradio UI (app.py)

Launch the web interface:

```bash
cd iteration1
source ../.venv/bin/activate
python app.py
```

Then open your browser to: `http://localhost:7860`

## Expected Behavior

### With API Keys Set

If you have `OPENAI_API_KEY` and `TAVILY_API_KEY` set:
- ✅ All nodes execute successfully
- ✅ LLM generates listing content
- ✅ Enrichment data is fetched
- ✅ Final formatted listing is produced

### Without API Keys (Current State)

Expected behavior:
- ✅ Nodes 1-3 execute successfully (input processing)
- ⚠️ Node 4: Enrichment skipped (Tavily API not available)
- ⚠️ Node 5: LLM generation fails (OpenAI API key not set)
- ✅ Nodes 6-7 execute (placeholders with debug output)
- ✅ Workflow completes gracefully with errors logged

## Debug Output

All nodes have debug print statements showing:
- When each node starts
- Key data being processed
- When each node completes
- Any errors encountered

Look for `[DEBUG]` messages in the output.

## Current Status

### ✅ Fully Implemented Nodes
- Node 1: `input_guardrail_node` - Safety checks
- Node 2: `validate_input_node` - Business logic validation
- Node 3: `normalize_text_node` - Text normalization
- Node 4: `enrich_data_node` - Web search enrichment
- Node 5: `generate_content_node` - LLM content generation

### ⏳ Placeholder Nodes (with debug output)
- Node 6: `output_guardrail_node` - Output validation (placeholder)
- Node 7: `format_output_node` - Final formatting (placeholder)

## Next Steps

1. Set API keys (optional for testing structure):
   ```bash
   export OPENAI_API_KEY="your-key-here"
   export TAVILY_API_KEY="your-key-here"
   ```

2. Implement Node 6: `output_guardrail_node`
3. Implement Node 7: `format_output_node`

## Troubleshooting

### Import Errors
- Make sure you're in the `iteration1` directory
- Virtual environment is activated: `source ../.venv/bin/activate`
- Dependencies installed: `pip install -r requirements.txt`

### API Key Errors
- These are expected if keys aren't set
- Workflow will continue with errors logged
- Nodes 6-7 will show "No LLM output" messages

### Workflow Not Executing
- Check that all nodes are registered in `workflow.py`
- Verify entry point is set correctly
- Check debug output to see which node is failing

