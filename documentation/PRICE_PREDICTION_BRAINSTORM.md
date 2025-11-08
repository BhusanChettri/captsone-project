# Price Prediction Feature - Brainstorming Document

## Overview

This document explores adding automated price prediction functionality to the Property Listing System. The goal is to predict property prices (sale or rental) using all available context information collected by the enrichment module.

## Available Data for Price Prediction

### Core Property Attributes (Always Available)
- **Address**: Full property address
- **Property Type**: Apartment, House, Condo, Townhouse, Studio, Loft
- **Bedrooms**: Number of bedrooms (integer)
- **Bathrooms**: Number of bathrooms (float, e.g., 1.5)
- **Square Footage**: Total living area (sqft)
- **Listing Type**: "sale" or "rent"
- **Region**: US, CA, UK, AU

### Enrichment Data (From Web Search - Optional)
- **ZIP Code**: Extracted from address
- **Neighborhood**: Neighborhood name/identifier
- **Landmarks**: List of nearby landmarks (top 3-5)
- **Key Amenities**:
  - Schools (list of school names)
  - Supermarkets (list of supermarket names)
  - Parks (list of park names)
  - Transportation (subway lines, bus routes, etc.)
- **Neighborhood Quality**:
  - Crime info (safety statistics)
  - Quality of life indicators
  - Safety information

### Optional Input Data (If Provided)
- **HOA Fees**: Monthly/annual HOA fees (sales)
- **Property Taxes**: Annual property taxes (sales)
- **Security Deposit**: Security deposit amount (rentals)
- **Lease Term**: Lease duration (rentals)

**Note**: Notes field has been removed from the system and is not used in price prediction.

## Approach Options

### Option 1: LLM-Based Price Prediction (Recommended for MVP)

**How it works:**
- Use GPT-4o or GPT-5 to analyze all available property data
- Provide structured context about the property
- Ask LLM to predict price based on comparable properties and market knowledge
- Return price estimate with confidence level and reasoning

**Advantages:**
- ✅ Can leverage LLM's knowledge of real estate markets
- ✅ Can handle missing data gracefully
- ✅ Can provide reasoning/explanation for the prediction
- ✅ Easy to implement (similar to content generation)
- ✅ Can adapt to different regions/markets
- ✅ Can consider qualitative factors (neighborhood quality, amenities)

**Disadvantages:**
- ❌ May not be as accurate as ML models trained on historical data
- ❌ Cost per prediction (LLM API calls)
- ❌ Less deterministic than statistical models
- ❌ May hallucinate or make up comparable properties

**Best for:**
- MVP/initial implementation
- When historical data is not available
- When you need explanations/reasoning
- When you want to leverage qualitative factors

### Option 2: Hybrid Approach (LLM + Structured Data)

**How it works:**
- Use LLM to extract/validate structured features from unstructured data
- Use LLM to find comparable properties or market trends
- Combine LLM insights with rule-based adjustments
- Apply market-specific multipliers based on region

**Advantages:**
- ✅ More accurate than pure LLM
- ✅ Can leverage both structured and unstructured data
- ✅ More explainable

**Disadvantages:**
- ❌ More complex to implement
- ❌ Requires market data/multipliers

### Option 3: Traditional ML Model (Future Enhancement)

**How it works:**
- Train a regression model (XGBoost, Random Forest, Neural Network) on historical property data
- Use all available features as input
- Predict price based on learned patterns

**Advantages:**
- ✅ Most accurate if trained on good data
- ✅ Fast inference (no API calls)
- ✅ Deterministic predictions

**Disadvantages:**
- ❌ Requires large dataset of historical property sales/rentals
- ❌ Needs feature engineering
- ❌ Harder to adapt to new markets
- ❌ Less explainable (unless using SHAP/LIME)

**Best for:**
- Production system with historical data
- When accuracy is critical
- When you have sufficient training data

## Recommended Implementation: LLM-Based Price Prediction

### Workflow Integration

**New Node: `predict_price_node`**

Place in workflow to run **in parallel** with `generate_content_node` after `enrich_data_node`:

```
START → input_guardrail → enrich_data → 
[predict_price || generate_content] (parallel) → 
output_guardrail → format_output → END
```

**Why parallel execution?**
- Price prediction and content generation are **independent** operations
- Both use the same enriched data as input
- Running in parallel reduces total execution time
- Both write to different state fields (no conflicts)
- Price prediction is optional: If it fails, workflow continues

### State Updates

Add to `PropertyListingState`:

