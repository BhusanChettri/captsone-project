"""
Comprehensive unit tests for guardrail utilities.

Tests cover:
- Text length validation
- Injection attack detection
- Inappropriate content detection
- Property-related validation
- Comprehensive input guardrail checks
- Edge cases
"""

import pytest
import sys
from pathlib import Path

# Add src to path so we can import
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.guardrails import (
    validate_text_length,
    detect_injection_attacks,
    detect_inappropriate_content,
    validate_property_related,
    check_input_guardrails,
    MAX_ADDRESS_LENGTH,
    MAX_NOTES_LENGTH,
)


# ============================================================================
# Text Length Validation Tests
# ============================================================================

class TestTextLengthValidation:
    """Test text length validation"""
    
    def test_valid_address_length(self):
        """Test that valid address length passes"""
        address = "123 Main St, New York, NY 10001"
        error = validate_text_length(address, MAX_ADDRESS_LENGTH, "Address")
        assert error is None
    
    def test_valid_notes_length(self):
        """Test that valid notes length passes"""
        notes = "2BR/1BA, 1000 sqft, pet-friendly"
        error = validate_text_length(notes, MAX_NOTES_LENGTH, "Notes")
        assert error is None
    
    def test_address_exceeds_max_length(self):
        """Test that address exceeding max length fails"""
        long_address = "A" * (MAX_ADDRESS_LENGTH + 1)
        error = validate_text_length(long_address, MAX_ADDRESS_LENGTH, "Address")
        assert error is not None
        assert "exceeds maximum length" in error
        assert "Address" in error
    
    def test_notes_exceeds_max_length(self):
        """Test that notes exceeding max length fails"""
        long_notes = "A" * (MAX_NOTES_LENGTH + 1)
        error = validate_text_length(long_notes, MAX_NOTES_LENGTH, "Notes")
        assert error is not None
        assert "exceeds maximum length" in error
        assert "Notes" in error
    
    def test_empty_text_passes(self):
        """Test that empty text passes (handled by required field validation)"""
        error = validate_text_length("", MAX_ADDRESS_LENGTH, "Address")
        assert error is None
    
    def test_exact_max_length_passes(self):
        """Test that text at exact max length passes"""
        address = "A" * MAX_ADDRESS_LENGTH
        error = validate_text_length(address, MAX_ADDRESS_LENGTH, "Address")
        assert error is None


# ============================================================================
# Injection Attack Detection Tests
# ============================================================================

class TestInjectionAttackDetection:
    """Test injection attack detection"""
    
    def test_valid_input_passes(self):
        """Test that valid input passes"""
        text = "123 Main St, New York, NY 10001"
        error = detect_injection_attacks(text)
        assert error is None
    
    def test_sql_injection_union_select(self):
        """Test SQL injection with UNION SELECT"""
        text = "123 Main St' UNION SELECT * FROM users--"
        error = detect_injection_attacks(text)
        assert error is not None
        assert "injection attack" in error.lower()
    
    def test_sql_injection_drop_table(self):
        """Test SQL injection with DROP TABLE"""
        text = "123 Main St; DROP TABLE listings;--"
        error = detect_injection_attacks(text)
        assert error is not None
    
    def test_sql_injection_or_1_equals_1(self):
        """Test SQL injection with OR 1=1"""
        text = "123 Main St' OR 1=1--"
        error = detect_injection_attacks(text)
        assert error is not None
    
    def test_script_injection_script_tag(self):
        """Test script injection with <script> tag"""
        text = "123 Main St<script>alert('xss')</script>"
        error = detect_injection_attacks(text)
        assert error is not None
    
    def test_script_injection_javascript(self):
        """Test script injection with javascript:"""
        text = "123 Main St javascript:alert('xss')"
        error = detect_injection_attacks(text)
        assert error is not None
    
    def test_command_injection_pipe(self):
        """Test command injection with pipe"""
        text = "123 Main St | cat /etc/passwd"
        error = detect_injection_attacks(text)
        assert error is not None
    
    def test_command_injection_ampersand(self):
        """Test command injection with &&"""
        text = "123 Main St && rm -rf /"
        error = detect_injection_attacks(text)
        assert error is not None
    
    def test_case_insensitive_detection(self):
        """Test that injection detection is case-insensitive"""
        text = "123 Main St UNION SELECT * FROM users"
        error = detect_injection_attacks(text)
        assert error is not None
    
    def test_empty_text_passes(self):
        """Test that empty text passes"""
        error = detect_injection_attacks("")
        assert error is None


# ============================================================================
# Inappropriate Content Detection Tests
# ============================================================================

class TestInappropriateContentDetection:
    """Test inappropriate content detection"""
    
    def test_valid_input_passes(self):
        """Test that valid input passes"""
        text = "Beautiful 3BR/2BA home with updated kitchen"
        error = detect_inappropriate_content(text)
        assert error is None
    
    def test_explicit_content_detected(self):
        """Test that explicit content is detected"""
        text = "123 Main St, explicit content here"
        error = detect_inappropriate_content(text)
        assert error is not None
        assert "inappropriate content" in error.lower()
    
    def test_hate_speech_detected(self):
        """Test that hate speech is detected"""
        text = "123 Main St, hate speech here"
        error = detect_inappropriate_content(text)
        assert error is not None
    
    def test_violent_content_detected(self):
        """Test that violent content is detected"""
        text = "123 Main St, violence and threats"
        error = detect_inappropriate_content(text)
        assert error is not None
    
    def test_scam_content_detected(self):
        """Test that scam content is detected"""
        text = "123 Main St, scam and fraud"
        error = detect_inappropriate_content(text)
        assert error is not None
    
    def test_case_insensitive_detection(self):
        """Test that inappropriate content detection is case-insensitive"""
        text = "123 Main St, EXPLICIT content"
        error = detect_inappropriate_content(text)
        assert error is not None
    
    def test_empty_text_passes(self):
        """Test that empty text passes"""
        error = detect_inappropriate_content("")
        assert error is None


