"""
LangGraph Node Functions for Property Listing System - Iteration 1

This module contains all node functions that process the state as it flows
through the workflow. Each node:
1. Receives the current state
2. Performs its specific processing
3. Updates the state with results
4. Returns the updated state

Node Functions:
1. input_guardrail_node - Safety checks on raw input (FIRST - prevents malicious/abusive content)
2. validate_input_node - Validates input fields (business logic validation)
3. normalize_text_node - Normalizes and cleans text inputs
4. enrich_data_node - Performs web search enrichment (Tavily)
5. generate_content_node - Generates listing content using LLM
6. output_guardrail_node - Validates LLM output (safety, compliance, quality)
7. format_output_node - Validates and formats final output
"""

from typing import Dict, Any
from core.state import PropertyListingState


def input_guardrail_node(state: PropertyListingState) -> PropertyListingState:
    """
    Node 1: Input guardrail - Safety checks on raw input (FIRST node).
    
    This is the FIRST node that processes raw user input. It performs safety
    and security checks to prevent malicious or abusive content from entering
    the system. This saves resources by rejecting invalid input early.
    
    Checks performed:
    - Malicious/abusive text detection
    - Injection attack prevention
    - Property-related query validation (only property listings allowed)
    - Content safety checks
    - Text length limits
    
    If validation fails, adds errors to state and workflow should stop.
    
    Args:
        state: Current workflow state with raw input
        
    Returns:
        Updated state with guardrail validation results
        If validation fails, state["errors"] will contain rejection reasons
    """
    print("[DEBUG] Node 1: input_guardrail_node - Starting input guardrail checks")
    from utils.guardrails import check_input_guardrails
    
    # Initialize errors list if not present
    if "errors" not in state:
        state["errors"] = []
    
    # Get input fields (handle None values)
    address = state.get("address", "") or ""
    notes = state.get("notes", "") or ""
    price = state.get("price")
    listing_type = state.get("listing_type", "") or ""
    
    # Check if required fields are present before doing property-related validation
    # If required fields are missing, skip property-related check and let validation handle it
    has_required_fields = (
        address and address.strip() and
        listing_type and listing_type.strip() and
        price is not None
    )
    
    # Perform comprehensive guardrail checks
    # Only do property-related validation if required fields are present
    # This prevents guardrail from masking validation errors
    guardrail_errors = check_input_guardrails(
        address=address,
        notes=notes,
        strict_property_validation=has_required_fields  # Only validate if required fields present
    )
    
    # Add any guardrail errors to state
    if guardrail_errors:
        state["errors"].extend(guardrail_errors)
    
    print(f"[DEBUG] Node 1: input_guardrail_node - Completed ({len(guardrail_errors)} guardrail errors found)")
    return state


def validate_input_node(state: PropertyListingState) -> PropertyListingState:
    """
    Node 2: Validate input fields (business logic validation).
    
    Validates that required fields are present and have valid values.
    This is business logic validation (different from guardrail safety checks).
    Adds validation errors to state.errors if any issues are found.
    
    Args:
        state: Current workflow state (after guardrail checks)
        
    Returns:
        Updated state with validation results
    """
    print("[DEBUG] Node 2: validate_input_node - Starting input validation")
    from utils.validators import validate_input_fields
    
    # Initialize errors list if not present
    if "errors" not in state:
        state["errors"] = []
    
    # Get all input fields from state
    address = state.get("address")
    listing_type = state.get("listing_type")
    price = state.get("price")
    notes = state.get("notes")
    billing_cycle = state.get("billing_cycle")
    lease_term = state.get("lease_term")
    security_deposit = state.get("security_deposit")
    hoa_fees = state.get("hoa_fees")
    property_taxes = state.get("property_taxes")
    
    # Perform comprehensive validation
    validation_errors = validate_input_fields(
        address=address,
        listing_type=listing_type,
        price=price,
        notes=notes,
        billing_cycle=billing_cycle,
        lease_term=lease_term,
        security_deposit=security_deposit,
        hoa_fees=hoa_fees,
        property_taxes=property_taxes,
    )
    
    # Add any validation errors to state
    if validation_errors:
        state["errors"].extend(validation_errors)
    
    print(f"[DEBUG] Node 2: validate_input_node - Completed ({len(validation_errors)} validation errors)")
    return state


