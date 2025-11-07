"""
Output Formatting Utilities for Property Listing System - Iteration 1

This module provides utilities for formatting the final property listing output.
It handles:
- Price removal from description (safety net)
- Final listing formatting with proper structure
- Disclaimer addition
- Text cleaning and normalization
- Region-specific currency formatting
"""

import re
from typing import Optional, Dict, Any
from utils.region_config import get_region_config, get_currency_symbol

# Price-related patterns to remove from description (multi-currency support)
PRICE_REMOVAL_PATTERNS = [
    r'[\$£€]\d+[\d,]*',  # $500,000, £500,000, €500,000
    r'\d+[\d,]*\s*(dollars?|pounds?|euros?)',  # "500,000 dollars", "500,000 pounds"
    r'\d+[\d,]*\s*(usd|cad|gbp|aud|eur)',  # "500000 USD", "500000 GBP"
    r'price[:\s]+[\$£€]?\d+[\d,]*',  # "Price: $500,000" or "Price: £500,000"
    r'cost[:\s]+[\$£€]?\d+[\d,]*',  # "Cost: $500,000"
    r'asking[:\s]+[\$£€]?\d+[\d,]*',  # "Asking: $500,000"
    r'rent[:\s]+[\$£€]?\d+[\d,]*',  # "Rent: $2,500"
    r'\d+[\d,]*\s*per\s*month',  # "2500 per month"
    r'\d+[\d,]*\s*per\s*week',  # "500 per week"
    r'\d+[\d,]*\s*/\s*month',  # "2500/month"
    r'\d+[\d,]*\s*/\s*week',  # "500/week"
    r'[\$£€]?\d+[\d,]*\s*monthly',  # "$2,500 monthly" or "£2,500 monthly"
    r'[\$£€]?\d+[\d,]*\s*weekly',  # "$500 weekly"
]


def remove_price_from_description(description: str) -> str:
    """
    Remove price information from description text.
    
    This is a safety net - even though output guardrails should catch
    price in description, this ensures it's removed during formatting.
    
    Args:
        description: Description text that may contain price information
        
    Returns:
        Description with price information removed
    """
    if not description:
        return description
    
    cleaned_description = description
    
    # Remove price patterns with context (remove common phrases that include price)
    # Patterns that include price with common words before/after
    contextual_patterns = [
        r'\bcosts?\s+\$?\d+[\d,]*',  # "costs $500,000" or "cost $500"
        r'\bpriced?\s+at\s+\$?\d+[\d,]*',  # "priced at $500,000"
        r'\basking\s+\$?\d+[\d,]*',  # "asking $500,000"
        r'\brent\s+is\s+\$?\d+[\d,]*',  # "rent is $2,500"
        r'\bfor\s+\$?\d+[\d,]*',  # "for $500,000"
        r'\bonly\s+\$?\d+[\d,]*',  # "only $500,000"
    ]
    
    # Remove contextual patterns first (removes entire phrases)
    for pattern in contextual_patterns:
        cleaned_description = re.sub(
            pattern,
            '',
            cleaned_description,
            flags=re.IGNORECASE
        )
    
    # Then remove standalone price patterns
    for pattern in PRICE_REMOVAL_PATTERNS:
        cleaned_description = re.sub(
            pattern,
            '',
            cleaned_description,
            flags=re.IGNORECASE
        )
    
    # Clean up extra whitespace and punctuation artifacts
    # Remove multiple spaces
    cleaned_description = re.sub(r'\s+', ' ', cleaned_description)
    # Remove leading/trailing spaces
    cleaned_description = cleaned_description.strip()
    # Remove orphaned words/phrases (e.g., "This property costs and is" -> "This property is")
    cleaned_description = re.sub(r'\s+(costs?|priced?|asking|rent|for|only)\s+(and|or|,|\.)', r'\2', cleaned_description, flags=re.IGNORECASE)
    # Remove orphaned "and" or "or" at start of phrases (e.g., "and is located" -> "is located")
    cleaned_description = re.sub(r'\s+(and|or)\s+([a-z])', r' \2', cleaned_description, flags=re.IGNORECASE)
    # Remove orphaned "per month/week" phrases
    cleaned_description = re.sub(r'\s+per\s+(month|week)', '', cleaned_description, flags=re.IGNORECASE)
    # Remove orphaned punctuation (e.g., "This property ." -> "This property.")
    cleaned_description = re.sub(r'\s+([.,;:])', r'\1', cleaned_description)
    # Remove multiple periods
    cleaned_description = re.sub(r'\.{2,}', '.', cleaned_description)
    # Remove trailing "and" or "or" at sentence boundaries
    cleaned_description = re.sub(r'\s+(and|or)\s*([.,;:])', r'\2', cleaned_description, flags=re.IGNORECASE)
    # Final cleanup: remove multiple spaces again
    cleaned_description = re.sub(r'\s+', ' ', cleaned_description).strip()
    
    return cleaned_description


