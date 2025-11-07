"""
Input Validation Utilities for Property Listing System - Iteration 1

This module provides business logic validation functions for input fields.
These validations are separate from guardrail safety checks and focus on:
- Required field validation
- Data type validation
- Format validation
- Business rule validation
"""

from typing import Optional, List, Literal
import re


# ============================================================================
# Configuration Constants
# ============================================================================

# Price validation
MIN_PRICE = 0.01  # Minimum valid price (1 cent)
MAX_PRICE = 999_999_999.99  # Maximum reasonable price

# Listing type validation
VALID_LISTING_TYPES = ["sale", "rent"]


# ============================================================================
# Required Field Validation
# ============================================================================

def validate_required_field(value: Optional[str], field_name: str) -> Optional[str]:
    """
    Validate that a required field is present and not empty.
    
    Args:
        value: Field value to validate
        field_name: Name of the field (for error messages)
        
    Returns:
        Error message if validation fails, None otherwise
    """
    if value is None:
        return f"{field_name} is required"
    
    if not isinstance(value, str):
        return f"{field_name} must be a string"
    
    if not value.strip():
        return f"{field_name} cannot be empty"
    
    return None


# ============================================================================
# Listing Type Validation
# ============================================================================

def validate_listing_type(listing_type: Optional[str]) -> Optional[str]:
    """
    Validate listing type is valid.
    
    Args:
        listing_type: Listing type to validate
        
    Returns:
        Error message if validation fails, None otherwise
    """
    if listing_type is None:
        return "listing_type is required"
    
    if not isinstance(listing_type, str):
        return "listing_type must be a string"
    
    listing_type_lower = listing_type.lower().strip()
    
    if listing_type_lower not in VALID_LISTING_TYPES:
        return f"listing_type must be one of {VALID_LISTING_TYPES}, got '{listing_type}'"
    
    return None


# ============================================================================
# Price Validation
# ============================================================================

def validate_price(price: Optional[float], field_name: str = "price", required: bool = True) -> Optional[str]:
    """
    Validate price is a valid positive number.
    
    Args:
        price: Price value to validate
        field_name: Name of the field (for error messages, e.g., "price", "security_deposit")
        required: Whether the price field is required (default: True for main price field)
        
    Returns:
        Error message if validation fails, None otherwise
    """
    if price is None:
        if required:
            return f"{field_name} is required"
        return None  # Price is optional
    
    if not isinstance(price, (int, float)):
        return f"{field_name} must be a number"
    
    if price < MIN_PRICE:
        return f"{field_name} must be at least ${MIN_PRICE:.2f}"
    
    if price > MAX_PRICE:
        return f"{field_name} exceeds maximum value of ${MAX_PRICE:,.2f}"
    
    return None


def validate_non_negative_number(
    value: Optional[float], 
    field_name: str
) -> Optional[str]:
    """
    Validate that a numeric field is non-negative (can be zero).
    
    Used for optional fields like security_deposit, hoa_fees, property_taxes.
    
    Args:
        value: Numeric value to validate
        field_name: Name of the field (for error messages)
        
    Returns:
        Error message if validation fails, None otherwise
    """
    if value is None:
        return None  # Field is optional
    
    if not isinstance(value, (int, float)):
        return f"{field_name} must be a number"
    
    if value < 0:
        return f"{field_name} cannot be negative"
    
    return None


# ============================================================================
# Address Validation
# ============================================================================

