"""
LangGraph Node Functions for Property Listing System - Iteration 1

This module contains all node functions that process the state as it flows
through the workflow. Each node:
1. Receives the current state
2. Performs its specific processing
3. Updates the state with results
4. Returns the updated state

Node Functions:
1. input_guardrail_node - Combined security checks, validation, and normalization (FIRST)
2. enrich_data_node - Performs web search enrichment (Tavily)
3. generate_content_node - Generates listing content using LLM
4. output_guardrail_node - Validates LLM output (safety, compliance, quality)
5. format_output_node - Validates and formats final output
"""

from typing import Dict, Any
from core.state import PropertyListingState


def input_guardrail_node(state: PropertyListingState) -> PropertyListingState:
    """
    Node 1: Input guardrail - Combined security, validation, and normalization.
    
    This is the FIRST node that processes raw user input. It performs:
    1. Security checks (injection attacks, text length limits)
    2. Field validation (required fields, types, values)
    3. Text normalization (trim whitespace, basic cleaning)
    
    This combined approach is faster and simpler than having separate nodes.
    
    Args:
        state: Current workflow state with raw input
        
    Returns:
        Updated state with:
        - Validation results (errors if any)
        - Normalized text fields (normalized_address, normalized_notes)
    """
    print("[DEBUG] Node 1: input_guardrail_node - Starting combined validation and normalization")
    from utils.guardrails import detect_injection_attacks, MAX_ADDRESS_LENGTH, MAX_NOTES_LENGTH
    from utils.validators import (
        validate_address, validate_listing_type, validate_property_type,
        validate_bedrooms, validate_bathrooms, validate_sqft, validate_notes
    )
    
    # Initialize errors list if not present
    if "errors" not in state:
        state["errors"] = []
    
    errors = []
    
    # Get input fields (handle None values)
    address = state.get("address", "") or ""
    notes = state.get("notes", "") or ""
    listing_type = state.get("listing_type")
    property_type = state.get("property_type")
    bedrooms = state.get("bedrooms")
    bathrooms = state.get("bathrooms")
    sqft = state.get("sqft")
    
    # ========================================================================
    # 1. SECURITY CHECKS (Injection attacks, text length)
    # ========================================================================
    
    # Check for injection attacks
    injection_error = detect_injection_attacks(address)
    if injection_error:
        errors.append(f"Address: {injection_error}")
    
    injection_error = detect_injection_attacks(notes)
    if injection_error:
        errors.append(f"Notes: {injection_error}")
    
    # Check text length limits
    if len(address) > MAX_ADDRESS_LENGTH:
        errors.append(f"Address exceeds maximum length of {MAX_ADDRESS_LENGTH} characters (got {len(address)})")
    
    if notes and len(notes) > MAX_NOTES_LENGTH:
        errors.append(f"Notes exceed maximum length of {MAX_NOTES_LENGTH} characters (got {len(notes)})")
    
    # ========================================================================
    # 2. FIELD VALIDATION (Required fields, types, values)
    # ========================================================================
    
    # Validate all required fields
    address_error = validate_address(address)
    if address_error:
        errors.append(address_error)
    
    listing_type_error = validate_listing_type(listing_type)
    if listing_type_error:
        errors.append(listing_type_error)
    
    property_type_error = validate_property_type(property_type)
    if property_type_error:
        errors.append(property_type_error)
    
    bedrooms_error = validate_bedrooms(bedrooms)
    if bedrooms_error:
        errors.append(bedrooms_error)
    
    bathrooms_error = validate_bathrooms(bathrooms)
    if bathrooms_error:
        errors.append(bathrooms_error)
    
    sqft_error = validate_sqft(sqft)
    if sqft_error:
        errors.append(sqft_error)
    
    # Validate optional fields
    notes_error = validate_notes(notes)
    if notes_error:
        errors.append(notes_error)
    
    # ========================================================================
    # 3. TEXT NORMALIZATION (Trim whitespace, basic cleaning)
    # ========================================================================
    
    # Basic normalization: trim whitespace and normalize line breaks
    normalized_address = address.strip() if address else ""
    normalized_notes = notes.strip() if notes else ""
    
    # Normalize line breaks (convert \r\n, \n to spaces)
    import re
    normalized_address = re.sub(r'[\r\n]+', ' ', normalized_address)
    normalized_notes = re.sub(r'[\r\n]+', ' ', normalized_notes)
    
    # Normalize multiple spaces to single space
    normalized_address = re.sub(r'\s+', ' ', normalized_address).strip()
    normalized_notes = re.sub(r'\s+', ' ', normalized_notes).strip()
    
    # Store normalized versions in state
    state["normalized_address"] = normalized_address
    state["normalized_notes"] = normalized_notes
    
    # Add any errors to state
    if errors:
        state["errors"].extend(errors)
    
    print(f"[DEBUG] Node 1: input_guardrail_node - Completed ({len(errors)} errors found)")
    if normalized_address:
        print(f"[DEBUG] Node 1: Normalized address: {normalized_address[:50]}...")
    if normalized_notes:
        print(f"[DEBUG] Node 1: Normalized notes: {normalized_notes[:50]}...")
    
    return state




