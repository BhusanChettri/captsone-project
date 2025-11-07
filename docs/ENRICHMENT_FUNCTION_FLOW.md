# Enrichment Function Call Flow

This document explains how all the functions in `enrichment.py` are connected and used.

## Function Call Hierarchy

```
enrich_data_node (nodes.py)
    └──> enrich_property_data (enrichment.py)  [MAIN ORCHESTRATOR]
            │
            ├──> build_neighborhood_search_query()
            │       └──> extract_keywords_from_notes()  [HELPER]
            │
            ├──> perform_tavily_search()
            │
            ├──> extract_zip_code()
            │
            ├──> extract_neighborhood()
            │
            ├──> build_landmarks_search_query()
            │
            ├──> perform_tavily_search()
            │
            ├──> extract_landmarks()
            │
            ├──> build_amenities_search_query()  [Called 4 times for each amenity type]
            │
            ├──> perform_tavily_search()  [Called 4 times]
            │
            └──> extract_amenities()  [Called 4 times]
```

## Detailed Function Usage

### 1. **Entry Point: `enrich_data_node`** (in `nodes.py`)
- **Called by**: LangGraph workflow
- **Calls**: `enrich_property_data()`
- **Purpose**: Node that orchestrates enrichment in the workflow

### 2. **Main Orchestrator: `enrich_property_data`** (in `enrichment.py`)
- **Called by**: `enrich_data_node`
- **Calls ALL other functions**:
  - `build_neighborhood_search_query()` - Builds query for neighborhood/ZIP search
  - `build_landmarks_search_query()` - Builds query for landmarks search
  - `build_amenities_search_query()` - Builds query for each amenity type (4 times)
  - `perform_tavily_search()` - Executes web search (6 times total)
  - `extract_zip_code()` - Extracts ZIP from results
  - `extract_neighborhood()` - Extracts neighborhood from results
  - `extract_landmarks()` - Extracts landmarks from results
  - `extract_amenities()` - Extracts amenities from results (4 times)

### 3. **Query Building Functions**

#### `build_neighborhood_search_query()`
- **Called by**: `enrich_property_data()` (line 472)
- **Calls**: `extract_keywords_from_notes()` (line 101)
- **Purpose**: Creates search query for neighborhood/ZIP code

#### `build_landmarks_search_query()`
- **Called by**: `enrich_property_data()` (line 494)
- **Purpose**: Creates search query for landmarks

#### `build_amenities_search_query()`
- **Called by**: `enrich_property_data()` (line 524, inside loop)
- **Called**: 4 times (once per amenity type: schools, parks, shopping, transportation)
- **Purpose**: Creates search query for specific amenity type

### 4. **Helper Function**

#### `extract_keywords_from_notes()`
- **Called by**: `build_neighborhood_search_query()` (line 101)
- **Purpose**: Extracts location/amenity keywords from notes to enhance queries

### 5. **Search Execution**

#### `perform_tavily_search()`
- **Called by**: `enrich_property_data()` 
- **Called**: 6 times total
  - Once for neighborhood search (line 477)
  - Once for landmarks search (line 499)
  - 4 times for amenities (line 530, inside loop)
- **Purpose**: Executes Tavily web search and returns results

### 6. **Result Extraction Functions**

#### `extract_zip_code()`
- **Called by**: `enrich_property_data()` (line 480)
- **Purpose**: Extracts ZIP code from search results using regex

#### `extract_neighborhood()`
- **Called by**: `enrich_property_data()` (line 484)
- **Purpose**: Extracts neighborhood name from search results using regex

#### `extract_landmarks()`
- **Called by**: `enrich_property_data()` (line 502)
- **Purpose**: Extracts landmark names from search results using regex

#### `extract_amenities()`
- **Called by**: `enrich_property_data()` (line 533, inside loop)
- **Called**: 4 times (once per amenity type)
- **Purpose**: Extracts amenity names from search results using regex

## Execution Flow Example

When `enrich_data_node` runs with:
- address: "123 Main St, New York, NY"
- notes: "Beautiful apartment near Central Park"
- listing_type: "rent"

Here's what happens:

1. **Node calls**: `enrich_property_data(address, notes, listing_type, ...)`

2. **Search 1 - Neighborhood**:
   - `build_neighborhood_search_query()` → "123 Main St, New York, NY neighborhood zip code location near"
   - `perform_tavily_search()` → Gets web results
   - `extract_zip_code()` → Extracts "10001"
   - `extract_neighborhood()` → Extracts "Midtown Manhattan"

3. **Search 2 - Landmarks**:
   - `build_landmarks_search_query()` → "123 Main St, New York, NY park nearby"
   - `perform_tavily_search()` → Gets web results
   - `extract_landmarks()` → Extracts ["Central Park", "Times Square"]

4. **Search 3-6 - Amenities** (prioritized for rentals: transportation first):
   - For each amenity type:
     - `build_amenities_search_query()` → Creates query
     - `perform_tavily_search()` → Gets web results
     - `extract_amenities()` → Extracts amenity names

5. **Returns**: Dictionary with all extracted data

## Why This Design?

- **Modularity**: Each function has a single responsibility
- **Testability**: Each function can be tested independently
- **Reusability**: Functions can be reused in different contexts
- **Maintainability**: Easy to modify individual pieces without affecting others

## Functions NOT Directly Called from Outside

These are **internal helper functions** only called by other functions in the same file:
- `extract_keywords_from_notes()` - Only called by `build_neighborhood_search_query()`
- All query builders - Only called by `enrich_property_data()`
- All extractors - Only called by `enrich_property_data()`
- `perform_tavily_search()` - Only called by `enrich_property_data()`

## Public API

The **only public function** that should be called from outside this module is:
- `enrich_property_data()` - This is the main entry point

All other functions are implementation details, though they're exported for testing purposes.

