"""
Region Configuration for Property Listing System - Iteration 1

This module defines region-specific configurations for property listings,
including which fields are relevant and what labels to use for each region.
"""

from typing import Dict, List, Optional, TypedDict
from enum import Enum


class Region(str, Enum):
    """Supported regions for property listings."""
    US = "US"
    CA = "CA"  # Canada
    UK = "UK"
    AU = "AU"  # Australia
    DEFAULT = "US"  # Default to US if not specified


class FieldType(str, Enum):
    """Types of optional fields."""
    HOA_FEES = "hoa_fees"
    PROPERTY_TAXES = "property_taxes"
    COUNCIL_TAX = "council_tax"  # UK equivalent
    RATES = "rates"  # Australia equivalent
    STRATA_FEES = "strata_fees"  # Australia/Canada equivalent
    SECURITY_DEPOSIT = "security_deposit"
    BILLING_CYCLE = "billing_cycle"
    LEASE_TERM = "lease_term"


class RegionFieldConfig(TypedDict):
    """Configuration for a field in a specific region."""
    label: str
    description: str
    unit: str  # e.g., "USD/month", "GBP/year"
    show_for_sale: bool
    show_for_rent: bool
    required: bool


class RegionConfig(TypedDict):
    """Complete configuration for a region."""
    region_name: str
    currency: str
    currency_symbol: str
    fields: Dict[str, RegionFieldConfig]
    address_format_hint: str


# Region-specific configurations
REGION_CONFIGS: Dict[Region, RegionConfig] = {
    Region.US: {
        "region_name": "United States",
        "currency": "USD",
        "currency_symbol": "$",
        "address_format_hint": "Street, City, State ZIP",
        "fields": {
            FieldType.HOA_FEES: {
                "label": "HOA Fees",
                "description": "Monthly homeowners association fees",
                "unit": "USD/month",
                "show_for_sale": True,
                "show_for_rent": False,
                "required": False,
            },
            FieldType.PROPERTY_TAXES: {
                "label": "Property Taxes",
                "description": "Annual property taxes",
                "unit": "USD/year",
                "show_for_sale": True,
                "show_for_rent": False,
                "required": False,
            },
            FieldType.SECURITY_DEPOSIT: {
                "label": "Security Deposit",
                "description": "Security deposit amount",
                "unit": "USD",
                "show_for_sale": False,
                "show_for_rent": True,
                "required": False,
            },
            FieldType.BILLING_CYCLE: {
                "label": "Billing Cycle",
                "description": "How often rent is paid (e.g., monthly, weekly)",
                "unit": "",
                "show_for_sale": False,
                "show_for_rent": True,
                "required": False,
            },
            FieldType.LEASE_TERM: {
                "label": "Lease Term",
                "description": "Lease duration (e.g., 12 months, 6 months)",
                "unit": "",
                "show_for_sale": False,
                "show_for_rent": True,
                "required": False,
            },
        },
    },
    Region.CA: {
        "region_name": "Canada",
        "currency": "CAD",
        "currency_symbol": "$",
        "address_format_hint": "Street, City, Province Postal Code",
        "fields": {
            FieldType.HOA_FEES: {
                "label": "Condo Fees / Strata Fees",
                "description": "Monthly condominium or strata fees",
                "unit": "CAD/month",
                "show_for_sale": True,
                "show_for_rent": False,
                "required": False,
            },
            FieldType.PROPERTY_TAXES: {
                "label": "Property Taxes",
                "description": "Annual property taxes",
                "unit": "CAD/year",
                "show_for_sale": True,
                "show_for_rent": False,
                "required": False,
            },
            FieldType.SECURITY_DEPOSIT: {
                "label": "Security Deposit",
                "description": "Security deposit amount",
                "unit": "CAD",
                "show_for_sale": False,
                "show_for_rent": True,
                "required": False,
            },
            FieldType.BILLING_CYCLE: {
                "label": "Billing Cycle",
                "description": "How often rent is paid (e.g., monthly, weekly)",
                "unit": "",
                "show_for_sale": False,
                "show_for_rent": True,
                "required": False,
            },
            FieldType.LEASE_TERM: {
                "label": "Lease Term",
                "description": "Lease duration (e.g., 12 months, 6 months)",
                "unit": "",
                "show_for_sale": False,
                "show_for_rent": True,
                "required": False,
            },
        },
    },
    Region.UK: {
        "region_name": "United Kingdom",
        "currency": "GBP",
        "currency_symbol": "£",
        "address_format_hint": "Street, City, Postcode",
        "fields": {
            # UK doesn't typically have HOA fees, but has service charges for flats
            FieldType.HOA_FEES: {
                "label": "Service Charge",
                "description": "Annual service charge (for flats/apartments)",
                "unit": "GBP/year",
                "show_for_sale": True,
                "show_for_rent": False,
                "required": False,
            },
            FieldType.COUNCIL_TAX: {
                "label": "Council Tax",
                "description": "Annual council tax (band A-H)",
                "unit": "GBP/year",
                "show_for_sale": True,
                "show_for_rent": True,  # Renters pay council tax
                "required": False,
            },
            FieldType.SECURITY_DEPOSIT: {
                "label": "Security Deposit",
                "description": "Security deposit amount (typically 5 weeks rent)",
                "unit": "GBP",
                "show_for_sale": False,
                "show_for_rent": True,
                "required": False,
            },
            FieldType.BILLING_CYCLE: {
                "label": "Billing Cycle",
                "description": "How often rent is paid (e.g., monthly, weekly)",
                "unit": "",
                "show_for_sale": False,
                "show_for_rent": True,
                "required": False,
            },
            FieldType.LEASE_TERM: {
                "label": "Lease Term",
                "description": "Lease duration (e.g., 12 months, 6 months)",
                "unit": "",
                "show_for_sale": False,
                "show_for_rent": True,
                "required": False,
            },
        },
    },
    Region.AU: {
        "region_name": "Australia",
        "currency": "AUD",
        "currency_symbol": "$",
        "address_format_hint": "Street, Suburb, State Postcode",
        "fields": {
            FieldType.STRATA_FEES: {
                "label": "Strata Fees / Body Corporate",
                "description": "Quarterly strata or body corporate fees",
                "unit": "AUD/quarter",
                "show_for_sale": True,
                "show_for_rent": False,
                "required": False,
            },
            FieldType.RATES: {
                "label": "Council Rates",
                "description": "Annual council rates",
                "unit": "AUD/year",
                "show_for_sale": True,
                "show_for_rent": False,
                "required": False,
            },
            FieldType.SECURITY_DEPOSIT: {
                "label": "Bond / Security Deposit",
                "description": "Bond or security deposit amount",
                "unit": "AUD",
                "show_for_sale": False,
                "show_for_rent": True,
                "required": False,
            },
            FieldType.BILLING_CYCLE: {
                "label": "Billing Cycle",
                "description": "How often rent is paid (e.g., monthly, weekly, fortnightly)",
                "unit": "",
                "show_for_sale": False,
                "show_for_rent": True,
                "required": False,
            },
            FieldType.LEASE_TERM: {
                "label": "Lease Term",
                "description": "Lease duration (e.g., 12 months, 6 months)",
                "unit": "",
                "show_for_sale": False,
                "show_for_rent": True,
                "required": False,
            },
        },
    },
}


