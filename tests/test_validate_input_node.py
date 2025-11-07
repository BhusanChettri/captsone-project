"""
Unit tests for validate_input_node.

Tests cover:
- Node execution with valid input
- Node execution with invalid input
- Error collection in state
- Edge cases
"""

import pytest
import sys
from pathlib import Path

# Add src to path so we can import
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.nodes import validate_input_node
from core.state import PropertyListingState


# ============================================================================
# Valid Input Tests
# ============================================================================

class TestValidateInputNodeValid:
    """Test validate_input_node with valid input"""
    
    def test_valid_rental_input_passes(self):
        """Test that valid rental input passes validation"""
        state: PropertyListingState = {
            "address": "123 Main St, New York, NY 10001",
            "listing_type": "rent",
            "price": 2500.0,
            "notes": "2BR/1BA, 1000 sqft, pet-friendly",
            "billing_cycle": "monthly",
            "security_deposit": 2500.0,
            "errors": []
        }
        
        result = validate_input_node(state)
        
        assert result["errors"] == []
        assert result["address"] == "123 Main St, New York, NY 10001"
    
    def test_valid_sale_input_passes(self):
        """Test that valid sale input passes validation"""
        state: PropertyListingState = {
            "address": "456 Oak Ave, Los Angeles, CA 90001",
            "listing_type": "sale",
            "price": 750000.0,
            "notes": "3BR/2BA, 1500 sqft",
            "hoa_fees": 200.0,
            "property_taxes": 8500.0,
            "errors": []
        }
        
        result = validate_input_node(state)
        
        assert result["errors"] == []
    
    def test_minimal_valid_input_passes(self):
        """Test that minimal valid input (only required fields) passes"""
        state: PropertyListingState = {
            "address": "123 Main St",
            "listing_type": "sale",
            "errors": []
        }
        
        result = validate_input_node(state)
        
        assert result["errors"] == []
    
    def test_node_preserves_state_fields(self):
        """Test that node preserves all state fields"""
        state: PropertyListingState = {
            "address": "123 Main St",
            "listing_type": "sale",
            "price": 500000.0,
            "notes": "2BR/1BA apartment",
            "errors": []
        }
        
        result = validate_input_node(state)
        
        assert result["address"] == "123 Main St"
        assert result["listing_type"] == "sale"
        assert result["price"] == 500000.0
        assert result["notes"] == "2BR/1BA apartment"


# ============================================================================
# Invalid Input Tests
# ============================================================================

class TestValidateInputNodeInvalid:
    """Test validate_input_node with invalid input"""
    
    def test_missing_address_adds_error(self):
        """Test that missing address adds error to state"""
        state: PropertyListingState = {
            "address": None,  # type: ignore
            "listing_type": "sale",
            "errors": []
        }
        
        result = validate_input_node(state)
        
        assert len(result["errors"]) > 0
        assert any("address" in error.lower() and "required" in error.lower() for error in result["errors"])
    
    def test_missing_listing_type_adds_error(self):
        """Test that missing listing_type adds error to state"""
        state: PropertyListingState = {
            "address": "123 Main St",
            "listing_type": None,  # type: ignore
            "errors": []
        }
        
        result = validate_input_node(state)
        
        assert len(result["errors"]) > 0
        assert any("listing_type" in error.lower() and "required" in error.lower() for error in result["errors"])
    
    def test_invalid_listing_type_adds_error(self):
        """Test that invalid listing_type adds error to state"""
        state: PropertyListingState = {
            "address": "123 Main St",
            "listing_type": "invalid",  # type: ignore
            "errors": []
        }
        
        result = validate_input_node(state)
        
        assert len(result["errors"]) > 0
        assert any("listing_type" in error.lower() for error in result["errors"])
    
    def test_negative_price_adds_error(self):
        """Test that negative price adds error to state"""
        state: PropertyListingState = {
            "address": "123 Main St",
            "listing_type": "sale",
            "price": -1000.0,
            "errors": []
        }
        
        result = validate_input_node(state)
        
        assert len(result["errors"]) > 0
        assert any("price" in error.lower() and "must be at least" in error.lower() for error in result["errors"])
    
    def test_negative_security_deposit_adds_error(self):
        """Test that negative security_deposit adds error to state"""
        state: PropertyListingState = {
            "address": "123 Main St",
            "listing_type": "rent",
            "security_deposit": -500.0,
            "errors": []
        }
        
        result = validate_input_node(state)
        
        assert len(result["errors"]) > 0
        assert any("security_deposit" in error.lower() and "cannot be negative" in error.lower() for error in result["errors"])
    
    def test_negative_hoa_fees_adds_error(self):
        """Test that negative hoa_fees adds error to state"""
        state: PropertyListingState = {
            "address": "123 Main St",
            "listing_type": "sale",
            "hoa_fees": -100.0,
            "errors": []
        }
        
        result = validate_input_node(state)
        
        assert len(result["errors"]) > 0
        assert any("hoa_fees" in error.lower() and "cannot be negative" in error.lower() for error in result["errors"])
    
    def test_multiple_errors_collected(self):
        """Test that multiple errors are collected in state"""
        state: PropertyListingState = {
            "address": None,  # type: ignore
            "listing_type": None,  # type: ignore
            "price": -1000.0,
            "errors": []
        }
        
        result = validate_input_node(state)
        
        assert len(result["errors"]) >= 3


