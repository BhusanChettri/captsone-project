"""
Gradio UI for Property Listing System - Iteration 1

This module provides a Gradio-based web interface for the property listing system.
Users can input property details and get AI-generated listings.
"""

import gradio as gr
from main import process_listing_request


def create_listing_ui(
    address: str,
    listing_type: str,
    price: float,
    notes: str,
    billing_cycle: str,
    lease_term: str,
    security_deposit: float,
    hoa_fees: float,
    property_taxes: float,
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
    
    # Convert empty strings to None for optional fields
    billing_cycle = billing_cycle.strip() if billing_cycle and billing_cycle.strip() else None
    lease_term = lease_term.strip() if lease_term and lease_term.strip() else None
    security_deposit = security_deposit if security_deposit and security_deposit > 0 else None
    hoa_fees = hoa_fees if hoa_fees and hoa_fees > 0 else None
    property_taxes = property_taxes if property_taxes and property_taxes > 0 else None
    
    # Process the request
    progress(0.3, desc="Processing listing request...")
    result = process_listing_request(
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
    with gr.Blocks(title="Property Listing AI System - Iteration 1") as demo:
        gr.Markdown("<h1 style='text-align: center;'>🏠 Property Listing AI System</h1>", elem_classes=["centered-title"])
        gr.Markdown("<p style='text-align: center;'>Generate professional property listings with AI assistance</p>", elem_classes=["centered-subtitle"])
        gr.Markdown("---")
        
        # Main container row - will be updated dynamically
        # Initially shows only input (centered), then splits into two columns after first generation
        with gr.Row() as main_row:
            # Input column - always visible, centered when output is hidden
            with gr.Column(scale=1, min_width=400) as input_column:
                
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
                    info="Price for sale listings"
                )
                
                notes_input = gr.Textbox(
                    label="Property Notes/Description",
                    placeholder="Beautiful 2BR/1BA apartment with modern kitchen, hardwood floors, and great natural light. Close to subway and Central Park.",
                    lines=5
                )
                
                # Rental-specific fields (initially visible if rent is selected)
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
                        label="Security Deposit (USD)",
                        value=0.0,
                        minimum=0,
                        precision=2
                    )
                
                # Sale-specific fields (initially visible if sale is selected)
                sale_accordion = gr.Accordion("Sale-Specific Fields (Optional)", open=False, visible=True)
                with sale_accordion:
                    hoa_fees_input = gr.Number(
                        label="HOA Fees (USD/month)",
                        value=0.0,
                        minimum=0,
                        precision=2
                    )
                    property_taxes_input = gr.Number(
                        label="Property Taxes (USD/year)",
                        value=0.0,
                        minimum=0,
                        precision=2
                    )
                
                submit_btn = gr.Button("Generate Listing", variant="primary", size="lg")
            
            # Output column - initially hidden, shown after first generation
            with gr.Column(scale=1, visible=False) as output_column:
                # Progress indicator - shown in the center of output area during processing
                progress_indicator = gr.Markdown(
                    value="",
                    visible=False,
                    elem_classes=["progress-indicator"]
                )
                
                # Single unified output area - displays listing or errors dynamically
                # This can be extended for chat capabilities in future iterations
                output_display = gr.Markdown(
                    value="",
                    label="Result",
                    elem_classes=["output-display"]
                )
        
        # Function to update field visibility and labels based on listing type
        def update_field_visibility(listing_type: str):
            """Show/hide rental or sale fields and update price label based on listing type selection"""
            if listing_type == "rent":
                return (
                    gr.update(visible=True),  # rental_accordion
                    gr.update(visible=False),  # sale_accordion
                    gr.update(label="Monthly Rent (USD) *", info="Monthly rental price")  # price_input
                )
            else:  # sale
                return (
                    gr.update(visible=False),  # rental_accordion
                    gr.update(visible=True),  # sale_accordion
                    gr.update(label="Asking Price (USD) *", info="Total sale price")  # price_input
                )
        
        # Update field visibility and price label when listing type changes
        listing_type_input.change(
            fn=update_field_visibility,
            inputs=[listing_type_input],
            outputs=[rental_accordion, sale_accordion, price_input]
        )
        
        # Function to show progress indicator and output column
        def show_progress_indicator():
            """Show progress indicator in the center of output area and make output column visible"""
            progress_html = """
            <div style="text-align: center; padding: 80px 20px; margin: 40px 0; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 300px;">
                <div style="display: inline-block; width: 60px; height: 60px; border: 5px solid #e0e0e0; border-top: 5px solid #4CAF50; border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 20px;"></div>
                <h3 style="margin: 0; color: #333; font-size: 18px; font-weight: 600;">Processing your listing...</h3>
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
        
        # Connect submit button
        # When clicked: show progress in output area, clear output, disable button, then generate listing, then hide progress and show results
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
            fn=create_listing_ui,
            inputs=[
                address_input,
                listing_type_input,
                price_input,
                notes_input,
                billing_cycle_input,
                lease_term_input,
                security_deposit_input,
                hoa_fees_input,
                property_taxes_input,
            ],
            outputs=[
                output_display,  # Output text
                output_column,   # Keep output column visible
                submit_btn,      # Re-enable button
            ],
            show_progress="full",  # Show full progress bar with timer
        ).then(
            fn=hide_progress_indicator,
            inputs=[],
            outputs=[progress_indicator],  # Hide progress indicator when output is ready
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

