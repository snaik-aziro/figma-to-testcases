"""Figma API client for extracting design data."""

import re
from typing import Optional, List, Dict, Any
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.schemas import ScreenData, ComponentData

settings = get_settings()


class FigmaClient:
    """Client for interacting with the Figma API."""

    def __init__(self, access_token: Optional[str] = None, enable_filtering: bool = True):
        self.access_token = access_token or settings.figma_access_token
        self.base_url = settings.figma_api_base_url
        self.headers = {"X-Figma-Token": self.access_token}
        self.enable_filtering = enable_filtering and settings.enable_component_filtering
        self.relevance_threshold = settings.component_relevance_threshold

    @staticmethod
    def extract_file_id(file_id_or_url: str) -> str:
        """Extract file ID from Figma URL or return as-is if already an ID."""
        # Pattern to match Figma URLs
        url_pattern = r"figma\.com/(?:file|design)/([a-zA-Z0-9]+)"
        match = re.search(url_pattern, file_id_or_url)
        if match:
            return match.group(1)
        return file_id_or_url

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_file(self, file_id: str) -> Dict[str, Any]:
        """Fetch Figma file data."""
        file_id = self.extract_file_id(file_id)
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/files/{file_id}",
                    headers=self.headers,
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                # Don't retry on client errors (4xx)
                if 400 <= e.response.status_code < 500:
                    raise
                # Retry on server errors (5xx) or other issues
                raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_file_nodes(self, file_id: str, node_ids: List[str]) -> Dict[str, Any]:
        """Fetch specific nodes from a Figma file."""
        file_id = self.extract_file_id(file_id)
        ids_param = ",".join(node_ids)
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/files/{file_id}/nodes",
                    headers=self.headers,
                    params={"ids": ids_param},
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                # Don't retry on client errors (4xx)
                if 400 <= e.response.status_code < 500:
                    raise
                # Retry on server errors (5xx) or other issues
                raise

    def _map_figma_type_to_component_type(self, figma_type: str, name: str) -> str:
        """Map Figma node types to semantic component types."""
        type_mapping = {
            "FRAME": "container",
            "GROUP": "group",
            "COMPONENT": "component",
            "COMPONENT_SET": "component_set",
            "INSTANCE": "component_instance",
            "TEXT": "text",
            "RECTANGLE": "rectangle",
            "ELLIPSE": "ellipse",
            "LINE": "line",
            "VECTOR": "icon",
            "BOOLEAN_OPERATION": "shape",
        }

        # Try to infer more specific types from name
        name_lower = name.lower()
        if any(btn in name_lower for btn in ["button", "btn", "cta"]):
            return "button"
        elif any(inp in name_lower for inp in ["input", "field", "textbox", "text field"]):
            return "input"
        elif any(nav in name_lower for nav in ["nav", "menu", "header", "footer"]):
            return "navigation"
        elif any(card in name_lower for card in ["card", "tile"]):
            return "card"
        elif any(img in name_lower for img in ["image", "img", "photo", "avatar"]):
            return "image"
        elif any(icon in name_lower for icon in ["icon", "ico"]):
            return "icon"
        elif any(chk in name_lower for chk in ["checkbox", "check", "toggle", "switch"]):
            return "checkbox"
        elif any(rad in name_lower for rad in ["radio", "option"]):
            return "radio"
        elif any(sel in name_lower for sel in ["select", "dropdown", "picker"]):
            return "dropdown"
        elif any(modal in name_lower for modal in ["modal", "dialog", "popup"]):
            return "modal"
        elif any(tab in name_lower for tab in ["tab"]):
            return "tab"
        elif any(list_item in name_lower for list_item in ["list", "item"]):
            return "list_item"

        return type_mapping.get(figma_type, "unknown")

    def _extract_component_properties(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant properties from a Figma node."""
        properties = {}

        # Text content
        if node.get("type") == "TEXT":
            properties["text"] = node.get("characters", "")
            properties["font_size"] = node.get("style", {}).get("fontSize")
            properties["font_weight"] = node.get("style", {}).get("fontWeight")

        # Visibility
        properties["visible"] = node.get("visible", True)

        # Opacity
        if "opacity" in node:
            properties["opacity"] = node["opacity"]

        # Background
        if "fills" in node and node["fills"]:
            properties["has_background"] = True
            fills = node["fills"]
            if fills and len(fills) > 0:
                first_fill = fills[0]
                if first_fill.get("type") == "SOLID":
                    properties["background_color"] = first_fill.get("color")

        # Interactions (if available)
        if "interactions" in node:
            properties["has_interactions"] = True
            properties["interaction_count"] = len(node["interactions"])

        # Component properties
        if "componentProperties" in node:
            properties["component_properties"] = node["componentProperties"]

        # Constraints
        if "constraints" in node:
            properties["constraints"] = node["constraints"]

        return properties

    def _extract_position(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """Extract position and size information from a node."""
        bounds = node.get("absoluteBoundingBox", {})
        return {
            "x": bounds.get("x", 0),
            "y": bounds.get("y", 0),
            "width": bounds.get("width", 0),
            "height": bounds.get("height", 0),
        }
    
    def _calculate_component_relevance(self, component: ComponentData) -> float:
        """Calculate relevance score for a component to determine if it should be included.
        
        Higher scores indicate more relevant/testable components.
        Decorative elements get lower scores.
        
        Args:
            component: Component to score (ComponentData object or dict)
            
        Returns:
            Relevance score (0-100)
        """
        score = 0.0
        
        # Helper to get attribute from dict or object
        def get_attr(obj, key, default=None):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)
        
        # Helper to get from properties safely
        def get_prop(obj, key, default=None):
            props = get_attr(obj, 'properties', {})
            if isinstance(props, dict):
                return props.get(key, default)
            return getattr(props, key, default) if props else default
        
        component_type = get_attr(component, 'component_type', 'unknown').lower()
        text = get_prop(component, 'text', '')
        
        # FUNCTIONAL COMPONENTS - These are testable
        # Buttons, inputs, form controls
        critical_types = {
            'button': 90,
            'input': 85,
            'textarea': 85,
            'dropdown': 80,
            'select': 80,
            'checkbox': 75,
            'radio': 75,
            'toggle': 75,
            'switch': 75,
            'slider': 70,
        }
        
        # Important structural components
        important_types = {
            'modal': 65,
            'dialog': 65,
            'form': 60,
            'table': 60,
            'list': 55,
            'navigation': 55,
            'card': 50,
            'container': 40,  # Generic container, might have important content
            'frame': 35,
            'group': 30,
        }
        
        # Content components
        content_types = {
            'text': 20,  # Low score by itself, but has value
            'label': 20,
            'heading': 25,
            'paragraph': 20,
            'image': 25,
            'icon': 15,  # Icons are often decorative
            'link': 40,  # Links are interactive
        }
        
        # Decorative/low-value components
        decorative_types = {
            'rectangle': -50,
            'ellipse': -50,
            'circle': -50,
            'line': -50,
            'shape': -50,
            'polygon': -50,
            'vector': -40,
            'divider': -20,
            'spacer': -50,
            'separator': -20,
            'background': -50,
            'overlay': -30,
        }
        
        # Assign score based on component type
        if component_type in critical_types:
            score = critical_types[component_type]
        elif component_type in important_types:
            score = important_types[component_type]
        elif component_type in content_types:
            score = content_types[component_type]
        elif component_type in decorative_types:
            score = decorative_types[component_type]
        else:
            # Unknown types - give a small positive score to be safe
            score = 15
        
        # BOOST SCORE for components with meaningful text
        if text and len(text.strip()) > 0:
            text_length = len(text.strip())
            # Components with substantive text are more important
            if text_length > 5:
                score += min(20, text_length // 3)  # Cap at +20
            # But penalize placeholder-like text
            if any(x in text.lower() for x in ['icon', 'btn', '<', '>', '[', ']']):
                score -= 5
        
        # PENALIZE very small/empty containers
        if component_type in ['container', 'frame', 'group']:
            if not text or len(text.strip()) == 0:
                score -= 10  # Generic empty container
        
        # Interactive elements get a boost
        if get_prop(component, 'has_interactions', False):
            score += 25
        
        # Check visibility
        if not get_prop(component, 'visible', True):
            score -= 50
        
        # Check opacity
        opacity = get_prop(component, 'opacity', 1.0)
        if opacity is not None and opacity < 0.3:
            score -= 15
        
        # Find the best match score from all type groups
        all_scores = [
            critical_types.get(component_type, 0),
            important_types.get(component_type, 0),
            content_types.get(component_type, 0),
            decorative_types.get(component_type, 0)
        ]
        
        score = max(all_scores) if all_scores else 0
        
        # Adjust score based on other properties
        return max(0, score)  # Don't return negative scores
    
    def _filter_components_by_relevance(self, components: List[ComponentData]) -> List[ComponentData]:
        """Filter out low-relevance components to reduce noise.
        
        Args:
            components: List of components to filter (ComponentData objects or dicts)
            
        Returns:
            Filtered list of relevant components
        """
        if not self.enable_filtering:
            return components
        
        filtered = []
        scores_dist = {'high': 0, 'medium': 0, 'low': 0, 'filtered': 0}
        
        for component in components:
            score = self._calculate_component_relevance(component)
            
            # Add score to component for display purposes
            if isinstance(component, dict):
                component['relevance_score'] = score
            else:
                component.relevance_score = score
            
            # Track score distribution
            if score >= 70:
                scores_dist['high'] += 1
            elif score >= 40:
                scores_dist['medium'] += 1
            elif score >= self.relevance_threshold:
                scores_dist['low'] += 1
            else:
                scores_dist['filtered'] += 1
            
            # Keep component if it meets threshold
            if score >= self.relevance_threshold:
                # Recursively filter children
                children = component.get('children', []) if isinstance(component, dict) else getattr(component, 'children', [])
                if children:
                    filtered_children = self._filter_components_by_relevance(children)
                    if isinstance(component, dict):
                        component['children'] = filtered_children
                    else:
                        component.children = filtered_children
                filtered.append(component)
        
        # Debug: Print score distribution
        print(f"[FILTERING DEBUG] Score distribution: High={scores_dist['high']}, Medium={scores_dist['medium']}, Low={scores_dist['low']}, Filtered={scores_dist['filtered']}")
        print(f"[FILTERING DEBUG] Threshold: {self.relevance_threshold}")
        
        return filtered

    def _parse_node_tree(
        self, node: Dict[str, Any], depth: int = 0, max_depth: int = 10
    ) -> Optional[ComponentData]:
        """Recursively parse Figma node tree into ComponentData."""
        if depth > max_depth:
            return None

        node_type = node.get("type", "")
        name = node.get("name", "Unnamed")

        # Skip certain node types
        skip_types = {"SLICE", "STICKY", "SHAPE_WITH_TEXT", "CONNECTOR"}
        if node_type in skip_types:
            return None

        component = ComponentData(
            node_id=node.get("id", ""),
            name=name,
            component_type=self._map_figma_type_to_component_type(node_type, name),
            properties=self._extract_component_properties(node),
            position=self._extract_position(node),
            children=[],
        )

        # Process children
        if "children" in node:
            for child in node["children"]:
                child_component = self._parse_node_tree(child, depth + 1, max_depth)
                if child_component:
                    component.children.append(child_component)

        return component

    def _is_screen(self, node: Dict[str, Any]) -> bool:
        """Determine if a node represents a screen/page."""
        node_type = node.get("type", "")
        name = node.get("name", "").lower()

        # Frames at top level are usually screens
        if node_type in ["FRAME", "COMPONENT", "COMPONENT_SET"]:
            # Skip small frames that are likely components, not screens
            bounds = node.get("absoluteBoundingBox", {})
            width = bounds.get("width", 0)
            height = bounds.get("height", 0)

            # Typical screen sizes (mobile, tablet, desktop)
            if width >= 320 and height >= 400:
                return True

            # Check for screen-like names
            screen_keywords = [
                "screen", "page", "view", "mobile", "desktop", 
                "tablet", "home", "login", "dashboard", "profile"
            ]
            if any(kw in name for kw in screen_keywords):
                return True

        return False

    def _determine_screen_type(self, node: Dict[str, Any]) -> str:
        """Determine the type of screen based on name and content."""
        name = node.get("name", "").lower()

        screen_type_mapping = {
            "login": "authentication",
            "signin": "authentication",
            "signup": "authentication",
            "register": "authentication",
            "home": "home",
            "dashboard": "dashboard",
            "profile": "profile",
            "settings": "settings",
            "list": "list",
            "detail": "detail",
            "form": "form",
            "checkout": "checkout",
            "cart": "cart",
            "search": "search",
            "navigation": "navigation",
            "modal": "modal",
            "error": "error",
            "success": "success",
            "loading": "loading",
            "empty": "empty_state",
            "onboarding": "onboarding",
        }

        for keyword, screen_type in screen_type_mapping.items():
            if keyword in name:
                return screen_type

        return "general"

    async def extract_screens(self, file_id: str) -> List[ScreenData]:
        """Extract all screens from a Figma file."""
        file_data = await self.get_file(file_id)
        screens = []

        document = file_data.get("document", {})

        def find_screens(node: Dict[str, Any], parent_page: str = ""):
            """Recursively find screens in the document tree."""
            node_type = node.get("type", "")

            # Canvas/Page level
            if node_type == "CANVAS":
                page_name = node.get("name", "")
                for child in node.get("children", []):
                    find_screens(child, page_name)

            # Check if this node is a screen
            elif self._is_screen(node):
                root_component = self._parse_node_tree(node)
                if root_component:
                    screen = ScreenData(
                        node_id=node.get("id", ""),
                        name=node.get("name", "Unnamed Screen"),
                        screen_type=self._determine_screen_type(node),
                        components=[root_component] if root_component.children else [],
                        metadata={
                            "page": parent_page,
                            "width": node.get("absoluteBoundingBox", {}).get("width"),
                            "height": node.get("absoluteBoundingBox", {}).get("height"),
                        },
                    )
                    # Flatten component tree for the screen
                    screen.components = root_component.children if root_component else []
                    
                    # Apply noise reduction filtering
                    if self.enable_filtering:
                        screen.components = self._filter_components_by_relevance(screen.components)
                    
                    screens.append(screen)

            # Continue searching in children
            elif "children" in node:
                for child in node.get("children", []):
                    find_screens(child, parent_page)

        find_screens(document)
        return screens

    def count_components(self, screens: List[ScreenData]) -> int:
        """Count total components across all screens."""

        def count_recursive(components: List[ComponentData]) -> int:
            total = len(components)
            for comp in components:
                if comp.children:
                    total += count_recursive(comp.children)
            return total

        return sum(count_recursive(screen.components) for screen in screens)
