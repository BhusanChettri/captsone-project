"""
Comprehensive unit tests for data models.

Tests cover:
- Valid inputs (happy paths)
- Invalid inputs (validation errors)
- Edge cases (boundary values, empty strings, whitespace, etc.)
- Type validation
- Optional field handling
"""

import pytest
import sys
from pathlib import Path

# Add src to path so we can import
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models import PropertyListingInput, ListingOutput


# ============================================================================
# PropertyListingInput - Valid Input Tests
# ============================================================================

class TestPropertyListingInputValid:
    """Test valid inputs for PropertyListingInput"""
    
    def test_rental_listing_with_all_fields(self):
        """Test creating a rental listing with all optional fields"""
        listing = PropertyListingInput(
            address="123 Main St, New York, NY 10001",
            listing_type="rent",
            price=2500.0,
            notes="2BR/1BA, 1000 sqft, pet-friendly",
            billing_cycle="monthly",
            lease_term="12 months",
            security_deposit=2500.0
        )
        assert listing.address == "123 Main St, New York, NY 10001"
        assert listing.listing_type == "rent"
        assert listing.price == 2500.0
        assert listing.security_deposit == 2500.0
    
    def test_sale_listing_with_all_fields(self):
        """Test creating a sale listing with all optional fields"""
        listing = PropertyListingInput(
            address="456 Oak Ave, Los Angeles, CA 90001",
            listing_type="sale",
            price=750000.0,
            notes="3BR/2BA, 1500 sqft, updated kitchen",
            hoa_fees=200.0,
            property_taxes=8500.0
        )
        assert listing.listing_type == "sale"
        assert listing.price == 750000.0
        assert listing.hoa_fees == 200.0
        assert listing.property_taxes == 8500.0
    
    def test_minimal_required_fields_only(self):
        """Test creating listing with only required fields"""
        listing = PropertyListingInput(
            address="789 Pine Rd, Chicago, IL 60601",
            listing_type="sale",
            price=400000.0,
            notes="2BR/1BA, 900 sqft"
        )
        assert listing.address == "789 Pine Rd, Chicago, IL 60601"
        assert listing.billing_cycle is None
        assert listing.hoa_fees is None
    
    def test_zero_security_deposit(self):
        """Test that zero security deposit is allowed (edge case)"""
        listing = PropertyListingInput(
            address="123 Test St",
            listing_type="rent",
            price=1000.0,
            notes="Test",
            security_deposit=0.0
        )
        assert listing.security_deposit == 0.0
    
    def test_zero_hoa_fees(self):
        """Test that zero HOA fees is allowed (edge case)"""
        listing = PropertyListingInput(
            address="123 Test St",
            listing_type="sale",
            price=100000.0,
            notes="Test",
            hoa_fees=0.0
        )
        assert listing.hoa_fees == 0.0
    
    def test_zero_property_taxes(self):
        """Test that zero property taxes is allowed (edge case)"""
        listing = PropertyListingInput(
            address="123 Test St",
            listing_type="sale",
            price=100000.0,
            notes="Test",
            property_taxes=0.0
        )
        assert listing.property_taxes == 0.0
    
    def test_very_small_price(self):
        """Test very small price value (edge case)"""
        listing = PropertyListingInput(
            address="123 Test St",
            listing_type="rent",
            price=0.01,  # Minimum positive value
            notes="Test"
        )
        assert listing.price == 0.01
    
    def test_very_large_price(self):
        """Test very large price value (edge case)"""
        listing = PropertyListingInput(
            address="123 Test St",
            listing_type="sale",
            price=999999999.99,  # Very large value
            notes="Test"
        )
        assert listing.price == 999999999.99
    
    def test_address_with_special_characters(self):
        """Test address with special characters"""
        listing = PropertyListingInput(
            address="123 Main St. #4B, New York, NY 10001",
            listing_type="sale",
            price=500000.0,
            notes="Test"
        )
        assert "#4B" in listing.address
    
    def test_notes_with_multiline_text(self):
        """Test notes with multiline text"""
        notes = "2BR/1BA\n1000 sqft\nPet-friendly\nParking included"
        listing = PropertyListingInput(
            address="123 Test St",
            listing_type="rent",
            price=2000.0,
            notes=notes
        )
        assert "\n" in listing.notes


# ============================================================================
# PropertyListingInput - Validation Error Tests
# ============================================================================

