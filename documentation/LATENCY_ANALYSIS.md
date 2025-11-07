# Latency Analysis - Property Listing System

## Summary

**Total API Calls per Request:**
- **Tavily Web Search: 6 calls** (sequential)
- **LLM (OpenAI): 1 call**

## Detailed Breakdown

### 1. Tavily Web Search Calls (6 total, sequential)

Located in: `src/utils/enrichment.py` → `enrich_property_data()`

Each call executes via `perform_tavily_search()` → `search_tool.invoke()`:

1. **Search #1: Neighborhood & ZIP Code**
   - Query: Address + "neighborhood zip code location" + notes context
   - Purpose: Extract ZIP code and neighborhood name
   - Estimated latency: **1-3 seconds**

2. **Search #2: Landmarks**
   - Query: Address + "landmarks nearby attractions" + notes context
   - Purpose: Find nearby landmarks (max 5)
   - Estimated latency: **1-3 seconds**

3. **Search #3: Schools**
   - Query: Address + "schools education" + notes context
   - Purpose: Find nearby schools (max 3)
   - Estimated latency: **1-3 seconds**

4. **Search #4: Parks**
   - Query: Address + "parks recreation" + notes context
   - Purpose: Find nearby parks (max 3)
   - Estimated latency: **1-3 seconds**

5. **Search #5: Shopping**
   - Query: Address + "shopping malls stores" + notes context
   - Purpose: Find nearby shopping areas (max 3)
   - Estimated latency: **1-3 seconds**

6. **Search #6: Transportation**
   - Query: Address + "transportation subway bus train" + notes context
   - Purpose: Find nearby transportation options (max 3)
   - Estimated latency: **1-3 seconds**

**Total Tavily Latency: 6-18 seconds** (sequential execution)

### 2. LLM Call (1 total)

Located in: `src/core/nodes.py` → `generate_content_node()`

- **Model**: `gpt-4o-mini` (OpenAI)
- **Purpose**: Generate listing title, description, and price_block
- **Estimated latency**: **2-5 seconds**

### 3. Other Operations (negligible)

- Input guardrails: Rule-based, < 0.1s
- Input validation: Rule-based, < 0.1s
- Text normalization: Rule-based, < 0.1s
- Output guardrails: Rule-based (placeholder), < 0.1s
- Output formatting: Rule-based, < 0.1s

## Bottleneck Analysis

### Primary Bottleneck: **Sequential Tavily API Calls**

**Problem:**
- All 6 Tavily searches execute **sequentially** (one after another)
- Each search waits for the previous one to complete
- Total time = sum of all individual call times

**Current Implementation:**
```python
# In enrich_property_data() - searches execute one by one
neighborhood_results = perform_tavily_search(...)  # Wait ~2s
landmarks_results = perform_tavily_search(...)     # Wait ~2s
amenity_results = perform_tavily_search(...)       # Wait ~2s (x4)
```

**Impact:**
- If each Tavily call takes 2 seconds: **6 × 2s = 12 seconds**
- If each Tavily call takes 3 seconds: **6 × 3s = 18 seconds**

### Secondary Bottleneck: **LLM Call**

- Single LLM call adds **2-5 seconds**
- Less significant than Tavily, but still contributes

## Total Estimated Latency

**Best Case:**
- Tavily (6 calls × 1s): 6 seconds
- LLM: 2 seconds
- Other: 0.5 seconds
- **Total: ~8.5 seconds**

**Typical Case:**
- Tavily (6 calls × 2s): 12 seconds
- LLM: 3 seconds
- Other: 0.5 seconds
- **Total: ~15.5 seconds**

**Worst Case:**
- Tavily (6 calls × 3s): 18 seconds
- LLM: 5 seconds
- Other: 0.5 seconds
- **Total: ~23.5 seconds**

## Optimization Opportunities

### 1. **Parallelize Tavily Calls** (High Impact)

**Current:** Sequential execution (6 calls × 2s = 12s)
**Optimized:** Parallel execution (max(6 calls) = 2s)

**Implementation:**
- Use `asyncio` or `concurrent.futures.ThreadPoolExecutor`
- Execute all 6 Tavily searches in parallel
- **Expected improvement: ~10 seconds reduction**

### 2. **Reduce Number of Tavily Calls** (Medium Impact)

**Options:**
- Combine searches (e.g., single search for "neighborhood landmarks amenities")
- Use Tavily's `include_answer=True` to get AI summaries (already enabled)
- Cache results for common addresses
- Make enrichment optional/async (show listing first, enrich later)

**Expected improvement: 3-6 seconds reduction** (if reducing to 2-3 calls)

### 3. **Optimize LLM Call** (Low Impact)

**Options:**
- Use faster model (already using `gpt-4o-mini` - fastest)
- Reduce prompt size (minimal impact)
- Stream response (improves perceived latency, not actual)

**Expected improvement: 0.5-1 second reduction**

### 4. **Caching** (High Impact for Repeated Queries)

**Options:**
- Cache enrichment results by address
- Cache LLM responses for identical inputs
- Use Redis or in-memory cache

**Expected improvement: Near-instant for cached queries**

## Recommended Next Steps

1. **Immediate (High Impact, Low Effort):**
   - Parallelize Tavily calls using `concurrent.futures`
   - **Expected: ~10 seconds reduction**

2. **Short-term (Medium Impact, Medium Effort):**
   - Reduce Tavily calls from 6 to 2-3 by combining queries
   - **Expected: 3-6 seconds reduction**

3. **Long-term (High Impact, High Effort):**
   - Implement caching for enrichment results
   - Make enrichment async (show listing first, update with enrichment)
   - **Expected: Near-instant for cached, better UX for new**

## Code Locations

- **Tavily calls**: `src/utils/enrichment.py` → `enrich_property_data()` (lines 429-558)
- **LLM call**: `src/core/nodes.py` → `generate_content_node()` (lines 300-397)
- **Workflow**: `src/core/workflow.py` → `create_workflow()`