def validate_address(address: Optional[str]) -> Optional[str]:
    """
    Validate address format with enhanced checks for completeness.
    
    Address is the MOST IMPORTANT input for generating accurate listings.
    This validation ensures the address has sufficient information to:
    - Enable accurate web search enrichment
    - Generate location-specific listing content
    - Provide context for price analysis (future iterations)
    
    This performs comprehensive format checks. More sophisticated validation
    (like geocoding) happens in enrichment step.
    
    Accepts various address formats:
    - Traditional US: "123 Main Street, City, State ZIP"
    - Building/Complex: "Building Name, Area, City, State" (no street number required)
    - International: "Street Name, City, Country" or "Building, District, City"
    
    Validation checks:
    1. Required field (not empty)
    2. Minimum length (5 characters)
    3. Contains alphanumeric content
    4. Has sufficient structure (recommends city/state/location info)
    
    Args:
        address: Address to validate
        
    Returns:
        Error message if validation fails, None otherwise
    """
    error = validate_required_field(address, "address")
    if error:
        return error
    
    # Basic format check: address should have some structure
    address_stripped = address.strip()  # type: ignore
    
    if len(address_stripped) < 5:
        return "address is too short (minimum 5 characters). Please provide a complete address for accurate listing generation."
    
    # Additional check: Address should contain at least some alphanumeric content
    # and not be just special characters
    has_alphanumeric = any(char.isalnum() for char in address_stripped)
    if not has_alphanumeric:
        return "address must contain letters or numbers"
    
    # Enhanced validation: Check for address completeness
    # Address should ideally contain location information (city, state, country, etc.)
    # This is crucial for accurate web search and listing generation
    
    address_lower = address_stripped.lower()
    
    # Check for common address components that indicate completeness
    # These are indicators that address has sufficient location information
    has_location_indicators = False
    
    # Check for commas (indicates structured address with multiple components)
    # Examples: "123 Main St, New York, NY" or "Building Name, Area, City"
    if ',' in address_stripped:
        has_location_indicators = True
    
    # Check for common location keywords (city, state, country indicators)
    location_keywords = [
        # US states (common abbreviations and full names)
        'ny', 'ca', 'tx', 'fl', 'il', 'pa', 'oh', 'ga', 'nc', 'mi',
        'new york', 'california', 'texas', 'florida', 'illinois',
        # Common location terms
        'city', 'state', 'street', 'st', 'avenue', 'ave', 'road', 'rd',
        'boulevard', 'blvd', 'drive', 'dr', 'lane', 'ln', 'way', 'court', 'ct',
        # International indicators
        'district', 'province', 'region', 'country', 'postal', 'zip',
        # Building/complex indicators (still valid addresses)
        'tower', 'residency', 'residence', 'building', 'complex', 'apartment', 'apt',
        'condo', 'condominium', 'villa', 'estate', 'park', 'plaza', 'center', 'centre'
    ]
    
    # Check if address contains location keywords
    if any(keyword in address_lower for keyword in location_keywords):
        has_location_indicators = True
    
    # Check for ZIP/postal code pattern (5 digits or 5+4 format)
    zip_pattern = r'\b\d{5}(-\d{4})?\b'
    if re.search(zip_pattern, address_stripped):
        has_location_indicators = True
    
    # If address doesn't have clear location indicators, it might be incomplete
    # However, we don't fail validation - we just note it might affect accuracy
    # Some valid addresses might not match these patterns (e.g., "123 Main St" alone)
    # The enrichment step will attempt to find more information via web search
    
    # Minimum requirement: Address should have at least 2 words (basic structure)
    # This catches cases like "123" or "Main" which are too vague
    word_count = len(address_stripped.split())
    if word_count < 2:
        return "address appears incomplete. Please provide a complete address including street name and city/location for accurate listing generation."
    
    # Address validation: Accept addresses with or without street numbers
    # Many valid addresses don't have street numbers (building names, complexes, etc.)
    # Examples: "Mayfair Residency, Business Bay, Dubai" or "Central Park Tower, NYC"
    # We accept these as valid, but recommend including city/state for better accuracy
    
    return None


# ============================================================================
# Notes Validation
# ============================================================================

def validate_notes(notes: Optional[str]) -> Optional[str]:
    """
    Validate notes field.
    
    Notes are optional but if provided, should not be empty.
    
    Args:
        notes: Notes to validate
        
    Returns:
        Error message if validation fails, None otherwise
    """
    if notes is None:
        return None  # Notes are optional
    
    if not isinstance(notes, str):
        return "notes must be a string"
    
    if notes.strip() == "":
        return "notes cannot be empty if provided"
    
    return None


# ============================================================================
# Rental-Specific Field Validation
# ============================================================================

def validate_rental_fields(
    listing_type: Optional[str],
    billing_cycle: Optional[str],
    lease_term: Optional[str],
    security_deposit: Optional[float]
) -> List[str]:
    """
    Validate rental-specific fields.
    
    These fields should only be provided for rental listings.
    
    Args:
        listing_type: Listing type
        billing_cycle: Billing cycle (e.g., "monthly", "weekly")
        lease_term: Lease term (e.g., "12 months")
        security_deposit: Security deposit amount
        
    Returns:
        List of error messages (empty if all valid)
    """
    errors: List[str] = []
    
    # Only validate if listing type is rent
    if listing_type and listing_type.lower().strip() != "rent":
        return errors  # Not a rental, skip rental-specific validation
    
    # Validate security_deposit
    deposit_error = validate_non_negative_number(security_deposit, "security_deposit")
    if deposit_error:
        errors.append(deposit_error)
    
    # billing_cycle and lease_term are optional strings - no validation needed
    # They're just informational fields
    
    return errors