# ============================================================================
# Edge Cases
# ============================================================================

class TestValidateInputNodeEdgeCases:
    """Test edge cases for validate_input_node"""
    
    def test_empty_address_adds_error(self):
        """Test that empty address adds error"""
        state: PropertyListingState = {
            "address": "",
            "listing_type": "sale",
            "errors": []
        }
        
        result = validate_input_node(state)
        
        assert len(result["errors"]) > 0
    
    def test_address_too_short_adds_error(self):
        """Test that address too short adds error"""
        state: PropertyListingState = {
            "address": "123",
            "listing_type": "sale",
            "errors": []
        }
        
        result = validate_input_node(state)
        
        assert len(result["errors"]) > 0
        assert any("too short" in error.lower() for error in result["errors"])
    
    def test_address_without_street_number_adds_error(self):
        """Test that address without street number adds error"""
        state: PropertyListingState = {
            "address": "Main Street",
            "listing_type": "sale",
            "errors": []
        }
        
        result = validate_input_node(state)
        
        assert len(result["errors"]) > 0
        assert any("street number" in error.lower() for error in result["errors"])
    
    def test_listing_type_case_insensitive(self):
        """Test that listing_type is case-insensitive"""
        state: PropertyListingState = {
            "address": "123 Main St",
            "listing_type": "SALE",  # Uppercase
            "errors": []
        }
        
        result = validate_input_node(state)
        
        # Should pass (case-insensitive)
        assert result["errors"] == []
    
    def test_errors_list_initialized_if_missing(self):
        """Test that errors list is initialized if missing"""
        state: PropertyListingState = {
            "address": "123 Main St",
            "listing_type": "sale"
            # errors not present
        }
        
        result = validate_input_node(state)
        
        assert "errors" in result
        assert isinstance(result["errors"], list)
    
    def test_existing_errors_preserved(self):
        """Test that existing errors are preserved"""
        state: PropertyListingState = {
            "address": "123 Main St",
            "listing_type": "sale",
            "errors": ["Existing error from guardrail"]
        }
        
        result = validate_input_node(state)
        
        assert "Existing error from guardrail" in result["errors"]
    
    def test_new_errors_appended_to_existing(self):
        """Test that new errors are appended to existing errors"""
        state: PropertyListingState = {
            "address": None,  # Will generate error
            "listing_type": "sale",
            "errors": ["Existing error"]
        }
        
        result = validate_input_node(state)
        
        assert "Existing error" in result["errors"]
        assert len(result["errors"]) > 1