def enrich_data_node(state: PropertyListingState) -> PropertyListingState:
    """
    Node 2: Enrich data with web search (Tavily).
    
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
    print("[DEBUG] Node 2: enrich_data_node - Starting data enrichment")
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
            print(f"[DEBUG] Node 2: Loaded .env file from {env_path}")
        elif os.getenv("TAVILY_API_KEY"):
            print("[DEBUG] Node 2: TAVILY_API_KEY found in environment")
        else:
            print("[DEBUG] Node 2: Warning - .env file not found and TAVILY_API_KEY not in environment")
        
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
            include_raw_content=False,  # We need raw content for our regex extraction
            include_images=False,
            search_depth="advanced",
        )
        
        # Perform enrichment using ONLY address (exactly 2 web search calls)
        # WEB SEARCH 1: Address + amenities (schools, shopping, subway, etc.)
        # WEB SEARCH 2: Address + neighborhood quality (crime rates, quality of life)
        enrichment_data = enrich_property_data(
            address=address,
            search_tool=search_tool
        )
        
        # DEBUG: Log what enrichment_data contains
        print(f"[DEBUG] Node 2: Enrichment data returned:")
        print(f"  - zip_code: {enrichment_data.get('zip_code')} (type: {type(enrichment_data.get('zip_code'))})")
        print(f"  - neighborhood: {enrichment_data.get('neighborhood')} (type: {type(enrichment_data.get('neighborhood'))})")
        print(f"  - landmarks: {enrichment_data.get('landmarks')} (type: {type(enrichment_data.get('landmarks'))}, length: {len(enrichment_data.get('landmarks', []))})")
        print(f"  - key_amenities: {enrichment_data.get('key_amenities')} (type: {type(enrichment_data.get('key_amenities'))})")
        if enrichment_data.get('key_amenities'):
            for category, items in enrichment_data.get('key_amenities', {}).items():
                print(f"    - {category}: {items} (length: {len(items) if items else 0})")
        
        # Store enrichment data in state
        stored_items = []
        if enrichment_data.get("zip_code"):
            state["zip_code"] = enrichment_data["zip_code"]
            stored_items.append(f"zip_code={enrichment_data['zip_code']}")
        else:
            print(f"[DEBUG] Node 2: zip_code NOT stored (value: {enrichment_data.get('zip_code')}, truthy: {bool(enrichment_data.get('zip_code'))})")
        
        if enrichment_data.get("neighborhood"):
            state["neighborhood"] = enrichment_data["neighborhood"]
            stored_items.append(f"neighborhood={enrichment_data['neighborhood']}")
        else:
            print(f"[DEBUG] Node 2: neighborhood NOT stored (value: {enrichment_data.get('neighborhood')}, truthy: {bool(enrichment_data.get('neighborhood'))})")
        
        if enrichment_data.get("landmarks"):
            state["landmarks"] = enrichment_data["landmarks"]
            stored_items.append(f"landmarks={enrichment_data['landmarks']}")
        else:
            landmarks_val = enrichment_data.get("landmarks")
            print(f"[DEBUG] Node 2: landmarks NOT stored (value: {landmarks_val}, type: {type(landmarks_val)}, truthy: {bool(landmarks_val)})")
        
        if enrichment_data.get("key_amenities"):
            state["key_amenities"] = enrichment_data["key_amenities"]
            stored_items.append(f"key_amenities={enrichment_data['key_amenities']}")
        else:
            key_amenities_val = enrichment_data.get("key_amenities")
            print(f"[DEBUG] Node 2: key_amenities NOT stored (value: {key_amenities_val}, type: {type(key_amenities_val)}, truthy: {bool(key_amenities_val)})")
        
        # Store neighborhood quality information
        if enrichment_data.get("neighborhood_quality"):
            state["neighborhood_quality"] = enrichment_data["neighborhood_quality"]
            stored_items.append("neighborhood_quality")
        
        print(f"[DEBUG] Node 2: Enrichment data stored in state: {', '.join(stored_items) if stored_items else 'NONE'}")
        print(f"[DEBUG] Node 2: Final state enrichment fields:")
        print(f"  - state['zip_code']: {state.get('zip_code')}")
        print(f"  - state['neighborhood']: {state.get('neighborhood')}")
        print(f"  - state['key_amenities']: {state.get('key_amenities')}")
        print(f"  - state['neighborhood_quality']: {state.get('neighborhood_quality')}")
    
    except ValueError as e:
        # Missing API key or configuration error
        error_msg = f"Enrichment configuration error: {str(e)}"
        state["errors"].append(error_msg)
        print(f"[DEBUG] Node 2: {error_msg}")
        # Continue without enrichment data
    except Exception as e:
        # Enrichment is optional - log error but don't break workflow
        error_msg = f"Enrichment failed: {str(e)}"
        state["errors"].append(error_msg)
        print(f"[DEBUG] Node 2: Enrichment failed (continuing): {error_msg}")
        # Continue without enrichment data
    
    print("[DEBUG] Node 2: enrich_data_node - Completed")
    return state


def predict_price_node(state: PropertyListingState) -> PropertyListingState:
    """
    Node: Price Prediction - Predicts market price using LLM.
    
    This node runs in parallel with generate_content_node after enrichment.
    It uses all available structured property data to predict the market price.
    
    Args:
        state: Current workflow state with enrichment data
        
    Returns:
        Updated state with predicted_price and predicted_price_reasoning
    """
    print("[DEBUG] Node: predict_price_node - Starting")
    
    # Track updates + new errors (returned to LangGraph so only touched keys are merged)
    updates: PropertyListingState = {}
    new_errors: list[str] = []
    
    # Extract required fields
    address = state.get("address", "")
    listing_type = state.get("listing_type", "")
    property_type = state.get("property_type", "")
    bedrooms = state.get("bedrooms")
    bathrooms = state.get("bathrooms")
    sqft = state.get("sqft")
    region = state.get("region", "US")
    
    # Extract enrichment data (optional)
    zip_code = state.get("zip_code")
    neighborhood = state.get("neighborhood")
    landmarks = state.get("landmarks")
    key_amenities = state.get("key_amenities")
    neighborhood_quality = state.get("neighborhood_quality")
    
    # Validate required fields
    if not address or not listing_type or not property_type:
        error_msg = "Price prediction requires address, listing_type, and property_type"
        new_errors.append(error_msg)
        print(f"[DEBUG] Node: predict_price_node - {error_msg}")
        updates["errors"] = new_errors
        return updates
    
    if bedrooms is None or bathrooms is None or sqft is None:
        error_msg = "Price prediction requires bedrooms, bathrooms, and sqft"
        new_errors.append(error_msg)
        print(f"[DEBUG] Node: predict_price_node - {error_msg}")
        updates["errors"] = new_errors
        return updates
    
    try:
        # Build price prediction prompt
        from utils.price_prediction import (
            build_price_prediction_prompt,
            parse_price_prediction_response,
            validate_predicted_price
        )
        
        prompt = build_price_prediction_prompt(
            address=address,
            listing_type=listing_type,
            property_type=property_type,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            sqft=sqft,
            zip_code=zip_code,
            neighborhood=neighborhood,
            landmarks=landmarks,
            key_amenities=key_amenities,
            neighborhood_quality=neighborhood_quality,
            region=region
        )
        
        print(f"[DEBUG] Node: predict_price_node - Prompt built (length: {len(prompt)} chars)")
        
        # Initialize LLM (use same model as content generation for consistency)
        from utils.llm_client import initialize_llm, call_llm_with_prompt
        
        llm = initialize_llm(
            model_name="gpt-5",
            model_provider="openai",
            reasoning_effort="minimal"
        )
        
        # Call LLM with prompt (lower temperature for more consistent predictions)
        llm_response = call_llm_with_prompt(
            llm,
            prompt,
            temperature=0.4,  # Lower temperature for more data-driven predictions
            model_name="gpt-5"
        )
        
        print(f"[DEBUG] Node: predict_price_node - LLM response received")
        
        # Parse JSON response
        parsed = parse_price_prediction_response(llm_response)
        
        predicted_price = float(parsed["predicted_price"])
        reasoning = parsed["reasoning"].strip()
        
        # Validate predicted price
        if not validate_predicted_price(predicted_price, listing_type, region):
            error_msg = f"Predicted price validation failed: {predicted_price}"
            new_errors.append(error_msg)
            print(f"[DEBUG] Node: predict_price_node - {error_msg}")
            updates["errors"] = new_errors
            return updates
        
        # Store predicted price and reasoning
        updates["predicted_price"] = predicted_price
        updates["predicted_price_reasoning"] = reasoning
        
        print(f"[DEBUG] Node: predict_price_node - Price predicted: ${predicted_price:,.2f}")
        print(f"[DEBUG] Node: predict_price_node - Reasoning: {reasoning[:100]}...")
        
    except Exception as e:
        # Price prediction is optional - log error but don't break workflow
        error_msg = f"Price prediction failed: {str(e)}"
        new_errors.append(error_msg)
        print(f"[DEBUG] Node: predict_price_node - {error_msg} (continuing)")
        # Continue without predicted price
    
    if new_errors:
        updates["errors"] = new_errors
    
    print("[DEBUG] Node: predict_price_node - Completed")
    return updates


def generate_content_node(state: PropertyListingState) -> PropertyListingState:
    """
    Node 3: Generate listing content using LLM.
    
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
    print("[DEBUG] Node 3: generate_content_node - Starting LLM content generation")
    from utils.prompts import build_listing_generation_prompt
    from utils.llm_client import initialize_llm, call_llm_with_prompt, parse_json_response
    
    updates: PropertyListingState = {}
    new_errors: list[str] = []
    
    # Validate required fields
    address = state.get("address")
    listing_type = state.get("listing_type")
    property_type = state.get("property_type")
    bedrooms = state.get("bedrooms")
    bathrooms = state.get("bathrooms")
    sqft = state.get("sqft")
    
    if not address or not listing_type or not property_type or bedrooms is None or bathrooms is None or sqft is None:
        new_errors.append(
            "Cannot generate content: missing required fields (address, listing_type, property_type, bedrooms, bathrooms, or sqft)"
        )
        updates["errors"] = new_errors
        return updates
    
    try:
        # Load environment variables from .env file in iteration1 folder
        from utils.env_loader import load_iteration1_env
        import os
        env_path = load_iteration1_env()
        if env_path:
            print(f"[DEBUG] Node 3: Loaded .env file from {env_path}")
        elif os.getenv("OPENAI_API_KEY"):
            print("[DEBUG] Node 3: OPENAI_API_KEY found in environment")
        
        # DEBUG: Log what enrichment data is retrieved from state
        print(f"[DEBUG] Node 3: Retrieving enrichment data from state:")
        print(f"  - state.get('zip_code'): {state.get('zip_code')} (type: {type(state.get('zip_code'))})")
        print(f"  - state.get('neighborhood'): {state.get('neighborhood')} (type: {type(state.get('neighborhood'))})")
        print(f"  - state.get('landmarks'): {state.get('landmarks')} (type: {type(state.get('landmarks'))}, length: {len(state.get('landmarks', [])) if state.get('landmarks') else 'N/A'})")
        print(f"  - state.get('key_amenities'): {state.get('key_amenities')} (type: {type(state.get('key_amenities'))})")
        if state.get('key_amenities'):
            for category, items in state.get('key_amenities', {}).items():
                print(f"    - {category}: {items} (length: {len(items) if items else 0})")
        
        # Build comprehensive prompt with all available data (with tracing)
        from utils.tracing import trace_prompt_building, set_trace_metadata
        
        prompt, prompt_metrics = trace_prompt_building(
            build_listing_generation_prompt,
            address=address,
            listing_type=listing_type,
            property_type=property_type,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            sqft=sqft,
            notes=state.get("notes"),
            normalized_address=state.get("normalized_address"),
            normalized_notes=state.get("normalized_notes"),
            zip_code=state.get("zip_code"),
            neighborhood=state.get("neighborhood"),
            landmarks=state.get("landmarks"),
            key_amenities=state.get("key_amenities"),
            neighborhood_quality=state.get("neighborhood_quality"),
            region=state.get("region", "US"),
        )
        
        # Store prompt building metrics
        set_trace_metadata("prompt_building_metrics", prompt_metrics)
        
        # DEBUG: Log prompt sections (first 2000 chars to see structure)
        print(f"[DEBUG] Node 3: Prompt preview (first 2000 chars):")
        print(prompt[:2000])
        if len(prompt) > 2000:
            print(f"[DEBUG] Node 3: ... (prompt continues, total length: {len(prompt)} chars)")
        
        # Initialize LLM (use environment variables for API keys)
        # Using gpt-4o (best model) for highest quality listing generation
        # This is a single critical call, so quality is prioritized over cost
        llm = initialize_llm(
            model_name="gpt-5",
            model_provider="openai",
            reasoning_effort="minimal"
        )
        
        # Call LLM with prompt (tracing is handled inside call_llm_with_prompt)
        llm_response = call_llm_with_prompt(
            llm, 
            prompt, 
            temperature=0.7,
            model_name="gpt-5-mini"
        )
        
        # Store raw + parsed output
        updates["llm_raw_output"] = llm_response
        parsed_json = parse_json_response(llm_response)
        updates["llm_parsed"] = parsed_json
        print(f"[DEBUG] Node 3: LLM content generated - Title: {parsed_json.get('title', 'N/A')[:50]}...")
        
    except Exception as e:
        # Log error but don't break workflow - errors will be handled downstream
        error_msg = f"Content generation failed: {str(e)}"
        new_errors.append(error_msg)
        print(f"[DEBUG] Node 3: Content generation failed (continuing): {error_msg}")
        # Continue without LLM output
    
    if new_errors:
        updates["errors"] = new_errors
    
    print("[DEBUG] Node 3: generate_content_node - Completed")
    return updates


