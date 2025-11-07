"""
Comprehensive unit tests for input validation utilities.

Tests cover:
- Required field validation
- Listing type validation
- Price validation
- Address validation
- Notes validation
- Rental-specific field validation
- Sale-specific field validation
- Comprehensive input validation
- Edge cases
"""

import pytest
import sys
from pathlib import Path

# Add src to path so we can import
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.validators import (
    validate_required_field,
    validate_listing_type,
    validate_price,
    validate_non_negative_number,
    validate_address,
    validate_notes,
    validate_rental_fields,
    validate_sale_fields,
    validate_input_fields,
    MIN_PRICE,
    MAX_PRICE,
)


# ============================================================================
# Required Field Validation Tests
# ============================================================================

class TestRequiredFieldValidation:
    """Test required field validation"""
    
    def test_valid_field_passes(self):
        """Test that valid field passes"""
        error = validate_required_field("123 Main St", "address")
        assert error is None
    
    def test_none_field_fails(self):
        """Test that None field fails"""
        error = validate_required_field(None, "address")
        assert error is not None
        assert "required" in error.lower()
    
    def test_empty_string_fails(self):
        """Test that empty string fails"""
        error = validate_required_field("", "address")
        assert error is not None
        assert "cannot be empty" in error.lower()
    
    def test_whitespace_only_fails(self):
        """Test that whitespace-only string fails"""
        error = validate_required_field("   ", "address")
        assert error is not None
        assert "cannot be empty" in error.lower()
    
    def test_non_string_fails(self):
        """Test that non-string value fails"""
        error = validate_required_field(123, "address")
        assert error is not None
        assert "must be a string" in error.lower()


# ============================================================================
# Listing Type Validation Tests
# ============================================================================

class TestListingTypeValidation:
    """Test listing type validation"""
    
    def test_valid_sale_passes(self):
        """Test that 'sale' passes"""
        error = validate_listing_type("sale")
        assert error is None
    
    def test_valid_rent_passes(self):
        """Test that 'rent' passes"""
        error = validate_listing_type("rent")
        assert error is None
    
    def test_case_insensitive_passes(self):
        """Test that case-insensitive values pass"""
        error = validate_listing_type("SALE")
        assert error is None
        
        error = validate_listing_type("RENT")
        assert error is None
    
    def test_none_fails(self):
        """Test that None fails"""
        error = validate_listing_type(None)
        assert error is not None
        assert "required" in error.lower()
    
    def test_invalid_type_fails(self):
        """Test that invalid type fails"""
        error = validate_listing_type("invalid")
        assert error is not None
        assert "must be one of" in error.lower()
    
    def test_non_string_fails(self):
        """Test that non-string fails"""
        error = validate_listing_type(123)
        assert error is not None
        assert "must be a string" in error.lower()


# ============================================================================
# Price Validation Tests
# ============================================================================

class TestPriceValidation:
    """Test price validation"""
    
    def test_valid_price_passes(self):
        """Test that valid price passes"""
        error = validate_price(500000.0)
        assert error is None
    
    def test_none_passes(self):
        """Test that None passes (price is optional)"""
        error = validate_price(None)
        assert error is None
    
    def test_minimum_price_passes(self):
        """Test that minimum price passes"""
        error = validate_price(MIN_PRICE)
        assert error is None
    
    def test_maximum_price_passes(self):
        """Test that maximum price passes"""
        error = validate_price(MAX_PRICE)
        assert error is None
    
    def test_zero_fails(self):
        """Test that zero fails"""
        error = validate_price(0.0)
        assert error is not None
        assert "must be at least" in error.lower()
    
    def test_negative_fails(self):
        """Test that negative price fails"""
        error = validate_price(-100.0)
        assert error is not None
        assert "must be at least" in error.lower()
    
    def test_too_large_fails(self):
        """Test that price exceeding max fails"""
        error = validate_price(MAX_PRICE + 1)
        assert error is not None
        assert "exceeds maximum" in error.lower()
    
    def test_non_number_fails(self):
        """Test that non-number fails"""
        error = validate_price("500000")
        assert error is not None
        assert "must be a number" in error.lower()


