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
    Validate address format (basic validation).
    
    This performs basic format checks. More sophisticated validation
    (like geocoding) happens in enrichment step.
    
    Accepts various address formats:
    - Traditional: "123 Main Street, City, State"
    - Building/Complex: "Building Name, Area, City" (no street number required)
    - International: Various formats common globally
    
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
        return "address is too short (minimum 5 characters)"
    
    # Address validation: Accept addresses with or without street numbers
    # Many valid addresses don't have street numbers (building names, complexes, etc.)
    # Examples: "Mayfair Residency, Business Bay, Dubai" or "Central Park Tower, NYC"
    # We just need to ensure it's not empty and has reasonable length
    
    # Additional check: Address should contain at least some alphanumeric content
    # and not be just special characters
    has_alphanumeric = any(char.isalnum() for char in address_stripped)
    if not has_alphanumeric:
        return "address must contain letters or numbers"
    
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
    property_taxes: Optional[float]
) -> List[str]:
    """
    Validate sale-specific fields.
    
    These fields should only be provided for sale listings.
    
    Args:
        listing_type: Listing type
        hoa_fees: HOA fees amount
        property_taxes: Property taxes amount
        
    Returns:
        List of error messages (empty if all valid)
    """
    errors: List[str] = []
    
    # Only validate if listing type is sale
    if listing_type and listing_type.lower().strip() != "sale":
        return errors  # Not a sale, skip sale-specific validation
    
    # Validate hoa_fees
    hoa_error = validate_non_negative_number(hoa_fees, "hoa_fees")
    if hoa_error:
        errors.append(hoa_error)
    
    # Validate property_taxes
    taxes_error = validate_non_negative_number(property_taxes, "property_taxes")
    if taxes_error:
        errors.append(taxes_error)
    
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
) -> List[str]:
    """
    Perform comprehensive validation of all input fields.
    
    This function runs all business logic validations and returns
    a list of errors. If the list is empty, all validations passed.
    
    Args:
        address: Property address (required)
        listing_type: Listing type - "sale" or "rent" (required)
        price: Asking price (required)
        notes: Property notes (optional)
        billing_cycle: Billing cycle for rentals (optional)
        lease_term: Lease term for rentals (optional)
        security_deposit: Security deposit for rentals (optional)
        hoa_fees: HOA fees for sales (optional)
        property_taxes: Property taxes for sales (optional)
        
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
    
    sale_errors = validate_sale_fields(listing_type, hoa_fees, property_taxes)
    errors.extend(sale_errors)
    
    return errors

