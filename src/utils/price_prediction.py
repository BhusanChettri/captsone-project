"""
Price Prediction Utilities for Property Listing System

This module provides LLM-based price prediction functionality.
It uses structured property data to predict market prices for sale or rental properties.
"""

import json
from typing import Optional, Dict, Any, List


def build_price_prediction_prompt(
    address: str,
    listing_type: str,  # "sale" or "rent"
    property_type: str,
    bedrooms: int,
    bathrooms: float,
    sqft: int,
    zip_code: Optional[str] = None,
    neighborhood: Optional[str] = None,
    landmarks: Optional[List[str]] = None,
    key_amenities: Optional[Dict[str, List[str]]] = None,
    neighborhood_quality: Optional[Dict[str, Optional[str]]] = None,
    region: str = "US"
) -> str:
    """
    Build prompt for LLM-based price prediction.
    
    This prompt provides all structured property data to the LLM and asks
    it to predict the market price based on comparable properties and market knowledge.
    
    Args:
        address: Property address
        listing_type: "sale" or "rent"
        property_type: Type of property (Apartment, House, Condo, etc.)
        bedrooms: Number of bedrooms
        bathrooms: Number of bathrooms (can be decimal)
        sqft: Square footage
        zip_code: ZIP code (optional, from enrichment)
        neighborhood: Neighborhood name (optional, from enrichment)
        landmarks: List of nearby landmarks (optional, from enrichment)
        key_amenities: Dictionary of amenities by category (optional, from enrichment)
        neighborhood_quality: Dictionary with crime_info, quality_of_life, safety_info (optional)
        region: Region code (US, CA, UK, AU)
        
    Returns:
        Complete prompt string for LLM price prediction
    """
    # Format bathrooms: show as integer if whole number
    bathrooms_display = int(bathrooms) if bathrooms == int(bathrooms) else bathrooms
    
    prompt_parts = []
    
    # Header
    prompt_parts.append("You are a real estate price estimation expert. Predict the market price for this property.")
    prompt_parts.append("")
    
    # Property Details Section
    prompt_parts.append("=== PROPERTY DETAILS ===")
    prompt_parts.append(f"Address: {address}")
    prompt_parts.append(f"Property Type: {property_type}")
    prompt_parts.append(f"Bedrooms: {bedrooms}")
    prompt_parts.append(f"Bathrooms: {bathrooms_display}")
    prompt_parts.append(f"Square Footage: {sqft:,} sqft")
    prompt_parts.append(f"Listing Type: {listing_type.upper()}")
    prompt_parts.append(f"Region: {region}")
    prompt_parts.append("")
    
    # Location Context Section
    location_info = []
    if zip_code:
        location_info.append(f"ZIP Code: {zip_code}")
    if neighborhood:
        location_info.append(f"Neighborhood: {neighborhood}")
    
    if location_info:
        prompt_parts.append("=== LOCATION CONTEXT ===")
        prompt_parts.append("\n".join(location_info))
        prompt_parts.append("")
    
    # Nearby Landmarks Section
    if landmarks:
        prompt_parts.append("=== NEARBY LANDMARKS ===")
        for landmark in landmarks:
            prompt_parts.append(f"- {landmark}")
        prompt_parts.append("")
    
    # Amenities Section
    if key_amenities:
        amenities_added = False
        prompt_parts.append("=== AMENITIES ===")
        for category, items in key_amenities.items():
            if items:
                category_name = category.capitalize()
                prompt_parts.append(f"{category_name}:")
                for item in items:
                    prompt_parts.append(f"  - {item}")
                amenities_added = True
        if amenities_added:
            prompt_parts.append("")
    
    # Neighborhood Quality Section
    if neighborhood_quality:
        quality_info = []
        if neighborhood_quality.get("crime_info"):
            quality_info.append(f"Crime & Safety: {neighborhood_quality['crime_info']}")
        if neighborhood_quality.get("quality_of_life"):
            quality_info.append(f"Quality of Life: {neighborhood_quality['quality_of_life']}")
        if neighborhood_quality.get("safety_info"):
            quality_info.append(f"Safety Information: {neighborhood_quality['safety_info']}")
        
        if quality_info:
            prompt_parts.append("=== NEIGHBORHOOD QUALITY ===")
            prompt_parts.append("\n".join(quality_info))
            prompt_parts.append("")
    
    # Instructions Section
    prompt_parts.append("=== INSTRUCTIONS ===")
    prompt_parts.append("Analyze all provided information and predict the market price for this property.")
    prompt_parts.append("")
    prompt_parts.append("Consider:")
    prompt_parts.append("  • Property size and features (bedrooms, bathrooms, square footage)")
    prompt_parts.append("  • Location desirability (neighborhood, ZIP code, landmarks)")
    prompt_parts.append("  • Nearby amenities (schools, parks, transportation, shopping)")
    prompt_parts.append("  • Neighborhood quality (safety, crime rates, quality of life)")
    prompt_parts.append("  • Comparable properties in the area")
    prompt_parts.append("  • Market trends for the region")
    prompt_parts.append("")
    
    if listing_type == "rent":
        prompt_parts.append("For RENTAL properties:")
        prompt_parts.append("  • Predict monthly rental price in USD")
        prompt_parts.append("  • Consider rental market rates for similar properties")
        prompt_parts.append("  • Factor in location convenience and amenities")
    else:
        prompt_parts.append("For SALE properties:")
        prompt_parts.append("  • Predict total sale price in USD")
        prompt_parts.append("  • Consider recent sales of comparable properties")
        prompt_parts.append("  • Factor in property value and investment potential")
    prompt_parts.append("")
    
    prompt_parts.append("=== OUTPUT FORMAT ===")
    prompt_parts.append("Return ONLY valid JSON (no markdown, no code blocks, no extra text):")
    prompt_parts.append("")
    prompt_parts.append("{")
    prompt_parts.append('  "predicted_price": 500000.0,')
    prompt_parts.append('  "reasoning": "Brief 1-2 sentence explanation of the price prediction"')
    prompt_parts.append("}")
    prompt_parts.append("")
    prompt_parts.append("IMPORTANT:")
    prompt_parts.append("  • predicted_price: Numeric value in USD (float)")
    prompt_parts.append("  • reasoning: 1-2 sentences explaining the prediction")
    prompt_parts.append("  • Return ONLY the JSON object, no other text")
    
    return "\n".join(prompt_parts)