def normalize_text_node(state: PropertyListingState) -> PropertyListingState:
    """
    Node 3: Normalize and clean text inputs.
    
    Normalizes address and notes fields:
    - Trims whitespace
    - Normalizes line breaks
    - Basic text cleaning
    - Preserves address and notes structure
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with normalized_address and normalized_notes
    """
    from utils.text_processor import normalize_address, normalize_notes
    
    # Get input fields (handle None values)
    address = state.get("address") or ""
    notes = state.get("notes") or ""
    
    # Normalize address
    normalized_addr = normalize_address(address)
    state["normalized_address"] = normalized_addr
    
    # Normalize notes
    normalized_notes = normalize_notes(notes)
    state["normalized_notes"] = normalized_notes
    
    if normalized_addr:
        print(f"[DEBUG] Node 3: Normalized address: {normalized_addr[:50]}...")
    if normalized_notes:
        print(f"[DEBUG] Node 3: Normalized notes: {normalized_notes[:50]}...")
    
    print("[DEBUG] Node 3: normalize_text_node - Completed")
    return state


def enrich_data_node(state: PropertyListingState) -> PropertyListingState:
    """
    Node 4: Enrich data with web search (Tavily).
    
    Performs web search to gather local information:
    - Extracts ZIP code from address
    - Identifies neighborhood name
    - Finds nearby landmarks (top 3-5)
    - Extracts key amenities (schools, parks, shopping, transportation)
    
    This node is optional - if enrichment fails, it should continue gracefully
    without breaking the workflow.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with enrichment data:
        - zip_code
        - neighborhood
        - landmarks
        - key_amenities
    """
    print("[DEBUG] Node 4: enrich_data_node - Starting data enrichment")
    from utils.enrichment import enrich_property_data
    
    # Initialize errors list if not present
    if "errors" not in state:
        state["errors"] = []
    
    try:
        from langchain_tavily import TavilySearch
    except ImportError:
        # Tavily not available - skip enrichment
        state["errors"].append("Enrichment skipped: Tavily API not available")
        return state
    
    # Get address (prefer normalized_address if available, fallback to address)
    address = state.get("normalized_address") or state.get("address") or ""
    
    # Skip enrichment if no address available
    if not address or not address.strip():
        return state
    
    try:
        # Load environment variables from .env file in iteration1 folder
        from utils.env_loader import load_iteration1_env
        import os
        env_path = load_iteration1_env()
        if env_path:
            print(f"[DEBUG] Node 4: Loaded .env file from {env_path}")
        elif os.getenv("TAVILY_API_KEY"):
            print("[DEBUG] Node 4: TAVILY_API_KEY found in environment")
        else:
            print("[DEBUG] Node 4: Warning - .env file not found and TAVILY_API_KEY not in environment")
        
        # Initialize Tavily search tool
        # Note: Tavily API key should be in environment variable TAVILY_API_KEY
        # We use include_raw_content=True because we do our own extraction via regex
        # include_answer=True provides Tavily's AI summary, which can be useful context
        import os
        if not os.getenv("TAVILY_API_KEY"):
            raise ValueError(
                "TAVILY_API_KEY environment variable is not set. "
                "Please set it in your .env file or environment."
            )
        
        search_tool = TavilySearch(
            max_results=2,  # Optimized: Reduced from 3 to 2 (sufficient for extraction)
            include_answer=True,
            include_raw_content=True,  # We need raw content for our regex extraction
            include_images=False,
            search_depth="advanced",
        )
        
        # Get all available context for intelligent search query construction
        normalized_notes = state.get("normalized_notes") or state.get("notes") or ""
        listing_type = state.get("listing_type")
        price = state.get("price")
        
        # Perform enrichment using all available context
        enrichment_data = enrich_property_data(
            address=address,
            notes=normalized_notes,
            listing_type=listing_type,
            price=price,
            search_tool=search_tool
        )
        
        # Store enrichment data in state
        if enrichment_data.get("zip_code"):
            state["zip_code"] = enrichment_data["zip_code"]
        
        if enrichment_data.get("neighborhood"):
            state["neighborhood"] = enrichment_data["neighborhood"]
        
        if enrichment_data.get("landmarks"):
            state["landmarks"] = enrichment_data["landmarks"]
        
        if enrichment_data.get("key_amenities"):
            state["key_amenities"] = enrichment_data["key_amenities"]
        
        print(f"[DEBUG] Node 4: Enrichment completed - ZIP: {enrichment_data.get('zip_code', 'N/A')}, Neighborhood: {enrichment_data.get('neighborhood', 'N/A')}")
    
    except ValueError as e:
        # Missing API key or configuration error
        error_msg = f"Enrichment configuration error: {str(e)}"
        state["errors"].append(error_msg)
        print(f"[DEBUG] Node 4: {error_msg}")
        # Continue without enrichment data
    except Exception as e:
        # Enrichment is optional - log error but don't break workflow
        error_msg = f"Enrichment failed: {str(e)}"
        state["errors"].append(error_msg)
        print(f"[DEBUG] Node 4: Enrichment failed (continuing): {error_msg}")
        # Continue without enrichment data
    
    print("[DEBUG] Node 4: enrich_data_node - Completed")
    return state


