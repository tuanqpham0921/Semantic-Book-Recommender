# tests/integration/test_filter_query_integration.py
import pytest
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.filter_query import (
    extract_tone, extract_children, extract_query_filters
)

@pytest.mark.integration
class TestFilterQueryIntegration:
    """Integration tests with real OpenAI API calls - these cost money!"""
    
    @pytest.mark.skip(reason="Expensive - only run when needed")
    def test_extract_children_real_api_obvious_case(self):
        """Test children extraction with obvious case"""
        result = extract_children("children's books")
        
        # This should be very reliable
        assert result is True

    @pytest.mark.skip(reason="Expensive - only run when needed")
    def test_extract_children_real_api_adult_case(self):
        """Test children extraction returns false for adult content"""
        result = extract_children("adult horror novels")
        
        # This should reliably return False
        assert result is False

    @pytest.mark.skip(reason="Expensive - only run when needed")
    def test_full_pipeline_real_api(self):
        """End-to-end test with real API"""
        query = "fiction books for children by J.K. Rowling"
        result = extract_query_filters(query)
        
        # Test structure, not exact content
        assert "content" in result
        assert "filters" in result
        assert isinstance(result["content"], str)
        
        if result["filters"]:
            # Should detect children=True and genre=fiction reliably
            assert result["filters"].get("children") is True
