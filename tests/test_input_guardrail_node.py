"""
Unit tests for input_guardrail_node.

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

from core.nodes import input_guardrail_node
from core.state import PropertyListingState


# ============================================================================
# Valid Input Tests
# ============================================================================

class TestInputGuardrailNodeValid:
    """Test input_guardrail_node with valid input"""
    
    def test_valid_property_input_passes(self):
        """Test that valid property input passes guardrail checks"""
        state: PropertyListingState = {
            "address": "123 Main St, New York, NY 10001",
            "listing_type": "sale",
            "notes": "2BR/1BA, 1000 sqft, pet-friendly apartment",
            "errors": []
        }
        
        result = input_guardrail_node(state)
        
        assert result["errors"] == []
        assert result["address"] == "123 Main St, New York, NY 10001"
    
    def test_valid_rental_input_passes(self):
        """Test that valid rental input passes guardrail checks"""
        state: PropertyListingState = {
            "address": "456 Oak Ave, Los Angeles, CA 90001",
            "listing_type": "rent",
            "notes": "3BR/2BA, 1500 sqft, updated kitchen, $2500/month",
            "errors": []
        }
        
        result = input_guardrail_node(state)
        
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
        
        result = input_guardrail_node(state)
        
        assert result["address"] == "123 Main St"
        assert result["listing_type"] == "sale"
        assert result["price"] == 500000.0
        assert result["notes"] == "2BR/1BA apartment"


# ============================================================================
# Invalid Input Tests
# ============================================================================

class TestInputGuardrailNodeInvalid:
    """Test input_guardrail_node with invalid input"""
    
    def test_long_address_adds_error(self):
        """Test that long address adds error to state"""
        long_address = "A" * 501  # Exceeds MAX_ADDRESS_LENGTH
        state: PropertyListingState = {
            "address": long_address,
            "listing_type": "sale",
            "notes": "2BR/1BA apartment",
            "errors": []
        }
        
        result = input_guardrail_node(state)
        
        assert len(result["errors"]) > 0
        assert any("Address" in error and "exceeds" in error for error in result["errors"])
    
    def test_injection_attack_adds_error(self):
        """Test that injection attack adds error to state"""
        state: PropertyListingState = {
            "address": "123 Main St' UNION SELECT * FROM users--",
            "listing_type": "sale",
            "notes": "2BR/1BA apartment",
            "errors": []
        }
        
        result = input_guardrail_node(state)
        
        assert len(result["errors"]) > 0
        assert any("injection attack" in error.lower() for error in result["errors"])
    
    def test_inappropriate_content_adds_error(self):
        """Test that inappropriate content adds error to state"""
        state: PropertyListingState = {
            "address": "123 Main St",
            "listing_type": "sale",
            "notes": "explicit content here",
            "errors": []
        }
        
        result = input_guardrail_node(state)
        
        assert len(result["errors"]) > 0
        assert any("inappropriate content" in error.lower() for error in result["errors"])
    
    def test_non_property_input_adds_error(self):
        """Test that non-property input adds error to state"""
        state: PropertyListingState = {
            "address": "123 Main St",
            "listing_type": "sale",
            "notes": "This is completely unrelated content about cooking recipes and food preparation",
            "errors": []
        }
        
        result = input_guardrail_node(state)
        
        assert len(result["errors"]) > 0
        assert any("property-related" in error.lower() for error in result["errors"])
    
    def test_multiple_errors_collected(self):
        """Test that multiple errors are collected in state"""
        state: PropertyListingState = {
            "address": "A" * 501,  # Too long
            "listing_type": "sale",
            "notes": "A" * 2001,  # Too long
            "errors": []
        }
        
        result = input_guardrail_node(state)
        
        assert len(result["errors"]) >= 2


# ============================================================================
# Edge Cases
# ============================================================================

class TestInputGuardrailNodeEdgeCases:
    """Test edge cases for input_guardrail_node"""
    
    def test_none_address_handled(self):
        """Test that None address is handled gracefully"""
        state: PropertyListingState = {
            "address": None,  # type: ignore
            "listing_type": "sale",
            "notes": "2BR/1BA apartment",
            "errors": []
        }
        
        result = input_guardrail_node(state)
        
        # Should handle None gracefully (may add errors for empty address)
        assert "errors" in result
    
    def test_none_notes_handled(self):
        """Test that None notes is handled gracefully"""
        state: PropertyListingState = {
            "address": "123 Main St",
            "listing_type": "sale",
            "notes": None,  # type: ignore
            "errors": []
        }
        
        result = input_guardrail_node(state)
        
        # Should handle None gracefully
        assert "errors" in result
    
    def test_empty_strings_handled(self):
        """Test that empty strings are handled"""
        state: PropertyListingState = {
            "address": "",
            "listing_type": "sale",
            "notes": "",
            "errors": []
        }
        
        result = input_guardrail_node(state)
        
        # Should handle empty strings (may add errors for property validation)
        assert "errors" in result
    
    def test_errors_list_initialized_if_missing(self):
        """Test that errors list is initialized if missing"""
        state: PropertyListingState = {
            "address": "123 Main St",
            "listing_type": "sale",
            "notes": "2BR/1BA apartment"
            # errors not present
        }
        
        result = input_guardrail_node(state)
        
        assert "errors" in result
        assert isinstance(result["errors"], list)
    
    def test_existing_errors_preserved(self):
        """Test that existing errors are preserved"""
        state: PropertyListingState = {
            "address": "123 Main St",
            "listing_type": "sale",
            "notes": "2BR/1BA apartment",
            "errors": ["Existing error"]
        }
        
        result = input_guardrail_node(state)
        
        assert "Existing error" in result["errors"]
    
    def test_new_errors_appended_to_existing(self):
        """Test that new errors are appended to existing errors"""
        state: PropertyListingState = {
            "address": "A" * 501,  # Will generate error
            "listing_type": "sale",
            "notes": "2BR/1BA apartment",
            "errors": ["Existing error"]
        }
        
        result = input_guardrail_node(state)
        
        assert "Existing error" in result["errors"]
        assert len(result["errors"]) > 1

