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

    def __init__(self, access_token: Optional[str] = None, enable_filtering: bool = True,
                 prd_signals: Optional[Dict[str, Any]] = None):
        self.access_token = access_token or settings.figma_access_token
        self.base_url = settings.figma_api_base_url
        self.headers = {"X-Figma-Token": self.access_token}
        self.enable_filtering = enable_filtering and settings.enable_component_filtering
        self.relevance_threshold = settings.component_relevance_threshold
        # PRD-derived signals (optional). Expected shape: { 'keywords': {kw: weight}, 'intents': [...] }
        self.prd_signals = prd_signals or {}

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

        def get_attr(obj, key, default=None):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        def get_prop(obj, key, default=None):
            props = get_attr(obj, 'properties', {})
            if isinstance(props, dict):
                return props.get(key, default)
            return getattr(props, key, default) if props else default

        def area_of(obj):
            pos = get_attr(obj, 'position', {})
            width = pos.get('width', 0) if isinstance(pos, dict) else getattr(pos, 'width', 0)
            height = pos.get('height', 0) if isinstance(pos, dict) else getattr(pos, 'height', 0)
            try:
                return max(0.0, float(width) * float(height))
            except Exception:
                return 0.0

        component_type = get_attr(component, 'component_type', 'unknown').lower()
        text = (get_prop(component, 'text', '') or '').strip().lower()
        name = (get_attr(component, 'name', '') or '').lower()

        # ❌ HARD REMOVE — USELESS NAMES (MAIN FIX)

        if name.startswith("rectangle"):
            return 0

        if "arrow" in name:
            return 0

        if "icon" in name:
            return 0

        if "vector" in name:
            return 0

        # ❌ REMOVE BODY / IMAGE / INSTRUCTION CONTENT

        if text in ["fully body", "full body"]:
            return 0

        if any(x in text for x in ["left arm", "keep your"]):
            return 0

        # ❌ REMOVE DUPLICATE-LIKE TEXT (dates etc)

        if any(x in text for x in ["08/", "2021", "2022"]):
            return 0

        # ❌ HARD FILTER — REMOVE USELESS TYPES IMMEDIATELY
        REMOVE_TYPES = [
            'rectangle', 'ellipse', 'circle', 'line', 'vector',
            'polygon', 'shape', 'divider', 'spacer', 'separator',
            'background', 'overlay', 'icon'
        ]
        if component_type in REMOVE_TYPES:
            return 0

        # ❌ REMOVE USELESS TEXT
        if text:
            if text.isdigit():
                return 0
            if len(text) < 3:
                return 0
            if "copyright" in text:
                return 0
            if any(x in text for x in ["08/", "2021", "2022"]):
                return 0

        # ❌ REMOVE GROUPS WITHOUT VALUE
        if component_type in ['group', 'container', 'frame']:
            if not text:
                return 0
            if text.lower().startswith("rectangle"):
                return 0

        # ✅ BASE SCORE
        type_score_map = {
            'button': 90, 'input': 85, 'textarea': 85,
            'dropdown': 80, 'select': 80,
            'checkbox': 75, 'radio': 75,
            'form': 70, 'table': 65, 'list': 60,
            'navigation': 60, 'card': 55,
            'text': 40, 'label': 40, 'heading': 45,
            'link': 50
        }

        base = type_score_map.get(component_type, 20)

        # ✅ IMPORTANT KEYWORD BOOST (MAIN FIX)
        IMPORTANT_KEYWORDS = [
            "login", "sign", "submit", "search", "filter",
            "username", "password", "email",
            "dashboard", "user", "patient",
            "add", "edit", "delete", "manage"
        ]

        keyword_boost = 0
        for kw in IMPORTANT_KEYWORDS:
            if kw in text or kw in name:
                keyword_boost += 25

        # ❌ REMOVE REPEATED / INSTRUCTION TEXT
        if text:
            if text.count(" ") > 6:
                return 0
            if any(x in text for x in ["keep your", "left arm"]):
                return 0

        # Interaction
        interaction_count = get_prop(component, 'interaction_count', 0) or 0
        interaction_boost = min(30, int(interaction_count) * 8) if interaction_count else 0

        # Visibility
        visible = get_prop(component, 'visible', True)
        opacity = get_prop(component, 'opacity', 1.0)

        if not visible:
            return 0
        if opacity is not None and opacity < 0.3:
            return 0

        # Area filter (remove tiny icons)
        area = area_of(component)
        if area and area < 300:
            return 0

        # FINAL SCORE
        raw = base + keyword_boost + interaction_boost

        return max(0.0, min(100.0, float(raw)))

    # New API: percentile-based filtering
    def filter_components_percentile(self, components: List[ComponentData], drop_percent: float = 10.0) -> Dict[
        str, Any]:
        """Filter components by dropping the bottom `drop_percent` percentile.

        Returns a dict with `components` (filtered list) and `stats` for UI preview.
        """

        # Flatten components to compute global scores
        def flatten(comps: List[ComponentData], out: List[ComponentData]):
            for c in comps:
                out.append(c)
                children = c.get('children', []) if isinstance(c, dict) else getattr(c, 'children', [])
                if children:
                    flatten(children, out)

        all_comps: List[ComponentData] = []
        flatten(components, all_comps)

        # Compute scores
        scores = []
        comp_to_score = {}
        for c in all_comps:
            s = self._calculate_component_relevance(c)
            comp_to_score[id(c)] = s
            scores.append(s)

        if not scores:
            return {'components': components, 'stats': {'dropped': 0, 'total': 0}}

        # Determine cutoff
        scores_sorted = sorted(scores)
        k = int(len(scores_sorted) * (drop_percent / 100.0))
        cutoff = scores_sorted[k] if k < len(scores_sorted) else scores_sorted[-1]

        # Use modified recursive filter (promote children when parent filtered)
        def apply_filter(comps: List[ComponentData]) -> List[ComponentData]:
            out = []
            for comp in comps:
                score = comp_to_score.get(id(comp), self._calculate_component_relevance(comp))
                children = comp.get('children', []) if isinstance(comp, dict) else getattr(comp, 'children', [])
                kept_children = apply_filter(children) if children else []

                if score > cutoff:
                    # attach kept children
                    if isinstance(comp, dict):
                        comp['children'] = kept_children
                    else:
                        comp.children = kept_children
                    out.append(comp)
                else:
                    # promote kept children
                    out.extend(kept_children)
            return out

        filtered = apply_filter(components)

        dropped = len(all_comps) - sum(1 for c in filtered if c in all_comps)
        stats = {
            'total_components': len(all_comps),
            'drop_percent': drop_percent,
            'cutoff_score': cutoff,
            'dropped_estimate': dropped
        }

        return {'components': filtered, 'stats': stats}

    def _filter_components_by_relevance(self, components: List[ComponentData]) -> List[ComponentData]:
        """Filter out low-relevance components to reduce noise and ensure count only decreases."""

        if not self.enable_filtering:
            return components

        filtered = []

        TEST_RELEVANT_TYPES = {"button", "input", "dropdown", "checkbox", "radio", "form", "modal"}
        IMPORTANT_KEYWORDS = ["login", "signin", "submit", "email", "password"]

        before_count = len(components)

        for component in components:
            # Score
            raw_score = self._calculate_component_relevance(component)
            score = max(0, min(100, raw_score))

            # Attach score
            if isinstance(component, dict):
                component['relevance_score'] = score
                children = component.get('children', [])
                component_type = component.get("component_type", "")
                name = component.get("name", "").lower()
                if name.startswith("rectangle"):
                    continue
            else:
                component.relevance_score = score
                children = getattr(component, 'children', [])
                component_type = getattr(component, "component_type", "")
                name = getattr(component, "name", "").lower()

            # Recursive filtering of children
            filtered_children = self._filter_components_by_relevance(children) if children else []

            is_test_type = component_type in TEST_RELEVANT_TYPES
            has_keyword = any(k in name for k in IMPORTANT_KEYWORDS)

            # ✅ KEEP only valid components
            if score >= self.relevance_threshold or is_test_type or has_keyword:
                if isinstance(component, dict):
                    component['children'] = filtered_children
                else:
                    component.children = filtered_children

                filtered.append(component)

            # ❌ DO NOT push children if parent is removed (THIS FIXES YOUR ISSUE)

        # after_count = len(filtered)
        # removed = before_count - after_count

        # print(f"[FILTER SUMMARY] Before: {before_count} | After: {after_count} | Removed: {removed}")

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
