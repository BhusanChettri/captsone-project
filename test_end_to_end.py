"""
End-to-End Test Script for Property Listing Workflow

This script tests the entire workflow from start to finish with sample data.
It helps verify that all nodes execute in the correct order and state flows properly.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core import create_workflow, PropertyListingState


def test_end_to_end_workflow():
    """Test the complete workflow with sample data"""
    
    print("=" * 80)
    print("END-TO-END WORKFLOW TEST")
    print("=" * 80)
    print()
    
    # Step 1: Create workflow
    print("Step 1: Creating workflow...")
    workflow = create_workflow()
    print("✓ Workflow created successfully")
    print()
    
    # Step 2: Create initial state with sample data
    print("Step 2: Creating initial state with sample data...")
    initial_state: PropertyListingState = {
        "address": "123 Main Street, New York, NY 10001",
        "listing_type": "sale",
        "price": 500000.0,
        "notes": "Beautiful 2BR/1BA apartment with modern kitchen, hardwood floors, and great natural light. Close to subway and Central Park.",
        "errors": []
    }
    print(f"  Address: {initial_state['address']}")
    print(f"  Listing Type: {initial_state['listing_type']}")
    print(f"  Price: ${initial_state['price']:,.2f}")
    print(f"  Notes: {initial_state['notes'][:80]}...")
    print("✓ Initial state created")
    print()
    
    # Step 3: Execute workflow
    print("Step 3: Executing workflow...")
    print("-" * 80)
    try:
        result = workflow.invoke(initial_state)
        print("-" * 80)
        print("✓ Workflow execution completed")
        print()
    except Exception as e:
        print(f"✗ Workflow execution failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 4: Display results
    print("Step 4: Workflow Results")
    print("=" * 80)
    
    # Display input data (preserved)
    print("\n[INPUT DATA]")
    print(f"  Address: {result.get('address', 'N/A')}")
    print(f"  Listing Type: {result.get('listing_type', 'N/A')}")
    print(f"  Price: ${result.get('price', 0):,.2f}")
    
    # Display processed data
    print("\n[PROCESSED DATA]")
    if result.get("normalized_address"):
        print(f"  Normalized Address: {result['normalized_address']}")
    if result.get("normalized_notes"):
        print(f"  Normalized Notes: {result['normalized_notes'][:100]}...")
    
    # Display enrichment data
    print("\n[ENRICHMENT DATA]")
    if result.get("zip_code"):
        print(f"  ZIP Code: {result['zip_code']}")
    if result.get("neighborhood"):
        print(f"  Neighborhood: {result['neighborhood']}")
    if result.get("landmarks"):
        print(f"  Landmarks: {result['landmarks']}")
    if result.get("key_amenities"):
        print(f"  Key Amenities: {result['key_amenities']}")
    
    # Display LLM output
    print("\n[LLM OUTPUT]")
    if result.get("llm_parsed"):
        llm_output = result["llm_parsed"]
        print(f"  Title: {llm_output.get('title', 'N/A')}")
        print(f"  Description: {llm_output.get('description', 'N/A')[:100]}...")
        print(f"  Price Block: {llm_output.get('price_block', 'N/A')}")
    else:
        print("  No LLM output generated")
    
    # Display final output
    print("\n[FINAL OUTPUT]")
    if result.get("title"):
        print(f"  Title: {result['title']}")
    if result.get("description"):
        print(f"  Description: {result['description'][:100]}...")
    if result.get("price_block"):
        print(f"  Price Block: {result['price_block']}")
    if result.get("formatted_listing"):
        print(f"  Formatted Listing:\n{result['formatted_listing']}")
    
    # Display errors
    print("\n[ERRORS]")
    errors = result.get("errors", [])
    if errors:
        print(f"  Found {len(errors)} error(s):")
        for i, error in enumerate(errors, 1):
            print(f"    {i}. {error}")
    else:
        print("  No errors")
    
    print()
    print("=" * 80)
    print("END-TO-END TEST COMPLETED")
    print("=" * 80)
    
    return result


if __name__ == "__main__":
    test_end_to_end_workflow()

