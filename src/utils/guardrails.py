"""
Guardrail Utilities for Input and Output Validation

This module provides rule-based guardrail functions for:
- Input safety checks (malicious content, injection attacks, inappropriate content)
- Output safety checks (LLM output validation)
- Content moderation (keyword-based filtering)

Note: This is iteration 1 - rule-based approach. Future iterations may add
LLM-based checks for more nuanced content moderation.
"""

import re
from typing import List, Tuple, Optional, Dict, Any


# ============================================================================
# Configuration Constants
# ============================================================================

# Text length limits
MAX_ADDRESS_LENGTH = 500
MAX_NOTES_LENGTH = 2000

# Property-related keywords (for validation)
# Includes full words and common abbreviations
PROPERTY_KEYWORDS = [
    "address", "property", "house", "home", "apartment", "condo", "rent", "rental",
    "sale", "sell", "buy", "bedroom", "bathroom", "bed", "bath", "sqft", "square feet",
    "price", "cost", "listing", "real estate", "agent", "landlord", "tenant",
    "lease", "deposit", "security", "hoa", "tax", "amenities", "parking", "garage",
    "kitchen", "bathroom", "bedroom", "living room", "yard", "garden", "pool",
    "furnished", "unfurnished", "pet", "dog", "cat", "utilities", "included",
    # Property types and building terms
    "residency", "residence", "tower", "building", "complex", "villa", "townhouse",
    "studio", "loft", "penthouse", "duplex", "mansion", "estate", "flat", "unit",
    # Location indicators (common in property addresses)
    "street", "st", "avenue", "ave", "road", "rd", "boulevard", "blvd", "drive", "dr",
    "lane", "ln", "way", "court", "ct", "place", "pl", "circle", "cir",
    "bay", "beach", "park", "hills", "valley", "creek", "river", "lake",
    # Common abbreviations
    "br", "ba", "bd", "bath", "bed", "sq", "ft", "$"
]

# Inappropriate content keywords (basic list - can be expanded)
INAPPROPRIATE_KEYWORDS = [
    # Explicit sexual content (basic list)
    "explicit", "porn", "xxx", "nsfw",
    # Hate speech indicators (basic list)
    "hate", "racist", "discrimination",
    # Dangerous/violent content
    "violence", "threat", "kill", "harm", "attack",
    # Spam/scam indicators
    "scam", "fraud", "phishing", "spam",
]

# Injection attack patterns
INJECTION_PATTERNS = [
    # SQL injection patterns
    r"(?i)(union\s+select|drop\s+table|insert\s+into|delete\s+from|update\s+set)",
    r"(?i)(or\s+1\s*=\s*1|or\s+'1'\s*=\s*'1')",
    r"(?i)(;.*--|;.*#|/\*.*\*/)",
    # Script injection patterns
    r"(?i)(<script|</script>|javascript:|onerror=|onclick=)",
    r"(?i)(eval\(|exec\(|system\(|shell_exec\()",
    # Command injection patterns
    r"(?i)(\|\s*cat|\|\s*ls|\|\s*rm|\|\s*sh|\|\s*bash)",
    r"(?i)(&&\s*cat|&&\s*ls|&&\s*rm|&&\s*sh|&&\s*bash)",
]


# ============================================================================
# Text Length Validation
# ============================================================================

def validate_text_length(text: str, max_length: int, field_name: str) -> Optional[str]:
    """
    Validate text length.
    
    Args:
        text: Text to validate
        max_length: Maximum allowed length
        field_name: Name of the field (for error messages)
        
    Returns:
        Error message if validation fails, None otherwise
    """
    if not text:
        return None  # Empty text is handled by required field validation
    
    if len(text) > max_length:
        return f"{field_name} exceeds maximum length of {max_length} characters (got {len(text)})"
    
    return None


# ============================================================================
# Injection Attack Detection
# ============================================================================

def detect_injection_attacks(text: str) -> Optional[str]:
    """
    Detect potential injection attacks (SQL, script, command injection).
    
    Args:
        text: Text to check
        
    Returns:
        Error message if injection pattern detected, None otherwise
    """
    if not text:
        return None
    
    text_lower = text.lower()
    
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text_lower):
            return f"Potential injection attack detected in input"
    
    return None


