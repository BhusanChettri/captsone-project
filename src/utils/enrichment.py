"""
Web Search Enrichment Utilities for Property Listing System - Iteration 1

This module provides intelligent web search enrichment using Tavily API.
It performs targeted searches to extract:
- ZIP code
- Neighborhood name
- Nearby landmarks
- Key amenities (schools, parks, shopping, transportation)

The enrichment uses multiple targeted searches to avoid ambiguous results
and extract structured information.
"""

import re
from typing import Optional, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# Tavily import - may not be available in test environment
try:
    from langchain_tavily import TavilySearch
except ImportError:
    # For testing or when Tavily is not installed
    TavilySearch = None


# ============================================================================
# Search Query Construction
# ============================================================================

def extract_keywords_from_notes(notes: str) -> List[str]:
    """
    Extract relevant location/amenity keywords from notes.
    
    Looks for mentions of neighborhoods, landmarks, amenities, etc.
    that can enhance search queries.
    
    Args:
        notes: Normalized notes text
        
    Returns:
        List of extracted keywords
    """
    if not notes:
        return []
    
    keywords = []
    notes_lower = notes.lower()
    
    # Common location/amenity keywords
    location_keywords = [
        "near", "close to", "walking distance", "minutes from",
        "downtown", "uptown", "midtown", "suburb", "neighborhood"
    ]
    
    amenity_keywords = [
        "park", "school", "mall", "shopping", "restaurant", "cafe",
        "subway", "metro", "bus", "train", "station", "transportation",
        "beach", "lake", "river", "museum", "theater", "hospital"
    ]
    
    # Check for location keywords
    for keyword in location_keywords:
        if keyword in notes_lower:
            keywords.append(keyword)
    
    # Check for amenity keywords
    for keyword in amenity_keywords:
        if keyword in notes_lower:
            keywords.append(keyword)
    
    return keywords


def build_neighborhood_search_query(
    address: str,
    notes: str = "",
    listing_type: Optional[str] = None
) -> str:
    """
    Build search query for neighborhood and ZIP code information.
    
    Intelligently combines address with context from notes and listing type
    to create a more targeted search query.
    
    Args:
        address: Property address
        notes: Normalized notes (optional, for context)
        listing_type: "sale" or "rent" (optional, for context)
        
    Returns:
        Search query string
    """
    # Start with address
    query_parts = [address]
    
    # Add neighborhood/location keywords
    query_parts.append("neighborhood zip code location")
    
    # If notes mention a specific area/neighborhood, include it
    if notes:
        keywords = extract_keywords_from_notes(notes)
        location_keywords = [k for k in keywords if k in ["near", "close to", "downtown", "uptown", "midtown", "neighborhood"]]
        if location_keywords:
            query_parts.extend(location_keywords[:2])  # Add top 2 location keywords
    
    query = " ".join(query_parts)
    return query.strip()


def build_landmarks_search_query(
    address: str,
    notes: str = "",
    listing_type: Optional[str] = None
) -> str:
    """
    Build search query for nearby landmarks.
    
    Uses address and notes to find relevant landmarks and attractions.
    
    Args:
        address: Property address
        notes: Normalized notes (optional, may mention specific landmarks)
        listing_type: "sale" or "rent" (optional, for context)
        
    Returns:
        Search query string
    """
    query_parts = [address]
    
    # If notes mention specific landmarks, prioritize those
    if notes:
        notes_lower = notes.lower()
        landmark_mentions = []
        common_landmarks = ["park", "museum", "theater", "stadium", "plaza", "square", "bridge"]
        for landmark in common_landmarks:
            if landmark in notes_lower:
                landmark_mentions.append(landmark)
        
        if landmark_mentions:
            query_parts.extend(landmark_mentions[:2])  # Add mentioned landmarks
            query_parts.append("nearby")
        else:
            query_parts.append("nearby landmarks attractions points of interest")
    else:
        query_parts.append("nearby landmarks attractions points of interest")
    
    query = " ".join(query_parts)
    return query.strip()