# ============================================================================
# Sale-Specific Field Validation
# ============================================================================

def validate_sale_fields(
    listing_type: Optional[str],
    hoa_fees: Optional[float],
    property_taxes: Optional[float],
    council_tax: Optional[float] = None,
    rates: Optional[float] = None,
    strata_fees: Optional[float] = None
) -> List[str]:
    """
    Validate sale-specific fields (region-dependent).
    
    These fields should only be provided for sale listings.
    Different regions have different fields.
    
    Args:
        listing_type: Listing type
        hoa_fees: HOA fees / Condo fees / Service charge (US/CA/UK)
        property_taxes: Property taxes (US/CA)
        council_tax: Council tax (UK)
        rates: Council rates (Australia)
        strata_fees: Strata fees / Body corporate (Australia/Canada)
        
    Returns:
        List of error messages (empty if all valid)
    """
    errors: List[str] = []
    
    # Only validate if listing type is sale
    if listing_type and listing_type.lower().strip() != "sale":
        return errors  # Not a sale, skip sale-specific validation
    
    # Validate hoa_fees (US/CA/UK)
    hoa_error = validate_non_negative_number(hoa_fees, "hoa_fees")
    if hoa_error:
        errors.append(hoa_error)
    
    # Validate property_taxes (US/CA)
    taxes_error = validate_non_negative_number(property_taxes, "property_taxes")
    if taxes_error:
        errors.append(taxes_error)
    
    # Validate council_tax (UK)
    council_tax_error = validate_non_negative_number(council_tax, "council_tax")
    if council_tax_error:
        errors.append(council_tax_error)
    
    # Validate rates (Australia)
    rates_error = validate_non_negative_number(rates, "rates")
    if rates_error:
        errors.append(rates_error)
    
    # Validate strata_fees (Australia/Canada)
    strata_error = validate_non_negative_number(strata_fees, "strata_fees")
    if strata_error:
        errors.append(strata_error)
    
    return errors


# ============================================================================
# Comprehensive Input Validation
# ============================================================================

def validate_input_fields(
    address: Optional[str],
    listing_type: Optional[str],
    price: Optional[float],
    notes: Optional[str],
    billing_cycle: Optional[str] = None,
    lease_term: Optional[str] = None,
    security_deposit: Optional[float] = None,
    hoa_fees: Optional[float] = None,
    property_taxes: Optional[float] = None,
    council_tax: Optional[float] = None,
    rates: Optional[float] = None,
    strata_fees: Optional[float] = None,
) -> List[str]:
    """
    Perform comprehensive validation of all input fields.
    
    This function runs all business logic validations and returns
    a list of errors. If the list is empty, all validations passed.
    
    Args:
        address: Property address (required)
        listing_type: Listing type - "sale" or "rent" (required)
        price: Asking price (required, currency depends on region)
        notes: Property notes (optional)
        billing_cycle: Billing cycle for rentals (optional)
        lease_term: Lease term for rentals (optional)
        security_deposit: Security deposit / bond for rentals (optional, currency depends on region)
        hoa_fees: HOA fees / Condo fees / Service charge for sales (optional, region-dependent)
        property_taxes: Property taxes for sales (optional, US/CA)
        council_tax: Council tax (optional, UK - sale or rent)
        rates: Council rates (optional, Australia - sale only)
        strata_fees: Strata fees / Body corporate (optional, Australia/Canada - sale only)
        
    Returns:
        List of error messages (empty if all validations pass)
    """
    errors: List[str] = []
    
    # Validate required fields
    address_error = validate_address(address)
    if address_error:
        errors.append(address_error)
    
    listing_type_error = validate_listing_type(listing_type)
    if listing_type_error:
        errors.append(listing_type_error)
    
    # Validate price (required field)
    price_error = validate_price(price, "price", required=True)
    if price_error:
        errors.append(price_error)
    
    notes_error = validate_notes(notes)
    if notes_error:
        errors.append(notes_error)
    
    # Validate type-specific fields
    rental_errors = validate_rental_fields(
        listing_type, billing_cycle, lease_term, security_deposit
    )
    errors.extend(rental_errors)
    
    sale_errors = validate_sale_fields(
        listing_type, 
        hoa_fees, 
        property_taxes,
        council_tax=council_tax,
        rates=rates,
        strata_fees=strata_fees
    )
    errors.extend(sale_errors)
    
    return errors