# ============================================================================
# Inappropriate Content Detection
# ============================================================================

def detect_inappropriate_content(text: str) -> Optional[str]:
    """
    Detect inappropriate content using keyword-based filtering.
    
    This is a basic rule-based approach. Future iterations may use
    LLM-based checks for more nuanced detection.
    
    Args:
        text: Text to check
        
    Returns:
        Error message if inappropriate content detected, None otherwise
    """
    if not text:
        return None
    
    text_lower = text.lower()
    
    # Check for inappropriate keywords
    for keyword in INAPPROPRIATE_KEYWORDS:
        if keyword in text_lower:
            return f"Inappropriate content detected in input"
    
    return None


# ============================================================================
# Property-Related Validation
# ============================================================================

def validate_property_related(text: str, min_keywords: int = 1) -> Optional[str]:
    """
    Validate that input is property-related by checking for property keywords.
    
    This ensures users are submitting property listing information,
    not random or off-topic content.
    
    Uses multiple heuristics:
    1. Property-related keywords
    2. Address-like patterns (contains location terms, numbers, etc.)
    3. Property-related context
    
    Args:
        text: Text to validate
        min_keywords: Minimum number of property keywords required
        
    Returns:
        Error message if not property-related, None otherwise
    """
    if not text or not text.strip():
        # Empty text should fail property validation
        return f"Input does not appear to be property-related. Please provide property listing information."
    
    text_lower = text.lower()
    
    # Count property-related keywords found
    # Use word boundaries for better matching (handle abbreviations like "3br", "2ba")
    keyword_count = 0
    for keyword in PROPERTY_KEYWORDS:
        # For short keywords (1-2 chars), check if they appear as part of property-related patterns
        if len(keyword) <= 2:
            # Check for patterns like "3br", "2ba", "$500", etc.
            if keyword == "$":
                # Special handling for dollar sign
                if "$" in text_lower:
                    keyword_count += 1
            else:
                # Check for patterns like "3br", "2ba" (number + abbreviation)
                pattern = r'\d+' + re.escape(keyword) + r'\b'
                if re.search(pattern, text_lower, re.IGNORECASE):
                    keyword_count += 1
        else:
            # For longer keywords, check if they appear in text (word boundary aware)
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text_lower, re.IGNORECASE):
                keyword_count += 1
    
    # Additional heuristics: If text looks like an address (contains location terms, commas, etc.)
    # and has some structure, consider it property-related even without explicit keywords
    looks_like_address = False
    if keyword_count == 0:
        # Check if it has address-like characteristics:
        # - Contains commas (typical of addresses: "street, city, state")
        # - Contains location-related terms (bay, street, avenue, etc.)
        # - Has some structure (multiple words)
        has_commas = ',' in text
        has_location_terms = any(term in text_lower for term in [
            'street', 'st', 'avenue', 'ave', 'road', 'rd', 'boulevard', 'blvd',
            'drive', 'dr', 'lane', 'ln', 'way', 'court', 'ct', 'place', 'pl',
            'bay', 'beach', 'park', 'hills', 'valley', 'creek', 'residency',
            'residence', 'tower', 'building', 'complex', 'villa'
        ])
        has_multiple_words = len(text.split()) >= 2
        
        if (has_commas or has_location_terms) and has_multiple_words:
            looks_like_address = True
            keyword_count = 1  # Treat as property-related
    
    if keyword_count < min_keywords:
        return f"Input does not appear to be property-related. Please provide property listing information."
    
    return None


# ============================================================================
# Comprehensive Input Guardrail Check
# ============================================================================

