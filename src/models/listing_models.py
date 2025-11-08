"""
Data models for Property Listing System - Iteration 1

This module defines the data structures for:
- Input: What the user provides (address, price, notes, etc.)
- Output: What the system generates (title, description, price_block)
"""

from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class PropertyListingInput:
    """
    Represents the input data for creating a property listing.
    
    Required fields:
    - address: Property address (e.g., "123 Main St, New York, NY 10001")
    - listing_type: Either "sale" or "rent"
    - notes: Free-text description with key features (beds, baths, sqft, amenities)
    
    Optional fields:
    - price: Asking price (currency depends on region) - can be added later when posting
    - region: Region code (US, CA, UK, AU). Defaults to US if not specified.
    
    Optional fields for rental listings (region-dependent):
    - billing_cycle: How often rent is paid (e.g., "monthly", "weekly")
    - lease_term: Lease duration (e.g., "12 months", "6 months")
    - security_deposit: Security deposit / bond amount (currency depends on region)
    
    Optional fields for sale listings (region-dependent):
    - hoa_fees: HOA fees / Condo fees / Service charge (US/CA/UK)
    - property_taxes: Property taxes (US/CA)
    - council_tax: Council tax (UK)
    - rates: Council rates (Australia)
    - strata_fees: Strata fees / Body corporate (Australia/Canada)
    """
    
    # Required fields (must come before optional fields in dataclass)
    address: str
    listing_type: Literal["sale", "rent"]
    notes: str
    
    # Optional fields (must come after required fields)
    price: Optional[float] = None  # Optional - can be added later when posting
    region: Optional[str] = None
    
    # Optional fields for rentals
    billing_cycle: Optional[str] = None
    lease_term: Optional[str] = None
    security_deposit: Optional[float] = None
    
    # Optional fields for sales (region-dependent)
    hoa_fees: Optional[float] = None
    property_taxes: Optional[float] = None
    council_tax: Optional[float] = None  # UK
    rates: Optional[float] = None  # Australia
    strata_fees: Optional[float] = None  # Australia/Canada
    
    def __post_init__(self):
        """
        Basic validation after initialization.
        This ensures data integrity at the model level.
        """
        # Validate required string fields are not empty
        if not self.address or not self.address.strip():
            raise ValueError("address cannot be empty")
        
        if not self.notes or not self.notes.strip():
            raise ValueError("notes cannot be empty")
        
        # Validate listing_type
        if self.listing_type not in ["sale", "rent"]:
            raise ValueError(f"listing_type must be 'sale' or 'rent', got '{self.listing_type}'")
        
        # Validate price is positive if provided (price is optional)
        if self.price is not None and self.price <= 0:
            raise ValueError(f"price must be positive if provided, got {self.price}")
        
        # Validate optional numeric fields are non-negative if provided
        if self.security_deposit is not None and self.security_deposit < 0:
            raise ValueError(f"security_deposit must be non-negative, got {self.security_deposit}")
        
        if self.hoa_fees is not None and self.hoa_fees < 0:
            raise ValueError(f"hoa_fees must be non-negative, got {self.hoa_fees}")
        
        if self.property_taxes is not None and self.property_taxes < 0:
            raise ValueError(f"property_taxes must be non-negative, got {self.property_taxes}")


@dataclass
class ListingOutput:
    """
    Represents the generated output from the listing system.
    
    Fields:
    - title: Generated listing title (e.g., "Beautiful 3BR/2BA Home in Downtown")
    - description: Generated listing description (professional, SEO-friendly prose)
    - price_block: Formatted price information (e.g., "$500,000" or "$2,500/month")
    
    Note: The description should NOT contain price information - that goes in price_block.
    """
    
    title: str
    description: str
    price_block: str
    
    def __post_init__(self):
        """
        Basic validation to ensure output fields are not empty.
        """
        if not self.title or not self.title.strip():
            raise ValueError("title cannot be empty")
        
        if not self.description or not self.description.strip():
            raise ValueError("description cannot be empty")
        
        if not self.price_block or not self.price_block.strip():
            raise ValueError("price_block cannot be empty")

