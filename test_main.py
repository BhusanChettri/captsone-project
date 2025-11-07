"""
Test script for main.py - End-to-End Testing

This script tests the main processing function with various scenarios.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from main import process_listing_request


def test_sale_listing():
    """Test processing a sale listing"""
    print("\n" + "=" * 80)
    print("TEST 1: Sale Listing")
    print("=" * 80)
    
    result = process_listing_request(
        address="123 Main Street, New York, NY 10001",
        listing_type="sale",
        price=500000.0,
        notes="Beautiful 2BR/1BA apartment with modern kitchen, hardwood floors, and great natural light. Close to subway and Central Park.",
        hoa_fees=200.0,
        property_taxes=5000.0
    )
    
    print(f"\nSuccess: {result['success']}")
    print(f"Errors: {len(result['errors'])}")
    if result['listing']:
        print(f"Title: {result['listing'].get('title', 'N/A')}")
        print(f"Description: {result['listing'].get('description', 'N/A')[:100]}...")
    
    return result


def test_rental_listing():
    """Test processing a rental listing"""
    print("\n" + "=" * 80)
    print("TEST 2: Rental Listing")
    print("=" * 80)
    
    result = process_listing_request(
        address="456 Oak Avenue, Brooklyn, NY 11201",
        listing_type="rent",
        price=2500.0,
        notes="Spacious 1BR apartment, recently renovated, pet-friendly building",
        billing_cycle="monthly",
        lease_term="12 months",
        security_deposit=2500.0
    )
    
    print(f"\nSuccess: {result['success']}")
    print(f"Errors: {len(result['errors'])}")
    if result['listing']:
        print(f"Title: {result['listing'].get('title', 'N/A')}")
        print(f"Description: {result['listing'].get('description', 'N/A')[:100]}...")
    
    return result


def test_minimal_input():
    """Test with minimal required input only"""
    print("\n" + "=" * 80)
    print("TEST 3: Minimal Input (Required Fields Only)")
    print("=" * 80)
    
    result = process_listing_request(
        address="789 Pine Street, Queens, NY 11101",
        listing_type="sale",
        price=350000.0,
        notes=""
    )
    
    print(f"\nSuccess: {result['success']}")
    print(f"Errors: {len(result['errors'])}")
    
    return result


if __name__ == "__main__":
    print("=" * 80)
    print("END-TO-END TESTING - MAIN FUNCTION")
    print("=" * 80)
    
    # Run all tests
    test_sale_listing()
    test_rental_listing()
    test_minimal_input()
    
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)

