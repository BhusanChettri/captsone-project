"""
Prompt Templates for Property Listing System - Iteration 1

This module contains prompt templates for LLM content generation.
The prompts are designed to generate structured JSON output with
title, description, and price_block fields.
"""

from typing import Optional, Dict, Any, List
from .region_config import get_region_config, get_currency_symbol, FieldType


def build_listing_generation_prompt(
    address: str,
    listing_type: str,
    property_type: str,
    bedrooms: int,
    bathrooms: float,
    sqft: int,
    notes: Optional[str] = None,
    normalized_address: Optional[str] = None,
    normalized_notes: Optional[str] = None,
    zip_code: Optional[str] = None,
    neighborhood: Optional[str] = None,
    landmarks: Optional[List[str]] = None,
    key_amenities: Optional[Dict[str, List[str]]] = None,
    neighborhood_quality: Optional[Dict[str, Optional[str]]] = None,
    region: Optional[str] = "US",
) -> str:
    """
    Build a comprehensive prompt for LLM to generate property listing content.
    
    This prompt merges all available data (input, normalized, enriched) to create
    a complete context for the LLM to generate professional listing content.
    
    Args:
        address: Property address
        listing_type: "sale" or "rent"
        property_type: Type of property (Apartment, House, Condo, Townhouse, Studio, Loft)
        bedrooms: Number of bedrooms
        bathrooms: Number of bathrooms (can be decimal like 1.5)
        sqft: Square footage / total living area
        notes: Free-text notes with key features, amenities, condition, etc. (optional)
        normalized_address: Cleaned/normalized address
        normalized_notes: Cleaned/normalized notes
        zip_code: ZIP code from enrichment
        neighborhood: Neighborhood name from enrichment
        landmarks: List of nearby landmarks
        key_amenities: Dictionary of amenities by category (schools, supermarkets, parks, transportation)
        neighborhood_quality: Dictionary with crime_info, quality_of_life, safety_info
        region: Region code (US, CA, UK, AU)
        
    Returns:
        Complete prompt string for LLM
    """
    # Use normalized data if available, otherwise fall back to original
    final_address = normalized_address or address
    final_notes = normalized_notes or notes or ""
    
    # Get region configuration
    region = region.upper() if region else "US"
    config = get_region_config(region)
    currency_symbol = config["currency_symbol"]
    currency = config["currency"]
    
    # Build prompt sections
    prompt_parts = []
    
    # Header
    prompt_parts.append("You are a professional real estate listing writer. Generate a property listing based on the following information.")
    prompt_parts.append("")
    
    # Format bathrooms: show as integer if whole number, otherwise show decimal
    bathrooms_display = int(bathrooms) if bathrooms == int(bathrooms) else bathrooms
    
    # Property Information Section
    prompt_parts.append("=== PROPERTY INFORMATION ===")
    prompt_parts.append(f"Address: {final_address}")
    prompt_parts.append(f"Listing Type: {listing_type.upper()}")
    prompt_parts.append(f"Property Type: {property_type}")
    prompt_parts.append(f"Bedrooms: {bedrooms}")
    prompt_parts.append(f"Bathrooms: {bathrooms_display}")
    prompt_parts.append(f"Square Footage: {sqft:,} sqft")
    prompt_parts.append(f"Region: {config['region_name']}")
    prompt_parts.append("")
    prompt_parts.append("IMPORTANT: Use the city/area from the address (e.g., 'New York, NY', 'Manhattan') for location references if neighborhood data is invalid or unclear.")
    prompt_parts.append("")
    
    # Property Features Section
    if final_notes:
        prompt_parts.append("=== PROPERTY FEATURES ===")
        prompt_parts.append(final_notes)
        prompt_parts.append("")
    
    # Location & Neighborhood Section
    # Filter out invalid/garbage neighborhood names
    location_info = []
    print(f"[DEBUG] Prompt Builder: Checking location data - zip_code: {zip_code} (truthy: {bool(zip_code)}), neighborhood: {neighborhood} (truthy: {bool(neighborhood)})")
    
    # Invalid words that should never be used as neighborhood names
    INVALID_NEIGHBORHOOD_WORDS = [
        "what", "where", "when", "who", "why", "how", "which", "this", "that",
        "area", "neighborhood", "location", "place"
    ]
    
    if zip_code:
        location_info.append(f"ZIP Code: {zip_code}")
    
    # Only include neighborhood if it's valid (not a garbage word)
    if neighborhood:
        neighborhood_lower = neighborhood.lower().strip()
        # Check if neighborhood is invalid
        if (neighborhood_lower not in INVALID_NEIGHBORHOOD_WORDS and 
            not any(word in neighborhood_lower for word in INVALID_NEIGHBORHOOD_WORDS) and
            len(neighborhood.strip()) > 3):
            location_info.append(f"Neighborhood: {neighborhood}")
        else:
            print(f"[DEBUG] Prompt Builder: ⚠️ Filtered out invalid neighborhood: '{neighborhood}'")
    
    if location_info:
        prompt_parts.append("=== LOCATION & NEIGHBORHOOD ===")
        prompt_parts.append("\n".join(location_info))
        prompt_parts.append("")
        print(f"[DEBUG] Prompt Builder: ✅ Added LOCATION & NEIGHBORHOOD section with: {location_info}")
    else:
        print(f"[DEBUG] Prompt Builder: ❌ Skipped LOCATION & NEIGHBORHOOD section (no data)")
    
    # Nearby Landmarks Section
    print(f"[DEBUG] Prompt Builder: Checking landmarks - value: {landmarks}, type: {type(landmarks)}, truthy: {bool(landmarks)}")
    if landmarks:
        prompt_parts.append("=== NEARBY LANDMARKS ===")
        for landmark in landmarks:
            prompt_parts.append(f"- {landmark}")
        prompt_parts.append("")
        print(f"[DEBUG] Prompt Builder: ✅ Added NEARBY LANDMARKS section with {len(landmarks)} landmarks")
    else:
        print(f"[DEBUG] Prompt Builder: ❌ Skipped NEARBY LANDMARKS section (no data or empty list)")
    
    # Key Amenities Section
    # Filter out invalid/garbage amenity names
    INVALID_AMENITY_WORDS = [
        "what", "where", "when", "who", "why", "how", "which", "this", "that",
        "overview", "website", "click", "here", "more", "details", "page"
    ]
    
    print(f"[DEBUG] Prompt Builder: Checking key_amenities - value: {key_amenities}, type: {type(key_amenities)}, truthy: {bool(key_amenities)}")
    if key_amenities:
        amenities_added = []
        prompt_parts.append("=== KEY AMENITIES ===")
        for category, items in key_amenities.items():
            print(f"[DEBUG] Prompt Builder:   - Category '{category}': {items} (length: {len(items) if items else 0}, truthy: {bool(items)})")
            if items:
                # Filter out invalid amenity names
                valid_items = []
                for item in items:
                    if isinstance(item, str):
                        item_lower = item.lower().strip()
                        # Skip invalid items
                        if (item_lower not in INVALID_AMENITY_WORDS and
                            not any(word in item_lower for word in INVALID_AMENITY_WORDS) and
                            len(item.strip()) > 2):
                            valid_items.append(item)
                
                if valid_items:
                    category_name = category.capitalize()
                    prompt_parts.append(f"{category_name}:")
                    for item in valid_items:
                        prompt_parts.append(f"  - {item}")
                    amenities_added.append(f"{category}({len(valid_items)} items)")
        prompt_parts.append("")
        if amenities_added:
            print(f"[DEBUG] Prompt Builder: ✅ Added KEY AMENITIES section with: {', '.join(amenities_added)}")
        else:
            print(f"[DEBUG] Prompt Builder: ⚠️ Added KEY AMENITIES section header but no items (all categories empty or filtered)")
    else:
        print(f"[DEBUG] Prompt Builder: ❌ Skipped KEY AMENITIES section (no data or empty dict)")
    
    # Neighborhood Quality Section (from WEB SEARCH 2)
    print(f"[DEBUG] Prompt Builder: Checking neighborhood_quality - value: {neighborhood_quality}, type: {type(neighborhood_quality)}, truthy: {bool(neighborhood_quality)}")
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
            print(f"[DEBUG] Prompt Builder: ✅ Added NEIGHBORHOOD QUALITY section with {len(quality_info)} items")
        else:
            print(f"[DEBUG] Prompt Builder: ⚠️ neighborhood_quality provided but all fields empty")
    else:
        print(f"[DEBUG] Prompt Builder: ❌ Skipped NEIGHBORHOOD QUALITY section (no data)")
    
    # Instructions Section
    prompt_parts.append("=== INSTRUCTIONS ===")
    prompt_parts.append("Generate a professional property listing with the following requirements:")
    prompt_parts.append("")
    prompt_parts.append("1. TITLE:")
    prompt_parts.append("   - Create a compelling, SEO-friendly title (max 100 characters)")
    prompt_parts.append(f"   - MUST include: {bedrooms}BR/{bathrooms_display}BA {property_type}")
    prompt_parts.append(f"   - Include square footage: {sqft:,} sqft")
    prompt_parts.append("   - Mention location ONLY if you have a valid neighborhood name (do NOT use placeholder words like 'What', 'Where', etc.)")
    prompt_parts.append("   - If neighborhood information is unclear or invalid, use the city/area from the address instead")
    prompt_parts.append("   - DO NOT include invalid words, placeholders, or garbage text in the title")
    prompt_parts.append("   - Use proper capitalization and professional language")
    if listing_type == "rent":
        prompt_parts.append("   - For rentals: Include 'For Rent' or 'Available for Rent' in title")
        prompt_parts.append(f"   - Example: 'Beautiful {bedrooms}BR/{bathrooms_display}BA {property_type} for Rent in Manhattan' or 'Modern {property_type} for Rent in New York, NY'")
    else:
        prompt_parts.append("   - For sales: Include 'For Sale' or focus on property type")
        prompt_parts.append(f"   - Example: 'Beautiful {bedrooms}BR/{bathrooms_display}BA {property_type} for Sale in Manhattan' or 'Charming {property_type} for Sale in New York, NY'")
    prompt_parts.append("")
    prompt_parts.append("2. DESCRIPTION:")
    prompt_parts.append("   - Write professional, engaging prose (2-4 paragraphs)")
    prompt_parts.append(f"   - MUST include property details: {bedrooms} bedrooms, {bathrooms_display} bathrooms, {sqft:,} sqft {property_type}")
    prompt_parts.append("   - Highlight key features from the property information and property features section")
    prompt_parts.append("   - Mention location benefits (neighborhood, landmarks, amenities) ONLY if the information is valid and meaningful")
    prompt_parts.append("   - Include neighborhood quality information (safety, crime rates, quality of life) if provided and valid")
    prompt_parts.append("   - DO NOT use placeholder words, invalid data, or garbage text (e.g., 'What', 'Where', etc.)")
    prompt_parts.append("   - If neighborhood/amenity data seems invalid, skip it and focus on the address and property features")
    prompt_parts.append("   - Use descriptive, appealing language")
    prompt_parts.append("   - DO NOT include price information in the description")
    prompt_parts.append("   - Make it SEO-friendly and suitable for real estate websites")
    prompt_parts.append("   - Only mention specific schools, parks, or amenities if they have valid, meaningful names")
    
    # Adapt description style based on listing type
    if listing_type == "rent":
        prompt_parts.append("   - RENTAL-SPECIFIC: Adapt language for rental listings:")
        prompt_parts.append("     * Use phrases like 'available for rent', 'perfect rental opportunity', 'ideal for renters'")
        prompt_parts.append("     * Emphasize lifestyle benefits, convenience, and move-in ready features")
        prompt_parts.append("     * Highlight transportation access, nearby conveniences, and rental-friendly amenities")
        prompt_parts.append("     * Mention lease terms if provided (e.g., '12-month lease available')")
        prompt_parts.append("     * Use present tense ('features', 'is located', 'offers')")
        prompt_parts.append("     * Focus on what makes it a great place to live NOW")
    else:  # sale
        prompt_parts.append("   - SALE-SPECIFIC: Adapt language for sale listings:")
        prompt_parts.append("     * Use phrases like 'for sale', 'investment opportunity', 'perfect home'")
        prompt_parts.append("     * Emphasize long-term value, equity potential, and ownership benefits")
        prompt_parts.append("     * Highlight schools, property taxes, HOA benefits (important for buyers)")
        prompt_parts.append("     * Mention neighborhood growth, investment potential, and property value")
        prompt_parts.append("     * Can use future-oriented language ('will appreciate', 'potential for growth')")
        prompt_parts.append("     * Focus on what makes it a great long-term investment")
    prompt_parts.append("")
    prompt_parts.append("3. PRICE_BLOCK:")
    prompt_parts.append("   - Price not provided - return empty string for price_block (price can be added later when posting)")
    prompt_parts.append("")
    prompt_parts.append("=== IMPORTANT GUIDELINES ===")
    prompt_parts.append("- Be factual and accurate - only use information provided")
    prompt_parts.append("- Do NOT invent or make up any details")
    prompt_parts.append("- Do NOT include price in the description (only in price_block)")
    prompt_parts.append("- Do NOT use placeholder words, invalid data, or garbage text (e.g., 'What', 'Where', 'This', 'That')")
    prompt_parts.append("- If enrichment data (neighborhood, amenities) contains invalid words or seems like garbage, IGNORE it")
    prompt_parts.append("- Focus on the address, property features from notes, and only valid enrichment data")
    prompt_parts.append("- Keep content professional and suitable for real estate websites")
    prompt_parts.append("- Ensure content is property listing-related only")
    prompt_parts.append("- Quality over quantity: Better to omit unclear information than to include garbage text")
    prompt_parts.append("")
    prompt_parts.append("=== OUTPUT FORMAT ===")
    prompt_parts.append("Return ONLY valid JSON with the following structure:")
    prompt_parts.append("{")
    prompt_parts.append('  "title": "Your generated title here",')
    prompt_parts.append('  "description": "Your generated description here",')
    prompt_parts.append('  "price_block": "Your formatted price block here"')
    prompt_parts.append("}")
    prompt_parts.append("")
    prompt_parts.append("Do not include any text before or after the JSON. Return only the JSON object.")
    
    return "\n".join(prompt_parts)