def generate_content_node(state: PropertyListingState) -> PropertyListingState:
    """
    Node 5: Generate listing content using LLM.
    
    Uses LLM to generate:
    - title: Listing title
    - description: Listing description
    - price_block: Formatted price information
    
    Merges all collected data (input, normalized, enriched) into a prompt
    and calls the LLM. Parses JSON response and stores in state.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with LLM output:
        - llm_raw_output: Raw JSON string from LLM
        - llm_parsed: Parsed JSON dictionary
    """
    print("[DEBUG] Node 5: generate_content_node - Starting LLM content generation")
    from utils.prompts import build_listing_generation_prompt
    from utils.llm_client import initialize_llm, call_llm_with_prompt, parse_json_response
    
    # Initialize errors list if not present
    if "errors" not in state:
        state["errors"] = []
    
    # Validate required fields
    address = state.get("address")
    listing_type = state.get("listing_type")
    price = state.get("price")
    
    if not address or not listing_type or price is None:
        state["errors"].append(
            "Cannot generate content: missing required fields (address, listing_type, or price)"
        )
        return state
    
    try:
        # Load environment variables from .env file in iteration1 folder
        from utils.env_loader import load_iteration1_env
        import os
        env_path = load_iteration1_env()
        if env_path:
            print(f"[DEBUG] Node 5: Loaded .env file from {env_path}")
        elif os.getenv("OPENAI_API_KEY"):
            print("[DEBUG] Node 5: OPENAI_API_KEY found in environment")
        
        # Build comprehensive prompt with all available data
        prompt = build_listing_generation_prompt(
            address=address,
            listing_type=listing_type,
            price=price,
            notes=state.get("notes"),
            normalized_address=state.get("normalized_address"),
            normalized_notes=state.get("normalized_notes"),
            zip_code=state.get("zip_code"),
            neighborhood=state.get("neighborhood"),
            landmarks=state.get("landmarks"),
            key_amenities=state.get("key_amenities"),
            billing_cycle=state.get("billing_cycle"),
            lease_term=state.get("lease_term"),
            security_deposit=state.get("security_deposit"),
            hoa_fees=state.get("hoa_fees"),
            property_taxes=state.get("property_taxes"),
        )
        
        # Initialize LLM (use environment variables for API keys)
        # Default to gpt-4o-mini for cost-effectiveness
        llm = initialize_llm(
            model_name="gpt-5-mini",
            model_provider="openai",
            reasoning_effort="minimal"
        )
        
        
        # Call LLM with prompt
        llm_response = call_llm_with_prompt(llm, prompt, temperature=0.5)
        
        # Store raw output
        state["llm_raw_output"] = llm_response
        
        # Parse JSON response
        parsed_json = parse_json_response(llm_response)
        
        # Store parsed output
        state["llm_parsed"] = parsed_json
        print(f"[DEBUG] Node 5: LLM content generated - Title: {parsed_json.get('title', 'N/A')[:50]}...")
        
    except Exception as e:
        # Log error but don't break workflow - errors will be handled downstream
        error_msg = f"Content generation failed: {str(e)}"
        state["errors"].append(error_msg)
        print(f"[DEBUG] Node 5: Content generation failed (continuing): {error_msg}")
        # Continue without LLM output
    
    print("[DEBUG] Node 5: generate_content_node - Completed")
    return state


