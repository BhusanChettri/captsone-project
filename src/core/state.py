"""
LangGraph State Definition for Property Listing System - Iteration 1

This module defines the state that flows between nodes in the LangGraph workflow.
The state is a TypedDict that tracks all data as it moves through the pipeline.

State Flow:
1. Input data (address, listing_type, price, notes, optional fields)
2. Normalized data (after text processing)
3. Enrichment data (ZIP code, neighborhood, landmarks, key amenities from Tavily web search)
4. LLM output (raw and parsed JSON)
5. Final output (title, description, price_block, formatted listing)
6. Error tracking (validation errors, processing errors)
"""

from typing import TypedDict, Literal, Optional, List, Dict, Any


class PropertyListingState(TypedDict, total=False):
    """
    State definition for the Property Listing LangGraph workflow.
    
    This TypedDict defines all possible fields that can exist in the state.
    Fields marked as 'total=False' means all fields are optional EXCEPT
    those that are required by the workflow logic (address, listing_type).
    
    Required Fields (must be set before workflow starts):
    - address: Property address (required for processing)
    - listing_type: Either "sale" or "rent" (required to determine content type)
    
    Optional Input Fields:
    - price: Asking price in USD
    - notes: Free-text description with key features
    - billing_cycle: How often rent is paid (rental only)
    - lease_term: Lease duration (rental only)
    - security_deposit: Security deposit amount in USD (rental only)
    - hoa_fees: HOA fees in USD (sale only)
    - property_taxes: Annual property taxes in USD (sale only)
    
    Processing Fields (set by nodes during workflow):
    - normalized_address: Cleaned/normalized address
    - normalized_notes: Cleaned/normalized notes
    
    Enrichment Fields (set by enrichment node, optional):
    - zip_code: ZIP code extracted from address via geocoding
    - neighborhood: Neighborhood name/location identifier
    - landmarks: List of nearby landmarks from web search (top 3-5)
    - key_amenities: Dictionary of amenities by category (schools, parks, shopping, transportation)
    
    LLM Output Fields (set by LLM generation node):
    - llm_raw_output: Raw JSON string response from LLM
    - llm_parsed: Parsed JSON dictionary with title, description, price_block
    
    Final Output Fields (set by formatting node):
    - title: Generated listing title
    - description: Generated listing description
    - price_block: Formatted price information
    - formatted_listing: Final formatted listing with disclaimer
    
    Error Tracking:
    - errors: List of error messages encountered during processing
    """
    
    # ========================================================================
    # Required Input Fields
    # ========================================================================
    
    address: str
    """Property address. Required field."""
    
    listing_type: Literal["sale", "rent"]
    """Listing type: "sale" or "rent". Required field."""
    
    # ========================================================================
    # Optional Input Fields
    # ========================================================================
    
    price: Optional[float]
    """Asking price in USD. Optional but typically provided."""
    
    notes: Optional[str]
    """Free-text description with key features (beds, baths, sqft, amenities)."""
    
    # Rental-specific optional fields
    billing_cycle: Optional[str]
    """How often rent is paid (e.g., "monthly", "weekly"). For rentals only."""
    
    lease_term: Optional[str]
    """Lease duration (e.g., "12 months", "6 months"). For rentals only."""
    
    security_deposit: Optional[float]
    """Security deposit amount in USD. For rentals only."""
    
    # Sale-specific optional fields
    hoa_fees: Optional[float]
    """HOA fees in USD. For sales only."""
    
    property_taxes: Optional[float]
    """Annual property taxes in USD. For sales only."""
    
    # ========================================================================
    # Processing Fields (set by normalization node)
    # ========================================================================
    
    normalized_address: Optional[str]
    """Cleaned and normalized address after text processing."""
    
    normalized_notes: Optional[str]
    """Cleaned and normalized notes after text processing."""
    
    # ========================================================================
    # Enrichment Fields (set by enrichment node, optional)
    # ========================================================================
    
    zip_code: Optional[str]
    """ZIP code extracted from address via geocoding."""
    
    neighborhood: Optional[str]
    """Neighborhood name/location identifier (e.g., "Midtown Manhattan")."""
    
    landmarks: Optional[List[str]]
    """List of nearby landmarks fetched from web search (top 3-5 most relevant)."""
    
    key_amenities: Optional[Dict[str, List[str]]]
    """
    Dictionary of key amenities organized by category.
    Structure: {
        "schools": ["School Name 1", "School Name 2"],
        "parks": ["Park Name 1"],
        "shopping": ["Shopping Center 1"],
        "transportation": ["Subway: Line 1, Line 2"]
    }
    """
    
    # ========================================================================
    # LLM Output Fields (set by LLM generation node)
    # ========================================================================
    
    llm_raw_output: Optional[str]
    """Raw JSON string response from LLM before parsing."""
    
    llm_parsed: Optional[Dict[str, Any]]
    """Parsed JSON dictionary containing title, description, and price_block."""
    
    # ========================================================================
    # Final Output Fields (set by formatting node)
    # ========================================================================
    
    title: Optional[str]
    """Generated listing title (e.g., "Beautiful 3BR/2BA Home in Downtown")."""
    
    description: Optional[str]
    """Generated listing description (professional, SEO-friendly prose)."""
    
    price_block: Optional[str]
    """Formatted price information (e.g., "$500,000" or "$2,500/month")."""
    
    formatted_listing: Optional[str]
    """Final formatted listing text with disclaimer ready for publishing."""
    
    # ========================================================================
    # Error Tracking
    # ========================================================================
    
    errors: List[str]
    """List of error messages encountered during processing. Always present, empty if no errors."""

