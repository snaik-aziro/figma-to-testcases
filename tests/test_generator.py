"""Tests for the test generator service."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from app.services.test_generator import TestGenerator
from app.schemas import ScreenData, ComponentData
from app.models.database import TestCaseType, TestCasePriority


class TestTestGenerator:
    """Test cases for TestGenerator."""

    def setup_method(self):
        """Setup test fixtures."""
        # Mock the Gemini client
        with patch('app.services.test_generator.genai') as mock_genai:
            mock_client = MagicMock()
            mock_genai.Client.return_value = mock_client
            self.generator = TestGenerator(api_key="test_api_key")
        
        # Sample screen data
        self.sample_screen = ScreenData(
            node_id="123",
            name="Login Screen",
            screen_type="authentication",
            components=[
                ComponentData(
                    node_id="c1",
                    name="Email Input",
                    component_type="input",
                    properties={"text": "Email"},
                ),
                ComponentData(
                    node_id="c2",
                    name="Password Input",
                    component_type="input",
                    properties={"text": "Password"},
                ),
                ComponentData(
                    node_id="c3",
                    name="Login Button",
                    component_type="button",
                    properties={"text": "Sign In"},
                ),
            ],
            metadata={"width": 375, "height": 812},
        )

    def test_build_system_prompt_functional(self):
        """Test system prompt for functional tests."""
        prompt = self.generator._build_system_prompt(TestCaseType.FUNCTIONAL)
        
        assert "QA engineer" in prompt
        assert "functional" in prompt.lower()
        assert "user interactions" in prompt.lower()

    def test_build_system_prompt_accessibility(self):
        """Test system prompt for accessibility tests."""
        prompt = self.generator._build_system_prompt(TestCaseType.ACCESSIBILITY)
        
        assert "accessibility" in prompt.lower()
        assert "WCAG" in prompt

    def test_build_context(self):
        """Test context building from screen data."""
        context = self.generator._build_context(self.sample_screen)
        
        assert "Login Screen" in context
        assert "authentication" in context
        assert "Email Input" in context
        assert "Login Button" in context

    def test_build_context_with_requirements(self):
        """Test context building with requirements."""
        requirements = [
            {
                "requirement_id": "REQ-001",
                "title": "User can login",
                "acceptance_criteria": ["Valid credentials accepted"],
            }
        ]
        
        context = self.generator._build_context(self.sample_screen, requirements)
        
        assert "REQ-001" in context
        assert "User can login" in context

    def test_validate_test_case(self):
        """Test test case validation."""
        raw_test_case = {
            "title": "Test Login",
            "description": "Verify login works",
            "test_type": "functional",
            "priority": "high",
            "preconditions": ["User on login page"],
            "test_steps": [
                {
                    "step_number": 1,
                    "action": "Enter email",
                    "expected_result": "Email accepted",
                }
            ],
            "expected_results": ["Login successful"],
            "tags": ["login"],
            "confidence_score": 0.9,
        }
        
        validated = self.generator.validate_test_case(raw_test_case)
        
        assert validated["title"] == "Test Login"
        assert validated["priority"] == "high"
        assert len(validated["test_steps"]) == 1
        assert validated["confidence_score"] == 0.9

    def test_validate_test_case_defaults(self):
        """Test test case validation with defaults."""
        raw_test_case = {}
        
        validated = self.generator.validate_test_case(raw_test_case)
        
        assert validated["title"] == "Untitled Test Case"
        assert validated["test_type"] == TestCaseType.FUNCTIONAL.value
        assert validated["priority"] == TestCasePriority.MEDIUM.value
        assert validated["confidence_score"] == 0.7

    def test_validate_confidence_score_bounds(self):
        """Test confidence score is bounded correctly."""
        high_score = {"confidence_score": 1.5}
        low_score = {"confidence_score": -0.5}
        
        validated_high = self.generator.validate_test_case(high_score)
        validated_low = self.generator.validate_test_case(low_score)
        
        assert validated_high["confidence_score"] == 1.0
        assert validated_low["confidence_score"] == 0.0

    def test_deduplicate_tests_empty(self):
        """Test deduplication with empty list."""
        result = self.generator.deduplicate_tests([])
        assert result == []

    def test_deduplicate_tests_no_duplicates(self):
        """Test deduplication with unique tests."""
        tests = [
            {"title": "Login with valid credentials"},
            {"title": "Logout user"},
            {"title": "Reset password"},
        ]
        
        result = self.generator.deduplicate_tests(tests)
        
        assert len(result) == 3

    def test_deduplicate_tests_with_duplicates(self):
        """Test deduplication removes similar tests."""
        tests = [
            {"title": "Verify user can login with valid credentials"},
            {"title": "Verify user can login with valid email and password"},  # Similar
            {"title": "Verify logout functionality"},
        ]
        
        result = self.generator.deduplicate_tests(tests, similarity_threshold=0.6)
        
        # Should remove the highly similar login tests
        assert len(result) < 3