```python
# Price Prediction Fields
predicted_price: Optional[float]
"""Predicted price from LLM (in USD)."""
predicted_price_reasoning: Optional[str]
"""LLM's reasoning for the price prediction (1-2 sentences)."""
```

### Prompt Structure

```python
def build_price_prediction_prompt(
    address: str,
    listing_type: str,  # "sale" or "rent"
    property_type: str,
    bedrooms: int,
    bathrooms: float,
    sqft: int,
    zip_code: Optional[str] = None,
    neighborhood: Optional[str] = None,
    landmarks: Optional[List[str]] = None,
    key_amenities: Optional[Dict[str, List[str]]] = None,
    neighborhood_quality: Optional[Dict[str, Optional[str]]] = None,
    region: str = "US"
) -> str:
    """
    Build prompt for price prediction.
    
    Structure:
    1. Task description
    2. Property details (structured)
    3. Location & neighborhood context
    4. Amenities & quality factors
    5. Market context instructions
    6. Output format (JSON with price, confidence, reasoning, range)
    """
```

### Example Prompt Structure

```
You are a real estate price estimation expert. Predict the market price for this property.

=== PROPERTY DETAILS ===
Address: {address}
Property Type: {property_type}
Bedrooms: {bedrooms}
Bathrooms: {bathrooms}
Square Footage: {sqft:,} sqft
Listing Type: {listing_type}  # "sale" or "rent"
Region: {region}

=== LOCATION CONTEXT ===
ZIP Code: {zip_code}
Neighborhood: {neighborhood}
Nearby Landmarks: {landmarks}

=== AMENITIES & QUALITY ===
Schools: {schools}
Parks: {parks}
Transportation: {transportation}
Supermarkets: {supermarkets}
Crime & Safety: {crime_info}
Quality of Life: {quality_of_life}


=== INSTRUCTIONS ===
1. Analyze all provided information
2. Consider comparable properties in the area
3. Factor in:
   - Property size and features
   - Location desirability
   - Neighborhood quality and safety
   - Nearby amenities
   - Market trends for {region}
4. Provide:
   - Predicted price (single number in USD)
   - Brief reasoning (1-2 sentences explaining the prediction)

=== OUTPUT FORMAT ===
Return JSON:
{
  "predicted_price": 500000.0,
  "reasoning": "Based on comparable 3BR/2BA properties in this neighborhood with similar amenities, the estimated market value is $500,000."
}
```

### Implementation Considerations

#### 1. Model Selection
- **For Price Prediction**: Use `gpt-4o` or `gpt-5` (same as content generation)
- **Temperature**: Lower (0.3-0.5) for more consistent, data-driven predictions
- **Reasoning**: Can use chain-of-thought prompting for better accuracy

#### 2. Error Handling
- Price prediction is **optional** - if it fails, workflow continues
- Log errors but don't block listing generation
- Provide fallback: "Price available upon request" or similar

#### 3. Validation
- Validate predicted price is reasonable (not negative, not absurdly high)
- Check price range (min < predicted < max)
- Validate confidence level is one of: high/medium/low

#### 4. Integration with Existing Flow
- If user provided price: Use user's price, but can show predicted price as comparison
- If user didn't provide price: Use predicted price in the listing
- Always show predicted price as "Estimated Market Value" or "Price Estimate"

#### 5. Regional Considerations
- Different markets have different price ranges
- Need to adjust prompts/instructions based on region (US, CA, UK, AU)
- Currency conversion if needed

#### 6. Rental vs Sale
- Different pricing models (monthly rent vs total sale price)
- Different factors matter (rental: monthly cost, sale: investment value)
- Different comparable properties

## Example Use Cases

### Use Case 1: User Provides No Price
```
Input: Property details only, no price
→ System predicts price
→ Generated listing includes: "Estimated Market Value: $500,000"
→ Description mentions: "Priced competitively based on market analysis"
```

### Use Case 2: User Provides Price, System Validates
```
Input: Property details + user price: $450,000
→ System predicts: $500,000 (high confidence)
→ Generated listing includes: "Asking Price: $450,000"
→ Optional: Show predicted range for comparison
```

### Use Case 3: Price Prediction Fails
```
Input: Property details
→ Price prediction fails (API error, insufficient data)
→ Workflow continues
→ Generated listing: "Price available upon request"
```

## Advanced Features (Future)

### 1. Comparable Properties
- LLM could provide list of comparable properties it considered
- Show "Based on similar properties in the area"

### 2. Market Trends
- Include recent market trends in the prediction
- "Market is trending up/down in this area"