def check_input_guardrails(
    address: str,
    notes: str,
    strict_property_validation: bool = True
) -> List[str]:
    """
    Perform comprehensive input guardrail checks.
    
    This function runs all guardrail checks and returns a list of errors.
    If the list is empty, all checks passed.
    
    Args:
        address: Property address
        notes: Property notes/description
        strict_property_validation: If True, requires property keywords in input
        
    Returns:
        List of error messages (empty if all checks pass)
    """
    errors: List[str] = []
    
    # Check address length
    address_error = validate_text_length(address, MAX_ADDRESS_LENGTH, "Address")
    if address_error:
        errors.append(address_error)
    
    # Check notes length
    notes_error = validate_text_length(notes, MAX_NOTES_LENGTH, "Notes")
    if notes_error:
        errors.append(notes_error)
    
    # Check for injection attacks in address
    injection_error = detect_injection_attacks(address)
    if injection_error:
        errors.append(f"Address: {injection_error}")
    
    # Check for injection attacks in notes
    injection_error = detect_injection_attacks(notes)
    if injection_error:
        errors.append(f"Notes: {injection_error}")
    
    # Check for inappropriate content in address
    inappropriate_error = detect_inappropriate_content(address)
    if inappropriate_error:
        errors.append(f"Address: {inappropriate_error}")
    
    # Check for inappropriate content in notes
    inappropriate_error = detect_inappropriate_content(notes)
    if inappropriate_error:
        errors.append(f"Notes: {inappropriate_error}")
    
    # Validate property-related content (combine address and notes)
    if strict_property_validation:
        combined_text = f"{address} {notes}"
        property_error = validate_property_related(combined_text, min_keywords=1)
        if property_error:
            errors.append(property_error)
    
    return errors


# ============================================================================
# Output Guardrail Functions (LLM Output Validation)
# ============================================================================

# Output length limits
MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 2000
MAX_PRICE_BLOCK_LENGTH = 100

# Price-related keywords that should NOT appear in description
PRICE_KEYWORDS_IN_DESCRIPTION = [
    r'\$\d+',  # Dollar amounts like $500,000
    r'\d+\s*dollars?',  # "500 dollars"
    r'\d+\s*usd',  # "500 USD"
    r'price[:\s]+\$?\d+',  # "Price: $500"
    r'cost[:\s]+\$?\d+',  # "Cost: $500"
    r'asking[:\s]+\$?\d+',  # "Asking: $500"
    r'rent[:\s]+\$?\d+',  # "Rent: $500" (in description, should be in price_block)
    r'\d+\s*per\s*month',  # "2500 per month"
    r'\d+\s*per\s*week',  # "500 per week"
    r'\d+\s*/\s*month',  # "2500/month"
    r'\d+\s*/\s*week',  # "500/week"
]


def validate_output_structure(llm_parsed: Dict[str, Any]) -> Optional[str]:
    """
    Validate that LLM output has the required structure.
    
    Args:
        llm_parsed: Parsed JSON dictionary from LLM
        
    Returns:
        Error message if structure is invalid, None otherwise
    """
    if not llm_parsed:
        return "LLM output is empty or invalid"
    
    if not isinstance(llm_parsed, dict):
        return "LLM output is not a valid JSON object"
    
    # Check required fields
    required_fields = ["title", "description", "price_block"]
    missing_fields = [field for field in required_fields if field not in llm_parsed]
    
    if missing_fields:
        return f"LLM output missing required fields: {', '.join(missing_fields)}"
    
    # Check field types
    if not isinstance(llm_parsed.get("title"), str):
        return "LLM output 'title' must be a string"
    
    if not isinstance(llm_parsed.get("description"), str):
        return "LLM output 'description' must be a string"
    
    if not isinstance(llm_parsed.get("price_block"), str):
        return "LLM output 'price_block' must be a string"
    
    # Check fields are not empty
    if not llm_parsed.get("title", "").strip():
        return "LLM output 'title' cannot be empty"
    
    if not llm_parsed.get("description", "").strip():
        return "LLM output 'description' cannot be empty"
    
    if not llm_parsed.get("price_block", "").strip():
        return "LLM output 'price_block' cannot be empty"
    
    return None