def parse_price_prediction_response(response: str) -> Dict[str, Any]:
    """
    Parse JSON response from LLM price prediction.
    
    Handles cases where LLM might return:
    - Plain JSON: {"predicted_price": 500000.0, "reasoning": "..."}
    - JSON wrapped in markdown code blocks: ```json {...} ```
    - JSON with extra text before/after
    
    Args:
        response: Raw response string from LLM
        
    Returns:
        Parsed dictionary with keys: predicted_price, reasoning
        
    Raises:
        ValueError: If JSON cannot be parsed or required keys are missing
    """
    if not response or not response.strip():
        raise ValueError("Empty response from LLM")
    
    # Clean the response
    cleaned_response = response.strip()
    
    # Remove markdown code blocks if present
    if cleaned_response.startswith("```"):
        lines = cleaned_response.split("\n")
        start_idx = None
        end_idx = None
        for i, line in enumerate(lines):
            if line.strip().startswith("```"):
                if start_idx is None:
                    start_idx = i + 1
                else:
                    end_idx = i
                    break
        if start_idx is not None and end_idx is not None:
            cleaned_response = "\n".join(lines[start_idx:end_idx])
        elif start_idx is not None:
            cleaned_response = "\n".join(lines[start_idx:])
    
    # Try to find JSON object in the response
    start_brace = cleaned_response.find("{")
    end_brace = cleaned_response.rfind("}")
    
    if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
        json_str = cleaned_response[start_brace:end_brace + 1]
    else:
        json_str = cleaned_response
    
    # Parse JSON
    try:
        parsed = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from LLM response: {str(e)}")
    
    # Validate required keys
    required_keys = ["predicted_price", "reasoning"]
    missing_keys = [key for key in required_keys if key not in parsed]
    if missing_keys:
        raise ValueError(f"Missing required keys in LLM response: {missing_keys}")
    
    # Validate types
    if not isinstance(parsed["predicted_price"], (int, float)):
        raise ValueError(f"Invalid predicted_price type: must be numeric, got {type(parsed['predicted_price'])}")
    
    if not isinstance(parsed["reasoning"], str):
        raise ValueError(f"Invalid reasoning type: must be string, got {type(parsed['reasoning'])}")
    
    # Validate predicted_price is reasonable (positive, not absurdly high)
    if parsed["predicted_price"] < 0:
        raise ValueError(f"Invalid predicted_price: must be positive, got {parsed['predicted_price']}")
    
    if parsed["predicted_price"] > 1_000_000_000:  # 1 billion USD
        raise ValueError(f"Invalid predicted_price: seems unreasonably high, got {parsed['predicted_price']}")
    
    # Validate reasoning is not empty
    if not parsed["reasoning"].strip():
        raise ValueError("Invalid reasoning: must be non-empty string")
    
    return parsed


def validate_predicted_price(predicted_price: float, listing_type: str, region: str) -> bool:
    """
    Validate that predicted price is reasonable for the listing type and region.
    
    Args:
        predicted_price: Predicted price value
        listing_type: "sale" or "rent"
        region: Region code (US, CA, UK, AU)
        
    Returns:
        True if price seems reasonable, False otherwise
    """
    # Basic sanity checks
    if predicted_price < 0:
        return False
    
    # Rough sanity checks by listing type
    if listing_type == "rent":
        # Monthly rent should be between $100 and $50,000/month
        if predicted_price < 100 or predicted_price > 50_000:
            return False
    else:  # sale
        # Sale price should be between $10,000 and $100,000,000
        if predicted_price < 10_000 or predicted_price > 100_000_000:
            return False
    
    return True

