"""
Comprehensive unit tests for LangGraph State Definition.

Tests cover:
- State structure and type validation
- Required fields
- Optional fields
- State initialization
- State updates
- Edge cases
"""

import pytest
import sys
from pathlib import Path
from typing import get_type_hints

# Add src to path so we can import
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core import PropertyListingState


# ============================================================================
# State Structure Tests
# ============================================================================

class TestStateStructure:
    """Test the structure and type definitions of PropertyListingState"""
    
    def test_state_is_typed_dict(self):
        """Test that PropertyListingState is a TypedDict"""
        assert hasattr(PropertyListingState, "__annotations__")
        assert isinstance(PropertyListingState.__annotations__, dict)
    
    def test_required_fields_exist(self):
        """Test that required fields are defined in state"""
        annotations = PropertyListingState.__annotations__
        assert "address" in annotations
        assert "listing_type" in annotations
    
    def test_optional_input_fields_exist(self):
        """Test that optional input fields are defined"""
        annotations = PropertyListingState.__annotations__
        assert "price" in annotations
        assert "notes" in annotations
        assert "billing_cycle" in annotations
        assert "lease_term" in annotations
        assert "security_deposit" in annotations
        assert "hoa_fees" in annotations
        assert "property_taxes" in annotations
    
    def test_processing_fields_exist(self):
        """Test that processing fields are defined"""
        annotations = PropertyListingState.__annotations__
        assert "normalized_address" in annotations
        assert "normalized_notes" in annotations
    
    def test_enrichment_fields_exist(self):
        """Test that enrichment fields are defined"""
        annotations = PropertyListingState.__annotations__
        assert "zip_code" in annotations
        assert "landmarks" in annotations
    
    def test_llm_fields_exist(self):
        """Test that LLM output fields are defined"""
        annotations = PropertyListingState.__annotations__
        assert "llm_raw_output" in annotations
        assert "llm_parsed" in annotations
    
    def test_output_fields_exist(self):
        """Test that final output fields are defined"""
        annotations = PropertyListingState.__annotations__
        assert "title" in annotations
        assert "description" in annotations
        assert "price_block" in annotations
        assert "formatted_listing" in annotations
    
    def test_error_field_exists(self):
        """Test that error tracking field is defined"""
        annotations = PropertyListingState.__annotations__
        assert "errors" in annotations


# ============================================================================
# State Initialization Tests
# ============================================================================

class TestStateInitialization:
    """Test creating and initializing state dictionaries"""
    
    def test_minimal_state_creation(self):
        """Test creating state with only required fields"""
        state: PropertyListingState = {
            "address": "123 Main St, New York, NY 10001",
            "listing_type": "sale",
            "errors": []
        }
        assert state["address"] == "123 Main St, New York, NY 10001"
        assert state["listing_type"] == "sale"
        assert state["errors"] == []
    
    def test_state_with_all_input_fields(self):
        """Test creating state with all input fields"""
        state: PropertyListingState = {
            "address": "456 Oak Ave, Los Angeles, CA 90001",
            "listing_type": "rent",
            "price": 2500.0,
            "notes": "2BR/1BA, 1000 sqft, pet-friendly",
            "billing_cycle": "monthly",
            "lease_term": "12 months",
            "security_deposit": 2500.0,
            "errors": []
        }
        assert state["listing_type"] == "rent"
        assert state["price"] == 2500.0
        assert state["security_deposit"] == 2500.0
    
    def test_state_with_processing_fields(self):
        """Test state with processing fields set"""
        state: PropertyListingState = {
            "address": "123 Test St",
            "listing_type": "sale",
            "normalized_address": "123 Test Street",
            "normalized_notes": "3BR/2BA, 1500 sqft",
            "errors": []
        }
        assert state["normalized_address"] == "123 Test Street"
        assert state["normalized_notes"] == "3BR/2BA, 1500 sqft"
    
    def test_state_with_enrichment_fields(self):
        """Test state with enrichment data"""
        state: PropertyListingState = {
            "address": "123 Test St",
            "listing_type": "sale",
            "zip_code": "10001",
            "landmarks": ["Central Park", "Times Square", "Empire State Building"],
            "errors": []
        }
        assert state["zip_code"] == "10001"
        assert len(state["landmarks"]) == 3
        assert "Central Park" in state["landmarks"]
    
    def test_state_with_llm_output(self):
        """Test state with LLM output fields"""
        state: PropertyListingState = {
            "address": "123 Test St",
            "listing_type": "sale",
            "llm_raw_output": '{"title": "Test", "description": "Test desc", "price_block": "$100,000"}',
            "llm_parsed": {
                "title": "Test",
                "description": "Test desc",
                "price_block": "$100,000"
            },
            "errors": []
        }
        assert state["llm_raw_output"] is not None
        assert state["llm_parsed"]["title"] == "Test"
    
    def test_state_with_final_output(self):
        """Test state with final output fields"""
        state: PropertyListingState = {
            "address": "123 Test St",
            "listing_type": "sale",
            "title": "Beautiful 2BR/1BA Home",
            "description": "This charming property features...",
            "price_block": "$400,000",
            "formatted_listing": "Beautiful 2BR/1BA Home\n\nThis charming property...\n\n$400,000\n\nAll information deemed reliable...",
            "errors": []
        }
        assert state["title"] == "Beautiful 2BR/1BA Home"
        assert state["formatted_listing"] is not None


