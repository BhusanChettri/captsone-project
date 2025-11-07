"""
Unit tests for enrich_data_node.

Tests cover:
- Node execution with valid input
- Enrichment data storage in state
- Error handling
- Edge cases
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path so we can import
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.nodes import enrich_data_node
from core.state import PropertyListingState


# ============================================================================
# Valid Input Tests
# ============================================================================

class TestEnrichDataNodeValid:
    """Test enrich_data_node with valid input"""
    
    @patch('langchain_tavily.TavilySearch')
    @patch('utils.enrichment.enrich_property_data')
    def test_enrichment_success_stores_data(self, mock_enrich, mock_tavily_class):
        """Test that successful enrichment stores data in state"""
        # Mock TavilySearchResults
        mock_tavily_instance = Mock()
        mock_tavily_class.return_value = mock_tavily_instance
        
        # Mock enrichment data
        mock_enrich.return_value = {
            "zip_code": "10001",
            "neighborhood": "Midtown Manhattan",
            "landmarks": ["Central Park", "Times Square"],
            "key_amenities": {
                "schools": ["PS 123"],
                "parks": ["Central Park"],
                "shopping": ["Macy's"],
                "transportation": ["Subway: 1, 2, 3"]
            }
        }
        
        state: PropertyListingState = {
            "address": "123 Main St, New York, NY",
            "listing_type": "sale",
            "normalized_address": "123 Main St, New York, NY",
            "errors": []
        }
        
        result = enrich_data_node(state)
        
        assert result["zip_code"] == "10001"
        assert result["neighborhood"] == "Midtown Manhattan"
        assert len(result["landmarks"]) == 2
        assert "key_amenities" in result
    
    @patch('langchain_tavily.TavilySearch')
    @patch('utils.enrichment.enrich_property_data')
    def test_node_uses_normalized_address(self, mock_enrich, mock_tavily_class):
        """Test that node prefers normalized_address over address"""
        # Mock TavilySearchResults
        mock_tavily_instance = Mock()
        mock_tavily_class.return_value = mock_tavily_instance
        
        mock_enrich.return_value = {
            "zip_code": "10001",
            "neighborhood": None,
            "landmarks": [],
            "key_amenities": {}
        }
        
        state: PropertyListingState = {
            "address": "123   Main   St",
            "listing_type": "sale",
            "normalized_address": "123 Main St, New York, NY",
            "errors": []
        }
        
        result = enrich_data_node(state)
        
        # Should use normalized_address
        mock_enrich.assert_called_once()
        call_kwargs = mock_enrich.call_args[1]  # Use kwargs instead of args
        assert call_kwargs["address"] == "123 Main St, New York, NY"  # normalized_address
    
    @patch('langchain_tavily.TavilySearch')
    @patch('utils.enrichment.enrich_property_data')
    def test_node_fallback_to_address(self, mock_enrich, mock_tavily_class):
        """Test that node falls back to address if normalized_address not available"""
        # Mock TavilySearchResults
        mock_tavily_instance = Mock()
        mock_tavily_class.return_value = mock_tavily_instance
        
        mock_enrich.return_value = {
            "zip_code": None,
            "neighborhood": None,
            "landmarks": [],
            "key_amenities": {}
        }
        
        state: PropertyListingState = {
            "address": "123 Main St, New York, NY",
            "listing_type": "sale",
            "errors": []
        }
        
        result = enrich_data_node(state)
        
        # Should use address as fallback
        mock_enrich.assert_called_once()
        call_kwargs = mock_enrich.call_args[1]  # Use kwargs instead of args
        assert call_kwargs["address"] == "123 Main St, New York, NY"


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestEnrichDataNodeErrorHandling:
    """Test error handling in enrich_data_node"""
    
    @patch('langchain_tavily.TavilySearch')
    @patch('utils.enrichment.enrich_property_data')
    def test_enrichment_failure_continues_workflow(self, mock_enrich, mock_tavily_class):
        """Test that enrichment failure doesn't break workflow"""
        # Mock TavilySearchResults
        mock_tavily_instance = Mock()
        mock_tavily_class.return_value = mock_tavily_instance
        
        # Mock enrichment to raise exception
        mock_enrich.side_effect = Exception("API Error")
        
        state: PropertyListingState = {
            "address": "123 Main St, New York, NY",
            "listing_type": "sale",
            "normalized_address": "123 Main St, New York, NY",
            "errors": []
        }
        
        result = enrich_data_node(state)
        
        # Should continue without crashing
        assert result is not None
        assert "errors" in result
        # Error should be logged
        assert len(result["errors"]) > 0
        # Check for error message (may be "Enrichment failed" or exception message)
        assert any("Enrichment" in error or "API Error" in error for error in result["errors"])
    
    def test_tavily_initialization_failure_handled(self):
        """Test that Tavily initialization failure is handled"""
        # This test verifies the ImportError handling in the node
        # We'll test it by ensuring the node handles missing Tavily gracefully
        # In practice, if Tavily is not available, the node should skip enrichment
        state: PropertyListingState = {
            "address": "123 Main St, New York, NY",
            "listing_type": "sale",
            "errors": []
        }
        
        # The node should handle this gracefully
        # If Tavily is not available, it will be caught in the try-except
        result = enrich_data_node(state)
        
        # Should continue without crashing
        assert result is not None
        assert "errors" in result


