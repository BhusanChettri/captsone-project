# Web Search Execution Flow

This document shows exactly how and when web searches are executed.

## Web Search Execution Points

The `enrich_property_data()` function executes **6 web searches** total:

### Search 1: Neighborhood & ZIP Code
```python
# Line 472-477
neighborhood_query = build_neighborhood_search_query(...)
neighborhood_results = perform_tavily_search(neighborhood_query, search_tool)
                                                      ↑
                                                      └──> ACTUAL WEB SEARCH HAPPENS HERE
```

**Query Example**: `"123 Main St, New York, NY neighborhood zip code location near"`

### Search 2: Landmarks
```python
# Line 494-499
landmarks_query = build_landmarks_search_query(...)
landmarks_results = perform_tavily_search(landmarks_query, search_tool)
                                                      ↑
                                                      └──> ACTUAL WEB SEARCH HAPPENS HERE
```

**Query Example**: `"123 Main St, New York, NY park nearby"`

### Searches 3-6: Amenities (4 separate searches)
```python
# Line 522-530 (inside loop)
for amenity_type in ["transportation", "schools", "parks", "shopping"]:
    amenity_query = build_amenities_search_query(...)
    amenity_results = perform_tavily_search(amenity_query, search_tool)
                                                      ↑
                                                      └──> ACTUAL WEB SEARCH HAPPENS HERE (4 times)
```

**Query Examples**:
- `"123 Main St, New York, NY subway metro bus transportation public transit nearby public transit access"`
- `"123 Main St, New York, NY schools education nearby school district ratings"`
- `"123 Main St, New York, NY parks recreation nearby"`
- `"123 Main St, New York, NY shopping malls stores nearby"`

## How `perform_tavily_search()` Works

```python
def perform_tavily_search(query: str, search_tool: Any, max_results: int = 3):
    # Line 400: THIS IS WHERE THE ACTUAL WEB SEARCH HAPPENS
    results = search_tool.invoke({"query": query})
    #                    ↑
    #                    └──> Calls Tavily API to search the web
    
    # Process and return results
    if isinstance(results, dict) and "results" in results:
        return results["results"][:max_results]
    return []
```

## Complete Execution Flow

```
enrich_property_data()
    │
    ├─→ [1] build_neighborhood_search_query()
    │       └─→ Returns: "123 Main St neighborhood zip code location"
    │
    ├─→ [2] perform_tavily_search(query="123 Main St...", search_tool)
    │       └─→ search_tool.invoke({"query": "123 Main St..."})  ← WEB SEARCH #1
    │       └─→ Returns: [{"content": "...", "title": "..."}, ...]
    │
    ├─→ [3] extract_zip_code(results)
    │       └─→ Extracts: "10001"
    │
    ├─→ [4] extract_neighborhood(results)
    │       └─→ Extracts: "Midtown Manhattan"
    │
    ├─→ [5] build_landmarks_search_query()
    │       └─→ Returns: "123 Main St park nearby"
    │
    ├─→ [6] perform_tavily_search(query="123 Main St park...", search_tool)
    │       └─→ search_tool.invoke({"query": "123 Main St park..."})  ← WEB SEARCH #2
    │       └─→ Returns: [{"content": "...", "title": "..."}, ...]
    │
    ├─→ [7] extract_landmarks(results)
    │       └─→ Extracts: ["Central Park", "Times Square"]
    │
    └─→ [8-19] For each amenity type (4 iterations):
            │
            ├─→ build_amenities_search_query()
            │       └─→ Returns: "123 Main St schools education..."
            │
            ├─→ perform_tavily_search(query="123 Main St schools...", search_tool)
            │       └─→ search_tool.invoke({"query": "123 Main St schools..."})  ← WEB SEARCH #3, #4, #5, #6
            │       └─→ Returns: [{"content": "...", "title": "..."}, ...]
            │
            └─→ extract_amenities(results)
                    └─→ Extracts: ["PS 123", "High School XYZ"]
```

## Verification: All 6 Web Searches Happen

✅ **Search 1**: Line 477 - Neighborhood/ZIP search  
✅ **Search 2**: Line 499 - Landmarks search  
✅ **Search 3**: Line 530 (loop iteration 1) - Transportation search  
✅ **Search 4**: Line 530 (loop iteration 2) - Schools search  
✅ **Search 5**: Line 530 (loop iteration 3) - Parks search  
✅ **Search 6**: Line 530 (loop iteration 4) - Shopping search  

## What Happens in Each Web Search

1. **Query is built** using context (address, notes, listing_type)
2. **`perform_tavily_search()` is called** with the query
3. **`search_tool.invoke({"query": query})` executes** - This makes the actual HTTP request to Tavily API
4. **Tavily searches the web** and returns results
5. **Results are processed** and data is extracted using regex patterns
6. **Extracted data is stored** in the enrichment_data dictionary

## Important Notes

- Each search is **independent** - if one fails, others continue
- Each search uses **different queries** based on context
- All searches happen **sequentially** (one after another)
- Each search can return up to **3 results** (max_results=3)
- The `search_tool` is a **TavilySearch** instance that makes real web API calls

## Testing Web Search Execution

To verify web searches are happening, you can:

1. **Add logging** to see queries being executed
2. **Check Tavily API logs** (if you have access)
3. **Mock the search_tool** in tests to verify it's called 6 times
4. **Add print statements** to see each query before execution

