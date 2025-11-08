"""
Gradio UI for Property List Mate - Simplified Essential Fields

This module provides a Gradio-based web interface for Property List Mate.
Users can input essential property details and get AI-generated listings.
"""

import gradio as gr
from main import process_listing_request
from utils.region_config import (
    get_region_config,
)


def create_listing_ui(
    address: str,
    listing_type: str,
    property_type: str,
    bedrooms: int | None,
    bathrooms: float | None,
    sqft: int | None,
    notes: str,
    progress: gr.Progress = gr.Progress(),
) -> tuple:
    """
    Process listing request from Gradio UI and return unified output.
    
    The AI workflow focuses on generating content from essential property details
    (address, type, size) with neighborhood enrichment. Administrative details 
    (price, lease terms, etc.) can be added later when posting the listing.
    
    Args:
        address: Property address
        listing_type: "sale" or "rent"
        property_type: Type of property (Apartment, House, etc.)
        bedrooms: Number of bedrooms
        bathrooms: Number of bathrooms
        sqft: Square footage
        notes: Property description/notes (features, amenities, etc.)
        
    Returns:
        Single unified output string containing either:
        - Generated listing (if successful)
        - Error messages (if validation failed)
    """
    # Update progress
    progress(0.1, desc="Validating input...")
    
    # Handle None/empty values for required fields
    address = address.strip() if address else ""
    listing_type = listing_type.strip() if listing_type else ""
    property_type = property_type.strip() if property_type else ""
    
    # Handle numeric required fields
    bedrooms = bedrooms if bedrooms is not None and bedrooms >= 0 else None
    bathrooms = bathrooms if bathrooms is not None and bathrooms >= 0 else None
    sqft = sqft if sqft is not None and sqft > 0 else None
    
    # Notes is optional - convert empty string to None
    notes = notes.strip() if notes and notes.strip() else None
    
    # Default region to US
    region = "US"
    
    # Process the request
    progress(0.3, desc="Processing listing request...")
    result = process_listing_request(
        address=address,
        listing_type=listing_type,
        property_type=property_type,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        sqft=sqft,
        notes=notes,
        region=region,
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
    # Custom CSS
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
        color: #4b5563 !important;
        font-weight: 500 !important;
    }
    
    /* Soft gray colors for radio button labels */
    .gradio-container .radio-group label,
    .gradio-container input[type="radio"] + label {
        color: #4b5563 !important;
    }
    
    /* Soft gray info text colors */
    .gradio-container .form-text,
    .gradio-container .info-text,
    .gradio-container small {
        color: #6b7280 !important;
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
    
    /* Reduce spacing between form elements to make it more compact */
    /* REDUCED BY 2px TOTAL: 8px -> 7px -> 6px */
    .gradio-container [class*="form"] {
        margin-bottom: 6px !important;
    }
    
    /* Reduce spacing before button row - make it more compact */
    /* REDUCED BY 2px TOTAL: margin-top 4px -> 3px -> 2px, margin-bottom 4px -> 3px -> 2px */
    .button-row {
        gap: 12px !important;
        margin-top: 2px !important;
        margin-bottom: 2px !important;
    }
    
    /* Reduce spacing after textarea/notes field */
    /* REDUCED BY 2px TOTAL: 4px -> 3px -> 2px */
    .gradio-container textarea {
        margin-bottom: 2px !important;
    }
    
    /* Reduce overall container padding */
    /* REDUCED BY 2px TOTAL: 8px -> 7px -> 6px */
    .gradio-container {
        padding: 6px !important;
    }
    
    /* Reduce spacing in columns */
    /* REDUCED BY 2px TOTAL: 6px -> 5px -> 4px */
    .gradio-container [class*="column"] {
        gap: 4px !important;
    }
    
    /* Reduce header spacing */
    /* REDUCED BY 2px TOTAL: 8px 0 4px 0 -> 7px 0 3px 0 -> 6px 0 2px 0 */
    .gradio-container h1 {
        margin: 6px 0 2px 0 !important;
    }
    
    /* REDUCED BY 2px TOTAL: 2px 0 8px 0 -> 1px 0 7px 0 -> 0px 0 6px 0 */
    .gradio-container p {
        margin: 0px 0 6px 0 !important;
    }
    
    /* Reduce spacing for info text */
    /* REDUCED BY 2px TOTAL: margin-top 2px -> 1px -> 0px, margin-bottom 4px -> 3px -> 2px */
    .gradio-container [class*="info"],
    .gradio-container small {
        margin-top: 0px !important;
        margin-bottom: 2px !important;
    }
    
    /* Compact centered layout for input column */
    .input-column-container {
        max-width: 600px !important;
    }
    
    /* Center the main row when output is hidden */
    .main-row-centered {
        display: flex !important;
        justify-content: center !important;
    }
    
    /* When centered, the input column should be centered */
    .main-row-centered .input-column-container {
        margin: 0 auto !important;
    }
    
    /* When not centered (output visible), input column stays on left with max-width */
    .gradio-row:not(.main-row-centered) .input-column-container {
        margin: 0 !important;
    }
    
    /* Output column - proportional and centered when visible */
    .output-column-container {
        max-width: 600px !important;
    }
    
    /* When output is visible, center both columns proportionally */
    .gradio-row:not(.main-row-centered) {
        display: flex !important;
        justify-content: center !important;
        gap: 20px !important;
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
    
    /* Make accordion dropdown arrows more visible */
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
    
    .gradio-container .accordion-header button svg,
    .gradio-container .accordion-title button svg {
        color: #1f2937 !important;
        stroke: #1f2937 !important;
        fill: #1f2937 !important;
        opacity: 1 !important;
        stroke-width: 2.5 !important;
    }
    
    .gradio-container [class*="accordion"] button {
        opacity: 1 !important;
    }
    
    .gradio-container [class*="accordion"]:hover svg,
    .gradio-container [class*="accordion"]:hover path {
        opacity: 1 !important;
        stroke: #111827 !important;
        color: #111827 !important;
    }
    """
    
    with gr.Blocks(title="Property List Mate", theme=gr.themes.Soft(), css=custom_css) as demo:
        gr.Markdown("<h1 style='text-align: center;'>🏠 Property List Mate</h1>")
        gr.Markdown("<p style='text-align: center;'>Generate professional property listings with AI assistance</p>")
        gr.Markdown("---")
        
        # Main container row
        with gr.Row(elem_classes=["main-row-centered"]) as main_row:
            # Input column
            with gr.Column(scale=1, min_width=400, elem_classes=["input-column-container"]) as input_column:
                
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
                
                property_type_input = gr.Dropdown(
                    label="Property Type *",
                    choices=["Apartment", "House", "Condo", "Townhouse", "Studio", "Loft"],
                    value=None,
                    info="Select the type of property"
                )
                
                with gr.Row():
                    bedrooms_input = gr.Number(
                        label="Bedrooms *",
                        minimum=0,
                        precision=0,
                        value=None
                    )
                    bathrooms_input = gr.Number(
                        label="Bathrooms *",
                        minimum=0,
                        precision=1,
                        value=None
                    )
                
                sqft_input = gr.Number(
                    label="Square Footage *",
                    minimum=0,
                    precision=0,
                    value=None,
                    info="Total living area in square feet"
                )
                
                notes_input = gr.Textbox(
                    label="Property Notes/Description",
                    placeholder="Beautiful apartment with modern kitchen, hardwood floors, and great natural light. Close to subway and Central Park. Parking available, built in 2015.",
                    lines=5,
                    info="Add any special features, amenities, condition, year built, parking, or other details"
                )
                
                # Button row
                with gr.Row(elem_classes=["button-row"]):
                    submit_btn = gr.Button("Generate Listing", variant="primary", size="lg", scale=2, interactive=False)
                    clear_btn = gr.Button("Clear", variant="secondary", size="lg", scale=1)
            
            # Output column - initially hidden
            with gr.Column(scale=1, visible=False, elem_classes=["output-column-container"]) as output_column:
                progress_indicator = gr.Markdown(
                    value="",
                    visible=False,
                    elem_classes=["progress-indicator"],
                    elem_id="progress-indicator"
                )
                
                output_display = gr.Markdown(
                    value="",
                    label="Generated Listing",
                    elem_classes=["output-display"]
                )
        
        # Function to validate required fields
        def validate_required_fields(address: str, listing_type: str, property_type: str, 
                                     bedrooms, bathrooms, sqft):
            """Check if all required fields are filled"""
            has_address = address and str(address).strip() != ""
            has_listing_type = listing_type and str(listing_type).strip() != ""
            has_property_type = property_type and str(property_type).strip() != ""
            
            # Check numeric fields are provided and valid
            has_bedrooms = bedrooms is not None and bedrooms >= 0
            has_bathrooms = bathrooms is not None and bathrooms >= 0
            has_sqft = sqft is not None and sqft > 0
            
            all_fields_filled = (has_address and has_listing_type and has_property_type and 
                                has_bedrooms and has_bathrooms and has_sqft)
            
            return gr.update(interactive=all_fields_filled)
        
        # Validate on field changes
        for field in [address_input, listing_type_input, property_type_input, 
                     bedrooms_input, bathrooms_input, sqft_input]:
            field.change(
                fn=validate_required_fields,
                inputs=[address_input, listing_type_input, property_type_input, 
                       bedrooms_input, bathrooms_input, sqft_input],
                outputs=[submit_btn]
            )
        
        # Function to show progress indicator
        def show_progress_indicator():
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
                "",  # Clear output
                gr.update(interactive=False),  # Disable button
                gr.update(visible=True),  # Show output column
                gr.update(visible=True, value=progress_html),  # Show spinner
                gr.update(elem_classes=[]),  # Remove centered class
            )
        
        # Function to disable all inputs
        def disable_all_inputs():
            return tuple([gr.update(interactive=False)] * 7)
        
        # Function to enable all inputs
        def enable_all_inputs():
            return tuple([gr.update(interactive=True)] * 7)
        
        # Function to hide progress
        def hide_progress_indicator():
            return gr.update(visible=False, value="")
        
        # Function to clear all fields
        def clear_all_fields():
            return (
                "",  # address
                "sale",  # listing_type
                None,  # property_type
                None,  # bedrooms
                None,  # bathrooms
                None,  # sqft
                "",  # notes
                "",  # output_display
                gr.update(visible=False),  # output_column
                gr.update(visible=False, value=""),  # progress_indicator
                gr.update(interactive=False),  # submit_btn
                gr.update(elem_classes=["main-row-centered"]),  # main_row
            )
        
        # Clear button
        clear_btn.click(
            fn=clear_all_fields,
            inputs=[],
            outputs=[
                address_input, listing_type_input, property_type_input,
                bedrooms_input, bathrooms_input, sqft_input, notes_input,
                output_display, output_column, progress_indicator, submit_btn, main_row
            ],
        )
        
        # Submit button
        submit_btn.click(
            fn=show_progress_indicator,
            inputs=[],
            outputs=[
                output_display, submit_btn, output_column, progress_indicator, main_row
            ],
        ).then(
            fn=disable_all_inputs,
            inputs=[],
            outputs=[
                address_input, listing_type_input, property_type_input,
                bedrooms_input, bathrooms_input, sqft_input, notes_input
            ],
        ).then(
            fn=create_listing_ui,
            inputs=[
                address_input, listing_type_input, property_type_input,
                bedrooms_input, bathrooms_input, sqft_input, notes_input
            ],
            outputs=[
                output_display, output_column, submit_btn
            ],
            show_progress="full",
        ).then(
            fn=hide_progress_indicator,
            inputs=[],
            outputs=[progress_indicator],
        ).then(
            fn=enable_all_inputs,
            inputs=[],
            outputs=[
                address_input, listing_type_input, property_type_input,
                bedrooms_input, bathrooms_input, sqft_input, notes_input
            ],
        )
    
    return demo


def main():
    """Launch Gradio interface"""
    import os
    demo = create_gradio_interface()
    port = int(os.getenv("GRADIO_SERVER_PORT", 7860))
    print(f"Starting Gradio server on port {port}...")
    demo.launch(share=False, server_name="0.0.0.0", server_port=port)


if __name__ == "__main__":
    main()