def validate_output_lengths(llm_parsed: Dict[str, Any]) -> List[str]:
    """
    Validate output field lengths.
    
    Args:
        llm_parsed: Parsed JSON dictionary from LLM
        
    Returns:
        List of error messages (empty if all valid)
    """
    errors: List[str] = []
    
    title = llm_parsed.get("title", "")
    description = llm_parsed.get("description", "")
    price_block = llm_parsed.get("price_block", "")
    
    if len(title) > MAX_TITLE_LENGTH:
        errors.append(f"Title exceeds maximum length of {MAX_TITLE_LENGTH} characters (got {len(title)})")
    
    if len(description) > MAX_DESCRIPTION_LENGTH:
        errors.append(f"Description exceeds maximum length of {MAX_DESCRIPTION_LENGTH} characters (got {len(description)})")
    
    if len(price_block) > MAX_PRICE_BLOCK_LENGTH:
        errors.append(f"Price block exceeds maximum length of {MAX_PRICE_BLOCK_LENGTH} characters (got {len(price_block)})")
    
    return errors


def detect_price_in_description(description: str) -> Optional[str]:
    """
    Detect if price information appears in description (should only be in price_block).
    
    Args:
        description: Description text to check
        
    Returns:
        Error message if price detected in description, None otherwise
    """
    if not description:
        return None
    
    description_lower = description.lower()
    
    # Check for price-related patterns
    for pattern in PRICE_KEYWORDS_IN_DESCRIPTION:
        if re.search(pattern, description_lower, re.IGNORECASE):
            return "Price information should not appear in description (it should only be in price_block)"
    
    return None


def validate_output_property_related(llm_parsed: Dict[str, Any]) -> List[str]:
    """
    Validate that LLM output is property listing-related.
    
    Checks title and description to ensure they're about property listings,
    not off-topic content.
    
    Args:
        llm_parsed: Parsed JSON dictionary from LLM
        
    Returns:
        List of error messages (empty if all valid)
    """
    errors: List[str] = []
    
    title = llm_parsed.get("title", "")
    description = llm_parsed.get("description", "")
    
    # Check title is property-related
    if title:
        title_error = validate_property_related(title, min_keywords=1)
        if title_error:
            errors.append(f"Title: {title_error}")
    
    # Check description is property-related
    if description:
        # For description, require at least 2 keywords (more lenient since it's longer)
        desc_error = validate_property_related(description, min_keywords=2)
        if desc_error:
            errors.append(f"Description: {desc_error}")
    
    return errors


def detect_inappropriate_output(llm_parsed: Dict[str, Any]) -> List[str]:
    """
    Detect inappropriate content in LLM output.
    
    Checks all text fields (title, description) for inappropriate content.
    
    Args:
        llm_parsed: Parsed JSON dictionary from LLM
        
    Returns:
        List of error messages (empty if all valid)
    """
    errors: List[str] = []
    
    title = llm_parsed.get("title", "")
    description = llm_parsed.get("description", "")
    
    # Check title for inappropriate content
    if title:
        inappropriate_error = detect_inappropriate_content(title)
        if inappropriate_error:
            errors.append(f"Title: {inappropriate_error}")
    
    # Check description for inappropriate content
    if description:
        inappropriate_error = detect_inappropriate_content(description)
        if inappropriate_error:
            errors.append(f"Description: {inappropriate_error}")
    
    return errors


def detect_injection_in_output(llm_parsed: Dict[str, Any]) -> List[str]:
    """
    Detect injection attacks in LLM output (safety check).
    
    Args:
        llm_parsed: Parsed JSON dictionary from LLM
        
    Returns:
        List of error messages (empty if all valid)
    """
    errors: List[str] = []
    
    title = llm_parsed.get("title", "")
    description = llm_parsed.get("description", "")
    price_block = llm_parsed.get("price_block", "")
    
    # Check all fields for injection patterns
    for field_name, field_value in [("title", title), ("description", description), ("price_block", price_block)]:
        if field_value:
            injection_error = detect_injection_attacks(field_value)
            if injection_error:
                errors.append(f"{field_name.capitalize()}: {injection_error}")
    
    return errors


