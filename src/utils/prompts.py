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
    
    # Instructions Section - Rewritten for better quality and clarity
    prompt_parts.append("=== YOUR TASK ===")
    prompt_parts.append("Create a compelling, professional property listing that will attract qualified buyers/renters.")
    prompt_parts.append("Write with enthusiasm and precision, making the property sound desirable while remaining factual.")
    prompt_parts.append("")
    
    prompt_parts.append("=== WRITING STYLE ===")
    prompt_parts.append("• Use vivid, descriptive language that paints a picture")
    prompt_parts.append("• Write in an active, engaging voice (avoid passive constructions)")
    prompt_parts.append("• Use power words: 'spacious', 'stunning', 'pristine', 'luxurious', 'charming', 'modern', 'bright'")
    prompt_parts.append("• Create emotional appeal while staying truthful to the facts")
    prompt_parts.append("• Vary sentence length for rhythm and readability")
    prompt_parts.append("• Use specific details rather than generic statements")
    prompt_parts.append("")
    
    prompt_parts.append("=== 1. TITLE (Max 100 characters) ===")
    prompt_parts.append("Create a compelling, SEO-optimized title that captures attention.")
    prompt_parts.append("")
    prompt_parts.append("REQUIRED ELEMENTS:")
    prompt_parts.append(f"  ✓ {bedrooms}BR/{bathrooms_display}BA {property_type}")
    prompt_parts.append(f"  ✓ {sqft:,} sqft")
    prompt_parts.append("  ✓ Location (use neighborhood if valid, otherwise city/area from address)")
    prompt_parts.append("  ✓ Listing type indicator")
    prompt_parts.append("")
    prompt_parts.append("TITLE EXAMPLES:")
    if listing_type == "rent":
        prompt_parts.append(f"  • 'Stunning {bedrooms}BR/{bathrooms_display}BA {property_type} for Rent - {sqft:,} sqft in [Location]'")
        prompt_parts.append(f"  • 'Modern {bedrooms}BR/{bathrooms_display}BA {property_type} Available for Rent - {sqft:,} sqft'")
        prompt_parts.append(f"  • 'Bright & Spacious {bedrooms}BR/{bathrooms_display}BA {property_type} for Rent in [Location]'")
    else:
        prompt_parts.append(f"  • 'Beautiful {bedrooms}BR/{bathrooms_display}BA {property_type} for Sale - {sqft:,} sqft in [Location]'")
        prompt_parts.append(f"  • 'Charming {bedrooms}BR/{bathrooms_display}BA {property_type} - {sqft:,} sqft in [Location]'")
        prompt_parts.append(f"  • 'Stunning {bedrooms}BR/{bathrooms_display}BA {property_type} for Sale - {sqft:,} sqft'")
    prompt_parts.append("")
    prompt_parts.append("QUALITY CHECK:")
    prompt_parts.append("  • Only use valid location names (skip if neighborhood data seems invalid)")
    prompt_parts.append("  • Use Title Case for proper nouns")
    prompt_parts.append("  • Make it scannable and keyword-rich for search")
    prompt_parts.append("")
    
    prompt_parts.append("=== 2. DESCRIPTION (2-4 paragraphs, 150-300 words) ===")
    prompt_parts.append("Write engaging, persuasive prose that makes readers want to see this property.")
    prompt_parts.append("")
    prompt_parts.append("STRUCTURE:")
    prompt_parts.append("  PARAGRAPH 1 - Opening Hook:")
    prompt_parts.append(f"    • Start with an attention-grabbing statement about the {property_type}")
    prompt_parts.append(f"    • Include key specs: {bedrooms} bedrooms, {bathrooms_display} bathrooms, {sqft:,} sqft")
    prompt_parts.append("    • Mention the location and what makes it special")
    prompt_parts.append("    • Set the tone (e.g., 'Discover your perfect home...', 'Welcome to...')")
    prompt_parts.append("")
    prompt_parts.append("  PARAGRAPH 2 - Property Features:")
    prompt_parts.append("    • Describe the interior spaces with vivid detail")
    prompt_parts.append("    • Highlight features from the Property Features section")
    prompt_parts.append("    • Use sensory language (bright, spacious, airy, cozy, elegant)")
    prompt_parts.append("    • Mention layout, natural light, finishes, or unique characteristics")
    prompt_parts.append("")
    prompt_parts.append("  PARAGRAPH 3 - Location & Lifestyle:")
    prompt_parts.append("    • Describe the neighborhood and what makes it desirable")
    prompt_parts.append("    • Mention nearby amenities (schools, parks, shopping, transit) - ONLY if valid")
    prompt_parts.append("    • Include neighborhood quality info if provided and meaningful")
    prompt_parts.append("    • Connect location benefits to lifestyle (e.g., 'perfect for families', 'urban convenience')")
    prompt_parts.append("")
    prompt_parts.append("  PARAGRAPH 4 - Call to Action (Optional):")
    if listing_type == "rent":
        prompt_parts.append("    • Emphasize move-in readiness and rental benefits")
        prompt_parts.append("    • Create urgency (e.g., 'Don't miss this opportunity')")
    else:
        prompt_parts.append("    • Emphasize investment potential or long-term value")
        prompt_parts.append("    • Create urgency (e.g., 'Schedule your showing today')")
    prompt_parts.append("")
    
    if listing_type == "rent":
        prompt_parts.append("RENTAL-SPECIFIC LANGUAGE:")
        prompt_parts.append("  • Use present tense: 'features', 'offers', 'includes', 'is located'")
        prompt_parts.append("  • Emphasize: move-in ready, convenience, lifestyle, flexibility")
        prompt_parts.append("  • Phrases: 'perfect rental opportunity', 'ideal for renters', 'available now'")
        prompt_parts.append("  • Focus on: what makes it great to live here NOW")
    else:
        prompt_parts.append("SALE-SPECIFIC LANGUAGE:")
        prompt_parts.append("  • Emphasize: investment value, equity potential, long-term benefits")
        prompt_parts.append("  • Phrases: 'investment opportunity', 'perfect home', 'build equity'")
        prompt_parts.append("  • Focus on: what makes it a smart long-term investment")
        prompt_parts.append("  • Can mention: neighborhood growth, property value appreciation")
    prompt_parts.append("")
    
    prompt_parts.append("DESCRIPTION QUALITY CHECK:")
    prompt_parts.append("  ✓ Only use valid, meaningful location/amenity data (skip invalid entries)")
    prompt_parts.append("  ✓ Be specific and concrete (avoid vague statements)")
    prompt_parts.append("  ✓ Create emotional connection while staying factual")
    prompt_parts.append("  ✓ Do NOT include price information (price goes in price_block only)")
    prompt_parts.append("  ✓ Make it scannable with varied sentence structure")
    prompt_parts.append("")
    
    prompt_parts.append("=== 3. PRICE_BLOCK ===")
    prompt_parts.append("Price not provided - return empty string: \"\"")
    prompt_parts.append("(Price can be added later when posting the listing)")
    prompt_parts.append("")
    
    prompt_parts.append("=== CRITICAL RULES ===")
    prompt_parts.append("✓ ONLY use information provided in the sections above")
    prompt_parts.append("✓ Do NOT invent, fabricate, or assume any details")
    prompt_parts.append("✓ If enrichment data (neighborhood, amenities) seems invalid or unclear, omit it")
    prompt_parts.append("✓ Focus on property features from notes and valid location data")
    prompt_parts.append("✓ Quality over quantity - better to omit unclear info than include garbage text")
    prompt_parts.append("✓ Keep content professional and suitable for real estate websites")
    prompt_parts.append("")
    prompt_parts.append("=== OUTPUT FORMAT ===")
    prompt_parts.append("Return ONLY valid JSON (no markdown, no code blocks, no extra text):")
    prompt_parts.append("")
    prompt_parts.append("{")
    prompt_parts.append('  "title": "Your compelling title here",')
    prompt_parts.append('  "description": "Your engaging description here (2-4 paragraphs)",')
    prompt_parts.append('  "price_block": ""')
    prompt_parts.append("}")
    prompt_parts.append("")
    prompt_parts.append("IMPORTANT: Return ONLY the JSON object. No explanations, no markdown formatting, no code blocks.")
    
    return "\n".join(prompt_parts)

