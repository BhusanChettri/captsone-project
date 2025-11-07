# Iteration 1 - Strategic Implementation Plan

## Overview
Build a lightweight Gradio-based prototype that generates clean, ready-to-publish property listings from minimal structured inputs.

## Core Requirements Summary
- **Input**: Address, listing type (sale/rent), price, notes, optional fields
- **Output**: Polished title, description, and formatted listing with disclaimer
- **Pipeline**: 5 simple steps with validation and guardrails
- **Goal**: Minimal, working foundation for future iterations

---

## Implementation Strategy: Step-by-Step Plan

### **PHASE 1: Foundation & Data Models** 🏗️

#### Step 1.1: Define Data Models
**What**: Create Python dataclasses/models to represent input and output data
**Why**: Type safety, validation, and clear data contracts
**Files**: `src/models/listing_models.py`
**Details**:
- Input model: PropertyListingInput (address, listing_type, price, notes, optional fields)
- Output model: ListingOutput (title, description, price_block)
- Validation: Basic type checking

#### Step 1.2: Create Configuration Structure
**What**: Set up config file for constants (disclaimer text, validation rules, etc.)
**Why**: Centralize configuration, easy to modify
**Files**: `config/config.yaml` or `src/core/config.py`
**Details**:
- Disclaimer text
- Price validation rules
- Text length limits

---

### **PHASE 2: Input Validation & Processing** ✅

#### Step 2.1: Input Validation Functions
**What**: Create validation functions for each input field
**Why**: Ensure data quality before processing
**Files**: `src/utils/validators.py`
**Details**:
- Address validation (non-empty, basic format check)
- Price validation (positive number, valid USD format)
- Listing type validation (sale or rent only)
- Text normalization (trim whitespace, basic cleaning)

#### Step 2.2: Text Normalization
**What**: Clean and normalize user input text
**Why**: Consistent data format for LLM processing
**Files**: `src/utils/text_processor.py`
**Details**:
- Trim whitespace
- Normalize line breaks
- Basic text cleaning

---

### **PHASE 3: Optional Enrichment** 🌍

#### Step 3.1: Geocoding Service (Optional)
**What**: Extract ZIP code and geocode address
**Why**: Add location context for better listings
**Files**: `src/utils/geocoder.py`
**Details**:
- Extract ZIP from address
- Use geocoding API (e.g., geopy or similar)
- Handle errors gracefully (make it truly optional)

#### Step 3.2: Landmark Enrichment (Optional)
**What**: Fetch nearby landmarks for context
**Why**: Add neighborhood context to listings
**Files**: `src/utils/enrichment.py`
**Details**:
- Query nearby landmarks (simple API or mock data for now)
- Return empty if service unavailable (fail gracefully)

---

### **PHASE 4: LLM Integration** 🤖

#### Step 4.1: Prompt Template
**What**: Create the LLM prompt that merges all data
**Why**: Structured prompt ensures consistent output format
**Files**: `src/core/prompts.py`
**Details**:
- Template that includes: address, type, price, notes, optional fields, enrichment data
- Instructions for JSON output format
- Guardrails: no invented pricing, factual only, SEO-friendly

#### Step 4.2: LLM Client Setup
**What**: Set up LLM client (OpenAI, Anthropic, etc.)
**Why**: Interface to generate listing content
**Files**: `src/core/llm_client.py`
**Details**:
- Initialize LLM client
- Function to call LLM with prompt
- Error handling

#### Step 4.3: Content Generation
**What**: Main function that calls LLM and returns JSON
**Why**: Core business logic - generates the listing
**Files**: `src/core/generator.py`
**Details**:
- Combine all inputs + enrichment
- Call LLM with prompt
- Parse JSON response
- Return structured output

---

### **PHASE 5: Output Processing & Formatting** 📝