def clean_text(text: str) -> str:
    """
    Clean and normalize text for final output.
    
    Removes extra whitespace, normalizes line breaks, etc.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return text
    
    # Normalize line breaks (convert various line break types to single newline)
    text = re.sub(r'\r\n|\r', '\n', text)
    # Remove multiple consecutive newlines (max 2)
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove trailing whitespace from each line
    lines = [line.rstrip() for line in text.split('\n')]
    text = '\n'.join(lines)
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def format_listing(
    title: str,
    description: str,
    price_block: str,
    seller_price: Optional[float] = None,
    listing_type: Optional[str] = None,
    region: Optional[str] = "US",
    remove_price_from_desc: bool = True
) -> str:
    """
    Format final property listing with organized structure.
    
    Creates a well-formatted listing with organized sections:
    - Title: Generated listing title
    - Listing Details: Generated description
    - Seller Asking Price: Original price from user input
    - Predicted Price: Currently same as seller price (will be enhanced later)
    
    Args:
        title: Listing title
        description: Listing description
        price_block: Formatted price information (from LLM)
        seller_price: Original asking price from user (for Seller Asking Price section)
        remove_price_from_desc: If True, remove price from description (safety net)
        
    Returns:
        Formatted listing string ready for display with organized sections
    """
    # Get region configuration for currency formatting
    region = region.upper() if region else "US"
    config = get_region_config(region)
    currency_symbol = config["currency_symbol"]
    currency = config["currency"]
    
    # Clean inputs
    title = clean_text(title) if title else ""
    description = clean_text(description) if description else ""
    price_block = clean_text(price_block) if price_block else ""
    
    # Remove price from description if requested (safety net)
    if remove_price_from_desc:
        description = remove_price_from_description(description)
        description = clean_text(description)  # Re-clean after price removal
    
    # Build formatted listing with organized sections
    parts = []
    
    # Title section
    if title:
        parts.append("**Title:**")
        parts.append(title)
        parts.append("")  # Empty line after title
    
    # Listing Details section
    if description:
        parts.append("**Listing Details:**")
        parts.append(description)
        parts.append("")  # Empty line after description
    
    # Price section (label changes based on listing type, currency based on region)
    if seller_price is not None:
        # Use appropriate label based on listing type
        if listing_type and listing_type.lower() == "rent":
            price_label = "**Monthly Rent:**"
        else:
            price_label = "**Seller Asking Price:**"
        
        parts.append(price_label)
        parts.append(f"{currency_symbol}{seller_price:,.2f} ({currency})")
        
        # Extract additional pricing details from price_block (HOA fees, taxes, deposit, etc.)
        # These are already in price_block but we want to show them as sub-items with bullet points
        additional_details = []
        if price_block and price_block.strip():
            # Look for additional details in price_block (lines that don't contain the main price)
            price_block_lines = price_block.split('\n')
            for line in price_block_lines:
                line = line.strip()
                if not line:
                    continue
                # Skip if this line is just the main price
                if seller_price is not None:
                    # Check if line contains just the price (with or without currency symbol and formatting)
                    price_str = f"{currency_symbol}{seller_price:,.2f}"
                    price_str_no_comma = f"{currency_symbol}{seller_price:.2f}"
                    price_str_usd = f"${seller_price:,.2f}"  # Also check USD format
                    price_str_usd_no_comma = f"${seller_price:.2f}"
                    if (line == price_str or line == price_str_no_comma or 
                        line == price_str_usd or line == price_str_usd_no_comma or 
                        line == str(int(seller_price))):
                        continue
                    # Check if line starts with price (like "$234,560.00 HOA Fees..." or "£234,560.00 HOA Fees...")
                    if (line.startswith(price_str) or line.startswith(price_str_no_comma) or
                        line.startswith(price_str_usd) or line.startswith(price_str_usd_no_comma)):
                        # Extract the part after the price
                        remaining = (line.replace(price_str, "")
                                    .replace(price_str_no_comma, "")
                                    .replace(price_str_usd, "")
                                    .replace(price_str_usd_no_comma, "")
                                    .strip())
                        if remaining:
                            additional_details.append(remaining)
                        continue
                # If line contains keywords for additional details, include it
                # Keywords for sales: HOA, taxes
                # Keywords for rentals: security deposit, lease, billing cycle
                rental_keywords = ["security deposit", "deposit", "lease", "billing cycle", "lease term", "term"]
                sale_keywords = ["hoa", "tax", "property tax", "taxes"]
                common_keywords = ["fee", "fees", "month", "year", "weekly", "monthly"]
                
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in rental_keywords + sale_keywords + common_keywords):
                    additional_details.append(line)
        
        # Add additional details as sub-items with bullet points
        if additional_details:
            for detail in additional_details:
                parts.append(f"  * {detail}")
        
        parts.append("")  # Empty line after seller price section
    
    # Predicted Price section (for now, same as seller price)
    # TODO: In future iterations, this will be calculated by price analysis model
    if seller_price is not None:
        parts.append("**Predicted Price:**")
        predicted_price = seller_price  # For now, use seller price as predicted
        parts.append(f"{currency_symbol}{predicted_price:,.2f} ({currency})")
        parts.append("")  # Empty line after predicted price
    
    # Join all parts with newlines
    formatted_listing = "\n".join(parts)
    
    # Final cleanup
    formatted_listing = clean_text(formatted_listing)
    
    return formatted_listing


def extract_and_format_output(llm_parsed: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract and format output fields from LLM parsed JSON.
    
    This function:
    1. Extracts title, description, price_block from llm_parsed
    2. Removes price from description (safety net)
    3. Cleans and normalizes all fields
    4. Returns formatted fields ready for state
    
    Args:
        llm_parsed: Parsed JSON dictionary from LLM
        
    Returns:
        Dictionary with formatted fields:
        {
            "title": str,
            "description": str,  # Price removed
            "price_block": str
        }
    """
    if not llm_parsed:
        return {
            "title": "",
            "description": "",
            "price_block": ""
        }
    
    # Extract fields
    title = llm_parsed.get("title", "")
    description = llm_parsed.get("description", "")
    price_block = llm_parsed.get("price_block", "")
    
    # Clean and format
    title = clean_text(title) if title else ""
    description = remove_price_from_description(description) if description else ""
    description = clean_text(description) if description else ""
    price_block = clean_text(price_block) if price_block else ""
    
    return {
        "title": title,
        "description": description,
        "price_block": price_block
    }

