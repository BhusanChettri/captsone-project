"""
Main Entry Point for Property List Mate - Iteration 1

This module provides the main entry point for the application.
It handles:
1. Input from UI (Gradio form)
2. Conversion to workflow state
3. Workflow execution
4. Result formatting and return
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core import create_workflow, PropertyListingState
from models import PropertyListingInput
from utils.tracing import clear_trace_metadata, set_trace_metadata, get_trace_metadata


def process_listing_request(
    address: str,
    listing_type: str,
    property_type: str | None = None,
    bedrooms: int | None = None,
    bathrooms: float | None = None,
    sqft: int | None = None,
    notes: str = "",
    region: str = "US",
) -> dict:
    """
    Process a property listing request from UI.
    
    This is the main function that:
    1. Takes input from Gradio UI
    2. Creates initial workflow state
    3. Executes the workflow
    4. Returns formatted results
    
    Args:
        address: Property address (required)
        listing_type: "sale" or "rent" (required)
        property_type: Type of property - "Apartment", "House", "Condo", "Townhouse", "Studio", "Loft" (required)
        bedrooms: Number of bedrooms (required)
        bathrooms: Number of bathrooms, can be decimal like 1.5 (required)
        sqft: Square footage / total living area (required)
        notes: Free-text description with key features, amenities, condition, etc. (optional)
        region: Region code (US, CA, UK, AU). Defaults to "US" if not specified.
        
    Returns:
        Dictionary with:
        - success: bool - Whether processing was successful
        - listing: dict - Generated listing (title, description, price_block, formatted_listing)
        - errors: list - List of errors/warnings encountered
        - state: dict - Full workflow state (for debugging)
    """
    print("\n" + "=" * 80)
    print("PROCESSING LISTING REQUEST")
    print("=" * 80)
    print(f"Address: {address or 'Not provided'}")
    print(f"Listing Type: {listing_type or 'Not provided'}")
    print(f"Property Type: {property_type or 'Not provided'}")
    print(f"Bedrooms: {bedrooms or 'Not provided'}")
    print(f"Bathrooms: {bathrooms or 'Not provided'}")
    print(f"Square Footage: {sqft or 'Not provided'}")
    print(f"Notes: {notes[:100] if notes else 'None'}...")
    print("=" * 80 + "\n")
    
    # Step 1: Create workflow with tracing
    try:
        # Clear any previous trace metadata
        clear_trace_metadata()
        
        # Set trace metadata for this request
        set_trace_metadata("request_id", str(time.time()))
        set_trace_metadata("address", address[:100] if address else None)
        set_trace_metadata("listing_type", listing_type)
        set_trace_metadata("property_type", property_type)
        set_trace_metadata("bedrooms", bedrooms)
        set_trace_metadata("bathrooms", bathrooms)
        set_trace_metadata("sqft", sqft)
        
        workflow, tracer = create_workflow(enable_tracing=True)
        print("✓ Workflow initialized")
        if tracer:
            print("✓ Tracing enabled")
    except Exception as e:
        return {
            "success": False,
            "listing": None,
            "errors": [f"Failed to initialize workflow: {str(e)}"],
            "state": None
        }
    
    # Step 2: Create initial state from UI input
    # Handle None values and empty strings properly
    # Notes is optional - preserve None if not provided
    initial_state: PropertyListingState = {
        "address": address.strip() if address and address.strip() else "",
        "listing_type": listing_type.strip().lower() if listing_type and listing_type.strip() else "",
        "property_type": property_type.strip() if property_type and property_type.strip() else "",
        "bedrooms": int(bedrooms) if bedrooms is not None and bedrooms >= 0 else None,
        "bathrooms": float(bathrooms) if bathrooms is not None and bathrooms >= 0 else None,
        "sqft": int(sqft) if sqft is not None and sqft > 0 else None,
        "notes": notes.strip() if notes and notes.strip() else None,  # Preserve None for optional field
        "region": region.strip().upper() if region and region.strip() else "US",  # Default to US
        "errors": []
    }
    
    # Step 3: Execute workflow with tracing
    try:
        print("Executing workflow...\n")
        
        # Track total execution time
        workflow_start_time = time.time()
        
        # Prepare config with tracer callback if available
        config = {
            "configurable": {
                "thread_id": f"listing_{int(time.time())}"
            }
        }
        
        # Add tracer as callback if available
        if tracer:
            config["callbacks"] = [tracer]
            print("[TRACE] Opik tracer attached to workflow execution")
        
        # Execute workflow
        result_state = workflow.invoke(initial_state, config=config)
        
        # Calculate total execution time
        workflow_end_time = time.time()
        total_execution_time = workflow_end_time - workflow_start_time
        
        # Store timing in trace metadata
        set_trace_metadata("total_execution_time", total_execution_time)
        set_trace_metadata("workflow_completed", True)
        
        print(f"\n✓ Workflow execution completed in {total_execution_time:.3f}s\n")
        print(f"[TRACE] Total execution time: {total_execution_time:.3f}s")
        
    except Exception as e:
        set_trace_metadata("workflow_error", str(e))
        set_trace_metadata("workflow_completed", False)
        return {
            "success": False,
            "listing": None,
            "errors": [f"Workflow execution failed: {str(e)}"],
            "state": None
        }
    
    # Step 4: Extract results
    errors = result_state.get("errors", [])
    
    # Check if we have a formatted listing
    formatted_listing = result_state.get("formatted_listing", "")
    title = result_state.get("title", "")
    description = result_state.get("description", "")
    price_block = result_state.get("price_block", "")
    
    # If no formatted listing but we have individual fields, create one
    if not formatted_listing and (title or description or price_block):
        formatted_listing = f"{title}\n\n{description}\n\n{price_block}\n\nAll information deemed reliable but not guaranteed. Equal Housing Opportunity."
    
    # Determine success (has output and no critical errors)
    success = bool(formatted_listing or (title and description and price_block))
    
    listing_result = {
        "title": title,
        "description": description,
        "price_block": price_block,
        "formatted_listing": formatted_listing
    }
    
    # Include trace metadata in response for debugging
    trace_metadata = get_trace_metadata()
    
    return {
        "success": success,
        "listing": listing_result if success else None,
        "errors": errors,
        "state": result_state,  # Include full state for debugging
        "trace_metadata": trace_metadata  # Include trace metadata
    }


def main():
    """
    Main function for command-line testing.
    
    This allows testing the workflow without Gradio UI.
    """
    print("=" * 80)
    print("PROPERTY LIST MATE - ITERATION 1")
    print("=" * 80)
    print()
    
    # Sample test data
    result = process_listing_request(
        address="123 Main Street, New York, NY 10001",
        listing_type="sale",
        property_type="Apartment",
        bedrooms=2,
        bathrooms=1.0,
        sqft=1200,
        notes="Beautiful apartment with modern kitchen, hardwood floors, and great natural light. Close to subway and Central Park."
    )
    
    # Display results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"Success: {result['success']}")
    print()
    
    if result['success'] and result['listing']:
        print("GENERATED LISTING:")
        print("-" * 80)
        print(result['listing']['formatted_listing'])
        print("-" * 80)
    else:
        print("No listing generated")
    
    if result['errors']:
        print(f"\nErrors/Warnings ({len(result['errors'])}):")
        for i, error in enumerate(result['errors'], 1):
            print(f"  {i}. {error}")
    
    print("\n" + "=" * 80)
    
    return result


if __name__ == "__main__":
    main()