def build_amenities_search_query(
    address: str,
    amenity_type: str,
    notes: str = "",
    listing_type: Optional[str] = None
) -> str:
    """
    Build search query for specific amenity type.
    
    Intelligently constructs query based on address, notes, and listing type.
    For rentals, transportation might be more important. For sales, schools might be prioritized.
    
    Args:
        address: Property address
        amenity_type: Type of amenity ("schools", "parks", "shopping", "transportation")
        notes: Normalized notes (optional, may mention specific amenities)
        listing_type: "sale" or "rent" (optional, affects query focus)
        
    Returns:
        Search query string
    """
    query_parts = [address]
    
    amenity_keywords = {
        "schools": "schools education",
        "parks": "parks recreation",
        "shopping": "shopping malls stores",
        "transportation": "subway metro bus transportation public transit"
    }
    
    keywords = amenity_keywords.get(amenity_type, amenity_type)
    query_parts.append(keywords)
    
    # If notes mention this amenity type, add context
    if notes:
        notes_lower = notes.lower()
        if amenity_type in notes_lower or keywords.split()[0] in notes_lower:
            query_parts.append("nearby")
    
    # Add listing-type specific context
    if listing_type == "rent":
        if amenity_type == "transportation":
            query_parts.append("public transit access")
    elif listing_type == "sale":
        if amenity_type == "schools":
            query_parts.append("school district ratings")
    
    query = " ".join(query_parts)
    return query.strip()


def build_combined_amenities_search_query(
    address: str,
    notes: str = "",
    listing_type: Optional[str] = None
) -> str:
    """
    Build combined search query for key amenities (schools + transportation).
    
    This is an optimized query that combines the most important amenities
    into a single search to reduce API calls and latency.
    
    Prioritizes based on listing_type:
    - Rentals: Transportation + Schools
    - Sales: Schools + Transportation
    
    Args:
        address: Property address
        notes: Normalized notes (optional, may mention specific amenities)
        listing_type: "sale" or "rent" (optional, affects query focus)
        
    Returns:
        Combined search query string
    """
    query_parts = [address]
    
    # Always include schools and transportation (most important amenities)
    if listing_type == "rent":
        # For rentals, transportation is more important
        query_parts.append("transportation subway metro bus public transit")
        query_parts.append("schools education")
    else:
        # For sales, schools are more important
        query_parts.append("schools education")
        query_parts.append("transportation subway metro bus public transit")
    
    # Add context from notes if available
    if notes:
        notes_lower = notes.lower()
        if any(keyword in notes_lower for keyword in ["school", "transportation", "subway", "metro", "bus"]):
            query_parts.append("nearby")
    
    query = " ".join(query_parts)
    return query.strip()


# ============================================================================
# Result Extraction
# ============================================================================

def extract_zip_code(search_results: List[Dict[str, Any]]) -> Optional[str]:
    """
    Extract ZIP code from search results.
    
    Looks for ZIP code patterns in the search result content.
    
    Args:
        search_results: List of search result dictionaries from Tavily
        
    Returns:
        ZIP code string if found, None otherwise
    """
    zip_pattern = r'\b\d{5}(?:-\d{4})?\b'  # 5 digits or 5+4 format
    
    for result in search_results:
        content = result.get("content", "")
        # Look for ZIP code pattern
        matches = re.findall(zip_pattern, content)
        if matches:
            # Return first valid ZIP code (5 digits)
            for match in matches:
                zip_code = match.split("-")[0]  # Take first 5 digits
                if len(zip_code) == 5 and zip_code.isdigit():
                    return zip_code
    
    return None


def extract_neighborhood(search_results: List[Dict[str, Any]], address: str) -> Optional[str]:
    """
    Extract neighborhood name from search results.
    
    Looks for neighborhood names in the search result content.
    Common patterns: "in [Neighborhood]", "located in [Neighborhood]", etc.
    
    Args:
        search_results: List of search result dictionaries from Tavily
        address: Original address for context
        
    Returns:
        Neighborhood name if found, None otherwise
    """
    neighborhood_patterns = [
        r'(?:in|located in|neighborhood of|area of)\s+([A-Z][a-zA-Z\s]+?)(?:,|\.|$)',
        r'([A-Z][a-zA-Z\s]+?)\s+neighborhood',
        r'neighborhood:\s*([A-Z][a-zA-Z\s]+?)(?:,|\.|$)',
    ]
    
    for result in search_results:
        content = result.get("content", "") or ""
        title = result.get("title", "") or ""
        combined_text = f"{title} {content}".lower()
        
        # Skip if content is not a string
        if not isinstance(combined_text, str):
            continue
        
        # Look for neighborhood patterns
        for pattern in neighborhood_patterns:
            try:
                matches = re.findall(pattern, combined_text, re.IGNORECASE)
                if matches:
                    # Return first match that looks like a neighborhood name
                    for match in matches:
                        neighborhood = match.strip()
                        # Filter out common false positives
                        if len(neighborhood) > 3 and len(neighborhood) < 50:
                            # Exclude common words that aren't neighborhoods
                            exclude_words = ["the", "and", "or", "for", "with", "from"]
                            if not any(word in neighborhood.lower() for word in exclude_words):
                                return neighborhood.title()
            except (TypeError, AttributeError):
                # Skip if pattern matching fails
                continue
    
    return None