class TestPropertyListingInputValidationErrors:
    """Test validation errors for PropertyListingInput"""
    
    def test_invalid_listing_type(self):
        """Test that invalid listing_type raises ValueError"""
        with pytest.raises(ValueError, match="listing_type must be 'sale' or 'rent'"):
            PropertyListingInput(
                address="123 Test St",
                listing_type="invalid",
                price=100000.0,
                notes="Test"
            )
    
    def test_listing_type_case_sensitive(self):
        """Test that listing_type is case-sensitive"""
        with pytest.raises(ValueError):
            PropertyListingInput(
                address="123 Test St",
                listing_type="SALE",  # Wrong case
                price=100000.0,
                notes="Test"
            )
    
    def test_negative_price(self):
        """Test that negative price raises ValueError"""
        with pytest.raises(ValueError, match="price must be positive"):
            PropertyListingInput(
                address="123 Test St",
                listing_type="sale",
                price=-1000.0,
                notes="Test"
            )
    
    def test_zero_price(self):
        """Test that zero price raises ValueError (edge case)"""
        with pytest.raises(ValueError, match="price must be positive"):
            PropertyListingInput(
                address="123 Test St",
                listing_type="sale",
                price=0.0,
                notes="Test"
            )
    
    def test_negative_security_deposit(self):
        """Test that negative security_deposit raises ValueError"""
        with pytest.raises(ValueError, match="security_deposit must be non-negative"):
            PropertyListingInput(
                address="123 Test St",
                listing_type="rent",
                price=2000.0,
                notes="Test",
                security_deposit=-500.0
            )
    
    def test_negative_hoa_fees(self):
        """Test that negative hoa_fees raises ValueError"""
        with pytest.raises(ValueError, match="hoa_fees must be non-negative"):
            PropertyListingInput(
                address="123 Test St",
                listing_type="sale",
                price=500000.0,
                notes="Test",
                hoa_fees=-100.0
            )
    
    def test_negative_property_taxes(self):
        """Test that negative property_taxes raises ValueError"""
        with pytest.raises(ValueError, match="property_taxes must be non-negative"):
            PropertyListingInput(
                address="123 Test St",
                listing_type="sale",
                price=500000.0,
                notes="Test",
                property_taxes=-1000.0
            )


# ============================================================================
# PropertyListingInput - Edge Cases
# ============================================================================

class TestPropertyListingInputEdgeCases:
    """Test edge cases for PropertyListingInput"""
    
    def test_empty_address_string(self):
        """Test that empty string address raises ValueError"""
        with pytest.raises(ValueError, match="address cannot be empty"):
            PropertyListingInput(
                address="",
                listing_type="sale",
                price=100000.0,
                notes="Test"
            )
    
    def test_whitespace_only_address(self):
        """Test that whitespace-only address raises ValueError"""
        with pytest.raises(ValueError, match="address cannot be empty"):
            PropertyListingInput(
                address="   ",
                listing_type="sale",
                price=100000.0,
                notes="Test"
            )
    
    def test_empty_notes_string(self):
        """Test that empty string notes raises ValueError"""
        with pytest.raises(ValueError, match="notes cannot be empty"):
            PropertyListingInput(
                address="123 Test St",
                listing_type="sale",
                price=100000.0,
                notes=""
            )
    
    def test_whitespace_only_notes(self):
        """Test that whitespace-only notes raises ValueError"""
        with pytest.raises(ValueError, match="notes cannot be empty"):
            PropertyListingInput(
                address="123 Test St",
                listing_type="sale",
                price=100000.0,
                notes="   \n\t  "
            )
    
    def test_very_long_address(self):
        """Test very long address string (edge case)"""
        long_address = "A" * 1000
        listing = PropertyListingInput(
            address=long_address,
            listing_type="sale",
            price=100000.0,
            notes="Test"
        )
        assert len(listing.address) == 1000
    
    def test_very_long_notes(self):
        """Test very long notes string (edge case)"""
        long_notes = "Test " * 1000
        listing = PropertyListingInput(
            address="123 Test St",
            listing_type="sale",
            price=100000.0,
            notes=long_notes
        )
        assert len(listing.notes) > 1000
    
    def test_float_price_precision(self):
        """Test float price with many decimal places"""
        listing = PropertyListingInput(
            address="123 Test St",
            listing_type="sale",
            price=123456.789012345,
            notes="Test"
        )
        assert listing.price == 123456.789012345
    
    def test_optional_fields_all_none(self):
        """Test that all optional fields can be None"""
        listing = PropertyListingInput(
            address="123 Test St",
            listing_type="sale",
            price=100000.0,
            notes="Test",
            billing_cycle=None,
            lease_term=None,
            security_deposit=None,
            hoa_fees=None,
            property_taxes=None
        )
        assert listing.billing_cycle is None
        assert listing.hoa_fees is None


# ============================================================================
# ListingOutput - Valid Input Tests
# ============================================================================

class TestListingOutputValid:
    """Test valid inputs for ListingOutput"""
    
    def test_valid_output(self):
        """Test creating valid listing output"""
        output = ListingOutput(
            title="Beautiful 2BR/1BA Home",
            description="This charming property features...",
            price_block="$400,000"
        )
        assert output.title == "Beautiful 2BR/1BA Home"
        assert output.description == "This charming property features..."
        assert output.price_block == "$400,000"
    
    def test_output_with_long_text(self):
        """Test output with long text fields"""
        long_desc = "A" * 5000
        output = ListingOutput(
            title="Test Title",
            description=long_desc,
            price_block="$100,000"
        )
        assert len(output.description) == 5000
    
    def test_output_with_special_characters(self):
        """Test output with special characters"""
        output = ListingOutput(
            title="Luxury Home - 3BR/2BA!",
            description="Features: Pool, Spa & More!",
            price_block="$500,000"
        )
        assert "!" in output.title
        assert "&" in output.description


