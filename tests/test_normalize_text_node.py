"""
Unit tests for normalize_text_node.

Tests cover:
- Node execution with valid input
- Address normalization
- Notes normalization
- State updates
- Edge cases
"""

import pytest
import sys
from pathlib import Path

# Add src to path so we can import
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.nodes import normalize_text_node
from core.state import PropertyListingState


# ============================================================================
# Valid Input Tests
# ============================================================================

class TestNormalizeTextNodeValid:
    """Test normalize_text_node with valid input"""
    
    def test_clean_input_normalized(self):
        """Test that clean input is normalized"""
        state: PropertyListingState = {
            "address": "123 Main St, New York, NY 10001",
            "listing_type": "sale",
            "notes": "2BR/1BA, 1000 sqft",
            "errors": []
        }
        
        result = normalize_text_node(state)
        
        assert "normalized_address" in result
        assert "normalized_notes" in result
        assert result["normalized_address"] == "123 Main St, New York, NY 10001"
        assert result["normalized_notes"] == "2BR/1BA, 1000 sqft"
    
    def test_address_with_extra_spaces_normalized(self):
        """Test that address with extra spaces is normalized"""
        state: PropertyListingState = {
            "address": "123   Main   St,  New York",
            "listing_type": "sale",
            "notes": "2BR/1BA",
            "errors": []
        }
        
        result = normalize_text_node(state)
        
        assert "normalized_address" in result
        assert result["normalized_address"] == "123 Main St, New York"
    
    def test_notes_with_line_breaks_normalized(self):
        """Test that notes with line breaks are normalized"""
        state: PropertyListingState = {
            "address": "123 Main St",
            "listing_type": "sale",
            "notes": "2BR/1BA\n1000 sqft\npet-friendly",
            "errors": []
        }
        
        result = normalize_text_node(state)
        
        assert "normalized_notes" in result
        assert "2BR/1BA" in result["normalized_notes"]
        assert "1000 sqft" in result["normalized_notes"]
    
    def test_node_preserves_original_fields(self):
        """Test that node preserves original address and notes fields"""
        state: PropertyListingState = {
            "address": "123 Main St",
            "listing_type": "sale",
            "notes": "2BR/1BA",
            "errors": []
        }
        
        result = normalize_text_node(state)
        
        # Original fields should still be present
        assert result["address"] == "123 Main St"
        assert result["notes"] == "2BR/1BA"
        # Normalized fields should also be present
        assert "normalized_address" in result
        assert "normalized_notes" in result
    
    def test_node_preserves_other_state_fields(self):
        """Test that node preserves other state fields"""
        state: PropertyListingState = {
            "address": "123 Main St",
            "listing_type": "sale",
            "price": 500000.0,
            "notes": "2BR/1BA",
            "errors": []
        }
        
        result = normalize_text_node(state)
        
        assert result["listing_type"] == "sale"
        assert result["price"] == 500000.0
        assert result["errors"] == []


# ============================================================================
# Edge Cases
# ============================================================================

class TestNormalizeTextNodeEdgeCases:
    """Test edge cases for normalize_text_node"""
    
    def test_none_address_handled(self):
        """Test that None address is handled gracefully"""
        state: PropertyListingState = {
            "address": None,  # type: ignore
            "listing_type": "sale",
            "notes": "2BR/1BA",
            "errors": []
        }
        
        result = normalize_text_node(state)
        
        assert "normalized_address" in result
        assert result["normalized_address"] == ""
    
    def test_none_notes_handled(self):
        """Test that None notes is handled gracefully"""
        state: PropertyListingState = {
            "address": "123 Main St",
            "listing_type": "sale",
            "notes": None,  # type: ignore
            "errors": []
        }
        
        result = normalize_text_node(state)
        
        assert "normalized_notes" in result
        assert result["normalized_notes"] == ""
    
    def test_empty_strings_handled(self):
        """Test that empty strings are handled"""
        state: PropertyListingState = {
            "address": "",
            "listing_type": "sale",
            "notes": "",
            "errors": []
        }
        
        result = normalize_text_node(state)
        
        assert "normalized_address" in result
        assert "normalized_notes" in result
        assert result["normalized_address"] == ""
        assert result["normalized_notes"] == ""
    
    def test_whitespace_only_normalized(self):
        """Test that whitespace-only strings are normalized"""
        state: PropertyListingState = {
            "address": "  123 Main St  ",
            "listing_type": "sale",
            "notes": "  2BR/1BA  ",
            "errors": []
        }
        
        result = normalize_text_node(state)
        
        assert result["normalized_address"] == "123 Main St"
        assert result["normalized_notes"] == "2BR/1BA"
    
    def test_address_with_special_characters_preserved(self):
        """Test that special characters in address are preserved"""
        state: PropertyListingState = {
            "address": "123 Main St. #4B, New York, NY 10001",
            "listing_type": "sale",
            "notes": "2BR/1BA",
            "errors": []
        }
        
        result = normalize_text_node(state)
        
        assert "#4B" in result["normalized_address"]
        assert "." in result["normalized_address"]
    
    def test_notes_with_special_formatting_preserved(self):
        """Test that special formatting in notes is preserved"""
        state: PropertyListingState = {
            "address": "123 Main St",
            "listing_type": "sale",
            "notes": "2BR/1BA, $500,000, pet-friendly!",
            "errors": []
        }
        
        result = normalize_text_node(state)
        
        assert "2BR/1BA" in result["normalized_notes"]
        assert "$500,000" in result["normalized_notes"]
        assert "!" in result["normalized_notes"]
    
    def test_multiline_address_normalized(self):
        """Test that multiline address is normalized"""
        state: PropertyListingState = {
            "address": "123 Main St\nNew York\nNY 10001",
            "listing_type": "sale",
            "notes": "2BR/1BA",
            "errors": []
        }
        
        result = normalize_text_node(state)
        
        # Should be normalized to single line with proper comma spacing
        assert "123 Main St" in result["normalized_address"]
        assert "New York" in result["normalized_address"]
        assert "NY 10001" in result["normalized_address"]