# ============================================================================
# Non-Negative Number Validation Tests
# ============================================================================

class TestNonNegativeNumberValidation:
    """Test non-negative number validation"""
    
    def test_valid_number_passes(self):
        """Test that valid number passes"""
        error = validate_non_negative_number(2500.0, "security_deposit")
        assert error is None
    
    def test_zero_passes(self):
        """Test that zero passes"""
        error = validate_non_negative_number(0.0, "security_deposit")
        assert error is None
    
    def test_none_passes(self):
        """Test that None passes (field is optional)"""
        error = validate_non_negative_number(None, "security_deposit")
        assert error is None
    
    def test_negative_fails(self):
        """Test that negative number fails"""
        error = validate_non_negative_number(-100.0, "security_deposit")
        assert error is not None
        assert "cannot be negative" in error.lower()
    
    def test_non_number_fails(self):
        """Test that non-number fails"""
        error = validate_non_negative_number("2500", "security_deposit")
        assert error is not None
        assert "must be a number" in error.lower()


# ============================================================================
# Address Validation Tests
# ============================================================================

class TestAddressValidation:
    """Test address validation"""
    
    def test_valid_address_passes(self):
        """Test that valid address passes"""
        error = validate_address("123 Main St, New York, NY 10001")
        assert error is None
    
    def test_none_fails(self):
        """Test that None fails"""
        error = validate_address(None)
        assert error is not None
        assert "required" in error.lower()
    
    def test_empty_fails(self):
        """Test that empty string fails"""
        error = validate_address("")
        assert error is not None
    
    def test_too_short_fails(self):
        """Test that address too short fails"""
        error = validate_address("123")
        assert error is not None
        assert "too short" in error.lower()
    
    def test_no_street_number_fails(self):
        """Test that address without street number fails"""
        error = validate_address("Main Street")
        assert error is not None
        assert "street number" in error.lower()
    
    def test_address_with_street_number_passes(self):
        """Test that address with street number passes"""
        error = validate_address("123 Main St")
        assert error is None


# ============================================================================
# Notes Validation Tests
# ============================================================================

class TestNotesValidation:
    """Test notes validation"""
    
    def test_valid_notes_passes(self):
        """Test that valid notes pass"""
        error = validate_notes("2BR/1BA, 1000 sqft")
        assert error is None
    
    def test_none_passes(self):
        """Test that None passes (notes are optional)"""
        error = validate_notes(None)
        assert error is None
    
    def test_empty_string_fails(self):
        """Test that empty string fails if provided"""
        error = validate_notes("")
        assert error is not None
        assert "cannot be empty if provided" in error.lower()
    
    def test_whitespace_only_fails(self):
        """Test that whitespace-only fails"""
        error = validate_notes("   ")
        assert error is not None
    
    def test_non_string_fails(self):
        """Test that non-string fails"""
        error = validate_notes(123)
        assert error is not None
        assert "must be a string" in error.lower()


# ============================================================================
# Rental-Specific Field Validation Tests
# ============================================================================

class TestRentalFieldsValidation:
    """Test rental-specific field validation"""
    
    def test_rental_with_valid_fields_passes(self):
        """Test that rental with valid fields passes"""
        errors = validate_rental_fields(
            listing_type="rent",
            billing_cycle="monthly",
            lease_term="12 months",
            security_deposit=2500.0
        )
        assert errors == []
    
    def test_rental_with_negative_deposit_fails(self):
        """Test that rental with negative deposit fails"""
        errors = validate_rental_fields(
            listing_type="rent",
            billing_cycle=None,
            lease_term=None,
            security_deposit=-100.0
        )
        assert len(errors) > 0
        assert any("cannot be negative" in error for error in errors)
    
    def test_sale_listing_skips_rental_validation(self):
        """Test that sale listing skips rental validation"""
        errors = validate_rental_fields(
            listing_type="sale",
            billing_cycle=None,
            lease_term=None,
            security_deposit=None
        )
        assert errors == []


# ============================================================================
# Sale-Specific Field Validation Tests
# ============================================================================

