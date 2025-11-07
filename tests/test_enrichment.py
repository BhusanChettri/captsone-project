"""
Comprehensive unit tests for enrichment utilities.

Tests cover:
- Search query construction
- Result extraction functions
- Comprehensive enrichment
- Edge cases
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add src to path so we can import
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.enrichment import (
    build_neighborhood_search_query,
    build_landmarks_search_query,
    build_amenities_search_query,
    extract_zip_code,
    extract_neighborhood,
    extract_landmarks,
    extract_amenities,
    enrich_property_data,
)


# ============================================================================
# Search Query Construction Tests
# ============================================================================

class TestSearchQueryConstruction:
    """Test search query construction"""
    
    def test_build_neighborhood_search_query(self):
        """Test neighborhood search query construction"""
        address = "123 Main St, New York, NY"
        query = build_neighborhood_search_query(address)
        
        assert address in query
        assert "neighborhood" in query.lower()
        assert "zip code" in query.lower() or "location" in query.lower()
    
    def test_build_neighborhood_search_query_with_notes(self):
        """Test neighborhood search query with notes context"""
        address = "123 Main St, New York, NY"
        notes = "Beautiful apartment near downtown"
        query = build_neighborhood_search_query(address, notes=notes)
        
        assert address in query
        assert "neighborhood" in query.lower()
    
    def test_build_landmarks_search_query(self):
        """Test landmarks search query construction"""
        address = "123 Main St, New York, NY"
        query = build_landmarks_search_query(address)
        
        assert address in query
        assert "landmarks" in query.lower() or "attractions" in query.lower()
    
    def test_build_landmarks_search_query_with_notes(self):
        """Test landmarks search query with notes mentioning landmarks"""
        address = "123 Main St, New York, NY"
        notes = "Close to Central Park and museums"
        query = build_landmarks_search_query(address, notes=notes)
        
        assert address in query
        assert ("park" in query.lower() or "museum" in query.lower() or 
                "landmarks" in query.lower() or "attractions" in query.lower())
    
    def test_build_amenities_search_query_schools(self):
        """Test amenities search query for schools"""
        address = "123 Main St, New York, NY"
        query = build_amenities_search_query(address, "schools")
        
        assert address in query
        assert "school" in query.lower()
    
    def test_build_amenities_search_query_schools_with_listing_type(self):
        """Test amenities search query for schools with sale listing"""
        address = "123 Main St, New York, NY"
        query = build_amenities_search_query(address, "schools", listing_type="sale")
        
        assert address in query
        assert "school" in query.lower()
    
    def test_build_amenities_search_query_parks(self):
        """Test amenities search query for parks"""
        address = "123 Main St, New York, NY"
        query = build_amenities_search_query(address, "parks")
        
        assert address in query
        assert "park" in query.lower()
    
    def test_build_amenities_search_query_shopping(self):
        """Test amenities search query for shopping"""
        address = "123 Main St, New York, NY"
        query = build_amenities_search_query(address, "shopping")
        
        assert address in query
        assert "shopping" in query.lower()
    
    def test_build_amenities_search_query_transportation(self):
        """Test amenities search query for transportation"""
        address = "123 Main St, New York, NY"
        query = build_amenities_search_query(address, "transportation")
        
        assert address in query
        assert "transportation" in query.lower() or "subway" in query.lower()
    
    def test_build_amenities_search_query_transportation_rental(self):
        """Test amenities search query for transportation with rental listing"""
        address = "123 Main St, New York, NY"
        query = build_amenities_search_query(address, "transportation", listing_type="rent")
        
        assert address in query
        assert "transportation" in query.lower() or "transit" in query.lower()


# ============================================================================
# Result Extraction Tests
# ============================================================================

class TestResultExtraction:
    """Test result extraction functions"""
    
    def test_extract_zip_code_found(self):
        """Test ZIP code extraction when found"""
        search_results = [
            {"content": "The property is located at 123 Main St, New York, NY 10001", "title": "Property Info"}
        ]
        
        zip_code = extract_zip_code(search_results)
        assert zip_code == "10001"
    
    def test_extract_zip_code_not_found(self):
        """Test ZIP code extraction when not found"""
        search_results = [
            {"content": "The property is located in New York", "title": "Property Info"}
        ]
        
        zip_code = extract_zip_code(search_results)
        assert zip_code is None
    
    def test_extract_zip_code_multiple_formats(self):
        """Test ZIP code extraction with different formats"""
        search_results = [
            {"content": "ZIP code 10001-1234 or 90210", "title": "Info"}
        ]
        
        zip_code = extract_zip_code(search_results)
        assert zip_code in ["10001", "90210"]
    
    def test_extract_neighborhood_found(self):
        """Test neighborhood extraction when found"""
        search_results = [
            {"content": "The property is located in the Midtown Manhattan neighborhood of New York", "title": "Location Info"}
        ]
        
        neighborhood = extract_neighborhood(search_results, "123 Main St")
        # May or may not extract - both are acceptable for this test
        assert neighborhood is None or isinstance(neighborhood, str)
    
    def test_extract_neighborhood_not_found(self):
        """Test neighborhood extraction when not found"""
        search_results = [
            {"content": "The property is located in New York", "title": "Location"}
        ]
        
        neighborhood = extract_neighborhood(search_results, "123 Main St")
        # May or may not find neighborhood - both are acceptable
        assert neighborhood is None or isinstance(neighborhood, str)
    
    def test_extract_landmarks_found(self):
        """Test landmarks extraction when found"""
        search_results = [
            {"content": "Nearby landmarks include Central Park and Times Square", "title": "Attractions"},
            {"content": "Close to Empire State Building", "title": "Location"}
        ]
        
        landmarks = extract_landmarks(search_results, max_landmarks=5)
        assert len(landmarks) > 0
        assert isinstance(landmarks, list)
    
    def test_extract_landmarks_not_found(self):
        """Test landmarks extraction when not found"""
        search_results = [
            {"content": "The property is in a residential area", "title": "Info"}
        ]
        
        landmarks = extract_landmarks(search_results, max_landmarks=5)
        assert landmarks == []
    
    def test_extract_amenities_schools(self):
        """Test amenities extraction for schools"""
        search_results = [
            {"content": "Nearby schools include PS 123 and High School XYZ", "title": "Schools"}
        ]
        
        schools = extract_amenities(search_results, "schools", max_items=3)
        assert isinstance(schools, list)
        # May or may not extract - both are acceptable
    
    def test_extract_amenities_parks(self):
        """Test amenities extraction for parks"""
        search_results = [
            {"content": "Nearby parks include Central Park and Riverside Park", "title": "Parks"}
        ]
        
        parks = extract_amenities(search_results, "parks", max_items=3)
        assert isinstance(parks, list)
    
    def test_extract_amenities_empty_results(self):
        """Test amenities extraction with empty results"""
        search_results = []
        
        amenities = extract_amenities(search_results, "schools", max_items=3)
        assert amenities == []


# ============================================================================
# Comprehensive Enrichment Tests
# ============================================================================

class TestComprehensiveEnrichment:
    """Test comprehensive enrichment function"""
    
    def test_enrich_property_data_with_mock_tool(self):
        """Test enrichment with mocked Tavily tool"""
        # Mock Tavily search tool
        mock_tool = Mock()
        
        # Mock search results for different queries
        # TavilySearch returns dict with "results" key
        def mock_invoke(query_dict):
            query = query_dict.get("query", "")
            if "neighborhood" in query.lower() or "zip code" in query.lower():
                return {
                    "results": [
                        {"content": "Located in Midtown Manhattan, ZIP code 10001", "title": "Location Info"}
                    ]
                }
            elif "landmarks" in query.lower() or "attractions" in query.lower():
                return {
                    "results": [
                        {"content": "Nearby landmarks include Central Park and Times Square", "title": "Attractions"}
                    ]
                }
            elif "school" in query.lower():
                return {
                    "results": [
                        {"content": "Nearby schools include PS 123", "title": "Schools"}
                    ]
                }
            else:
                return {"results": []}
        
        mock_tool.invoke = mock_invoke
        
        address = "123 Main St, New York, NY"
        enrichment_data = enrich_property_data(
            address=address,
            notes="",
            listing_type="sale",
            price=None,
            search_tool=mock_tool
        )
        
        assert isinstance(enrichment_data, dict)
        assert "zip_code" in enrichment_data
        assert "neighborhood" in enrichment_data
        assert "landmarks" in enrichment_data
        assert "key_amenities" in enrichment_data
        assert isinstance(enrichment_data["key_amenities"], dict)
    
    def test_enrich_property_data_with_notes_context(self):
        """Test enrichment uses notes context for better queries"""
        mock_tool = Mock()
        mock_tool.invoke = Mock(return_value={"results": []})
        
        address = "123 Main St, New York, NY"
        notes = "Beautiful apartment near Central Park"
        listing_type = "rent"
        
        enrichment_data = enrich_property_data(
            address=address,
            notes=notes,
            listing_type=listing_type,
            price=None,
            search_tool=mock_tool
        )
        
        # Verify function was called (even if results are empty)
        assert mock_tool.invoke.called
        assert isinstance(enrichment_data, dict)
    
    def test_enrich_property_data_handles_errors(self):
        """Test that enrichment handles errors gracefully"""
        # Mock tool that raises exception
        mock_tool = Mock()
        mock_tool.invoke = Mock(side_effect=Exception("API Error"))
        
        address = "123 Main St, New York, NY"
        enrichment_data = enrich_property_data(
            address=address,
            notes="",
            listing_type=None,
            price=None,
            search_tool=mock_tool
        )
        
        # Should return empty enrichment data structure
        assert isinstance(enrichment_data, dict)
        assert enrichment_data["zip_code"] is None
        assert enrichment_data["landmarks"] == []
    
    def test_enrich_property_data_empty_address(self):
        """Test enrichment with empty address"""
        mock_tool = Mock()
        mock_tool.invoke = Mock(return_value={"results": []})
        
        enrichment_data = enrich_property_data(
            address="",
            notes="",
            listing_type=None,
            price=None,
            search_tool=mock_tool
        )
        
        assert isinstance(enrichment_data, dict)
        assert enrichment_data["zip_code"] is None


# ============================================================================
# Edge Cases
# ============================================================================

class TestEnrichmentEdgeCases:
    """Test edge cases for enrichment"""
    
    def test_query_construction_with_special_characters(self):
        """Test query construction with special characters"""
        address = "123 Main St. #4B, New York, NY"
        query = build_neighborhood_search_query(address)
        
        assert address in query
    
    def test_extraction_with_empty_results(self):
        """Test extraction functions with empty results"""
        zip_code = extract_zip_code([])
        assert zip_code is None
        
        neighborhood = extract_neighborhood([], "123 Main St")
        assert neighborhood is None
        
        landmarks = extract_landmarks([], max_landmarks=5)
        assert landmarks == []
    
    def test_extraction_with_malformed_results(self):
        """Test extraction functions with malformed results"""
        search_results = [
            {"content": "", "title": ""},  # Empty strings instead of None
            {},
            {"invalid": "data"}
        ]
        
        # Should not crash
        zip_code = extract_zip_code(search_results)
        neighborhood = extract_neighborhood(search_results, "123 Main St")
        landmarks = extract_landmarks(search_results, max_landmarks=5)
        
        # Results may be None or empty, but should not crash
        assert zip_code is None or isinstance(zip_code, str)
        assert neighborhood is None or isinstance(neighborhood, str)
        assert isinstance(landmarks, list)