def get_region_config(region: str) -> RegionConfig:
    """
    Get configuration for a specific region.
    
    Args:
        region: Region code (US, CA, UK, AU) or region name
        
    Returns:
        RegionConfig for the specified region, or US config as default
    """
    # Try to match by enum value
    try:
        region_enum = Region(region.upper())
        return REGION_CONFIGS[region_enum]
    except (ValueError, KeyError):
        # Try to match by region name
        for reg, config in REGION_CONFIGS.items():
            if config["region_name"].upper() == region.upper():
                return config
        # Default to US
        return REGION_CONFIGS[Region.US]


def get_field_config(region: str, field_type: str, listing_type: str) -> Optional[RegionFieldConfig]:
    """
    Get field configuration for a specific region and listing type.
    
    Args:
        region: Region code (US, CA, UK, AU)
        field_type: Type of field (hoa_fees, property_taxes, etc.)
        listing_type: "sale" or "rent"
        
    Returns:
        Field configuration if field should be shown, None otherwise
    """
    config = get_region_config(region)
    fields = config["fields"]
    
    if field_type not in fields:
        return None
    
    field_config = fields[field_type]
    
    # Check if field should be shown for this listing type
    if listing_type == "sale" and not field_config["show_for_sale"]:
        return None
    if listing_type == "rent" and not field_config["show_for_rent"]:
        return None
    
    return field_config


def get_fields_for_listing_type(region: str, listing_type: str) -> Dict[str, RegionFieldConfig]:
    """
    Get all fields that should be shown for a region and listing type.
    
    Args:
        region: Region code (US, CA, UK, AU)
        listing_type: "sale" or "rent"
        
    Returns:
        Dictionary of field_type -> field_config for fields that should be shown
    """
    config = get_region_config(region)
    fields = config["fields"]
    
    result = {}
    for field_type, field_config in fields.items():
        if listing_type == "sale" and field_config["show_for_sale"]:
            result[field_type] = field_config
        elif listing_type == "rent" and field_config["show_for_rent"]:
            result[field_type] = field_config
    
    return result


def get_currency_symbol(region: str) -> str:
    """Get currency symbol for a region."""
    config = get_region_config(region)
    return config["currency_symbol"]


def get_currency(region: str) -> str:
    """Get currency code for a region."""
    config = get_region_config(region)
    return config["currency"]


def get_region_name(region: str) -> str:
    """Get full region name."""
    config = get_region_config(region)
    return config["region_name"]


def get_supported_regions() -> List[Dict[str, str]]:
    """
    Get list of supported regions.
    
    Returns:
        List of dictionaries with region code and name
    """
    return [
        {"code": reg.value, "name": config["region_name"]}
        for reg, config in REGION_CONFIGS.items()
    ]

