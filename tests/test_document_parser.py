"""Tests for the document parser service."""

import pytest
from app.services.document_parser import DocumentParser
from app.models.database import TestCasePriority


class TestDocumentParser:
    """Test cases for DocumentParser."""

    def setup_method(self):
        """Setup test fixtures."""
        self.parser = DocumentParser()

    def test_parse_text_basic(self):
        """Test basic text parsing."""
        content = """
        Requirements Document
        
        1. User Login
        The system must allow users to login with email and password.
        Users should be able to reset their password.
        
        2. Dashboard
        Display user statistics on the main dashboard.
        Show recent activity feed.
        """
        
        result = self.parser.parse_text(content)
        
        assert result["file_type"] == "text"
        assert "full_text" in result
        assert len(result["sections"]) > 0

    def test_extract_requirements(self):
        """Test requirement extraction."""
        parsed_data = {
            "full_text": "User login requirement",
            "sections": [
                {
                    "heading": "REQ-001: User Authentication",
                    "content": [
                        "The system must allow users to login.",
                        "Password must be at least 8 characters.",
                    ]
                },
                {
                    "heading": "REQ-002: Dashboard",
                    "content": [
                        "Display user metrics on dashboard.",
                    ]
                }
            ]
        }
        
        requirements = self.parser.extract_requirements(parsed_data)
        
        assert len(requirements) >= 2
        assert requirements[0]["category"] == "authentication"

    def test_detect_priority_critical(self):
        """Test priority detection for critical items."""
        text = "This is a critical requirement that must be implemented"
        priority = self.parser._detect_priority(text)
        assert priority == TestCasePriority.CRITICAL

    def test_detect_priority_high(self):
        """Test priority detection for high priority items."""
        text = "This is an important feature that should be available"
        priority = self.parser._detect_priority(text)
        assert priority == TestCasePriority.HIGH

    def test_categorize_requirement_authentication(self):
        """Test requirement categorization for auth."""
        text = "User should be able to login with credentials"
        category = self.parser._categorize_requirement(text)
        assert category == "authentication"

    def test_categorize_requirement_ui(self):
        """Test requirement categorization for UI."""
        text = "Display the user profile information on screen"
        category = self.parser._categorize_requirement(text)
        assert category == "user_interface"

    def test_extract_acceptance_criteria(self):
        """Test acceptance criteria extraction."""
        text = """
        Given the user is on login page
        When they enter valid credentials
        Then they should be redirected to dashboard
        
        Should display error for invalid password
        Must validate email format
        """
        
        criteria = self.parser._extract_acceptance_criteria(text)
        
        assert len(criteria) > 0
        # Check for BDD-style criteria
        assert any("Given" in c or "When" in c or "Then" in c for c in criteria)