# ============================================================================
# ListingOutput - Validation Error Tests
# ============================================================================

class TestListingOutputValidationErrors:
    """Test validation errors for ListingOutput"""
    
    def test_empty_title(self):
        """Test that empty title raises ValueError"""
        with pytest.raises(ValueError, match="title cannot be empty"):
            ListingOutput(
                title="",
                description="Test description",
                price_block="$100,000"
            )
    
    def test_whitespace_only_title(self):
        """Test that whitespace-only title raises ValueError"""
        with pytest.raises(ValueError, match="title cannot be empty"):
            ListingOutput(
                title="   ",
                description="Test description",
                price_block="$100,000"
            )
    
    def test_empty_description(self):
        """Test that empty description raises ValueError"""
        with pytest.raises(ValueError, match="description cannot be empty"):
            ListingOutput(
                title="Test Title",
                description="",
                price_block="$100,000"
            )
    
    def test_whitespace_only_description(self):
        """Test that whitespace-only description raises ValueError"""
        with pytest.raises(ValueError, match="description cannot be empty"):
            ListingOutput(
                title="Test Title",
                description="\n\t  ",
                price_block="$100,000"
            )
    
    def test_empty_price_block(self):
        """Test that empty price_block raises ValueError"""
        with pytest.raises(ValueError, match="price_block cannot be empty"):
            ListingOutput(
                title="Test Title",
                description="Test description",
                price_block=""
            )
    
    def test_whitespace_only_price_block(self):
        """Test that whitespace-only price_block raises ValueError"""
        with pytest.raises(ValueError, match="price_block cannot be empty"):
            ListingOutput(
                title="Test Title",
                description="Test description",
                price_block="  \t\n  "
            )


# ============================================================================
# ListingOutput - Edge Cases
# ============================================================================

class TestListingOutputEdgeCases:
    """Test edge cases for ListingOutput"""
    
    def test_single_character_fields(self):
        """Test output with single character fields (minimum valid)"""
        output = ListingOutput(
            title="A",
            description="B",
            price_block="C"
        )
        assert output.title == "A"
        assert output.description == "B"
        assert output.price_block == "C"
    
    def test_title_with_leading_trailing_whitespace(self):
        """Test that title with whitespace is trimmed but still valid"""
        output = ListingOutput(
            title="  Test Title  ",
            description="Description",
            price_block="$100,000"
        )
        # The field stores the value as-is, but validation checks .strip()
        assert output.title == "  Test Title  "
    
    def test_price_block_with_currency_symbols(self):
        """Test price_block with various currency formats"""
        output = ListingOutput(
            title="Test",
            description="Test",
            price_block="$2,500/month"
        )
        assert "/month" in output.price_block


# ============================================================================
# Integration Tests
# ============================================================================

class TestModelIntegration:
    """Integration tests showing models work together"""
    
    def test_full_rental_workflow(self):
        """Test complete rental listing workflow"""
        # Step 1: Create input
        input_data = PropertyListingInput(
            address="123 Main St, New York, NY 10001",
            listing_type="rent",
            price=2500.0,
            notes="2BR/1BA, 1000 sqft, pet-friendly",
            billing_cycle="monthly",
            security_deposit=2500.0
        )
        
        # Step 2: Simulate processing (would call LLM in real system)
        # Step 3: Create output
        output = ListingOutput(
            title="Cozy 2BR/1BA Apartment in New York",
            description="This charming apartment features 2 bedrooms...",
            price_block="$2,500/month"
        )
        
        # Verify both models are valid
        assert input_data.listing_type == "rent"
        assert output.price_block == "$2,500/month"
    
    def test_full_sale_workflow(self):
        """Test complete sale listing workflow"""
        # Step 1: Create input
        input_data = PropertyListingInput(
            address="456 Oak Ave, Los Angeles, CA 90001",
            listing_type="sale",
            price=750000.0,
            notes="3BR/2BA, 1500 sqft, updated kitchen",
            hoa_fees=200.0,
            property_taxes=8500.0
        )
        
        # Step 2: Simulate processing
        # Step 3: Create output
        output = ListingOutput(
            title="Stunning 3BR/2BA Home in Los Angeles",
            description="This beautiful home features 3 bedrooms...",
            price_block="$750,000"
        )
        
        # Verify both models are valid
        assert input_data.listing_type == "sale"
        assert output.price_block == "$750,000"
    
    def test_minimal_workflow(self):
        """Test workflow with minimal required fields"""
        input_data = PropertyListingInput(
            address="789 Pine Rd",
            listing_type="sale",
            price=400000.0,
            notes="2BR/1BA"
        )
        
        output = ListingOutput(
            title="Property for Sale",
            description="A nice property.",
            price_block="$400,000"
        )
        
        assert input_data.price == 400000.0
        assert output.price_block == "$400,000"
