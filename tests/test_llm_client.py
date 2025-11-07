"""
Unit tests for LLM client utilities.

Tests cover:
- JSON parsing with various formats
- Error handling
- Edge cases
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add src to path so we can import
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.llm_client import parse_json_response, initialize_llm, call_llm_with_prompt


# ============================================================================
# JSON Parsing Tests
# ============================================================================

class TestJSONParsing:
    """Test JSON response parsing"""
    
    def test_parse_plain_json(self):
        """Test parsing plain JSON response"""
        response = '{"title": "Test Title", "description": "Test Description", "price_block": "$500,000"}'
        parsed = parse_json_response(response)
        
        assert parsed["title"] == "Test Title"
        assert parsed["description"] == "Test Description"
        assert parsed["price_block"] == "$500,000"
    
    def test_parse_json_with_markdown_code_block(self):
        """Test parsing JSON wrapped in markdown code block"""
        response = """```json
{
  "title": "Test Title",
  "description": "Test Description",
  "price_block": "$500,000"
}
```"""
        parsed = parse_json_response(response)
        
        assert parsed["title"] == "Test Title"
        assert parsed["description"] == "Test Description"
        assert parsed["price_block"] == "$500,000"
    
    def test_parse_json_with_extra_text(self):
        """Test parsing JSON with extra text before/after"""
        response = """Here is the JSON:
{
  "title": "Test Title",
  "description": "Test Description",
  "price_block": "$500,000"
}
That's the response."""
        parsed = parse_json_response(response)
        
        assert parsed["title"] == "Test Title"
        assert parsed["description"] == "Test Description"
        assert parsed["price_block"] == "$500,000"
    
    def test_parse_json_missing_keys(self):
        """Test parsing JSON with missing required keys"""
        response = '{"title": "Test Title", "description": "Test Description"}'
        
        with pytest.raises(ValueError, match="Missing required keys"):
            parse_json_response(response)
    
    def test_parse_json_empty_values(self):
        """Test parsing JSON with empty string values"""
        response = '{"title": "", "description": "Test", "price_block": "$500"}'
        
        with pytest.raises(ValueError, match="Invalid value"):
            parse_json_response(response)
    
    def test_parse_json_invalid_json(self):
        """Test parsing invalid JSON"""
        response = "This is not JSON at all"
        
        with pytest.raises(ValueError, match="Failed to parse JSON"):
            parse_json_response(response)
    
    def test_parse_json_empty_response(self):
        """Test parsing empty response"""
        with pytest.raises(ValueError, match="Empty response"):
            parse_json_response("")
    
    def test_parse_json_with_whitespace(self):
        """Test parsing JSON with extra whitespace"""
        response = """   
        {
          "title": "Test Title",
          "description": "Test Description",
          "price_block": "$500,000"
        }
        """
        parsed = parse_json_response(response)
        
        assert parsed["title"] == "Test Title"
        assert parsed["description"] == "Test Description"
        assert parsed["price_block"] == "$500,000"


# ============================================================================
# LLM Client Tests
# ============================================================================

class TestLLMClient:
    """Test LLM client functions"""
    
    @pytest.mark.skip(reason="Requires actual LLM API key - test manually")
    def test_initialize_llm(self):
        """Test LLM initialization (skipped - requires API key)"""
        # This test would require actual API key
        # llm = initialize_llm("gpt-4o-mini", "openai")
        # assert llm is not None
        pass
    
    def test_call_llm_with_prompt_mock(self):
        """Test LLM call with mocked LLM"""
        # Mock LLM
        mock_llm = Mock()
        mock_output_parser = Mock()
        mock_output_parser.invoke = Mock(return_value='{"title": "Test", "description": "Test", "price_block": "$500"}')
        
        # Mock the chain
        mock_chain = Mock()
        mock_chain.invoke = Mock(return_value='{"title": "Test", "description": "Test", "price_block": "$500"}')
        
        # This test would require more complex mocking of LangChain internals
        # For now, we'll test the actual integration in integration tests
        pass

