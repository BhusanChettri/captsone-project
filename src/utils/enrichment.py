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


def build_neighborhood_quality_search_query(address: str) -> str:
    """
    Build search query for neighborhood quality information.
    
    Searches for: crime rates, quality of life, safety, neighborhood statistics.
    Uses ONLY the address - no other parameters.
    
    Args:
        address: Property address (ONLY parameter needed)
        
    Returns:
        Search query string
    """
    # Use ONLY address for search query
    query = f"{address} crime rates quality of life safety neighborhood statistics"
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


def build_amenities_search_query(address: str) -> str:
    """
    Build search query for nearby amenities.
    
    Searches for: schools, shopping amenities, supermarkets, parks, subway, transportation.
    Uses ONLY the address - no other parameters.
    
    Args:
        address: Property address (ONLY parameter needed)
        
    Returns:
        Search query string
    """
    # Use ONLY address for search query - search for all amenities in one query
    query = f"{address} schools shopping amenities supermarkets parks subway transportation near"
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
    # Invalid words that should never be used as neighborhood names
    INVALID_NEIGHBORHOOD_WORDS = [
        "what", "where", "when", "who", "why", "how", "which", "this", "that",
        "the", "and", "or", "for", "with", "from", "about", "into", "onto",
        "area", "neighborhood", "location", "place", "city", "state", "zip",
        "code", "street", "avenue", "road", "drive", "lane", "boulevard"
    ]
    
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
                        
                        # Validate neighborhood name
                        neighborhood_lower = neighborhood.lower()
                        
                        # Filter out invalid words
                        if neighborhood_lower in INVALID_NEIGHBORHOOD_WORDS:
                            continue
                        
                        # Check if it contains invalid words
                        words = neighborhood_lower.split()
                        if any(word in INVALID_NEIGHBORHOOD_WORDS for word in words):
                            continue
                        
                        # Filter out common false positives
                        if len(neighborhood) > 3 and len(neighborhood) < 50:
                            # Must start with capital letter and look like a proper name
                            if neighborhood[0].isupper() and not neighborhood.isdigit():
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


