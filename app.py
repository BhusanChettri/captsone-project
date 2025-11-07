"""
Gradio UI for Property Listing System - Iteration 1

This module provides a Gradio-based web interface for the property listing system.
Users can input property details and get AI-generated listings.
"""

import gradio as gr
from main import process_listing_request
from utils.region_config import (
    get_region_config,
    get_fields_for_listing_type,
    get_currency_symbol,
    get_supported_regions,
    FieldType
)


def create_listing_ui(
    address: str,
    listing_type: str,
    price: float,
    notes: str,
    region: str,
    billing_cycle: str,
    lease_term: str,
    security_deposit: float,
    hoa_fees: float,
    property_taxes: float,
    council_tax_rental: float,
    council_tax_sale: float,
    rates: float,
    strata_fees: float,
    progress: gr.Progress = gr.Progress(),
) -> tuple:
    """
    Process listing request from Gradio UI and return unified output.
    
    Args:
        address: Property address
        listing_type: "sale" or "rent"
        price: Asking price
        notes: Property description/notes
        billing_cycle: Rental billing cycle (rental only)
        lease_term: Lease term (rental only)
        security_deposit: Security deposit (rental only)
        hoa_fees: HOA fees (sale only)
        property_taxes: Property taxes (sale only)
        
    Returns:
        Single unified output string containing either:
        - Generated listing (if successful)
        - Error messages (if validation failed)
    """
    # Update progress
    progress(0.1, desc="Validating input...")
    
    # Handle None/empty values for required fields
    # Convert to empty string or None as appropriate
    address = address.strip() if address else ""
    listing_type = listing_type.strip() if listing_type else ""
    price = price if price is not None and price != "" else None
    # Notes is optional - convert empty string to None
    notes = notes.strip() if notes and notes.strip() else None
    
    # Normalize region
    region = region.strip().upper() if region and region.strip() else "US"
    
    # Convert empty strings to None for optional fields
    billing_cycle = billing_cycle.strip() if billing_cycle and billing_cycle.strip() else None
    lease_term = lease_term.strip() if lease_term and lease_term.strip() else None
    security_deposit = security_deposit if security_deposit and security_deposit > 0 else None
    hoa_fees = hoa_fees if hoa_fees and hoa_fees > 0 else None
    property_taxes = property_taxes if property_taxes and property_taxes > 0 else None
    # Council tax can be for rental or sale (UK)
    council_tax = council_tax_rental if listing_type == "rent" else council_tax_sale
    council_tax = council_tax if council_tax and council_tax > 0 else None
    rates = rates if rates and rates > 0 else None
    strata_fees = strata_fees if strata_fees and strata_fees > 0 else None
    
    # Process the request
    progress(0.3, desc="Processing listing request...")
    result = process_listing_request(
        address=address,
        listing_type=listing_type,
        price=price,
        notes=notes,
        region=region,
        billing_cycle=billing_cycle,
        lease_term=lease_term,
        security_deposit=security_deposit,
        hoa_fees=hoa_fees,
        property_taxes=property_taxes,
        council_tax=council_tax,
        rates=rates,
        strata_fees=strata_fees,
    )
    
    # Format unified output
    progress(0.9, desc="Formatting output...")
    if result["success"] and result["listing"]:
        # Success: return the generated listing
        output_text = result["listing"]["formatted_listing"]
    else:
        # Error: format error message
        output_text = "## ⚠️ Processing Stopped\n\n"
        if result["errors"]:
            output_text += "**Errors Detected:**\n\n"
            for error in result["errors"]:
                output_text += f"• {error}\n"
        else:
            output_text += "No listing could be generated."
    
    # Complete progress
    progress(1.0, desc="Complete!")
    
    # Return output text, visibility update for output column, and re-enable button
    # After first generation, show the output column
    return (
        output_text,  # Output display
        gr.update(visible=True),  # Show output column
        gr.update(interactive=True),  # Re-enable submit button
    )


