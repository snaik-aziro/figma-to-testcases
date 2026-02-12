"""JSON loader for Figma exported data."""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict

from app.schemas import ScreenData, ComponentData


class FigmaJsonLoader:
    """Load and parse Figma JSON export files."""

    def __init__(self, json_path: str):
        self.json_path = Path(json_path)
        self.raw_data = self._load_json()

    def _load_json(self) -> Dict[str, Any]:
        """Load JSON file with error handling."""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: JSON file not found at {self.json_path}")
            return {}
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {self.json_path}")
            return {}

    def get_file_name(self) -> str:
        """Get the name of the JSON file."""
        return self.json_path.name

    def _parse_component_text(self, text: str) -> Dict[str, str]:
        """Parse component text like 'Frame 75 (FRAME)' into name and type."""
        match = re.match(r'^(.+?)\s*\(([A-Z_]+)\)$', text.strip())
        if match:
            return {
                "name": match.group(1).strip(),
                "type": match.group(2).strip()
            }
        return {"name": text, "type": "UNKNOWN"}

    def _is_screen_name(self, name: str) -> bool:
        """Check if a name looks like a screen identifier."""
        # Match numbered screens like "001", "014", "1.1", "Screen_01"
        if re.match(r'^\d{2,3}$', name):  # "001", "14", "014"
            return True
        if re.match(r'^\d+\.\d+', name):  # "1.1", "2.3"
            return True
        if re.match(r'^Screen[\s_-]?\d+', name, re.IGNORECASE):
            return True
        if re.match(r'^Page[\s_-]?\d+', name, re.IGNORECASE):
            return True
        # Named screens
        screen_keywords = ['login', 'dashboard', 'home', 'settings', 'profile', 
                          'detail', 'list', 'form', 'modal', 'popup']
        name_lower = name.lower()
        if any(kw in name_lower for kw in screen_keywords):
            return True
        return False

    def _extract_display_text(self, text: str) -> Optional[str]:
        """Extract display text from component text."""
        parsed = self._parse_component_text(text)
        name = parsed["name"]
        
        prefixes = ["Typography ", "Cell ", "Head ", "Button ", "Chip ", "Text "]
        for prefix in prefixes:
            if name.startswith(prefix):
                return name[len(prefix):]
        
        return name

    def _map_type_to_component_type(self, figma_type: str, name: str) -> str:
        """Map Figma types to semantic component types."""
        name_lower = name.lower()
        
        if any(btn in name_lower for btn in ["button", "btn", "cta"]):
            return "button"
        elif any(inp in name_lower for inp in ["input", "field", "textbox", "text field"]):
            return "input"
        elif any(nav in name_lower for nav in ["nav", "menu", "sidebar"]):
            return "navigation"
        elif any(card in name_lower for card in ["card", "tile", "paper"]):
            return "card"
        elif any(tbl in name_lower for tbl in ["table", "tablehead", "tablecell", "tablerow"]):
            return "table"
        elif any(img in name_lower for img in ["image", "img", "photo", "avatar"]):
            return "image"
        elif any(icon in name_lower for icon in ["icon", "ico", "filled"]):
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
        elif any(chip in name_lower for chip in ["chip", "tag", "badge"]):
            return "chip"
        elif any(progress in name_lower for progress in ["progress", "loading", "spinner"]):
            return "progress"
        elif any(typography in name_lower for typography in ["typography", "text", "label", "title", "heading"]):
            return "text"
        elif any(step in name_lower for step in ["stepper", "step"]):
            return "stepper"
        
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
        }
        
        return type_mapping.get(figma_type, "container")

    def _determine_screen_type(self, components: List[Dict]) -> str:
        """Determine screen type from components."""
        all_text = " ".join([c.get("text", "") for c in components]).lower()
        
        if any(term in all_text for term in ["login", "sign in", "signin", "email", "password"]):
            return "authentication"
        elif any(term in all_text for term in ["dashboard", "overview", "analytics", "metrics"]):
            return "dashboard"
        elif any(term in all_text for term in ["test suite", "test case", "testing"]):
            return "test_management"
        elif any(term in all_text for term in ["settings", "preferences", "configuration"]):
            return "settings"
        elif any(term in all_text for term in ["profile", "account", "user"]):
            return "profile"
        elif any(term in all_text for term in ["table", "list", "grid"]):
            return "list_view"
        elif any(term in all_text for term in ["form", "create", "add new", "edit", "stepper"]):
            return "form"
        
        return "general"

    def extract_screens(self) -> List[ScreenData]:
        """Extract screens from JSON data."""
        components = self.raw_data.get("components", [])
        
        if not components:
            return []

        # Build ID to component mapping
        id_to_comp = {c["id"]: c for c in components}
        
        # Find screen-level frames (numbered screens like "001", "014")
        screens = []
        screen_ids = set()
        
        for comp in components:
            comp_id = comp.get("id", "")
            text = comp.get("text", "")
            parsed = self._parse_component_text(text)
            
            # Check if this is a top-level screen frame
            is_nested = comp_id.startswith("I") or ";" in comp_id
            
            if not is_nested and parsed["type"] == "FRAME" and self._is_screen_name(parsed["name"]):
                screen_ids.add(comp_id)

        # Collect children for each screen
        for screen_id in screen_ids:
            screen_comp = id_to_comp[screen_id]
            screen_parsed = self._parse_component_text(screen_comp["text"])
            
            # Find all components that belong to this screen
            # by matching ID prefix patterns
            id_prefix = screen_id.split(":")[0]  # e.g., "217" from "217:4605"
            id_num = int(screen_id.split(":")[1])  # e.g., 4605
            
            children = []
            for comp in components:
                cid = comp.get("id", "")
                
                # Check if component is a child of this screen
                # Children have IDs that come after the screen ID numerically
                # or are instances starting with the screen's ID pattern
                if cid == screen_id:
                    continue
                    
                if cid.startswith(f"I{screen_id}"):
                    children.append(comp)
                elif cid.startswith(f"{id_prefix}:"):
                    try:
                        child_num = int(cid.split(":")[1])
                        # Heuristic: children have sequential IDs after the screen
                        if id_num < child_num < id_num + 100:
                            children.append(comp)
                    except (ValueError, IndexError):
                        pass

            if len(children) < 3:
                continue

            # Build component list
            component_list = []
            for child in children:
                child_parsed = self._parse_component_text(child.get("text", ""))
                display_text = self._extract_display_text(child["text"])
                
                component_list.append(ComponentData(
                    node_id=child["id"],
                    name=child_parsed["name"],
                    component_type=self._map_type_to_component_type(child_parsed["type"], child_parsed["name"]),
                    properties={
                        "text": display_text,
                        "figma_type": child_parsed["type"],
                    }
                ))

            screen_type = self._determine_screen_type(children)
            
            screens.append(ScreenData(
                node_id=screen_id,
                name=f"Screen {screen_parsed['name']}",
                screen_type=screen_type,
                components=component_list,
                metadata={
                    "source": "json_export",
                    "original_name": screen_parsed["name"],
                    "component_count": len(component_list)
                }
            ))

        # Sort screens by name
        screens.sort(key=lambda s: s.name)
        
        return screens

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the JSON data."""
        components = self.raw_data.get("components", [])
        
        type_counts = defaultdict(int)
        for comp in components:
            parsed = self._parse_component_text(comp.get("text", ""))
            type_counts[parsed["type"]] += 1
        
        screens = self.extract_screens()
        
        return {
            "total_components": len(components),
            "type_breakdown": dict(type_counts),
            "screens_detected": len(screens),
            "screen_names": [s.name for s in screens]
        }


def load_figma_json(json_path: str) -> List[ScreenData]:
    """Convenience function to load Figma JSON and extract screens."""
    loader = FigmaJsonLoader(json_path)
    return loader.extract_screens()