def extract_neighborhood_quality(search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract neighborhood quality information from search results.
    
    Extracts information about:
    - Crime rates
    - Quality of life indicators
    - Safety statistics
    - Neighborhood characteristics
    
    Args:
        search_results: List of search result dictionaries from Tavily
        
    Returns:
        Dictionary with neighborhood quality information:
        {
            "crime_info": str,  # Summary of crime rates/safety
            "quality_of_life": str,  # Quality of life indicators
            "safety_info": str,  # Safety information
            "neighborhood": Optional[str]  # Neighborhood name if found
        }
    """
    quality_info = {
        "crime_info": None,
        "quality_of_life": None,
        "safety_info": None,
        "neighborhood": None
    }
    
    # Patterns to extract crime and safety information
    crime_patterns = [
        r'crime rate[:\s]+([^\.]+)',
        r'safety[:\s]+([^\.]+)',
        r'crime statistics[:\s]+([^\.]+)',
    ]
    
    # Patterns to extract quality of life information
    quality_patterns = [
        r'quality of life[:\s]+([^\.]+)',
        r'livability[:\s]+([^\.]+)',
        r'neighborhood rating[:\s]+([^\.]+)',
    ]
    
    # Try to extract neighborhood name
    neighborhood = extract_neighborhood(search_results, "")
    if neighborhood:
        quality_info["neighborhood"] = neighborhood
    
    # Combine all search result content
    combined_text = ""
    for result in search_results:
        content = result.get("content", "") or ""
        title = result.get("title", "") or ""
        combined_text += f"{title} {content} "
    
    combined_text = combined_text.lower()
    
    # Extract crime/safety information
    crime_snippets = []
    for pattern in crime_patterns:
        matches = re.findall(pattern, combined_text, re.IGNORECASE)
        crime_snippets.extend(matches[:2])  # Take first 2 matches
    
    if crime_snippets:
        quality_info["crime_info"] = ". ".join(crime_snippets[:3])[:200]  # Limit length
    
    # Extract quality of life information
    quality_snippets = []
    for pattern in quality_patterns:
        matches = re.findall(pattern, combined_text, re.IGNORECASE)
        quality_snippets.extend(matches[:2])
    
    if quality_snippets:
        quality_info["quality_of_life"] = ". ".join(quality_snippets[:3])[:200]
    
    # Extract general safety information
    safety_keywords = ["safe", "safety", "secure", "low crime", "well-maintained"]
    safety_snippets = []
    sentences = combined_text.split('.')
    for sentence in sentences:
        if any(keyword in sentence for keyword in safety_keywords):
            if len(sentence.strip()) > 20:  # Only meaningful sentences
                safety_snippets.append(sentence.strip()[:150])
                if len(safety_snippets) >= 2:
                    break
    
    if safety_snippets:
        quality_info["safety_info"] = ". ".join(safety_snippets)
    return quality_info


def extract_amenities(
    search_results: List[Dict[str, Any]], 
    amenity_type: str = None,  # Now optional - we extract all amenities from combined results
    max_items: int = 3
) -> Dict[str, List[str]]:
    """
    Extract amenities from search results (all types combined).
    
    Extracts schools, supermarkets, parks, and transportation from combined search results.
    Improved extraction to get actual names, filtering out HTML artifacts and generic text.
    
    Args:
        search_results: List of search result dictionaries from Tavily
        amenity_type: Optional - kept for compatibility, but we extract all types
        max_items: Maximum number of items per category to return
        
    Returns:
        Dictionary with amenities by category:
        {
            "schools": List[str],
            "supermarkets": List[str],
            "parks": List[str],
            "transportation": List[str]
        }
    """
    amenities_by_type = {
        "schools": [],
        "supermarkets": [],
        "parks": [],
        "transportation": []
    }
    
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
    
    # Words to filter out (HTML artifacts, generic text, invalid words)
    filter_words = [
        "overview", "website", "contacts", "information", "school website",
        "click", "here", "more", "details", "page", "home", "about",
        "contact", "menu", "navigation", "search", "login", "sign up",
        "what", "where", "when", "who", "why", "how", "which", "this", "that"
    ]
    
    # Extract all amenity types from combined search results
    for result_idx, result in enumerate(search_results, 1):
        content = result.get("content", "") or ""
        title = result.get("title", "") or ""
        combined_text = f"{title} {content}"
        
        # Extract each amenity type
        for amenity_type, pattern_list in patterns.items():
            if len(amenities_by_type[amenity_type]) >= max_items:
                continue  # Already have enough of this type
            
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
                    
                    if amenity and amenity not in amenities_by_type[amenity_type]:
                        amenities_by_type[amenity_type].append(amenity)
                        if len(amenities_by_type[amenity_type]) >= max_items:
                            break
                if len(amenities_by_type[amenity_type]) >= max_items:
                    break
    
    return amenities_by_type


# ============================================================================
# Tavily Search Integration
# ============================================================================

def perform_tavily_search(
    query: str,
    search_tool: Any,
    max_results: int = 3
) -> List[Dict[str, Any]]:
    """
    Perform a Tavily web search with tracing.
    
    This function executes an actual web search via the Tavily API.
    The search_tool.invoke() call makes an HTTP request to Tavily's servers
    which then searches the web and returns results.
    
    All web searches are traced for observability, including:
    - Query string
    - Execution time
    - Result count
    - Success/failure status
    
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
        # Import tracing utilities
        from .tracing import trace_web_search, set_trace_metadata
        
        # Use tracing wrapper to track web search execution
        results_list, metrics = trace_web_search(
            search_tool=search_tool,
            query=query,
            max_results=max_results
        )
        
        # Store web search metrics in trace metadata
        # Use a list to track multiple searches
        from .tracing import get_trace_metadata
        existing_metadata = get_trace_metadata()
        existing_searches = existing_metadata.get("web_searches", [])
        existing_searches.append(metrics)
        set_trace_metadata("web_searches", existing_searches)
        
        return results_list
    except Exception as e:
        print(f"[WEB SEARCH ERROR] Query: '{query}'")
        print(f"[WEB SEARCH ERROR] {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        # Store error in trace metadata
        from .tracing import set_trace_metadata
        set_trace_metadata("web_search_error", str(e))
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
    # Note: Legacy function - using neighborhood quality search query (address only)
    try:
        neighborhood_query = build_neighborhood_quality_search_query(address)
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
    # Use address only to find relevant landmarks
    # WEB SEARCH #2: Executes here via perform_tavily_search()
    # Note: Legacy function - using address only
    try:
        landmarks_query = f"{address} nearby landmarks attractions points of interest"
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
    # Note: Legacy function - using address only for queries
    for amenity_type in amenity_types:
        try:
            # Use address-only query (legacy function)
            amenity_query = build_amenities_search_query(address)
            # Extract all amenities from combined results
            # This call executes an actual web search via Tavily API (4 times total)
            amenity_results = perform_tavily_search(amenity_query, search_tool)
            
            if amenity_results:
                # Extract all amenities and get the specific type we need
                all_amenities = extract_amenities(amenity_results, max_items=3)
                enrichment_data["key_amenities"][amenity_type] = all_amenities.get(amenity_type, [])
        except Exception:
            # Continue if this search fails
            pass
    
    return enrichment_data


# ============================================================================
# Optimized Enrichment (2 parallel searches - CURRENT IMPLEMENTATION)
# ============================================================================

def enrich_property_data(
    address: str,
    search_tool: Any = None
) -> Dict[str, Any]:
    """
    Perform property data enrichment using exactly 2 web search calls.
    
    WEB SEARCH CALL 1: Amenities search
    - Uses ONLY address
    - Searches for: schools, shopping amenities, supermarkets, parks, subway, transportation
    
    WEB SEARCH CALL 2: Neighborhood quality search
    - Uses ONLY address
    - Searches for: crime rates, quality of life, safety, neighborhood statistics
    
    ZIP code is parsed from address (not searched).
    
    Args:
        address: Property address (ONLY parameter needed - no notes, listing_type, price)
        search_tool: TavilySearch tool instance
        
    Returns:
        Dictionary with enrichment data:
        {
            "zip_code": Optional[str],  # Parsed from address
            "neighborhood": Optional[str],  # Extracted from neighborhood quality search
            "neighborhood_quality": {  # New field for quality information
                "crime_info": Optional[str],
                "quality_of_life": Optional[str],
                "safety_info": Optional[str]
            },
            "key_amenities": {
                "schools": List[str],
                "supermarkets": List[str],
                "parks": List[str],
                "transportation": List[str]
            }
        }
    """
    # Initialize enrichment data structure
    enrichment_data = {
        "zip_code": None,
        "neighborhood": None,
        "neighborhood_quality": {
            "crime_info": None,
            "quality_of_life": None,
            "safety_info": None
        },
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
    
    # Step 2: Build search queries (ONLY using address)
    amenities_query = build_amenities_search_query(address)
    neighborhood_quality_query = build_neighborhood_quality_search_query(address)
    
    print("\n" + "=" * 80)
    print("[WEB SEARCH] QUERY COMPOSITION")
    print("=" * 80)
    print(f"[WEB SEARCH 1] AMENITIES:")
    print(f"  Query: {amenities_query}")
    print("")
    print(f"[WEB SEARCH 2] NEIGHBORHOOD QUALITY:")
    print(f"  Query: {neighborhood_quality_query}")
    print("=" * 80 + "\n")
    
    # Step 3: Execute exactly 2 web searches in parallel
    def execute_amenities_search():
        """Execute amenities search (WEB SEARCH CALL 1)"""
        try:
            print(f"[WEB SEARCH 1] Executing: {amenities_query}")
            results = perform_tavily_search(amenities_query, search_tool, max_results=3)
            
            print(f"[WEB SEARCH 1] Results: {len(results) if results else 0} items")
            
            if results:
                # Print raw results for debugging
                for i, result in enumerate(results, 1):
                    print(f"\n[WEB SEARCH 1] Result {i}:")
                    print(f"  Title: {result.get('title', 'N/A')}")
                    print(f"  URL: {result.get('url', 'N/A')}")
                    content = result.get('content', '')
                    if content:
                        print(f"  Content: {content}")
                    else:
                        print(f"  Content: (empty)")
                
                amenities_dict = extract_amenities(results, max_items=3)
                print(f"\n[WEB SEARCH 1] Extracted: {amenities_dict}\n")
                return amenities_dict
            else:
                print("[WEB SEARCH 1] No results\n")
        except Exception as e:
            print(f"[WEB SEARCH 1] ERROR: {type(e).__name__}: {str(e)}\n")
            import traceback
            traceback.print_exc()
            return {
                "schools": [],
                "supermarkets": [],
                "parks": [],
                "transportation": []
            }
    
    def execute_neighborhood_quality_search():
        """Execute neighborhood quality search (WEB SEARCH CALL 2)"""
        try:
            print(f"[WEB SEARCH 2] Executing: {neighborhood_quality_query}")
            results = perform_tavily_search(neighborhood_quality_query, search_tool, max_results=3)
            
            print(f"[WEB SEARCH 2] Results: {len(results) if results else 0} items")
            
            if results:
                # Print raw results for debugging
                for i, result in enumerate(results, 1):
                    print(f"\n[WEB SEARCH 2] Result {i}:")
                    print(f"  Title: {result.get('title', 'N/A')}")
                    print(f"  URL: {result.get('url', 'N/A')}")
                    content = result.get('content', '')
                    if content:
                        print(f"  Content: {content}")
                    else:
                        print(f"  Content: (empty)")
                
                quality_info = extract_neighborhood_quality(results)
                print(f"\n[WEB SEARCH 2] Extracted: {quality_info}\n")
                return quality_info
            else:
                print("[WEB SEARCH 2] No results\n")
        except Exception as e:
            print(f"[WEB SEARCH 2] ERROR: {type(e).__name__}: {str(e)}\n")
            import traceback
            traceback.print_exc()
        return {
            "crime_info": None,
            "quality_of_life": None,
            "safety_info": None,
            "neighborhood": None
        }
    
    # Execute both searches in parallel
    with ThreadPoolExecutor(max_workers=2) as executor:
        amenities_future = executor.submit(execute_amenities_search)
        quality_future = executor.submit(execute_neighborhood_quality_search)
        
        # Wait for both to complete and collect results
        try:
            amenities_result = amenities_future.result(timeout=30)
        except Exception as e:
            print(f"[WEB SEARCH 1] Timeout/Error: {e}")
            amenities_result = {
                "schools": [],
                "supermarkets": [],
                "parks": [],
                "transportation": []
            }
        
        try:
            quality_result = quality_future.result(timeout=30)
        except Exception as e:
            print(f"[WEB SEARCH 2] Timeout/Error: {e}")
            quality_result = {
                "crime_info": None,
                "quality_of_life": None,
                "safety_info": None,
                "neighborhood": None
            }
        
        # Store amenities
        enrichment_data["key_amenities"] = amenities_result
        
        # Store neighborhood quality information
        enrichment_data["neighborhood_quality"] = {
            "crime_info": quality_result.get("crime_info"),
            "quality_of_life": quality_result.get("quality_of_life"),
            "safety_info": quality_result.get("safety_info")
        }
        
        # Store neighborhood name if found
        if quality_result.get("neighborhood"):
            enrichment_data["neighborhood"] = quality_result.get("neighborhood")
    
    print(f"[DEBUG] Enrichment: Completed 2 web searches")
    print(f"[DEBUG] Enrichment: Found {len(amenities_result.get('schools', []))} schools, {len(amenities_result.get('supermarkets', []))} supermarkets, {len(amenities_result.get('parks', []))} parks, {len(amenities_result.get('transportation', []))} transportation options")
    
    return enrichment_data