def output_guardrail_node(state: PropertyListingState) -> PropertyListingState:
    """
    Node 6: Output guardrail - Validates LLM output (safety and compliance).
    
    This node validates the LLM-generated content BEFORE formatting to ensure:
    - Output structure is valid (required fields, correct types)
    - Output is property listing-related only (no off-topic content)
    - No inappropriate content (racism, sexual content, dangerous material)
    - No malicious or abusive text
    - No injection attacks in output
    - Compliance with policies (no invented pricing, factual accuracy)
    - Price information only in price_block (not in description)
    - Content quality standards (length limits, structure)
    
    This ensures the LLM didn't generate inappropriate or dangerous content
    before it gets formatted and returned to the user.
    
    Args:
        state: Current workflow state with LLM output (llm_raw_output, llm_parsed)
        
    Returns:
        Updated state with guardrail validation results
        If validation fails, state["errors"] will contain rejection reasons
    """
    print("[DEBUG] Node 6: output_guardrail_node - Starting output guardrail validation")
    from utils.guardrails import check_output_guardrails
    
    # Initialize errors list if not present
    if "errors" not in state:
        state["errors"] = []
    
    # Get LLM output
    llm_parsed = state.get("llm_parsed")
    
    if not llm_parsed:
        error_msg = "Output guardrail: No LLM output to validate"
        state["errors"].append(error_msg)
        print(f"[DEBUG] Node 6: {error_msg}")
        print("[DEBUG] Node 6: output_guardrail_node - Completed (no output to validate)")
        return state
    
    # Get original input for compliance validation
    original_price = state.get("price")
    listing_type = state.get("listing_type")
    
    # Log what we're validating
    title_preview = llm_parsed.get("title", "N/A")[:50]
    print(f"[DEBUG] Node 6: Found LLM output - title: {title_preview}...")
    
    # Perform comprehensive output guardrail checks
    guardrail_errors = check_output_guardrails(
        llm_parsed=llm_parsed,
        original_price=original_price,
        listing_type=listing_type
    )
    
    # Add any guardrail errors to state
    if guardrail_errors:
        state["errors"].extend(guardrail_errors)
        print(f"[DEBUG] Node 6: Output guardrail validation failed - {len(guardrail_errors)} error(s) found")
        for error in guardrail_errors:
            print(f"[DEBUG] Node 6:   - {error}")
    else:
        print("[DEBUG] Node 6: Output guardrail validation passed - all checks successful")
    
    print("[DEBUG] Node 6: output_guardrail_node - Completed")
    return state


def format_output_node(state: PropertyListingState) -> PropertyListingState:
    """
    Node 7: Format final output.
    
    Formats the validated LLM output into the final listing format:
    - Extracts title, description, price_block from LLM output
    - Removes price mentions from description (safety net)
    - Cleans and normalizes all text fields
    - Formats final listing with proper structure and disclaimer
    - Applies final formatting rules
    
    Note: Safety and compliance checks are done in output_guardrail_node.
    This node focuses on formatting and structure.
    
    Args:
        state: Current workflow state (after output guardrail validation)
        
    Returns:
        Updated state with final output:
        - title: Validated and cleaned title
        - description: Validated and cleaned description (price removed)
        - price_block: Validated and cleaned price block
        - formatted_listing: Final formatted text with disclaimer
    """
    print("[DEBUG] Node 7: format_output_node - Starting output formatting")
    from utils.formatters import extract_and_format_output, format_listing
    
    # Initialize errors list if not present
    if "errors" not in state:
        state["errors"] = []
    
    # Check if LLM output exists
    llm_parsed = state.get("llm_parsed")
    
    if not llm_parsed:
        error_msg = "Format output: No LLM output to format"
        state["errors"].append(error_msg)
        print(f"[DEBUG] Node 7: {error_msg}")
        print("[DEBUG] Node 7: format_output_node - Completed (no output to format)")
        return state
    
    try:
        # Extract and format output fields
        formatted_fields = extract_and_format_output(llm_parsed)
        
        # Store formatted fields in state
        state["title"] = formatted_fields["title"]
        state["description"] = formatted_fields["description"]
        state["price_block"] = formatted_fields["price_block"]
        
        # Log what we formatted
        if state["title"]:
            print(f"[DEBUG] Node 7: Formatted title: {state['title'][:50]}...")
        if state["description"]:
            print(f"[DEBUG] Node 7: Formatted description: {state['description'][:50]}...")
        if state["price_block"]:
            print(f"[DEBUG] Node 7: Formatted price_block: {state['price_block']}")
        
        # Create final formatted listing with proper structure
        formatted_listing = format_listing(
            title=state["title"],
            description=state["description"],
            price_block=state["price_block"],
            remove_price_from_desc=True  # Safety net: remove price even if guardrails missed it
        )
        
        state["formatted_listing"] = formatted_listing
        print("[DEBUG] Node 7: Created formatted_listing with proper structure")
        
    except Exception as e:
        # Log error but don't break workflow - errors will be handled downstream
        error_msg = f"Format output failed: {str(e)}"
        state["errors"].append(error_msg)
        print(f"[DEBUG] Node 7: {error_msg}")
        # Continue without formatted output
    
    print("[DEBUG] Node 7: format_output_node - Completed")
    return state

