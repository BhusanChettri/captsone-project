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
    Build search query for neighborhood information.
    
    Only searches for neighborhood if it's not already in the address.
    ZIP code is NOT searched - it should come from address parsing.
    
    Args:
        address: Property address
        notes: Normalized notes (optional, for context)
        listing_type: "sale" or "rent" (optional, for context)
        
    Returns:
        Search query string
    """
    # Start with address
    query_parts = [address]
    
    # Add neighborhood keywords (not ZIP code - that comes from address)
    query_parts.append("neighborhood area")
    
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


def build_amenities_search_query(
    address: str,
    amenity_type: str,
    notes: str = "",
    listing_type: Optional[str] = None
) -> str:
    """
    Build search query for specific amenity type.
    
    Focuses on finding actual places/names, not generic information.
    Searches for: schools, supermarkets, parks, transportation.
    
    Args:
        address: Property address
        amenity_type: Type of amenity ("schools", "supermarkets", "parks", "transportation")
        notes: Normalized notes (optional, to check if already mentioned)
        listing_type: "sale" or "rent" (optional, affects query focus)
        
    Returns:
        Search query string
    """
    query_parts = [address]
    
    # Build specific query based on amenity type
    if amenity_type == "schools":
        query_parts.append("schools near")
    elif amenity_type == "supermarkets":
        query_parts.append("supermarkets grocery stores near")
    elif amenity_type == "parks":
        query_parts.append("parks near")
    elif amenity_type == "transportation":
        query_parts.append("transportation subway bus metro near")
    else:
        query_parts.append(f"{amenity_type} near")
    
    query = " ".join(query_parts)
    return query.strip()


# ============================================================================
# Address Parsing (ZIP Code Extraction)
# ============================================================================

def parse_zip_code_from_address(address: str) -> Optional[str]:
    """
    Parse ZIP code from user's address input.
    
    ZIP code should come from the address, not from web search.
    This function extracts it if present.
    
    Args:
        address: Property address string
        
    Returns:
        ZIP code string if found, None otherwise
    """
    if not address:
        return None
    
    # Pattern: 5 digits (optionally followed by -4 digits)
    # Look for ZIP code at the end of address (common format: "City, ST ZIP")
    zip_pattern = r'\b(\d{5})(?:-\d{4})?\b'
    
    # Try to find ZIP code (usually at the end)
    matches = re.findall(zip_pattern, address)
    if matches:
        # Return the last match (most likely the actual ZIP code)
        return matches[-1]
    
    return None


def check_amenity_in_notes(notes: str, amenity_type: str) -> bool:
    """
    Check if a specific amenity type is already mentioned in user's notes.
    
    This helps avoid redundant web searches for amenities already provided by user.
    
    Args:
        notes: User's notes/description
        amenity_type: Type of amenity to check ("schools", "supermarkets", "parks", "transportation")
        
    Returns:
        True if amenity type is mentioned, False otherwise
    """
    if not notes:
        return False
    
    notes_lower = notes.lower()
    
    # Keywords for each amenity type
    keywords = {
        "schools": ["school", "elementary", "high school", "academy", "university", "college"],
        "supermarkets": ["supermarket", "grocery", "store", "market", "whole foods", "trader joe", "walmart", "target"],
        "parks": ["park", "playground", "recreation", "green space"],
        "transportation": ["subway", "metro", "bus", "train", "station", "transit", "transportation", "line"]
    }
    
    amenity_keywords = keywords.get(amenity_type, [])
    return any(keyword in notes_lower for keyword in amenity_keywords)


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
                        # Clean up newlines and extra whitespace
                        neighborhood = re.sub(r'\s+', ' ', neighborhood)  # Normalize whitespace
                        neighborhood = neighborhood.strip()
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
    
    Improved extraction to get actual names, filtering out HTML artifacts
    and generic text.
    
    Args:
        search_results: List of search result dictionaries from Tavily
        amenity_type: Type of amenity ("schools", "supermarkets", "parks", "transportation")
        max_items: Maximum number of items to return
        
    Returns:
        List of clean amenity names
    """
    amenities = []
    
    # Patterns for different amenity types (improved to capture actual names)
    patterns = {
        "schools": [
            r'([A-Z][a-zA-Z0-9\s&\'-]+?)\s+(?:School|Elementary|High School|Academy|Middle School)',
            r'(?:PS|Public School|P\.S\.)\s+(\d+)',
            r'([A-Z][a-zA-Z\s]+?)\s+Elementary',
            r'([A-Z][a-zA-Z\s]+?)\s+High',
        ],
        "supermarkets": [
            r'([A-Z][a-zA-Z0-9\s&\'-]+?)\s+(?:Supermarket|Grocery|Market|Whole Foods|Trader Joe|Walmart|Target|Kroger|Safeway)',
            r'(?:Whole Foods|Trader Joe\'s?|Walmart|Target|Kroger|Safeway|Stop & Shop)',
        ],
        "parks": [
            r'([A-Z][a-zA-Z0-9\s&\'-]+?)\s+Park',
            r'([A-Z][a-zA-Z\s]+?)\s+Playground',
            r'([A-Z][a-zA-Z\s]+?)\s+Recreation\s+Area',
        ],
        "transportation": [
            r'(?:Subway|Metro|Bus)\s+(?:Line|Station):\s*([A-Z0-9\s,]+)',
            r'([A-Z0-9]+)\s+(?:line|station)',
            r'(?:near|at)\s+([A-Z][a-zA-Z\s]+?)\s+(?:Subway|Metro|Bus)\s+Station',
        ],
    }
    
    # Words to filter out (HTML artifacts, generic text)
    filter_words = [
        "overview", "website", "contacts", "information", "school website",
        "click", "here", "more", "details", "page", "home", "about",
        "contact", "menu", "navigation", "search", "login", "sign up"
    ]
    
    pattern_list = patterns.get(amenity_type, [])
    
    for result in search_results:
        content = result.get("content", "") or ""
        title = result.get("title", "") or ""
        combined_text = f"{title} {content}"
        
        for pattern in pattern_list:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            for match in matches:
                amenity = match.strip() if isinstance(match, str) else str(match).strip()
                
                # Filter out invalid results
                if len(amenity) < 3 or len(amenity) > 100:
                    continue
                
                # Filter out HTML artifacts and generic text
                amenity_lower = amenity.lower()
                if any(filter_word in amenity_lower for filter_word in filter_words):
                    continue
                
                # Filter out results that are just numbers or single words (unless it's a school number)
                if amenity_type != "schools" and len(amenity.split()) < 2:
                    continue
                
                # Clean up common artifacts
                amenity = re.sub(r'\s+', ' ', amenity)  # Normalize whitespace
                amenity = amenity.strip()
                
                if amenity and amenity not in amenities:
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
    
    FOCUS: Find amenities/features near the address to enrich listing description.
    - ZIP code: Parsed from address (not searched)
    - Neighborhood: Extracted from web search if not in address
    - Amenities: Schools, Supermarkets, Parks, Transportation (searched in parallel)
    
    Intelligently skips amenities already mentioned in user's notes (except parks).
    
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
            "zip_code": Optional[str],  # Parsed from address
            "neighborhood": Optional[str],  # Extracted from web search
            "landmarks": List[str],  # Empty in optimized version
            "key_amenities": {
                "schools": List[str],
                "supermarkets": List[str],
                "parks": List[str],
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
            "supermarkets": [],
            "parks": [],
            "transportation": []
        }
    }
    
    # Step 1: Parse ZIP code from address (not from web search)
    zip_code = parse_zip_code_from_address(address)
    enrichment_data["zip_code"] = zip_code
    if zip_code:
        print(f"[DEBUG] Enrichment: Parsed ZIP code from address: {zip_code}")
    
    # Step 2: Determine which amenities to search for
    # Check if amenities are already in notes (but always search for parks as requested)
    amenity_types_to_search = []
    
    if not check_amenity_in_notes(notes, "schools"):
        amenity_types_to_search.append("schools")
    else:
        print(f"[DEBUG] Enrichment: Skipping schools search (already in notes)")
    
    if not check_amenity_in_notes(notes, "supermarkets"):
        amenity_types_to_search.append("supermarkets")
    else:
        print(f"[DEBUG] Enrichment: Skipping supermarkets search (already in notes)")
    
    # Always search for parks (as per user request)
    amenity_types_to_search.append("parks")
    
    if not check_amenity_in_notes(notes, "transportation"):
        amenity_types_to_search.append("transportation")
    else:
        print(f"[DEBUG] Enrichment: Skipping transportation search (already in notes)")
    
    # Step 3: Build search queries
    neighborhood_query = build_neighborhood_search_query(
        address=address,
        notes=notes,
        listing_type=listing_type
    )
    
    # Build queries for each amenity type
    amenity_queries = {}
    for amenity_type in amenity_types_to_search:
        amenity_queries[amenity_type] = build_amenities_search_query(
            address=address,
            amenity_type=amenity_type,
            notes=notes,
            listing_type=listing_type
        )
    
    # Step 4: Execute searches in parallel
    def execute_neighborhood_search():
        """Execute neighborhood search"""
        try:
            results = perform_tavily_search(neighborhood_query, search_tool)
            if results:
                neighborhood = extract_neighborhood(results, address)
                return {"neighborhood": neighborhood}
        except Exception as e:
            print(f"[DEBUG] Neighborhood search failed: {e}")
        return {"neighborhood": None}
    
    def execute_amenity_search(amenity_type: str, query: str):
        """Execute search for specific amenity type"""
        try:
            results = perform_tavily_search(query, search_tool)
            if results:
                amenities = extract_amenities(results, amenity_type, max_items=3)
                return {amenity_type: amenities}
        except Exception as e:
            print(f"[DEBUG] {amenity_type} search failed: {e}")
        return {amenity_type: []}
    
    # Execute all searches in parallel
    with ThreadPoolExecutor(max_workers=len(amenity_queries) + 1) as executor:
        # Submit neighborhood search
        neighborhood_future = executor.submit(execute_neighborhood_search)
        
        # Submit all amenity searches
        amenity_futures = {}
        for amenity_type, query in amenity_queries.items():
            amenity_futures[amenity_type] = executor.submit(execute_amenity_search, amenity_type, query)
        
        # Wait for all to complete and collect results
        neighborhood_result = neighborhood_future.result()
        enrichment_data["neighborhood"] = neighborhood_result.get("neighborhood")
        
        # Collect amenity results
        for amenity_type, future in amenity_futures.items():
            result = future.result()
            enrichment_data["key_amenities"][amenity_type] = result.get(amenity_type, [])
    
    return enrichment_data