# ============================================================================
# Property-Related Validation Tests
# ============================================================================

class TestPropertyRelatedValidation:
    """Test property-related validation"""
    
    def test_valid_property_input_passes(self):
        """Test that valid property input passes"""
        text = "123 Main St, 3BR/2BA, $500,000"
        error = validate_property_related(text)
        assert error is None
    
    def test_property_keywords_in_address(self):
        """Test that property keywords in address pass"""
        text = "123 Main Street, apartment for rent"
        error = validate_property_related(text)
        assert error is None
    
    def test_property_keywords_in_description(self):
        """Test that property keywords in description pass"""
        text = "Beautiful home with 2 bedrooms and 1 bathroom"
        error = validate_property_related(text)
        assert error is None
    
    def test_non_property_input_fails(self):
        """Test that non-property input fails"""
        text = "This is a random text about cooking recipes"
        error = validate_property_related(text)
        assert error is not None
        assert "property-related" in error.lower()
    
    def test_empty_text_fails(self):
        """Test that empty text fails property validation"""
        error = validate_property_related("")
        assert error is not None
    
    def test_minimum_keywords_required(self):
        """Test that minimum keywords are required"""
        text = "This is completely unrelated content about cooking recipes and food preparation"
        error = validate_property_related(text, min_keywords=1)
        assert error is not None


# ============================================================================
# Comprehensive Input Guardrail Tests
# ============================================================================

class TestComprehensiveInputGuardrails:
    """Test comprehensive input guardrail checks"""
    
    def test_valid_input_passes_all_checks(self):
        """Test that valid property input passes all checks"""
        errors = check_input_guardrails(
            address="123 Main St, New York, NY 10001",
            notes="2BR/1BA, 1000 sqft, pet-friendly apartment for rent"
        )
        assert errors == []
    
    def test_long_address_fails(self):
        """Test that long address fails"""
        long_address = "A" * (MAX_ADDRESS_LENGTH + 1)
        errors = check_input_guardrails(
            address=long_address,
            notes="2BR/1BA apartment"
        )
        assert len(errors) > 0
        assert any("Address" in error and "exceeds" in error for error in errors)
    
    def test_long_notes_fails(self):
        """Test that long notes fails"""
        long_notes = "A" * (MAX_NOTES_LENGTH + 1)
        errors = check_input_guardrails(
            address="123 Main St",
            notes=long_notes
        )
        assert len(errors) > 0
        assert any("Notes" in error and "exceeds" in error for error in errors)
    
    def test_injection_in_address_fails(self):
        """Test that injection attack in address fails"""
        errors = check_input_guardrails(
            address="123 Main St' UNION SELECT * FROM users--",
            notes="2BR/1BA apartment"
        )
        assert len(errors) > 0
        assert any("injection attack" in error.lower() for error in errors)
    
    def test_inappropriate_content_fails(self):
        """Test that inappropriate content fails"""
        errors = check_input_guardrails(
            address="123 Main St",
            notes="explicit content here"
        )
        assert len(errors) > 0
        assert any("inappropriate content" in error.lower() for error in errors)
    
    def test_non_property_input_fails(self):
        """Test that non-property input fails"""
        errors = check_input_guardrails(
            address="123 Main St",
            notes="This is completely unrelated content about cooking recipes and food preparation techniques",
            strict_property_validation=True
        )
        assert len(errors) > 0
        assert any("property-related" in error.lower() for error in errors)
    
    def test_multiple_errors_collected(self):
        """Test that multiple errors are collected"""
        errors = check_input_guardrails(
            address="A" * (MAX_ADDRESS_LENGTH + 1),
            notes="A" * (MAX_NOTES_LENGTH + 1)
        )
        assert len(errors) >= 2
    
    def test_strict_validation_can_be_disabled(self):
        """Test that strict property validation can be disabled"""
        errors = check_input_guardrails(
            address="123 Main St",
            notes="Random text without property keywords",
            strict_property_validation=False
        )
        # Should not fail on property validation
        assert not any("property-related" in error.lower() for error in errors)


# ============================================================================
# Edge Cases
# ============================================================================

class TestGuardrailEdgeCases:
    """Test edge cases for guardrails"""
    
    def test_very_long_valid_text(self):
        """Test that text at exact max length passes"""
        prefix_address = "123 Main St, New York, NY 10001"
        prefix_notes = "2BR/1BA apartment for rent"
        address = prefix_address + "A" * (MAX_ADDRESS_LENGTH - len(prefix_address))
        notes = prefix_notes + "B" * (MAX_NOTES_LENGTH - len(prefix_notes))
        errors = check_input_guardrails(address=address, notes=notes)
        assert errors == []
    
    def test_special_characters_in_valid_input(self):
        """Test that special characters in valid input pass"""
        address = "123 Main St. #4B, New York, NY 10001"
        notes = "2BR/1BA, $500,000, pet-friendly!"
        errors = check_input_guardrails(address=address, notes=notes)
        assert errors == []
    
    def test_multiline_text(self):
        """Test that multiline text is handled"""
        notes = "2BR/1BA\n1000 sqft\nPet-friendly\nParking included"
        errors = check_input_guardrails(
            address="123 Main St",
            notes=notes
        )
        assert errors == []
    
    def test_unicode_characters(self):
        """Test that unicode characters are handled"""
        address = "123 Main St, São Paulo, Brazil"
        notes = "2BR/1BA, beautiful home"
        errors = check_input_guardrails(address=address, notes=notes)
        assert errors == []

