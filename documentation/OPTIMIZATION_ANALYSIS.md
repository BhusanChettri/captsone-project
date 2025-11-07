# Optimization Analysis - Web Search Calls

## Current State Analysis

### Current Web Searches (6 total):
1. **Neighborhood & ZIP Code** - Essential for location context
2. **Landmarks** - Nice-to-have, can be mentioned in user notes
3. **Schools** - Important for families (especially sales)
4. **Parks** - Nice-to-have, less critical
5. **Shopping** - Nice-to-have, less critical
6. **Transportation** - Important for rentals

### Current Configuration:
- `max_results=3` per search (Tavily returns up to 3 results per call)
- All searches execute **sequentially**
- Each search takes ~1-3 seconds

## Critical Analysis: What's Truly Essential?

### Essential (Must Have):
1. **ZIP Code & Neighborhood** ✅
   - **Why**: Provides location context, helps LLM understand area demographics
   - **Impact**: High - directly used in prompt for location context
   - **Keep**: YES

2. **Key Amenities (Combined)** ✅
   - **Why**: Schools and transportation are the most important amenities
   - **Impact**: Medium-High - helps LLM write better descriptions
   - **Keep**: YES, but combine into 1-2 searches

### Nice-to-Have (Can Reduce):
3. **Landmarks** ⚠️
   - **Why**: User notes often mention landmarks, web search is redundant
   - **Impact**: Low - rarely critical for listing quality
   - **Keep**: NO (or make optional)

4. **Parks** ⚠️
   - **Why**: Less critical than schools/transportation
   - **Impact**: Low - nice but not essential
   - **Keep**: NO (or combine with other amenities)

5. **Shopping** ⚠️
   - **Why**: Less critical than schools/transportation
   - **Impact**: Low - nice but not essential
   - **Keep**: NO (or combine with other amenities)

## Optimization Strategy

### Option 1: Minimal Essential (2 searches) - RECOMMENDED
**Searches:**
1. **Location Context**: ZIP code + Neighborhood
2. **Key Amenities**: Schools + Transportation (combined, prioritized by listing_type)

**Benefits:**
- Reduces from 6 to 2 searches = **~67% reduction**
- Latency: 2-6 seconds (vs 6-18 seconds)
- Still captures most important context
- Good balance of speed vs. quality

**Implementation:**
- Search 1: `"{address} neighborhood zip code location"`
- Search 2: `"{address} schools transportation"` (for rentals) or `"{address} schools parks"` (for sales)

### Option 2: Balanced (3 searches)
**Searches:**
1. **Location Context**: ZIP code + Neighborhood
2. **Primary Amenities**: Schools (for sales) or Transportation (for rentals)
3. **Secondary Amenities**: Parks + Shopping (combined)

**Benefits:**
- Reduces from 6 to 3 searches = **50% reduction**
- Latency: 3-9 seconds (vs 6-18 seconds)
- More comprehensive than Option 1

### Option 3: Smart Prioritized (2-3 searches based on listing_type)
**For Rentals:**
1. Location (ZIP + Neighborhood)
2. Transportation + Schools (combined)

**For Sales:**
1. Location (ZIP + Neighborhood)
2. Schools + Parks (combined)

**Benefits:**
- Context-aware optimization
- 2 searches per request
- Prioritizes what matters most for each listing type

## Reducing max_results

### Current: `max_results=3`
- Each search returns up to 3 results
- We extract 1-3 items from each result set

### Optimized: `max_results=2`
- Each search returns up to 2 results
- Still sufficient for extraction (we only need 1-3 items anyway)
- **Potential latency reduction: ~10-20% per search**

### Recommendation:
- Use `max_results=2` for location search (we only need 1 ZIP code, 1 neighborhood)
- Use `max_results=2` for amenities search (we only need 2-3 items per category)

## Combined Optimization Impact

### Current:
- 6 searches × 2 seconds = **12 seconds**
- `max_results=3` (more data than needed)

### Optimized (Option 1 + max_results=2):
- 2 searches × 1.5 seconds = **3 seconds** (parallel) or **3 seconds** (sequential)
- `max_results=2` (sufficient data)
- **Total reduction: ~75% latency improvement**

### With Parallelization:
- 2 searches in parallel = **1.5-2 seconds** (max of both)
- **Total reduction: ~85% latency improvement**

## Future Considerations (Prediction Model)

When adding a prediction model later, we'll need:
- **Historical data**: Price trends, market data
- **Comparable properties**: Similar listings in area
- **Market indicators**: Demand, inventory levels

**Current enrichment is NOT sufficient for prediction model.**

**Recommendation:**
- Keep current enrichment minimal (2 searches) for listing generation
- Add separate, targeted searches for prediction model when needed
- Don't over-optimize enrichment now for future prediction needs

## Recommended Implementation Plan

### Phase 1: Reduce Searches (Immediate)
1. **Reduce to 2 essential searches:**
   - Search 1: Location (ZIP + Neighborhood)
   - Search 2: Key Amenities (Schools + Transportation, prioritized by listing_type)

2. **Reduce max_results to 2:**
   - Sufficient for extraction needs
   - Faster API response

**Expected improvement: ~67% latency reduction (6-18s → 2-6s)**

### Phase 2: Parallelize (Next)
1. Execute 2 searches in parallel
2. Use `concurrent.futures.ThreadPoolExecutor`

**Expected improvement: Additional ~50% reduction (2-6s → 1-3s)**

### Phase 3: Caching (Future)
1. Cache enrichment results by address
2. Cache for 24-48 hours (location data doesn't change frequently)

**Expected improvement: Near-instant for repeated addresses**

## Code Changes Required

1. **`src/utils/enrichment.py`:**
   - Modify `enrich_property_data()` to make 2 searches instead of 6
   - Combine amenities into single search
   - Reduce `max_results` to 2

2. **`src/core/nodes.py`:**
   - Update `enrich_data_node()` to use `max_results=2` in TavilySearch

3. **Parallelization:**
   - Add `concurrent.futures` import
   - Execute searches in parallel using `ThreadPoolExecutor`