def output_guardrail_node(state: PropertyListingState) -> PropertyListingState:
    """
    Node 4: Output guardrail - Validates LLM output (safety and compliance).
    
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
    print("[DEBUG] Node 4: output_guardrail_node - Starting output guardrail validation")
    print(f"[DEBUG] Node 4: State keys: {list(state.keys())}")
    print(f"[DEBUG] Node 4: Has predicted_price: {state.get('predicted_price') is not None}")
    print(f"[DEBUG] Node 4: Has llm_parsed: {state.get('llm_parsed') is not None}")
    from utils.guardrails import check_output_guardrails
    
    # Initialize errors list if not present
    if "errors" not in state:
        state["errors"] = []
    
    # Get LLM output
    llm_parsed = state.get("llm_parsed")
    
    if not llm_parsed:
        error_msg = "Output guardrail: No LLM output to validate"
        state["errors"].append(error_msg)
        print(f"[DEBUG] Node 4: {error_msg}")
        print("[DEBUG] Node 4: output_guardrail_node - Completed (no output to validate)")
        return state
    
    # Get original input for compliance validation
    original_price = state.get("price")
    listing_type = state.get("listing_type")
    
    # Log what we're validating
    title_preview = llm_parsed.get("title", "N/A")[:50]
    print(f"[DEBUG] Node 4: Found LLM output - title: {title_preview}...")
    
    # Perform comprehensive output guardrail checks
    guardrail_errors = check_output_guardrails(
        llm_parsed=llm_parsed,
        original_price=original_price,
        listing_type=listing_type
    )
    
    # Add any guardrail errors to state
    if guardrail_errors:
        state["errors"].extend(guardrail_errors)
        print(f"[DEBUG] Node 4: Output guardrail validation failed - {len(guardrail_errors)} error(s) found")
        for error in guardrail_errors:
            print(f"[DEBUG] Node 4:   - {error}")
    else:
        print("[DEBUG] Node 4: Output guardrail validation passed - all checks successful")
    
    print("[DEBUG] Node 4: output_guardrail_node - Completed")
    return state


def format_output_node(state: PropertyListingState) -> PropertyListingState:
    """
    Node 5: Format final output.
    
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
    print("[DEBUG] Node 5: format_output_node - Starting output formatting")
    from utils.formatters import extract_and_format_output, format_listing
    
    # Initialize errors list if not present
    if "errors" not in state:
        state["errors"] = []
    
    # Check if LLM output exists
    llm_parsed = state.get("llm_parsed")
    
    if not llm_parsed:
        error_msg = "Format output: No LLM output to format"
        state["errors"].append(error_msg)
        print(f"[DEBUG] Node 5: {error_msg}")
        print("[DEBUG] Node 5: format_output_node - Completed (no output to format)")
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
            print(f"[DEBUG] Node 5: Formatted title: {state['title'][:50]}...")
        if state["description"]:
            print(f"[DEBUG] Node 5: Formatted description: {state['description'][:50]}...")
        if state["price_block"]:
            print(f"[DEBUG] Node 5: Formatted price_block: {state['price_block']}")
        
        # Get original seller price, predicted price, and listing type for display
        seller_price = state.get("price")
        predicted_price = state.get("predicted_price")  # Future feature: price prediction
        listing_type = state.get("listing_type")
        
        # Create final formatted listing with organized structure
        formatted_listing = format_listing(
            title=state["title"],
            description=state["description"],
            price_block=state["price_block"],
            seller_price=seller_price,  # Pass original seller price for display
            predicted_price=predicted_price,  # Pass predicted price (if available from future price prediction feature)
            listing_type=listing_type,  # Pass listing type for dynamic labeling
            region=state.get("region", "US"),  # Pass region for currency formatting
            remove_price_from_desc=True  # Safety net: remove price even if guardrails missed it
        )
        
        state["formatted_listing"] = formatted_listing
        print("[DEBUG] Node 5: Created formatted_listing with proper structure")
        
    except Exception as e:
        # Log error but don't break workflow - errors will be handled downstream
        error_msg = f"Format output failed: {str(e)}"
        state["errors"].append(error_msg)
        print(f"[DEBUG] Node 5: {error_msg}")
        # Continue without formatted output
    
    print("[DEBUG] Node 5: format_output_node - Completed")
    return state