### 3. Price History
- If available, show price history for the property
- Show neighborhood price trends

### 4. Confidence Indicators
- Visual indicators (high/medium/low)
- Explain what factors contributed to confidence level

### 5. Multiple Models
- Run multiple LLM calls with different prompts
- Average the results for better accuracy
- Show variance/agreement between models

## Implementation Steps

### Phase 1: Basic LLM Price Prediction (MVP)
1. ✅ Create `predict_price_node` function
2. ✅ Create `build_price_prediction_prompt` function
3. ✅ Add price prediction fields to state
4. ✅ Integrate into workflow (after enrichment, before content generation)
5. ✅ Update content generation to use predicted price if user didn't provide one
6. ✅ Add error handling (optional, non-blocking)

### Phase 2: Enhanced Features
1. Add confidence levels and reasoning
2. Add price range (min-max)
3. Regional market adjustments
4. Rental vs sale specific logic

### Phase 3: Advanced Features
1. Comparable properties analysis
2. Market trends integration
3. Multiple model ensemble
4. Historical data integration (if available)

## Code Structure

### New Files
- `src/utils/price_prediction.py`: Price prediction utilities
  - `build_price_prediction_prompt()`: Prompt builder
  - `parse_price_prediction_response()`: JSON parser
  - `validate_predicted_price()`: Validation logic

### Modified Files
- `src/core/state.py`: Add price prediction fields
- `src/core/nodes.py`: Add `predict_price_node()`
- `src/core/workflow.py`: Add node to workflow graph
- `src/utils/prompts.py`: Optionally reference predicted price in content generation

## Testing Strategy

### Unit Tests
- Test prompt building with various inputs
- Test JSON parsing
- Test validation logic
- Test error handling

### Integration Tests
- Test full workflow with price prediction
- Test with missing enrichment data
- Test with different regions
- Test rental vs sale

### Validation Tests
- Verify predicted prices are reasonable
- Check confidence levels are valid
- Ensure price ranges make sense (min < predicted < max)

## Metrics to Track

1. **Prediction Accuracy** (if you have ground truth):
   - Mean Absolute Error (MAE)
   - Mean Absolute Percentage Error (MAPE)
   - R² score

2. **User Engagement**:
   - How often predicted price is used
   - User feedback on price accuracy

3. **Performance**:
   - Time to predict
   - Cost per prediction (LLM API calls)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM hallucinates prices | High | Validate against reasonable ranges, add confidence levels |
| Prediction is inaccurate | Medium | Make it optional, show as "estimate", add disclaimers |
| API costs | Medium | Cache predictions, use cheaper model for initial estimate |
| Missing data affects accuracy | Low | Handle gracefully, use available data, show lower confidence |
| Regional differences | Medium | Region-specific prompts and adjustments |

## Disclaimers & Legal Considerations

**Important**: Price predictions should always include disclaimers:
- "Estimated market value based on available data"
- "Not a professional appraisal"
- "Actual price may vary"
- "Consult with a real estate professional for accurate pricing"

## Next Steps

1. **Review this document** - Discuss approach and get feedback
2. **Create prototype** - Implement basic `predict_price_node` with simple prompt
3. **Test with sample properties** - Validate predictions make sense
4. **Iterate on prompt** - Refine based on results
5. **Add to workflow** - Integrate into main workflow
6. **Add UI support** - Show predicted price in Gradio interface
7. **Monitor and improve** - Track accuracy and refine

## Questions to Consider

1. **Should price prediction be mandatory or optional?**
   - Recommendation: Optional (workflow continues if it fails)

2. **Should we show predicted price even if user provided price?**
   - Recommendation: Yes, as "Market Estimate" for comparison

3. **What confidence threshold should we use?**
   - Recommendation: Only show if confidence is "medium" or "high"

4. **Should we cache predictions?**
   - Recommendation: Yes, cache by (address, bedrooms, bathrooms, sqft) to reduce API costs

5. **How to handle different regions/currencies?**
   - Recommendation: Convert to USD for internal processing, show in local currency in UI

6. **Should we use a different model for price prediction?**
   - Recommendation: Start with same model (gpt-5), can optimize later

## Conclusion

LLM-based price prediction is a viable approach for MVP, offering:
- ✅ Quick implementation
- ✅ Leverages all available context
- ✅ Provides explanations
- ✅ Handles missing data gracefully

The key is to make it **optional** and **non-blocking**, with proper validation and disclaimers. As the system evolves, we can enhance it with traditional ML models trained on historical data for better accuracy.