#### Step 5.1: JSON Validation
**What**: Validate LLM output structure
**Why**: Ensure output matches expected format
**Files**: `src/utils/output_validator.py`
**Details**:
- Check JSON structure (title, description, price_block)
- Validate field types
- Handle malformed JSON gracefully

#### Step 5.2: Content Guardrails
**What**: Apply output guardrails (remove price from prose, etc.)
**Why**: Ensure compliance and quality
**Files**: `src/utils/output_processor.py`
**Details**:
- Remove price mentions from description
- Check for invented pricing
- Apply length limits

#### Step 5.3: Template Composition
**What**: Format final listing with template and disclaimer
**Why**: Consistent, professional output format
**Files**: `src/core/formatter.py`
**Details**:
- Combine title, description, price_block
- Add standard disclaimer
- Format for U.S. real-estate style

---

### **PHASE 6: Gradio UI** 🎨

#### Step 6.1: Basic Gradio Form
**What**: Create Gradio interface with input fields
**Why**: User-facing interface for the system
**Files**: `src/core/gradio_app.py`
**Details**:
- Required fields: address, listing_type (dropdown), price, notes
- Optional fields: conditional based on listing_type
- Basic layout

#### Step 6.2: Input Guardrails in UI
**What**: Add client-side validation in Gradio
**Why**: Better UX, catch errors early
**Files**: `src/core/gradio_app.py` (update)
**Details**:
- Required field validation
- Price format validation
- Real-time feedback

#### Step 6.3: Connect Pipeline to UI
**What**: Wire up all components to Gradio
**Why**: Complete end-to-end flow
**Files**: `src/core/gradio_app.py` (update)
**Details**:
- Process button handler
- Call validation → processing → generation → formatting
- Display output
- Error handling and user feedback

---

### **PHASE 7: Testing & Refinement** 🧪

#### Step 7.1: Unit Tests
**What**: Test individual components
**Why**: Ensure each piece works correctly
**Files**: `tests/test_*.py`
**Details**:
- Test validators
- Test text processors
- Test formatters
- Mock LLM calls

#### Step 7.2: Integration Test
**What**: Test full pipeline end-to-end
**Why**: Ensure components work together
**Files**: `tests/test_integration.py`
**Details**:
- Full flow with mock LLM
- Test error cases
- Test optional enrichment

#### Step 7.3: Manual Testing & Refinement
**What**: Test with real inputs, refine prompts
**Why**: Ensure quality output
**Details**:
- Test various property types
- Refine LLM prompt based on outputs
- Adjust validation rules

---

## Implementation Order (Recommended)

1. **Step 1.1** - Data Models (foundation)
2. **Step 1.2** - Configuration
3. **Step 2.1** - Input Validation
4. **Step 2.2** - Text Normalization
5. **Step 4.1** - Prompt Template
6. **Step 4.2** - LLM Client Setup
7. **Step 4.3** - Content Generation (basic version)
8. **Step 5.1** - JSON Validation
9. **Step 5.3** - Template Composition (basic)
10. **Step 6.1** - Basic Gradio Form
11. **Step 6.3** - Connect Pipeline (end-to-end working version)
12. **Step 5.2** - Content Guardrails (enhancement)
13. **Step 3.1 & 3.2** - Optional Enrichment (enhancement)
14. **Step 6.2** - UI Guardrails (enhancement)
15. **Step 7.x** - Testing throughout

---

## Key Principles

1. **Start Simple**: Get basic flow working first, then enhance
2. **Fail Gracefully**: Optional features should not break core flow
3. **One Step at a Time**: Complete and test each step before moving on
4. **Clear Separation**: Each component has a single responsibility
5. **Testable**: Each component can be tested independently

---

## Success Criteria

- ✅ Takes minimal inputs (address, type, price, notes)
- ✅ Produces clean title and description
- ✅ Includes standard disclaimer
- ✅ Validates inputs and outputs
- ✅ Handles errors gracefully
- ✅ Works end-to-end in Gradio UI