def create_gradio_interface():
    """
    Create and return Gradio interface.
    
    Returns:
        Gradio Blocks interface
    """
    # Custom CSS for gray color scheme only
    custom_css = """
    /* Primary button (Generate Listing) - Professional gray gradient */
    .gradio-container button.primary,
    .gradio-container button[data-testid*="primary"],
    button.primary {
        background: linear-gradient(135deg, #4b5563 0%, #374151 100%) !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 4px rgba(75, 85, 99, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    .gradio-container button.primary:hover,
    .gradio-container button[data-testid*="primary"]:hover,
    button.primary:hover {
        background: linear-gradient(135deg, #374151 0%, #1f2937 100%) !important;
        box-shadow: 0 4px 8px rgba(75, 85, 99, 0.4) !important;
        transform: translateY(-1px) !important;
    }
    .gradio-container button.primary:active,
    .gradio-container button[data-testid*="primary"]:active,
    button.primary:active {
        transform: translateY(0) !important;
        box-shadow: 0 2px 4px rgba(75, 85, 99, 0.3) !important;
    }
    
    /* Secondary button (Clear) - Clean outline style with gray */
    .gradio-container button.secondary,
    .gradio-container button[data-testid*="secondary"],
    button.secondary {
        background: white !important;
        color: #4b5563 !important;
        border: 2px solid #d1d5db !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
    }
    .gradio-container button.secondary:hover,
    .gradio-container button[data-testid*="secondary"]:hover,
    button.secondary:hover {
        background: #f9fafb !important;
        border-color: #9ca3af !important;
        color: #1f2937 !important;
    }
    .gradio-container button.secondary:active,
    .gradio-container button[data-testid*="secondary"]:active,
    button.secondary:active {
        background: #f3f4f6 !important;
    }
    
    /* Soft gray colors for input labels */
    .gradio-container label,
    .gradio-container .label-wrap,
    .gradio-container .form-label {
        color: #4b5563 !important; /* Medium gray */
        font-weight: 500 !important;
    }
    
    /* Soft gray colors for radio button labels */
    .gradio-container .radio-group label,
    .gradio-container input[type="radio"] + label {
        color: #4b5563 !important;
    }
    
    /* Soft gray colors for accordion headers */
    .gradio-container .accordion-header,
    .gradio-container .accordion-title {
        color: #4b5563 !important;
        font-weight: 500 !important;
    }
    
    /* Soft gray info text colors */
    .gradio-container .form-text,
    .gradio-container .info-text,
    .gradio-container small {
        color: #6b7280 !important; /* Lighter gray for hints */
    }
    
    /* Remove blue highlights from selected radio buttons - use gray instead */
    .gradio-container input[type="radio"]:checked + label,
    .gradio-container .radio-group input[type="radio"]:checked + label {
        color: #1f2937 !important;
    }
    
    /* Gray background for selected radio buttons */
    .gradio-container input[type="radio"]:checked {
        background-color: #4b5563 !important;
        border-color: #4b5563 !important;
    }
    
    /* Gray focus states instead of blue */
    .gradio-container input:focus,
    .gradio-container textarea:focus,
    .gradio-container select:focus {
        border-color: #9ca3af !important;
        box-shadow: 0 0 0 3px rgba(156, 163, 175, 0.1) !important;
    }
    
    /* Gray for active/selected states */
    .gradio-container .selected,
    .gradio-container [aria-selected="true"] {
        background-color: #f3f4f6 !important;
        color: #1f2937 !important;
    }
    
    /* Button row spacing */
    .button-row {
        gap: 12px !important;
    }
    
    /* Progress indicator centering */
    #progress-indicator {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        min-height: 500px !important;
        height: 100% !important;
    }
    
    #progress-indicator > div {
        width: 100% !important;
        height: 100% !important;
    }
    
    /* Make accordion dropdown arrows more visible - Target all possible arrow elements */
    .gradio-container [class*="accordion"] svg,
    .gradio-container [class*="accordion"] path,
    .gradio-container [class*="accordion"] [class*="icon"] svg,
    .gradio-container [class*="accordion"] [class*="arrow"] svg,
    .gradio-container [class*="accordion"] [class*="chevron"] svg {
        color: #1f2937 !important;
        stroke: #1f2937 !important;
        fill: #1f2937 !important;
        opacity: 1 !important;
        stroke-width: 2.5 !important;
    }
    
    /* Make accordion header arrows more prominent */
    .gradio-container [class*="accordion"] [class*="header"] svg,
    .gradio-container [class*="accordion"] [class*="title"] svg,
    .gradio-container [class*="accordion"] button svg {
        color: #1f2937 !important;
        stroke: #1f2937 !important;
        fill: #1f2937 !important;
        opacity: 1 !important;
        width: 18px !important;
        height: 18px !important;
        stroke-width: 2.5 !important;
    }
    
    /* Target Gradio's specific accordion arrow classes */
    .gradio-container .accordion-header button svg,
    .gradio-container .accordion-title button svg {
        color: #1f2937 !important;
        stroke: #1f2937 !important;
        fill: #1f2937 !important;
        opacity: 1 !important;
        stroke-width: 2.5 !important;
    }
    
    /* Make accordion toggle button more visible */
    .gradio-container [class*="accordion"] button {
        opacity: 1 !important;
    }
    
    /* Ensure arrow is visible on hover */
    .gradio-container [class*="accordion"]:hover svg,
    .gradio-container [class*="accordion"]:hover path {
        opacity: 1 !important;
        stroke: #111827 !important;
        color: #111827 !important;
    }
    """
    
    with gr.Blocks(title="Property Listing AI System - Iteration 1", theme=gr.themes.Soft(), css=custom_css) as demo:
        gr.Markdown("<h1 style='text-align: center;'>🏠 Property Listing AI System</h1>", elem_classes=["centered-title"])
        gr.Markdown("<p style='text-align: center;'>Generate professional property listings with AI assistance</p>", elem_classes=["centered-subtitle"])
        gr.Markdown("---")
        
        # Main container row - will be updated dynamically
        # Initially shows only input (centered), then splits into two columns after first generation
        with gr.Row() as main_row:
            # Input column - always visible, centered when output is hidden
            with gr.Column(scale=1, min_width=400) as input_column:
                
                region_input = gr.Dropdown(
                    label="Region *",
                    choices=[r["code"] for r in get_supported_regions()],
                    value="US",
                    info="Select the region/country for this listing"
                )
                
                address_input = gr.Textbox(
                    label="Property Address *",
                    placeholder="123 Main Street, New York, NY 10001",
                    lines=2
                )
                
                listing_type_input = gr.Radio(
                    label="Listing Type *",
                    choices=["sale", "rent"],
                    value="sale"
                )
                
                price_input = gr.Number(
                    label="Asking Price (USD) *",
                    minimum=0,
                    precision=2,
                    info="Total sale price in USD"
                )
                
                notes_input = gr.Textbox(
                    label="Property Notes/Description",
                    placeholder="Beautiful 2BR/1BA apartment with modern kitchen, hardwood floors, and great natural light. Close to subway and Central Park.",
                    lines=5
                )
                
                # Rental-specific fields (dynamically shown based on region)
                rental_accordion = gr.Accordion("Rental-Specific Fields (Optional)", open=False, visible=False)
                with rental_accordion:
                    billing_cycle_input = gr.Textbox(
                        label="Billing Cycle",
                        placeholder="e.g., monthly, weekly",
                        value=""
                    )
                    lease_term_input = gr.Textbox(
                        label="Lease Term",
                        placeholder="e.g., 12 months, 6 months",
                        value=""
                    )
                    security_deposit_input = gr.Number(
                        label="Security Deposit",
                        value=0.0,
                        minimum=0,
                        precision=2
                    )
                    council_tax_rental_input = gr.Number(
                        label="Council Tax (UK only)",
                        value=0.0,
                        minimum=0,
                        precision=2,
                        visible=False
                    )
                
                # Sale-specific fields (dynamically shown based on region)
                # Initialize with US defaults: hoa_fees and property_taxes visible
                sale_accordion = gr.Accordion("Sale-Specific Fields (Optional)", open=False, visible=True)
                with sale_accordion:
                    hoa_fees_input = gr.Number(
                        label="HOA Fees (USD/month)",
                        value=0.0,
                        minimum=0,
                        precision=2,
                        visible=True  # Visible by default for US
                    )
                    property_taxes_input = gr.Number(
                        label="Property Taxes (USD/year)",
                        value=0.0,
                        minimum=0,
                        precision=2,
                        visible=True  # Visible by default for US
                    )
                    council_tax_sale_input = gr.Number(
                        label="Council Tax (UK only)",
                        value=0.0,
                        minimum=0,
                        precision=2,
                        visible=False
                    )
                    rates_input = gr.Number(
                        label="Council Rates (Australia only)",
                        value=0.0,
                        minimum=0,
                        precision=2,
                        visible=False
                    )
                    strata_fees_input = gr.Number(
                        label="Strata Fees / Body Corporate",
                        value=0.0,
                        minimum=0,
                        precision=2,
                        visible=False
                    )
                
                # Button row with spacing
                with gr.Row(elem_classes=["button-row"]):
                    submit_btn = gr.Button("Generate Listing", variant="primary", size="lg", scale=2, interactive=False)
                    clear_btn = gr.Button("Clear", variant="secondary", size="lg", scale=1)
            
            # Output column - initially hidden, shown after first generation
            with gr.Column(scale=1, visible=False) as output_column:
                # Progress indicator - shown in the center of output area during processing
                progress_indicator = gr.Markdown(
                    value="",
                    visible=False,
                    elem_classes=["progress-indicator"],
                    elem_id="progress-indicator"
                )
                
                # Single unified output area - displays listing or errors dynamically
                # This can be extended for chat capabilities in future iterations
                output_display = gr.Markdown(
                    value="",
                    label="Result",
                    elem_classes=["output-display"]
                )
        
        # Function to update field visibility and labels based on listing type and region
        def update_field_visibility(listing_type: str, region: str):
            """Show/hide fields and update labels based on listing type and region selection"""
            region = region.upper() if region else "US"
            config = get_region_config(region)
            currency_symbol = config["currency_symbol"]
            currency = config["currency"]
            
            # Get fields for this listing type and region
            fields = get_fields_for_listing_type(region, listing_type)
            
            # Update price label
            if listing_type == "rent":
                price_label = f"Monthly Rent ({currency}) *"
                price_info = f"Monthly rental price in {currency}"
            else:
                price_label = f"Asking Price ({currency}) *"
                price_info = f"Total sale price in {currency}"
            
            # Determine visibility and labels for sale fields
            hoa_visible = FieldType.HOA_FEES in fields
            hoa_label = fields[FieldType.HOA_FEES]["label"] + f" ({fields[FieldType.HOA_FEES]['unit']})" if hoa_visible else "HOA Fees"
            
            property_taxes_visible = FieldType.PROPERTY_TAXES in fields
            property_taxes_label = fields[FieldType.PROPERTY_TAXES]["label"] + f" ({fields[FieldType.PROPERTY_TAXES]['unit']})" if property_taxes_visible else "Property Taxes"
            
            council_tax_visible = FieldType.COUNCIL_TAX in fields
            council_tax_label = fields[FieldType.COUNCIL_TAX]["label"] + f" ({fields[FieldType.COUNCIL_TAX]['unit']})" if council_tax_visible else "Council Tax"
            
            rates_visible = FieldType.RATES in fields
            rates_label = fields[FieldType.RATES]["label"] + f" ({fields[FieldType.RATES]['unit']})" if rates_visible else "Council Rates"
            
            strata_visible = FieldType.STRATA_FEES in fields
            strata_label = fields[FieldType.STRATA_FEES]["label"] + f" ({fields[FieldType.STRATA_FEES]['unit']})" if strata_visible else "Strata Fees"
            
            # Security deposit label
            security_deposit_label = "Security Deposit"
            if FieldType.SECURITY_DEPOSIT in fields:
                security_deposit_label = fields[FieldType.SECURITY_DEPOSIT]["label"]
                if fields[FieldType.SECURITY_DEPOSIT]["unit"]:
                    security_deposit_label += f" ({fields[FieldType.SECURITY_DEPOSIT]['unit']})"
            
            if listing_type == "rent":
                return (
                    gr.update(visible=True),  # rental_accordion
                    gr.update(visible=False),  # sale_accordion
                    gr.update(label=price_label, info=price_info),  # price_input
                    gr.update(label=security_deposit_label),  # security_deposit_input
                    gr.update(visible=council_tax_visible, label=council_tax_label),  # council_tax_rental_input
                    # Sale fields (hidden)
                    gr.update(visible=False),  # hoa_fees_input
                    gr.update(visible=False),  # property_taxes_input
                    gr.update(visible=False),  # council_tax_sale_input
                    gr.update(visible=False),  # rates_input
                    gr.update(visible=False),  # strata_fees_input
                )
            else:  # sale
                return (
                    gr.update(visible=False),  # rental_accordion
                    gr.update(visible=True),  # sale_accordion
                    gr.update(label=price_label, info=price_info),  # price_input
                    gr.update(label=security_deposit_label),  # security_deposit_input (not used but needed for consistency)
                    gr.update(visible=False),  # council_tax_rental_input
                    # Sale fields
                    gr.update(visible=hoa_visible, label=hoa_label),  # hoa_fees_input
                    gr.update(visible=property_taxes_visible, label=property_taxes_label),  # property_taxes_input
                    gr.update(visible=council_tax_visible, label=council_tax_label),  # council_tax_sale_input
                    gr.update(visible=rates_visible, label=rates_label),  # rates_input
                    gr.update(visible=strata_visible, label=strata_label),  # strata_fees_input
                )
        
        # Function to validate required fields and enable/disable submit button
        def validate_required_fields(address: str, listing_type: str, price):
            """Check if all required fields are filled and enable/disable submit button accordingly"""
            # Check if address is provided and not empty
            has_address = address and str(address).strip() != ""
            
            # Check if listing type is selected
            has_listing_type = listing_type and str(listing_type).strip() != ""
            
            # Check if price is provided and valid (not None, not 0, not empty string)
            # Handle both float and None types
            has_price = False
            if price is not None:
                try:
                    price_float = float(price)
                    has_price = price_float > 0  # Price must be greater than 0
                except (ValueError, TypeError):
                    has_price = False
            
            # Enable button only if all three required fields are filled
            all_fields_filled = has_address and has_listing_type and has_price
            
            return gr.update(interactive=all_fields_filled)
        
        # Update field visibility and labels when listing type or region changes
        def update_on_listing_or_region_change(listing_type: str, region: str):
            """Update fields when listing type or region changes"""
            return update_field_visibility(listing_type, region)
        
        listing_type_input.change(
            fn=update_on_listing_or_region_change,
            inputs=[listing_type_input, region_input],
            outputs=[
                rental_accordion, sale_accordion, price_input, security_deposit_input,
                council_tax_rental_input, hoa_fees_input, property_taxes_input,
                council_tax_sale_input, rates_input, strata_fees_input
            ]
        ).then(
            fn=validate_required_fields,
            inputs=[address_input, listing_type_input, price_input],
            outputs=[submit_btn]
        )
        
        region_input.change(
            fn=update_on_listing_or_region_change,
            inputs=[listing_type_input, region_input],
            outputs=[
                rental_accordion, sale_accordion, price_input, security_deposit_input,
                council_tax_rental_input, hoa_fees_input, property_taxes_input,
                council_tax_sale_input, rates_input, strata_fees_input
            ]
        ).then(
            fn=validate_required_fields,
            inputs=[address_input, listing_type_input, price_input],
            outputs=[submit_btn]
        )
        
        # Initialize fields on page load with default values (US, sale)
        def initialize_fields():
            """Initialize field visibility and labels on page load"""
            return update_field_visibility("sale", "US")
        
        # Use load event to initialize fields when page loads
        demo.load(
            fn=initialize_fields,
            inputs=[],
            outputs=[
                rental_accordion, sale_accordion, price_input, security_deposit_input,
                council_tax_rental_input, hoa_fees_input, property_taxes_input,
                council_tax_sale_input, rates_input, strata_fees_input
            ]
        )
        
        # Validate required fields when address changes
        address_input.change(
            fn=validate_required_fields,
            inputs=[address_input, listing_type_input, price_input],
            outputs=[submit_btn]
        )
        
        # Validate required fields when price changes
        price_input.change(
            fn=validate_required_fields,
            inputs=[address_input, listing_type_input, price_input],
            outputs=[submit_btn]
        )
        
        # Function to show progress indicator and output column
        def show_progress_indicator():
            """Show progress indicator in the center of output area and make output column visible"""
            progress_html = """
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 500px; height: 100%; text-align: center; padding: 40px 20px;">
                <div style="display: inline-block; width: 60px; height: 60px; border: 5px solid #e0e0e0; border-top: 5px solid #4b5563; border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 20px;"></div>
                <h3 style="margin: 0; color: #333; font-size: 18px; font-weight: 600;">Generating listing data..</h3>
                <p style="margin-top: 10px; font-size: 14px; color: #666;">This may take a few seconds</p>
            </div>
            <style>
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            </style>
            """
            return (
                "",  # Clear output display
                gr.update(interactive=False),  # Disable button
                gr.update(visible=True),  # Show output column
                gr.update(visible=True, value=progress_html),  # Show progress indicator in output area
            )
        
        # Function to disable all input fields (greyed out, non-editable)
        def disable_all_inputs():
            """Disable all input fields to prevent editing during processing"""
            return (
                gr.update(interactive=False),  # region_input
                gr.update(interactive=False),  # address_input
                gr.update(interactive=False),  # listing_type_input
                gr.update(interactive=False),  # price_input
                gr.update(interactive=False),  # notes_input
                gr.update(interactive=False),  # billing_cycle_input
                gr.update(interactive=False),  # lease_term_input
                gr.update(interactive=False),  # security_deposit_input
                gr.update(interactive=False),  # council_tax_rental_input
                gr.update(interactive=False),  # hoa_fees_input
                gr.update(interactive=False),  # property_taxes_input
                gr.update(interactive=False),  # council_tax_sale_input
                gr.update(interactive=False),  # rates_input
                gr.update(interactive=False),  # strata_fees_input
            )
        
        # Function to re-enable all input fields
        def enable_all_inputs():
            """Re-enable all input fields after processing completes"""
            return (
                gr.update(interactive=True),  # region_input
                gr.update(interactive=True),  # address_input
                gr.update(interactive=True),  # listing_type_input
                gr.update(interactive=True),  # price_input
                gr.update(interactive=True),  # notes_input
                gr.update(interactive=True),  # billing_cycle_input
                gr.update(interactive=True),  # lease_term_input
                gr.update(interactive=True),  # security_deposit_input
                gr.update(interactive=True),  # council_tax_rental_input
                gr.update(interactive=True),  # hoa_fees_input
                gr.update(interactive=True),  # property_taxes_input
                gr.update(interactive=True),  # council_tax_sale_input
                gr.update(interactive=True),  # rates_input
                gr.update(interactive=True),  # strata_fees_input
            )
        
        # Function to hide progress indicator
        def hide_progress_indicator():
            """Hide progress indicator"""
            return gr.update(visible=False, value="")
        
        # Function to clear previous output and disable button when processing starts
        def clear_output_and_disable_button():
            """Clear previous error/output messages and disable button immediately"""
            return (
                "",  # Clear output display
                gr.update(interactive=False),  # Disable button
            )
        
        # Function to clear all inputs and output
        def clear_all_fields():
            """Reset all input fields to empty/default values and clear output"""
            return (
                "US",  # region_input (default to US)
                "",  # address_input (empty string)
                "sale",  # listing_type_input (default to sale)
                gr.update(value=None, label="Asking Price (USD) *", info="Total sale price in USD"),  # price_input (reset value and label)
                "",  # notes_input (empty string)
                gr.update(visible=False),  # rental_accordion (hide for sale default)
                gr.update(visible=True),  # sale_accordion (show for sale default)
                "",  # billing_cycle_input (empty string)
                "",  # lease_term_input (empty string)
                0.0,  # security_deposit_input (reset to 0)
                0.0,  # council_tax_rental_input (reset to 0)
                0.0,  # hoa_fees_input (reset to 0)
                0.0,  # property_taxes_input (reset to 0)
                0.0,  # council_tax_sale_input (reset to 0)
                0.0,  # rates_input (reset to 0)
                0.0,  # strata_fees_input (reset to 0)
                "",  # output_display (clear output)
                gr.update(visible=False),  # output_column (hide output column)
                gr.update(visible=False, value=""),  # progress_indicator (hide)
                gr.update(interactive=False),  # submit_btn (disable button since fields are cleared)
            )
        
        # Connect clear button
        # When clicked: Reset all inputs to empty/default and clear output
        clear_btn.click(
            fn=clear_all_fields,
            inputs=[],
            outputs=[
                region_input,
                address_input,
                listing_type_input,
                price_input,  # Resets value and label
                notes_input,
                rental_accordion,  # Reset accordion visibility
                sale_accordion,  # Reset accordion visibility
                billing_cycle_input,
                lease_term_input,
                security_deposit_input,
                council_tax_rental_input,
                hoa_fees_input,
                property_taxes_input,
                council_tax_sale_input,
                rates_input,
                strata_fees_input,
                output_display,
                output_column,
                progress_indicator,
                submit_btn,  # Disable button when fields are cleared
            ],
        )
        
        # Connect submit button
        # When clicked: 
        # 1. Show progress indicator and disable button
        # 2. Disable all input fields (greyed out, no progress bars)
        # 3. Generate listing (with progress bar on right side only)
        # 4. Hide progress indicator and show results
        # 5. Re-enable all input fields and button
        submit_btn.click(
            fn=show_progress_indicator,
            inputs=[],
            outputs=[
                output_display,  # Clear output display immediately
                submit_btn,      # Disable button immediately
                output_column,   # Show output column (so progress is visible)
                progress_indicator,  # Show progress indicator in output area
            ],
        ).then(
            fn=disable_all_inputs,
            inputs=[],
            outputs=[
                region_input,
                address_input,
                listing_type_input,
                price_input,
                notes_input,
                billing_cycle_input,
                lease_term_input,
                security_deposit_input,
                council_tax_rental_input,
                hoa_fees_input,
                property_taxes_input,
                council_tax_sale_input,
                rates_input,
                strata_fees_input,
            ],
        ).then(
            fn=create_listing_ui,
            inputs=[
                address_input,
                listing_type_input,
                price_input,
                notes_input,
                region_input,
                billing_cycle_input,
                lease_term_input,
                security_deposit_input,
                hoa_fees_input,
                property_taxes_input,
                council_tax_rental_input,
                council_tax_sale_input,
                rates_input,
                strata_fees_input,
            ],
            outputs=[
                output_display,  # Output text
                output_column,   # Keep output column visible
                submit_btn,      # Re-enable button
            ],
            show_progress="full",  # Show full progress bar with timer (only on right side)
        ).then(
            fn=hide_progress_indicator,
            inputs=[],
            outputs=[progress_indicator],  # Hide progress indicator when output is ready
        ).then(
            fn=enable_all_inputs,
            inputs=[],
            outputs=[
                region_input,
                address_input,
                listing_type_input,
                price_input,
                notes_input,
                billing_cycle_input,
                lease_term_input,
                security_deposit_input,
                council_tax_rental_input,
                hoa_fees_input,
                property_taxes_input,
                council_tax_sale_input,
                rates_input,
                strata_fees_input,
            ],
        )
        
    
    return demo


def main():
    """Launch Gradio interface"""
    import os
    demo = create_gradio_interface()
    # Use environment variable or default to 7860
    port = int(os.getenv("GRADIO_SERVER_PORT", 7860))
    print(f"Starting Gradio server on port {port}...")
    demo.launch(share=False, server_name="0.0.0.0", server_port=port)


if __name__ == "__main__":
    main()