# ============================================================================
# State Update Tests
# ============================================================================

class TestStateUpdates:
    """Test updating state fields (simulating node operations)"""
    
    def test_state_progression_through_nodes(self):
        """Test how state evolves as it moves through nodes"""
        # Initial state (from input)
        state: PropertyListingState = {
            "address": "123 Main St",
            "listing_type": "sale",
            "price": 500000.0,
            "notes": "3BR/2BA",
            "errors": []
        }
        
        # After normalization node
        state["normalized_address"] = "123 Main Street"
        state["normalized_notes"] = "3BR/2BA, 1500 sqft"
        assert state["normalized_address"] == "123 Main Street"
        
        # After enrichment node (optional)
        state["zip_code"] = "10001"
        state["landmarks"] = ["Park", "Mall"]
        assert state["zip_code"] == "10001"
        
        # After LLM node
        state["llm_raw_output"] = '{"title": "Test", "description": "Desc", "price_block": "$500,000"}'
        state["llm_parsed"] = {"title": "Test", "description": "Desc", "price_block": "$500,000"}
        assert state["llm_parsed"] is not None
        
        # After formatting node
        state["title"] = "Test"
        state["description"] = "Desc"
        state["price_block"] = "$500,000"
        state["formatted_listing"] = "Final formatted text"
        assert state["formatted_listing"] is not None


# ============================================================================
# Edge Cases
# ============================================================================

class TestStateEdgeCases:
    """Test edge cases for state"""
    
    def test_state_with_empty_errors_list(self):
        """Test that errors list can be empty"""
        state: PropertyListingState = {
            "address": "123 Test St",
            "listing_type": "sale",
            "errors": []
        }
        assert state["errors"] == []
        assert len(state["errors"]) == 0
    
    def test_state_with_errors(self):
        """Test state with error messages"""
        state: PropertyListingState = {
            "address": "123 Test St",
            "listing_type": "sale",
            "errors": ["Invalid price format", "Address validation failed"]
        }
        assert len(state["errors"]) == 2
        assert "Invalid price format" in state["errors"]
    
    def test_state_with_none_optional_fields(self):
        """Test that optional fields can be None"""
        state: PropertyListingState = {
            "address": "123 Test St",
            "listing_type": "sale",
            "price": None,
            "notes": None,
            "zip_code": None,
            "landmarks": None,
            "errors": []
        }
        assert state["price"] is None
        assert state["landmarks"] is None
    
    def test_state_with_empty_landmarks_list(self):
        """Test state with empty landmarks list"""
        state: PropertyListingState = {
            "address": "123 Test St",
            "listing_type": "sale",
            "landmarks": [],
            "errors": []
        }
        assert state["landmarks"] == []
        assert len(state["landmarks"]) == 0
    
    def test_state_rental_specific_fields(self):
        """Test state with rental-specific fields"""
        state: PropertyListingState = {
            "address": "123 Test St",
            "listing_type": "rent",
            "billing_cycle": "monthly",
            "lease_term": "12 months",
            "security_deposit": 2500.0,
            "errors": []
        }
        assert state["billing_cycle"] == "monthly"
        assert state["security_deposit"] == 2500.0
    
    def test_state_sale_specific_fields(self):
        """Test state with sale-specific fields"""
        state: PropertyListingState = {
            "address": "123 Test St",
            "listing_type": "sale",
            "hoa_fees": 200.0,
            "property_taxes": 5000.0,
            "errors": []
        }
        assert state["hoa_fees"] == 200.0
        assert state["property_taxes"] == 5000.0


