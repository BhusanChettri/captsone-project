"""
Unit tests for prompt building utilities.

Tests cover:
- Prompt construction with all data fields
- Prompt with minimal data
- Prompt with enrichment data
- Edge cases
"""

import pytest
import sys
from pathlib import Path

# Add src to path so we can import
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.prompts import build_listing_generation_prompt


# ============================================================================
# Basic Prompt Construction Tests
# ============================================================================

class TestPromptConstruction:
    """Test prompt construction with various data combinations"""
    
    def test_prompt_with_minimal_data(self):
        """Test prompt with only required fields"""
        prompt = build_listing_generation_prompt(
            address="123 Main St, New York, NY",
            listing_type="sale",
            price=500000.0
        )
        
        assert "123 Main St, New York, NY" in prompt
        assert "sale" in prompt.upper() or "SALE" in prompt
        assert "$500,000.00" in prompt or "500000" in prompt
        assert "title" in prompt.lower()
        assert "description" in prompt.lower()
        assert "price_block" in prompt.lower()
        assert "JSON" in prompt or "json" in prompt
    
    def test_prompt_with_notes(self):
        """Test prompt includes notes"""
        prompt = build_listing_generation_prompt(
            address="123 Main St",
            listing_type="rent",
            price=2500.0,
            notes="2BR/1BA apartment, modern kitchen"
        )
        
        assert "2BR/1BA" in prompt or "2BR" in prompt
        assert "apartment" in prompt.lower()
        assert "kitchen" in prompt.lower()
    
    def test_prompt_with_normalized_data(self):
        """Test prompt uses normalized data when available"""
        prompt = build_listing_generation_prompt(
            address="123   Main   St",
            listing_type="sale",
            price=500000.0,
            normalized_address="123 Main St, New York, NY",
            normalized_notes="2BR/1BA apartment"
        )
        
        # Should use normalized address
        assert "123 Main St, New York, NY" in prompt
        assert "2BR/1BA" in prompt or "2BR" in prompt
    
    def test_prompt_with_rental_fields(self):
        """Test prompt includes rental-specific fields"""
        prompt = build_listing_generation_prompt(
            address="123 Main St",
            listing_type="rent",
            price=2500.0,
            billing_cycle="monthly",
            lease_term="12 months",
            security_deposit=2500.0
        )
        
        assert "monthly" in prompt.lower()
        assert "12 months" in prompt.lower() or "12" in prompt
        assert "2,500" in prompt or "2500" in prompt  # Security deposit (formatted with comma)
        assert "rent" in prompt.lower()
    
    def test_prompt_with_sale_fields(self):
        """Test prompt includes sale-specific fields"""
        prompt = build_listing_generation_prompt(
            address="123 Main St",
            listing_type="sale",
            price=500000.0,
            hoa_fees=200.0,
            property_taxes=5000.0
        )
        
        assert "200" in prompt  # HOA fees
        assert "5,000" in prompt or "5000" in prompt  # Property taxes (formatted with comma)
        assert "sale" in prompt.lower()
    
    def test_prompt_with_enrichment_data(self):
        """Test prompt includes enrichment data"""
        prompt = build_listing_generation_prompt(
            address="123 Main St",
            listing_type="sale",
            price=500000.0,
            zip_code="10001",
            neighborhood="Midtown Manhattan",
            landmarks=["Central Park", "Times Square"],
            key_amenities={
                "schools": ["PS 123"],
                "parks": ["Central Park"],
                "shopping": ["Macy's"],
                "transportation": ["Subway: 1, 2, 3"]
            }
        )
        
        assert "10001" in prompt
        assert "Midtown Manhattan" in prompt
        assert "Central Park" in prompt
        assert "Times Square" in prompt
        assert "PS 123" in prompt or "schools" in prompt.lower()
        assert "Macy" in prompt or "shopping" in prompt.lower()
        assert "Subway" in prompt or "transportation" in prompt.lower()
    
    def test_prompt_includes_instructions(self):
        """Test prompt includes generation instructions"""
        prompt = build_listing_generation_prompt(
            address="123 Main St",
            listing_type="sale",
            price=500000.0
        )
        
        assert "INSTRUCTIONS" in prompt or "instructions" in prompt.lower()
        assert "TITLE" in prompt or "title" in prompt.lower()
        assert "DESCRIPTION" in prompt or "description" in prompt.lower()
        assert "PRICE_BLOCK" in prompt or "price_block" in prompt.lower()
        assert "JSON" in prompt or "json" in prompt
    
    def test_prompt_includes_guidelines(self):
        """Test prompt includes important guidelines"""
        prompt = build_listing_generation_prompt(
            address="123 Main St",
            listing_type="sale",
            price=500000.0
        )
        
        assert "GUIDELINES" in prompt or "guidelines" in prompt.lower()
        assert "factual" in prompt.lower() or "accurate" in prompt.lower()
        assert "not invent" in prompt.lower() or "do not invent" in prompt.lower()
        assert "property listing" in prompt.lower()


# ============================================================================
# Edge Cases
# ============================================================================

class TestPromptEdgeCases:
    """Test edge cases for prompt construction"""
    
    def test_prompt_with_empty_notes(self):
        """Test prompt handles empty notes"""
        prompt = build_listing_generation_prompt(
            address="123 Main St",
            listing_type="sale",
            price=500000.0,
            notes=""
        )
        
        # Should still work without notes
        assert "123 Main St" in prompt
        assert "sale" in prompt.lower()
    
    def test_prompt_with_none_values(self):
        """Test prompt handles None values gracefully"""
        prompt = build_listing_generation_prompt(
            address="123 Main St",
            listing_type="sale",
            price=500000.0,
            notes=None,
            zip_code=None,
            neighborhood=None,
            landmarks=None,
            key_amenities=None
        )
        
        # Should still work
        assert "123 Main St" in prompt
        assert "sale" in prompt.lower()
    
    def test_prompt_with_empty_amenities(self):
        """Test prompt handles empty amenities"""
        prompt = build_listing_generation_prompt(
            address="123 Main St",
            listing_type="sale",
            price=500000.0,
            key_amenities={}
        )
        
        # Should still work
        assert "123 Main St" in prompt
    
    def test_prompt_with_partial_amenities(self):
        """Test prompt handles partial amenities"""
        prompt = build_listing_generation_prompt(
            address="123 Main St",
            listing_type="sale",
            price=500000.0,
            key_amenities={
                "schools": ["PS 123"],
                "parks": [],
                "shopping": None,
                "transportation": ["Subway"]
            }
        )
        
        # Should include schools and transportation
        assert "PS 123" in prompt or "schools" in prompt.lower()
        assert "Subway" in prompt or "transportation" in prompt.lower()