def extract_landmarks(search_results: List[Dict[str, Any]], max_landmarks: int = 5) -> List[str]:
    """
    Extract nearby landmarks from search results.
    
    Extracts landmark names from search results, prioritizing well-known locations.
    
    Args:
        search_results: List of search result dictionaries from Tavily
        max_landmarks: Maximum number of landmarks to return
        
    Returns:
        List of landmark names
    """
    landmarks = []
    
    for result in search_results:
        content = result.get("content", "")
        title = result.get("title", "")
        
        # Look for landmark indicators
        landmark_indicators = [
            r'([A-Z][a-zA-Z\s]+?)\s+(?:Park|Museum|Plaza|Square|Center|Tower|Bridge|Monument)',
            r'near\s+([A-Z][a-zA-Z\s]+?)(?:,|\.|$)',
            r'close to\s+([A-Z][a-zA-Z\s]+?)(?:,|\.|$)',
        ]
        
        for pattern in landmark_indicators:
            matches = re.findall(pattern, content + " " + title)
            for match in matches:
                landmark = match.strip()
                if len(landmark) > 3 and len(landmark) < 50:
                    if landmark not in landmarks:
                        landmarks.append(landmark)
                        if len(landmarks) >= max_landmarks:
                            return landmarks
    
    return landmarks[:max_landmarks]


def extract_amenities(
    search_results: List[Dict[str, Any]], 
    amenity_type: str,
    max_items: int = 3
) -> List[str]:
    """
    Extract amenities of a specific type from search results.
    
    Args:
        search_results: List of search result dictionaries from Tavily
        amenity_type: Type of amenity ("schools", "parks", "shopping", "transportation")
        max_items: Maximum number of items to return
        
    Returns:
        List of amenity names
    """
    amenities = []
    
    # Patterns for different amenity types
    patterns = {
        "schools": [
            r'([A-Z][a-zA-Z\s]+?)\s+(?:School|Elementary|High School|Academy)',
            r'(?:PS|Public School)\s+(\d+)',
        ],
        "parks": [
            r'([A-Z][a-zA-Z\s]+?)\s+Park',
        ],
        "shopping": [
            r'([A-Z][a-zA-Z\s]+?)\s+(?:Mall|Shopping Center|Plaza)',
        ],
        "transportation": [
            r'(?:Subway|Metro|Bus)\s+(?:Line|Station):\s*([A-Z0-9\s,]+)',
            r'([A-Z0-9]+)\s+(?:line|station)',
        ],
    }
    
    pattern_list = patterns.get(amenity_type, [])
    
    for result in search_results:
        content = result.get("content", "")
        title = result.get("title", "")
        combined_text = content + " " + title
        
        for pattern in pattern_list:
            matches = re.findall(pattern, combined_text)
            for match in matches:
                amenity = match.strip() if isinstance(match, str) else str(match).strip()
                if len(amenity) > 2 and len(amenity) < 100:
                    if amenity not in amenities:
                        amenities.append(amenity)
                        if len(amenities) >= max_items:
                            return amenities
    
    return amenities[:max_items]


# ============================================================================
# Tavily Search Integration
# ============================================================================

def perform_tavily_search(
    query: str,
    search_tool: Any,
    max_results: int = 3
) -> List[Dict[str, Any]]:
    """
    Perform a Tavily web search.
    
    This function executes an actual web search via the Tavily API.
    The search_tool.invoke() call makes an HTTP request to Tavily's servers
    which then searches the web and returns results.
    
    Args:
        query: Search query string
        search_tool: TavilySearch tool instance
        max_results: Maximum number of results to return
        
    Returns:
        List of search result dictionaries
        
    Note:
        This function makes a real web API call. Each call to this function
        results in one HTTP request to Tavily's API.
    """
    try:
        # THIS IS WHERE THE ACTUAL WEB SEARCH HAPPENS
        # search_tool.invoke() makes an HTTP request to Tavily API
        # which searches the web and returns results
        results = search_tool.invoke({"query": query})
        
        # TavilySearch returns a dictionary with 'results' key containing list of results
        if isinstance(results, dict) and "results" in results:
            return results["results"][:max_results]
        # Fallback: if it's already a list
        if isinstance(results, list):
            return results[:max_results]
        return []
    except Exception:
        # Return empty list on error (enrichment is optional)
        return []