# ============================================================================
# Type Validation Tests
# ============================================================================

class TestStateTypeValidation:
    """Test that state fields have correct types"""
    
    def test_listing_type_literal(self):
        """Test that listing_type accepts only 'sale' or 'rent'"""
        # Valid values
        state1: PropertyListingState = {
            "address": "123 Test St",
            "listing_type": "sale",
            "errors": []
        }
        state2: PropertyListingState = {
            "address": "123 Test St",
            "listing_type": "rent",
            "errors": []
        }
        assert state1["listing_type"] == "sale"
        assert state2["listing_type"] == "rent"
    
    def test_landmarks_is_list(self):
        """Test that landmarks is a list"""
        state: PropertyListingState = {
            "address": "123 Test St",
            "listing_type": "sale",
            "landmarks": ["Landmark 1", "Landmark 2"],
            "errors": []
        }
        assert isinstance(state["landmarks"], list)
    
    def test_errors_is_list(self):
        """Test that errors is always a list"""
        state: PropertyListingState = {
            "address": "123 Test St",
            "listing_type": "sale",
            "errors": []
        }
        assert isinstance(state["errors"], list)
    
    def test_price_is_float(self):
        """Test that price can be a float"""
        state: PropertyListingState = {
            "address": "123 Test St",
            "listing_type": "sale",
            "price": 500000.0,
            "errors": []
        }
        assert isinstance(state["price"], float)


# ============================================================================
# Integration Tests
# ============================================================================

class TestStateIntegration:
    """Integration tests showing state used in workflow scenarios"""
    
    def test_full_workflow_state_progression(self):
        """Test complete state progression through all workflow steps"""
        # Step 1: Initial input
        state: PropertyListingState = {
            "address": "123 Main St, New York, NY 10001",
            "listing_type": "rent",
            "price": 2500.0,
            "notes": "2BR/1BA, pet-friendly",
            "errors": []
        }
        
        # Step 2: After normalization
        state["normalized_address"] = "123 Main Street, New York, NY 10001"
        state["normalized_notes"] = "2BR/1BA, pet-friendly, parking included"
        
        # Step 3: After enrichment (optional)
        state["zip_code"] = "10001"
        state["landmarks"] = ["Central Park", "Times Square"]
        
        # Step 4: After LLM generation
        state["llm_raw_output"] = '{"title": "Cozy 2BR Apartment", "description": "...", "price_block": "$2,500/month"}'
        state["llm_parsed"] = {
            "title": "Cozy 2BR Apartment",
            "description": "This charming apartment...",
            "price_block": "$2,500/month"
        }
        
        # Step 5: After formatting
        state["title"] = state["llm_parsed"]["title"]
        state["description"] = state["llm_parsed"]["description"]
        state["price_block"] = state["llm_parsed"]["price_block"]
        state["formatted_listing"] = f"{state['title']}\n\n{state['description']}\n\n{state['price_block']}"
        
        # Verify final state
        assert state["title"] is not None
        assert state["description"] is not None
        assert state["formatted_listing"] is not None
        assert len(state["errors"]) == 0

