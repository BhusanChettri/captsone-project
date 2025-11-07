"""
Prompt Templates for Property Listing System - Iteration 1

This module contains prompt templates for LLM content generation.
The prompts are designed to generate structured JSON output with
title, description, and price_block fields.
"""

from typing import Optional, Dict, Any, List


def build_listing_generation_prompt(
    address: str,
    listing_type: str,
    price: float,
    notes: Optional[str] = None,
    normalized_address: Optional[str] = None,
    normalized_notes: Optional[str] = None,
    zip_code: Optional[str] = None,
    neighborhood: Optional[str] = None,
    landmarks: Optional[List[str]] = None,
    key_amenities: Optional[Dict[str, List[str]]] = None,
    billing_cycle: Optional[str] = None,
    lease_term: Optional[str] = None,
    security_deposit: Optional[float] = None,
    hoa_fees: Optional[float] = None,
    property_taxes: Optional[float] = None,
) -> str:
    """
    Build a comprehensive prompt for LLM to generate property listing content.
    
    This prompt merges all available data (input, normalized, enriched) to create
    a complete context for the LLM to generate professional listing content.
    
    Args:
        address: Property address
        listing_type: "sale" or "rent"
        price: Asking price in USD
        notes: Free-text notes with key features
        normalized_address: Cleaned/normalized address
        normalized_notes: Cleaned/normalized notes
        zip_code: ZIP code from enrichment
        neighborhood: Neighborhood name from enrichment
        landmarks: List of nearby landmarks
        key_amenities: Dictionary of amenities by category
        billing_cycle: Rental billing cycle (rental only)
        lease_term: Lease duration (rental only)
        security_deposit: Security deposit amount (rental only)
        hoa_fees: HOA fees (sale only)
        property_taxes: Annual property taxes (sale only)
        
    Returns:
        Complete prompt string for LLM
    """
    # Use normalized data if available, otherwise fall back to original
    final_address = normalized_address or address
    final_notes = normalized_notes or notes or ""
    
    # Build prompt sections
    prompt_parts = []
    
    # Header
    prompt_parts.append("You are a professional real estate listing writer. Generate a property listing based on the following information.")
    prompt_parts.append("")
    
    # Property Information Section
    prompt_parts.append("=== PROPERTY INFORMATION ===")
    prompt_parts.append(f"Address: {final_address}")
    prompt_parts.append(f"Listing Type: {listing_type.upper()}")
    prompt_parts.append(f"Asking Price: ${price:,.2f}")
    
    if listing_type == "rent":
        if billing_cycle:
            prompt_parts.append(f"Billing Cycle: {billing_cycle}")
        if lease_term:
            prompt_parts.append(f"Lease Term: {lease_term}")
        if security_deposit is not None:
            prompt_parts.append(f"Security Deposit: ${security_deposit:,.2f}")
    elif listing_type == "sale":
        if hoa_fees is not None:
            prompt_parts.append(f"HOA Fees: ${hoa_fees:,.2f}")
        if property_taxes is not None:
            prompt_parts.append(f"Annual Property Taxes: ${property_taxes:,.2f}")
    
    prompt_parts.append("")
    
    # Property Features Section
    if final_notes:
        prompt_parts.append("=== PROPERTY FEATURES ===")
        prompt_parts.append(final_notes)
        prompt_parts.append("")
    
    # Location & Neighborhood Section
    location_info = []
    if zip_code:
        location_info.append(f"ZIP Code: {zip_code}")
    if neighborhood:
        location_info.append(f"Neighborhood: {neighborhood}")
    
    if location_info:
        prompt_parts.append("=== LOCATION & NEIGHBORHOOD ===")
        prompt_parts.append("\n".join(location_info))
        prompt_parts.append("")
    
    # Nearby Landmarks Section
    if landmarks:
        prompt_parts.append("=== NEARBY LANDMARKS ===")
        for landmark in landmarks:
            prompt_parts.append(f"- {landmark}")
        prompt_parts.append("")
    
    # Key Amenities Section
    if key_amenities:
        prompt_parts.append("=== KEY AMENITIES ===")
        for category, items in key_amenities.items():
            if items:
                category_name = category.capitalize()
                prompt_parts.append(f"{category_name}:")
                for item in items:
                    prompt_parts.append(f"  - {item}")
        prompt_parts.append("")
    
    # Instructions Section
    prompt_parts.append("=== INSTRUCTIONS ===")
    prompt_parts.append("Generate a professional property listing with the following requirements:")
    prompt_parts.append("")
    prompt_parts.append("1. TITLE:")
    prompt_parts.append("   - Create a compelling, SEO-friendly title (max 100 characters)")
    prompt_parts.append("   - Include key features (bedrooms, bathrooms, square footage if mentioned)")
    prompt_parts.append("   - Mention location/neighborhood if available")
    prompt_parts.append("   - Example: 'Beautiful 3BR/2BA Home in Downtown Manhattan'")
    prompt_parts.append("")
    prompt_parts.append("2. DESCRIPTION:")
    prompt_parts.append("   - Write professional, engaging prose (2-4 paragraphs)")
    prompt_parts.append("   - Highlight key features from the property information")
    prompt_parts.append("   - Mention location benefits (neighborhood, landmarks, amenities)")
    prompt_parts.append("   - Use descriptive, appealing language")
    prompt_parts.append("   - DO NOT include price information in the description")
    prompt_parts.append("   - Make it SEO-friendly and suitable for real estate websites")
    prompt_parts.append("")
    prompt_parts.append("3. PRICE_BLOCK:")
    if listing_type == "rent":
        prompt_parts.append("   - Format as: '$X,XXX/month' or '$X,XXX/week' (based on billing_cycle)")
        if security_deposit is not None:
            prompt_parts.append(f"   - Include security deposit if provided: 'Security Deposit: ${security_deposit:,.2f}'")
    else:
        prompt_parts.append("   - Format as: '$X,XXX,XXX'")
        if hoa_fees is not None:
            prompt_parts.append(f"   - Include HOA fees if provided: 'HOA Fees: ${hoa_fees:,.2f}/month'")
        if property_taxes is not None:
            prompt_parts.append(f"   - Include property taxes if provided: 'Property Taxes: ${property_taxes:,.2f}/year'")
    prompt_parts.append("")
    prompt_parts.append("=== IMPORTANT GUIDELINES ===")
    prompt_parts.append("- Be factual and accurate - only use information provided")
    prompt_parts.append("- Do NOT invent or make up any details")
    prompt_parts.append("- Do NOT include price in the description (only in price_block)")
    prompt_parts.append("- Keep content professional and suitable for real estate websites")
    prompt_parts.append("- Ensure content is property listing-related only")
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