# ============================================================================
# Comprehensive Enrichment (Legacy - 6 searches, kept for future use)
# ============================================================================

def enrich_property_data_comprehensive(
    address: str,
    notes: str = "",
    listing_type: Optional[str] = None,
    price: Optional[float] = None,
    search_tool: Any = None
) -> Dict[str, Any]:
    """
    LEGACY: Comprehensive enrichment with 6 sequential searches.
    
    This function is kept for future use if comprehensive enrichment is needed.
    It performs 6 separate searches:
    1. Neighborhood & ZIP code
    2. Landmarks
    3-6. Individual amenity searches (schools, parks, shopping, transportation)
    
    To use this instead of the optimized version, call this function directly
    or set use_comprehensive=True in enrich_property_data().
    
    Args:
        address: Property address (normalized, preferred)
        notes: Normalized notes (optional, may contain location/amenity hints)
        listing_type: "sale" or "rent" (optional, affects search priorities)
        price: Property price (optional, can help understand neighborhood)
        search_tool: TavilySearch tool instance
        
    Returns:
        Dictionary with enrichment data:
        {
            "zip_code": Optional[str],
            "neighborhood": Optional[str],
            "landmarks": List[str],
            "key_amenities": {
                "schools": List[str],
                "parks": List[str],
                "shopping": List[str],
                "transportation": List[str]
            }
        }
    """
    enrichment_data = {
        "zip_code": None,
        "neighborhood": None,
        "landmarks": [],
        "key_amenities": {
            "schools": [],
            "parks": [],
            "shopping": [],
            "transportation": []
        }
    }
    
    # Search 1: Neighborhood and ZIP code
    # Use address + notes context to find neighborhood
    # WEB SEARCH #1: Executes here via perform_tavily_search()
    try:
        neighborhood_query = build_neighborhood_search_query(
            address=address,
            notes=notes,
            listing_type=listing_type
        )
        # This call executes an actual web search via Tavily API
        neighborhood_results = perform_tavily_search(neighborhood_query, search_tool)
        
        if neighborhood_results:
            zip_code = extract_zip_code(neighborhood_results)
            if zip_code:
                enrichment_data["zip_code"] = zip_code
            
            neighborhood = extract_neighborhood(neighborhood_results, address)
            if neighborhood:
                enrichment_data["neighborhood"] = neighborhood
    except Exception:
        # Continue if this search fails
        pass
    
    # Search 2: Landmarks
    # Use address + notes to find relevant landmarks
    # WEB SEARCH #2: Executes here via perform_tavily_search()
    try:
        landmarks_query = build_landmarks_search_query(
            address=address,
            notes=notes,
            listing_type=listing_type
        )
        # This call executes an actual web search via Tavily API
        landmarks_results = perform_tavily_search(landmarks_query, search_tool)
        
        if landmarks_results:
            landmarks = extract_landmarks(landmarks_results, max_landmarks=5)
            enrichment_data["landmarks"] = landmarks
    except Exception:
        # Continue if this search fails
        pass
    
    # Search 3-6: Amenities (one search per category)
    # Prioritize amenities based on listing_type:
    # - Rentals: prioritize transportation
    # - Sales: prioritize schools
    amenity_types = ["schools", "parks", "shopping", "transportation"]
    
    # Reorder based on listing type priority
    if listing_type == "rent":
        # For rentals, transportation is more important
        amenity_types = ["transportation", "schools", "parks", "shopping"]
    elif listing_type == "sale":
        # For sales, schools are more important
        amenity_types = ["schools", "parks", "shopping", "transportation"]
    
    # Searches 3-6: Amenities (one web search per amenity type)
    # WEB SEARCHES #3, #4, #5, #6: Execute here via perform_tavily_search() in loop
    for amenity_type in amenity_types:
        try:
            amenity_query = build_amenities_search_query(
                address=address,
                amenity_type=amenity_type,
                notes=notes,
                listing_type=listing_type
            )
            # This call executes an actual web search via Tavily API (4 times total)
            amenity_results = perform_tavily_search(amenity_query, search_tool)
            
            if amenity_results:
                amenities = extract_amenities(amenity_results, amenity_type, max_items=3)
                enrichment_data["key_amenities"][amenity_type] = amenities
        except Exception:
            # Continue if this search fails
            pass
    
    return enrichment_data


