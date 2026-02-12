"""Tests for the Figma client service."""

import pytest
from app.services.figma_client import FigmaClient


class TestFigmaClient:
    """Test cases for FigmaClient."""

    def setup_method(self):
        """Setup test fixtures."""
        self.client = FigmaClient(access_token="test_token")

    def test_extract_file_id_from_url(self):
        """Test extracting file ID from Figma URL."""
        url = "https://www.figma.com/file/ABC123xyz/My-Design-File"
        file_id = self.client.extract_file_id(url)
        assert file_id == "ABC123xyz"

    def test_extract_file_id_from_design_url(self):
        """Test extracting file ID from Figma design URL."""
        url = "https://www.figma.com/design/XYZ789abc/Another-Design"
        file_id = self.client.extract_file_id(url)
        assert file_id == "XYZ789abc"

    def test_extract_file_id_passthrough(self):
        """Test that raw file ID is returned as-is."""
        file_id = "ABC123xyz"
        result = self.client.extract_file_id(file_id)
        assert result == file_id

    def test_map_figma_type_button(self):
        """Test component type mapping for buttons."""
        result = self.client._map_figma_type_to_component_type("INSTANCE", "Login Button")
        assert result == "button"

    def test_map_figma_type_input(self):
        """Test component type mapping for inputs."""
        result = self.client._map_figma_type_to_component_type("FRAME", "Email Input Field")
        assert result == "input"

    def test_map_figma_type_navigation(self):
        """Test component type mapping for navigation."""
        result = self.client._map_figma_type_to_component_type("GROUP", "Header Nav")
        assert result == "navigation"

    def test_map_figma_type_fallback(self):
        """Test component type mapping fallback."""
        result = self.client._map_figma_type_to_component_type("FRAME", "SomeContainer")
        assert result == "container"

    def test_determine_screen_type_login(self):
        """Test screen type determination for login."""
        node = {"name": "Login Screen"}
        screen_type = self.client._determine_screen_type(node)
        assert screen_type == "authentication"

    def test_determine_screen_type_dashboard(self):
        """Test screen type determination for dashboard."""
        node = {"name": "Main Dashboard"}
        screen_type = self.client._determine_screen_type(node)
        assert screen_type == "dashboard"

    def test_determine_screen_type_general(self):
        """Test screen type determination fallback."""
        node = {"name": "Some Random Screen"}
        screen_type = self.client._determine_screen_type(node)
        assert screen_type == "general"

    def test_extract_component_properties_text(self):
        """Test component property extraction for text nodes."""
        node = {
            "type": "TEXT",
            "characters": "Hello World",
            "style": {"fontSize": 16, "fontWeight": 500},
            "visible": True,
        }
        
        props = self.client._extract_component_properties(node)
        
        assert props["text"] == "Hello World"
        assert props["font_size"] == 16
        assert props["visible"] is True

    def test_extract_position(self):
        """Test position extraction."""
        node = {
            "absoluteBoundingBox": {
                "x": 100,
                "y": 200,
                "width": 300,
                "height": 50,
            }
        }
        
        position = self.client._extract_position(node)
        
        assert position["x"] == 100
        assert position["y"] == 200
        assert position["width"] == 300
        assert position["height"] == 50

    def test_is_screen_true(self):
        """Test screen detection for valid screen."""
        node = {
            "type": "FRAME",
            "name": "Home Screen",
            "absoluteBoundingBox": {
                "width": 375,
                "height": 812,
            }
        }
        
        assert self.client._is_screen(node) is True

    def test_is_screen_false_small(self):
        """Test screen detection for small component."""
        node = {
            "type": "FRAME",
            "name": "Small Button",
            "absoluteBoundingBox": {
                "width": 100,
                "height": 40,
            }
        }
        
        assert self.client._is_screen(node) is False
