"""
Integration tests for generate_content_node.

Tests cover:
- Node execution with valid input
- LLM response parsing
- Error handling
- Edge cases
"""

import pytest
import sys
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path so we can import
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.nodes import generate_content_node
from core.state import PropertyListingState


# ============================================================================
# Valid Input Tests
# ============================================================================

class TestGenerateContentNodeValid:
    """Test generate_content_node with valid input"""
    
    @patch('utils.llm_client.initialize_llm')
    @patch('utils.llm_client.call_llm_with_prompt')
    @patch('utils.llm_client.parse_json_response')
    def test_node_generates_content_successfully(
        self, mock_parse, mock_call_llm, mock_init_llm
    ):
        """Test that node successfully generates content"""
        # Mock LLM initialization
        mock_llm = Mock()
        mock_init_llm.return_value = mock_llm
        
        # Mock LLM response
        mock_llm_response = '{"title": "Beautiful Home", "description": "Great property", "price_block": "$500,000"}'
        mock_call_llm.return_value = mock_llm_response
        
        # Mock JSON parsing
        mock_parsed = {
            "title": "Beautiful Home",
            "description": "Great property",
            "price_block": "$500,000"
        }
        mock_parse.return_value = mock_parsed
        
        state: PropertyListingState = {
            "address": "123 Main St, New York, NY",
            "listing_type": "sale",
            "price": 500000.0,
            "notes": "2BR/1BA apartment",
            "errors": []
        }
        
        result = generate_content_node(state)
        
        # Verify LLM was called
        mock_init_llm.assert_called_once()
        mock_call_llm.assert_called_once()
        mock_parse.assert_called_once_with(mock_llm_response)
        
        # Verify state was updated
        assert result["llm_raw_output"] == mock_llm_response
        assert result["llm_parsed"] == mock_parsed
    
    @patch('utils.llm_client.initialize_llm')
    @patch('utils.llm_client.call_llm_with_prompt')
    @patch('utils.llm_client.parse_json_response')
    def test_node_uses_all_available_data(
        self, mock_parse, mock_call_llm, mock_init_llm
    ):
        """Test that node uses all available data in prompt"""
        # Mock LLM
        mock_llm = Mock()
        mock_init_llm.return_value = mock_llm
        mock_call_llm.return_value = '{"title": "Test", "description": "Test", "price_block": "$500"}'
        mock_parse.return_value = {"title": "Test", "description": "Test", "price_block": "$500"}
        
        state: PropertyListingState = {
            "address": "123 Main St",
            "listing_type": "rent",
            "price": 2500.0,
            "notes": "2BR apartment",
            "normalized_address": "123 Main St, New York, NY",
            "normalized_notes": "2BR/1BA apartment",
            "zip_code": "10001",
            "neighborhood": "Midtown",
            "landmarks": ["Central Park"],
            "key_amenities": {"schools": ["PS 123"]},
            "billing_cycle": "monthly",
            "security_deposit": 2500.0,
            "errors": []
        }
        
        result = generate_content_node(state)
        
        # Verify prompt was built with all data
        call_args = mock_call_llm.call_args
        # call_llm_with_prompt(llm, prompt, temperature)
        prompt = call_args[0][1]  # Second positional argument is prompt
        
        # Check that all data is in prompt
        assert "123 Main St, New York, NY" in prompt  # normalized_address
        assert "2BR/1BA" in prompt or "2BR" in prompt  # normalized_notes
        assert "10001" in prompt  # zip_code
        assert "Midtown" in prompt  # neighborhood
        assert "Central Park" in prompt  # landmarks
        assert "PS 123" in prompt or "schools" in prompt.lower()  # amenities
        assert "monthly" in prompt.lower()  # billing_cycle
        assert "2,500" in prompt or "2500" in prompt  # security_deposit (formatted with comma)
        
        # Verify output was stored
        assert "llm_raw_output" in result
        assert "llm_parsed" in result


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestGenerateContentNodeErrorHandling:
    """Test error handling in generate_content_node"""
    
    def test_missing_required_fields(self):
        """Test that missing required fields adds error"""
        state: PropertyListingState = {
            "address": "123 Main St",
            # Missing listing_type and price
            "errors": []
        }
        
        result = generate_content_node(state)
        
        assert "errors" in result
        assert len(result["errors"]) > 0
        assert any("missing required fields" in error.lower() for error in result["errors"])
    
    @patch('utils.llm_client.initialize_llm')
    def test_llm_initialization_failure(self, mock_init_llm):
        """Test that LLM initialization failure is handled"""
        mock_init_llm.side_effect = Exception("API Key Error")
        
        state: PropertyListingState = {
            "address": "123 Main St",
            "listing_type": "sale",
            "price": 500000.0,
            "errors": []
        }
        
        result = generate_content_node(state)
        
        # Should continue without crashing
        assert result is not None
        assert "errors" in result
        assert len(result["errors"]) > 0
        assert any("Content generation failed" in error for error in result["errors"])
    
    @patch('utils.llm_client.initialize_llm')
    @patch('utils.llm_client.call_llm_with_prompt')
    def test_llm_call_failure(self, mock_call_llm, mock_init_llm):
        """Test that LLM call failure is handled"""
        mock_llm = Mock()
        mock_init_llm.return_value = mock_llm
        mock_call_llm.side_effect = Exception("API Error")
        
        state: PropertyListingState = {
            "address": "123 Main St",
            "listing_type": "sale",
            "price": 500000.0,
            "errors": []
        }
        
        result = generate_content_node(state)
        
        # Should continue without crashing
        assert result is not None
        assert "errors" in result
        assert len(result["errors"]) > 0
    
    @patch('utils.llm_client.initialize_llm')
    @patch('utils.llm_client.call_llm_with_prompt')
    @patch('utils.llm_client.parse_json_response')
    def test_json_parsing_failure(self, mock_parse, mock_call_llm, mock_init_llm):
        """Test that JSON parsing failure is handled"""
        mock_llm = Mock()
        mock_init_llm.return_value = mock_llm
        mock_call_llm.return_value = "Invalid JSON response"
        mock_parse.side_effect = ValueError("Failed to parse JSON")
        
        state: PropertyListingState = {
            "address": "123 Main St",
            "listing_type": "sale",
            "price": 500000.0,
            "errors": []
        }
        
        result = generate_content_node(state)
        
        # Should continue without crashing
        assert result is not None
        assert "errors" in result
        assert len(result["errors"]) > 0
        # Raw output should still be stored
        assert result["llm_raw_output"] == "Invalid JSON response"