# ============================================================================
# Optimized Enrichment (2 parallel searches - CURRENT IMPLEMENTATION)
# ============================================================================

def enrich_property_data(
    address: str,
    notes: str = "",
    listing_type: Optional[str] = None,
    price: Optional[float] = None,
    search_tool: Any = None,
    use_comprehensive: bool = False
) -> Dict[str, Any]:
    """
    Perform optimized property data enrichment using web search.
    
    OPTIMIZED VERSION (default): Performs 2 parallel searches:
    1. Location Context: ZIP code + Neighborhood
    2. Key Amenities: Schools + Transportation (combined, prioritized by listing_type)
    
    This reduces latency by ~67% compared to comprehensive version (6 searches).
    
    To use the comprehensive version (6 searches), set use_comprehensive=True
    or call enrich_property_data_comprehensive() directly.
    
    Args:
        address: Property address (normalized, preferred)
        notes: Normalized notes (optional, may contain location/amenity hints)
        listing_type: "sale" or "rent" (optional, affects search priorities)
        price: Property price (optional, can help understand neighborhood)
        search_tool: TavilySearch tool instance
        use_comprehensive: If True, use comprehensive 6-search version (legacy)
        
    Returns:
        Dictionary with enrichment data:
        {
            "zip_code": Optional[str],
            "neighborhood": Optional[str],
            "landmarks": List[str],  # Empty in optimized version
            "key_amenities": {
                "schools": List[str],
                "parks": List[str],  # Empty in optimized version
                "shopping": List[str],  # Empty in optimized version
                "transportation": List[str]
            }
        }
    """
    # Allow fallback to comprehensive version if needed
    if use_comprehensive:
        return enrich_property_data_comprehensive(
            address=address,
            notes=notes,
            listing_type=listing_type,
            price=price,
            search_tool=search_tool
        )
    
    # Initialize enrichment data structure
    enrichment_data = {
        "zip_code": None,
        "neighborhood": None,
        "landmarks": [],  # Not searched in optimized version
        "key_amenities": {
            "schools": [],
            "parks": [],  # Not searched in optimized version
            "shopping": [],  # Not searched in optimized version
            "transportation": []
        }
    }
    
    # Build queries for parallel execution
    location_query = build_neighborhood_search_query(
        address=address,
        notes=notes,
        listing_type=listing_type
    )
    
    amenities_query = build_combined_amenities_search_query(
        address=address,
        notes=notes,
        listing_type=listing_type
    )
    
    # Execute searches in parallel using ThreadPoolExecutor
    def execute_location_search():
        """Execute location search and extract ZIP + neighborhood"""
        try:
            results = perform_tavily_search(location_query, search_tool)
            if results:
                zip_code = extract_zip_code(results)
                neighborhood = extract_neighborhood(results, address)
                return {"zip_code": zip_code, "neighborhood": neighborhood}
        except Exception as e:
            print(f"[DEBUG] Location search failed: {e}")
        return {"zip_code": None, "neighborhood": None}
    
    def execute_amenities_search():
        """Execute combined amenities search and extract schools + transportation"""
        try:
            results = perform_tavily_search(amenities_query, search_tool)
            if results:
                # Extract schools from combined results
                schools = extract_amenities(results, "schools", max_items=3)
                # Extract transportation from combined results
                transportation = extract_amenities(results, "transportation", max_items=3)
                return {"schools": schools, "transportation": transportation}
        except Exception as e:
            print(f"[DEBUG] Amenities search failed: {e}")
        return {"schools": [], "transportation": []}
    
    # Execute both searches in parallel
    with ThreadPoolExecutor(max_workers=2) as executor:
        # Submit both tasks
        location_future = executor.submit(execute_location_search)
        amenities_future = executor.submit(execute_amenities_search)
        
        # Wait for both to complete and collect results
        location_result = location_future.result()
        amenities_result = amenities_future.result()
    
    # Populate enrichment data with results
    enrichment_data["zip_code"] = location_result.get("zip_code")
    enrichment_data["neighborhood"] = location_result.get("neighborhood")
    enrichment_data["key_amenities"]["schools"] = amenities_result.get("schools", [])
    enrichment_data["key_amenities"]["transportation"] = amenities_result.get("transportation", [])
    
    return enrichment_data