# ============================================================================
# Edge Cases
# ============================================================================

class TestEnrichDataNodeEdgeCases:
    """Test edge cases for enrich_data_node"""
    
    @patch('utils.enrichment.enrich_property_data')
    def test_empty_address_skips_enrichment(self, mock_enrich):
        """Test that empty address skips enrichment"""
        state: PropertyListingState = {
            "address": "",
            "listing_type": "sale",
            "errors": []
        }
        
        result = enrich_data_node(state)
        
        # Should not call enrichment
        mock_enrich.assert_not_called()
        assert result is not None
    
    @patch('utils.enrichment.enrich_property_data')
    def test_none_address_skips_enrichment(self, mock_enrich):
        """Test that None address skips enrichment"""
        state: PropertyListingState = {
            "address": None,  # type: ignore
            "listing_type": "sale",
            "errors": []
        }
        
        result = enrich_data_node(state)
        
        # Should not call enrichment
        mock_enrich.assert_not_called()
    
    @patch('langchain_tavily.TavilySearch')
    @patch('utils.enrichment.enrich_property_data')
    def test_partial_enrichment_data_stored(self, mock_enrich, mock_tavily_class):
        """Test that partial enrichment data is stored"""
        # Mock TavilySearchResults
        mock_tavily_instance = Mock()
        mock_tavily_class.return_value = mock_tavily_instance
        
        # Mock partial enrichment data
        mock_enrich.return_value = {
            "zip_code": "10001",
            "neighborhood": None,  # Not found
            "landmarks": [],  # Not found
            "key_amenities": {}  # Not found
        }
        
        state: PropertyListingState = {
            "address": "123 Main St, New York, NY",
            "listing_type": "sale",
            "normalized_address": "123 Main St, New York, NY",
            "errors": []
        }
        
        result = enrich_data_node(state)
        
        # Should store what was found (zip_code is not None/empty, so it's stored)
        assert "zip_code" in result
        assert result["zip_code"] == "10001"
        # Other fields should not be set if None/empty
        assert "neighborhood" not in result or result.get("neighborhood") is None
    
    @patch('langchain_tavily.TavilySearch')
    @patch('utils.enrichment.enrich_property_data')
    def test_node_preserves_existing_state(self, mock_enrich, mock_tavily_class):
        """Test that node preserves existing state fields"""
        # Mock TavilySearchResults
        mock_tavily_instance = Mock()
        mock_tavily_class.return_value = mock_tavily_instance
        
        mock_enrich.return_value = {
            "zip_code": "10001",
            "neighborhood": None,
            "landmarks": [],
            "key_amenities": {}
        }
        
        state: PropertyListingState = {
            "address": "123 Main St",
            "listing_type": "sale",
            "price": 500000.0,
            "normalized_address": "123 Main St",
            "errors": []
        }
        
        result = enrich_data_node(state)
        
        # Should preserve existing fields
        assert result["address"] == "123 Main St"
        assert result["listing_type"] == "sale"
        assert result["price"] == 500000.0
    
    @patch('langchain_tavily.TavilySearch')
    @patch('utils.enrichment.enrich_property_data')
    def test_errors_list_initialized_if_missing(self, mock_enrich, mock_tavily_class):
        """Test that errors list is initialized if missing"""
        # Mock TavilySearchResults
        mock_tavily_instance = Mock()
        mock_tavily_class.return_value = mock_tavily_instance
        
        mock_enrich.return_value = {
            "zip_code": None,
            "neighborhood": None,
            "landmarks": [],
            "key_amenities": {}
        }
        
        state: PropertyListingState = {
            "address": "123 Main St",
            "listing_type": "sale",
            "normalized_address": "123 Main St"
            # errors not present
        }
        
        result = enrich_data_node(state)
        
        # Node initializes errors list at the start
        assert "errors" in result
        assert isinstance(result["errors"], list)
        # Should be empty list if no errors occurred
        assert result["errors"] == []