# ============================================================================
# Edge Cases
# ============================================================================

class TestGenerateContentNodeEdgeCases:
    """Test edge cases for generate_content_node"""
    
    @patch('utils.llm_client.initialize_llm')
    @patch('utils.llm_client.call_llm_with_prompt')
    @patch('utils.llm_client.parse_json_response')
    def test_node_preserves_existing_state(
        self, mock_parse, mock_call_llm, mock_init_llm
    ):
        """Test that node preserves existing state fields"""
        mock_llm = Mock()
        mock_init_llm.return_value = mock_llm
        mock_call_llm.return_value = '{"title": "Test", "description": "Test", "price_block": "$500"}'
        mock_parse.return_value = {"title": "Test", "description": "Test", "price_block": "$500"}
        
        state: PropertyListingState = {
            "address": "123 Main St",
            "listing_type": "sale",
            "price": 500000.0,
            "normalized_address": "123 Main St, NY",
            "zip_code": "10001",
            "errors": []
        }
        
        result = generate_content_node(state)
        
        # Should preserve existing fields
        assert result["address"] == "123 Main St"
        assert result["listing_type"] == "sale"
        assert result["normalized_address"] == "123 Main St, NY"
        assert result["zip_code"] == "10001"
    
    @patch('utils.llm_client.initialize_llm')
    @patch('utils.llm_client.call_llm_with_prompt')
    @patch('utils.llm_client.parse_json_response')
    def test_node_with_minimal_data(
        self, mock_parse, mock_call_llm, mock_init_llm
    ):
        """Test node with minimal required data only"""
        mock_llm = Mock()
        mock_init_llm.return_value = mock_llm
        mock_call_llm.return_value = '{"title": "Test", "description": "Test", "price_block": "$500"}'
        mock_parse.return_value = {"title": "Test", "description": "Test", "price_block": "$500"}
        
        state: PropertyListingState = {
            "address": "123 Main St",
            "listing_type": "sale",
            "price": 500000.0,
            "errors": []
        }
        
        result = generate_content_node(state)
        
        # Should still work with minimal data
        assert "llm_raw_output" in result
        assert "llm_parsed" in result
    
    def test_errors_list_initialized_if_missing(self):
        """Test that errors list is initialized if missing"""
        state: PropertyListingState = {
            "address": "123 Main St",
            "listing_type": "sale",
            "price": 500000.0
            # errors not present
        }
        
        # Mock to avoid actual LLM call
        with patch('utils.llm_client.initialize_llm') as mock_init:
            mock_init.side_effect = Exception("Test error")
            result = generate_content_node(state)
        
        assert "errors" in result
        assert isinstance(result["errors"], list)

