"""
Text Processing Utilities for Property Listing System - Iteration 1

This module provides text normalization and cleaning functions for:
- Address normalization
- Notes normalization
- Text cleaning (whitespace, line breaks, etc.)
"""

import re
from typing import Optional


# ============================================================================
# Text Normalization Functions
# ============================================================================

def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text.
    
    - Trims leading and trailing whitespace
    - Collapses multiple spaces into single space
    - Normalizes tabs and other whitespace characters
    
    Args:
        text: Text to normalize
        
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    # Replace all whitespace characters (spaces, tabs, newlines) with single space
    normalized = re.sub(r'\s+', ' ', text)
    
    # Trim leading and trailing whitespace
    normalized = normalized.strip()
    
    return normalized


def normalize_line_breaks(text: str) -> str:
    """
    Normalize line breaks in text.
    
    - Converts various line break formats (\\r\\n, \\r, \\n) to single space
    - Useful for converting multiline text to single line
    
    Args:
        text: Text to normalize
        
    Returns:
        Text with normalized line breaks
    """
    if not text:
        return ""
    
    # Replace all line break variations with single space
    normalized = re.sub(r'[\r\n]+', ' ', text)
    
    return normalized


def normalize_address(address: str) -> str:
    """
    Normalize property address.
    
    Performs comprehensive normalization:
    - Trims whitespace
    - Normalizes multiple spaces
    - Normalizes line breaks
    - Preserves address structure
    
    Args:
        address: Address to normalize
        
    Returns:
        Normalized address
    """
    if not address:
        return ""
    
    # Normalize line breaks first
    normalized = normalize_line_breaks(address)
    
    # Normalize whitespace
    normalized = normalize_whitespace(normalized)
    
    # Address-specific: ensure comma spacing is consistent
    # "123 Main St,New York" -> "123 Main St, New York"
    # But don't break numbers like "$500,000" -> use negative lookahead/lookbehind
    # Match comma followed by optional whitespace, but not if it's part of a number
    normalized = re.sub(r',(\s*)', r', \1', normalized)  # Add space after comma
    normalized = re.sub(r',\s+', ', ', normalized)  # Normalize multiple spaces after comma
    
    # Address-specific: ensure period spacing (for abbreviations like "St.")
    # "123 Main St.New York" -> "123 Main St. New York"
    # But don't break decimals like "123.45" -> use word boundary
    normalized = re.sub(r'\.(\s*)', r'. \1', normalized)  # Add space after period
    normalized = re.sub(r'\.\s+', '. ', normalized)  # Normalize multiple spaces after period
    normalized = re.sub(r'\.\s*$', '.', normalized)  # Don't add space at end
    
    # Fix: Remove space that might have been added inside numbers
    # "$500, 000" -> "$500,000" (comma in number should not have space)
    normalized = re.sub(r'(\d+),\s+(\d+)', r'\1,\2', normalized)
    
    # Final trim
    normalized = normalized.strip()
    
    return normalized


def normalize_notes(notes: str) -> str:
    """
    Normalize property notes/description.
    
    Performs comprehensive normalization:
    - Trims whitespace
    - Normalizes multiple spaces
    - Normalizes line breaks
    - Preserves readability
    
    Args:
        notes: Notes to normalize
        
    Returns:
        Normalized notes
    """
    if not notes:
        return ""
    
    # Normalize line breaks first
    normalized = normalize_line_breaks(notes)
    
    # Normalize whitespace
    normalized = normalize_whitespace(normalized)
    
    # Notes-specific: ensure comma spacing is consistent
    # "2BR/1BA,1000 sqft" -> "2BR/1BA, 1000 sqft"
    # But don't break numbers like "$500,000"
    normalized = re.sub(r',(\s*)', r', \1', normalized)  # Add space after comma
    normalized = re.sub(r',\s+', ', ', normalized)  # Normalize multiple spaces after comma
    
    # Fix: Remove space that might have been added inside numbers
    # "$500, 000" -> "$500,000" (comma in number should not have space)
    normalized = re.sub(r'(\d+),\s+(\d+)', r'\1,\2', normalized)
    
    # Notes-specific: ensure slash spacing (for "2BR/1BA" format)
    # "2BR/1BA" should stay as is, but "2BR / 1BA" should become "2BR/1BA"
    normalized = re.sub(r'\s*/\s*', '/', normalized)
    
    # Final trim
    normalized = normalized.strip()
    
    return normalized


def clean_text(text: str) -> str:
    """
    Basic text cleaning (general purpose).
    
    Performs basic cleaning operations:
    - Trims whitespace
    - Normalizes whitespace
    - Removes control characters (except common ones)
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove control characters (except newline, tab, carriage return)
    # Keep common whitespace characters
    cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # Normalize whitespace
    cleaned = normalize_whitespace(cleaned)
    
    return cleaned