class TestSaleFieldsValidation:
    """Test sale-specific field validation"""
    
    def test_sale_with_valid_fields_passes(self):
        """Test that sale with valid fields passes"""
        errors = validate_sale_fields(
            listing_type="sale",
            hoa_fees=200.0,
            property_taxes=5000.0
        )
        assert errors == []
    
    def test_sale_with_negative_hoa_fails(self):
        """Test that sale with negative HOA fees fails"""
        errors = validate_sale_fields(
            listing_type="sale",
            hoa_fees=-100.0,
            property_taxes=None
        )
        assert len(errors) > 0
        assert any("cannot be negative" in error for error in errors)
    
    def test_rental_listing_skips_sale_validation(self):
        """Test that rental listing skips sale validation"""
        errors = validate_sale_fields(
            listing_type="rent",
            hoa_fees=None,
            property_taxes=None
        )
        assert errors == []


# ============================================================================
# Comprehensive Input Validation Tests
# ============================================================================

class TestComprehensiveInputValidation:
    """Test comprehensive input validation"""
    
    def test_valid_rental_input_passes(self):
        """Test that valid rental input passes all validations"""
        errors = validate_input_fields(
            address="123 Main St, New York, NY 10001",
            listing_type="rent",
            price=2500.0,
            notes="2BR/1BA, 1000 sqft",
            billing_cycle="monthly",
            security_deposit=2500.0
        )
        assert errors == []
    
    def test_valid_sale_input_passes(self):
        """Test that valid sale input passes all validations"""
        errors = validate_input_fields(
            address="456 Oak Ave, Los Angeles, CA 90001",
            listing_type="sale",
            price=750000.0,
            notes="3BR/2BA, 1500 sqft",
            hoa_fees=200.0,
            property_taxes=8500.0
        )
        assert errors == []
    
    def test_missing_address_fails(self):
        """Test that missing address fails"""
        errors = validate_input_fields(
            address=None,
            listing_type="sale",
            price=500000.0,
            notes=None
        )
        assert len(errors) > 0
        assert any("address" in error.lower() and "required" in error.lower() for error in errors)
    
    def test_missing_listing_type_fails(self):
        """Test that missing listing type fails"""
        errors = validate_input_fields(
            address="123 Main St",
            listing_type=None,
            price=500000.0,
            notes=None
        )
        assert len(errors) > 0
        assert any("listing_type" in error.lower() and "required" in error.lower() for error in errors)
    
    def test_invalid_listing_type_fails(self):
        """Test that invalid listing type fails"""
        errors = validate_input_fields(
            address="123 Main St",
            listing_type="invalid",
            price=500000.0,
            notes=None
        )
        assert len(errors) > 0
        assert any("listing_type" in error.lower() for error in errors)
    
    def test_negative_price_fails(self):
        """Test that negative price fails"""
        errors = validate_input_fields(
            address="123 Main St",
            listing_type="sale",
            price=-1000.0,
            notes=None
        )
        assert len(errors) > 0
        assert any("price" in error.lower() and "must be at least" in error.lower() for error in errors)
    
    def test_multiple_errors_collected(self):
        """Test that multiple errors are collected"""
        errors = validate_input_fields(
            address=None,
            listing_type=None,
            price=-1000.0,
            notes=None
        )
        assert len(errors) >= 3  # At least 3 errors


# ============================================================================
# Edge Cases
# ============================================================================

class TestValidationEdgeCases:
    """Test edge cases for validation"""
    
    def test_address_with_unicode_passes(self):
        """Test that address with unicode characters passes"""
        error = validate_address("123 Main St, São Paulo, Brazil")
        assert error is None
    
    def test_price_as_integer_passes(self):
        """Test that price as integer passes"""
        error = validate_price(500000)  # int instead of float
        assert error is None
    
    def test_listing_type_with_whitespace_passes(self):
        """Test that listing type with whitespace passes (after strip)"""
        error = validate_listing_type("  sale  ")
        assert error is None
    
    def test_very_small_price_passes(self):
        """Test that very small price passes"""
        error = validate_price(0.01)
        assert error is None
    
    def test_very_large_price_passes(self):
        """Test that very large price passes"""
        error = validate_price(999_999_999.99)
        assert error is None