def validate_output_compliance(
    llm_parsed: Dict[str, Any],
    original_price: Optional[float],
    listing_type: Optional[str]
) -> List[str]:
    """
    Validate compliance: ensure LLM didn't invent pricing or facts.
    
    Basic checks:
    - Price in price_block should match or be close to original price
    - No invented pricing information
    - Content should be factual (basic check)
    
    Args:
        llm_parsed: Parsed JSON dictionary from LLM
        original_price: Original price from input (for validation)
        listing_type: Original listing type (for validation)
        
    Returns:
        List of error messages (empty if all valid)
    """
    errors: List[str] = []
    
    price_block = llm_parsed.get("price_block", "")
    
    # If we have original price, check if price_block contains reasonable price
    if original_price is not None and price_block:
        # Extract numeric price from price_block (basic check)
        # Look for dollar amounts like $500,000 or $2,500/month
        price_patterns = [
            r'\$[\d,]+',  # $500,000 or $2,500
            r'\d+[\d,]*',  # 500000 or 2,500
        ]
        
        found_price = None
        for pattern in price_patterns:
            matches = re.findall(pattern, price_block)
            if matches:
                # Extract first match and clean it
                price_str = matches[0].replace('$', '').replace(',', '')
                try:
                    found_price = float(price_str)
                    break
                except ValueError:
                    continue
        
        # If we found a price, check if it's reasonable (within 10% of original)
        # This is a basic check - more sophisticated validation could be added
        if found_price is not None:
            # For monthly rent, original_price might be monthly, so check accordingly
            # For sale, original_price is total price
            if listing_type == "rent":
                # For rent, price_block might show monthly rent
                # Allow some flexibility (within 20% for rent)
                if abs(found_price - original_price) / original_price > 0.2:
                    errors.append("Price in price_block does not match original price (rental)")
            else:
                # For sale, price_block should match total price (within 10%)
                if abs(found_price - original_price) / original_price > 0.1:
                    errors.append("Price in price_block does not match original price (sale)")
    
    return errors


def check_output_guardrails(
    llm_parsed: Optional[Dict[str, Any]],
    original_price: Optional[float] = None,
    listing_type: Optional[str] = None
) -> List[str]:
    """
    Perform comprehensive output guardrail checks on LLM output.
    
    This function runs all output guardrail checks and returns a list of errors.
    If the list is empty, all checks passed.
    
    Checks performed:
    1. Output structure validation (required fields, types)
    2. Output length validation
    3. Property-related content validation
    4. Inappropriate content detection
    5. Injection attack detection
    6. Price in description detection (compliance)
    7. Price compliance validation (matches original price)
    
    Args:
        llm_parsed: Parsed JSON dictionary from LLM output
        original_price: Original price from input (for compliance validation)
        listing_type: Original listing type (for compliance validation)
        
    Returns:
        List of error messages (empty if all checks pass)
    """
    errors: List[str] = []
    
    # Check if LLM output exists
    if not llm_parsed:
        errors.append("Output guardrail: No LLM output to validate")
        return errors
    
    # 1. Validate structure
    structure_error = validate_output_structure(llm_parsed)
    if structure_error:
        errors.append(f"Output structure: {structure_error}")
        # If structure is invalid, skip other checks
        return errors
    
    # 2. Validate lengths
    length_errors = validate_output_lengths(llm_parsed)
    errors.extend(length_errors)
    
    # 3. Check for inappropriate content
    inappropriate_errors = detect_inappropriate_output(llm_parsed)
    errors.extend(inappropriate_errors)
    
    # 4. Check for injection attacks
    injection_errors = detect_injection_in_output(llm_parsed)
    errors.extend(injection_errors)
    
    # 5. Validate property-related content
    property_errors = validate_output_property_related(llm_parsed)
    errors.extend(property_errors)
    
    # 6. Check for price in description (compliance)
    description = llm_parsed.get("description", "")
    if description:
        price_in_desc_error = detect_price_in_description(description)
        if price_in_desc_error:
            errors.append(f"Compliance: {price_in_desc_error}")
    
    # 7. Validate price compliance (matches original)
    compliance_errors = validate_output_compliance(llm_parsed, original_price, listing_type)
    errors.extend(compliance_errors)
    
    return errors

