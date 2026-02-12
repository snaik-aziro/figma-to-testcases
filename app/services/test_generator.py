"""LLM-based test case generator using Google Gemini API."""

import json
import os
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.schemas import ScreenData, TestStep
from app.models.database import TestCaseType, TestCasePriority

settings = get_settings()


class TestGenerator:
    """AI-powered test case generator using Google Gemini with baseline knowledge."""

    def __init__(self, api_key: Optional[str] = None, enable_baseline: bool = True):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or settings.gemini_api_key
        
        if not self.api_key:
            raise ValueError("Gemini API Key not found. Please set it in your .env file or environment variables.")
        
        genai.configure(api_key=self.api_key)
        
        self.model_name = settings.llm_model
        self.model = genai.GenerativeModel(self.model_name)
        self.max_tokens = settings.llm_max_tokens
        self.temperature = settings.llm_temperature
        self.enable_baseline = enable_baseline and settings.enable_baseline_knowledge
        self.baseline = self._load_baseline() if self.enable_baseline else None
    
    def _load_baseline(self) -> Optional[Dict[str, Any]]:
        """Load test scenario baseline knowledge from JSON file.
        
        Returns:
            Baseline dictionary or None if file not found
        """
        try:
            baseline_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "data",
                "test_baseline.json"
            )
            if os.path.exists(baseline_path):
                with open(baseline_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"⚠️  Baseline file not found at {baseline_path}")
                return None
        except Exception as e:
            print(f"⚠️  Error loading baseline file: {e}")
            return None
    
    def _match_component_to_baseline(self, component_type: str) -> Optional[Dict[str, Any]]:
        """Match a Figma component type to baseline test scenarios.
        
        Args:
            component_type: Component type from Figma (e.g., 'button', 'input')
            
        Returns:
            Baseline entry with test scenarios or None
        """
        if not self.baseline:
            return None
        
        ui_components = self.baseline.get('ui_components', {})
        return ui_components.get(component_type)
    
    def _detect_screen_pattern(self, screen_type: str, screen_name: str) -> Optional[Dict[str, Any]]:
        """Detect screen pattern from baseline knowledge.
        
        Args:
            screen_type: Screen type from Figma analysis
            screen_name: Screen name
            
        Returns:
            Pattern definition with test scenarios or None
        """
        if not self.baseline:
            return None
        
        patterns = self.baseline.get('screen_patterns', {})
        
        # Direct match by screen type
        if screen_type in patterns:
            return patterns.get(screen_type)
        
        # Try to match by name keywords
        screen_name_lower = screen_name.lower()
        for pattern_name, pattern_def in patterns.items():
            keywords = pattern_def.get('detection_criteria', {}).get('screen_name_keywords', [])
            if any(keyword in screen_name_lower for keyword in keywords):
                return pattern_def
        
        return None
    
    def _extract_baseline_scenarios(self, screen) -> Dict[str, Any]:
        """Extract relevant baseline scenarios for the given screen.
        
        Args:
            screen: Screen data (dict or ScreenData object)
            
        Returns:
            Dictionary with component scenarios and screen pattern scenarios
        """
        if not self.baseline:
            return {'component_scenarios': [], 'pattern_scenarios': []}
        
        # Helper to get attribute from dict or object
        def get_attr(obj, key, default=None):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)
        
        screen_name = get_attr(screen, 'name', 'Unknown')
        screen_type = get_attr(screen, 'screen_type', 'general')
        components = get_attr(screen, 'components', []) or []
        
        # Extract component-based scenarios
        component_scenarios = []
        seen_types = set()
        
        def collect_component_types(comp_list):
            for comp in comp_list:
                comp_type = get_attr(comp, 'component_type', 'unknown')
                if comp_type not in seen_types:
                    baseline_entry = self._match_component_to_baseline(comp_type)
                    if baseline_entry:
                        comp_name = get_attr(comp, 'name', 'component')
                        scenarios = baseline_entry.get('test_scenarios', {})
                        
                        # Flatten all scenario categories
                        all_scenarios = []
                        for category, scenario_list in scenarios.items():
                            all_scenarios.extend(scenario_list)
                        
                        if all_scenarios:
                            component_scenarios.append({
                                'component_type': comp_type,
                                'component_name': comp_name,
                                'scenarios': all_scenarios[:5]  # Limit to top 5 per component
                            })
                            seen_types.add(comp_type)
                
                # Recursively check children
                children = get_attr(comp, 'children', [])
                if children:
                    collect_component_types(children)
        
        collect_component_types(components)
        
        # Extract screen pattern scenarios
        pattern_scenarios = []
        pattern = self._detect_screen_pattern(screen_type, screen_name)
        if pattern:
            pattern_scenarios = pattern.get('test_scenarios', [])[:10]  # Limit to top 10
        
        return {
            'component_scenarios': component_scenarios,
            'pattern_scenarios': pattern_scenarios
        }

    def _build_system_prompt(self, test_type: TestCaseType) -> str:
        """Build system prompt based on test type."""
        base_prompt = """You are an expert QA engineer specializing in creating comprehensive test cases. 
Your test cases should be:
- Clear and actionable
- Include specific steps and expected results
- Cover both happy path and edge cases
- Be traceable to requirements when provided

Always respond with valid JSON in the specified format."""

        type_specific = {
            TestCaseType.FUNCTIONAL: """
Focus on functional testing:
- Verify all user interactions work correctly
- Test form validations and data submissions
- Verify navigation flows
- Test business logic and calculations
- Cover positive and negative scenarios""",

            TestCaseType.VISUAL: """
Focus on visual/UI testing:
- Verify layout and component alignment
- Check responsive behavior
- Verify colors, fonts, and styling
- Test component states (hover, active, disabled)
- Check visual consistency across screens""",

            TestCaseType.ACCESSIBILITY: """
Focus on accessibility testing:
- Verify WCAG 2.1 compliance
- Test keyboard navigation
- Verify screen reader compatibility
- Check color contrast ratios
- Test focus indicators and tab order
- Verify ARIA labels and roles""",

            TestCaseType.EDGE_CASE: """
Focus on edge case and boundary testing:
- Test with empty/null values
- Test maximum/minimum input values
- Test special characters and Unicode
- Test concurrent operations
- Test error recovery scenarios
- Test offline/poor connectivity behavior""",
        }

        return base_prompt + type_specific.get(test_type, "")

    def _build_context(
        self,
        screen,
        requirements: Optional[List[Dict[str, Any]]] = None,
        prd_context: Optional[str] = None,
    ) -> str:
        """Build context string from screen and requirements."""
        context_parts = []
        
        # Helper to get attribute from dict or object
        def get_attr(obj, key, default=None):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        # Screen information
        screen_name = get_attr(screen, 'name', 'Unknown')
        screen_type = get_attr(screen, 'screen_type', 'general')
        metadata = get_attr(screen, 'metadata', {})
        components = get_attr(screen, 'components', []) or []
        
        context_parts.append(f"## Screen: {screen_name}")
        context_parts.append(f"Type: {screen_type}")
        
        if metadata:
            width = metadata.get('width') if isinstance(metadata, dict) else getattr(metadata, 'width', None)
            height = metadata.get('height') if isinstance(metadata, dict) else getattr(metadata, 'height', None)
            if width and height:
                context_parts.append(f"Dimensions: {width}x{height}")

        # Components
        context_parts.append("\n### UI Components:")
        
        def format_component(comp, indent=0):
            """Format component tree as text."""
            lines = []
            prefix = "  " * indent
            comp_name = get_attr(comp, 'name', 'Unknown')
            comp_type = get_attr(comp, 'component_type', 'unknown')
            props = get_attr(comp, 'properties', {}) or {}
            children = get_attr(comp, 'children', []) or []
            
            lines.append(f"{prefix}- {comp_name} ({comp_type})")
            
            if props:
                text_val = props.get('text') if isinstance(props, dict) else getattr(props, 'text', None)
                has_interactions = props.get('has_interactions') if isinstance(props, dict) else getattr(props, 'has_interactions', None)
                if text_val:
                    lines.append(f"{prefix}  Text: \"{text_val}\"")
                if has_interactions:
                    lines.append(f"{prefix}  Has interactions: Yes")
            
            if children:
                for child in children:
                    lines.extend(format_component(child, indent + 1))
            
            return lines

        for component in components:
            context_parts.extend(format_component(component))

        # PRD Context (raw text from PRD document)
        if prd_context:
            context_parts.append("\n### PRD/Requirements Document Context:")
            context_parts.append(prd_context[:2000])  # Limit to avoid token overflow

        # Structured Requirements
        if requirements:
            context_parts.append("\n### Related Requirements:")
            for req in requirements:
                context_parts.append(f"- [{req.get('requirement_id', 'N/A')}] {req.get('title', '')}")
                if req.get('acceptance_criteria'):
                    context_parts.append(f"  Acceptance Criteria: {', '.join(req['acceptance_criteria'][:3])}")

        return "\n".join(context_parts)

    def _build_test_generation_prompt(
        self,
        context: str,
        test_type: TestCaseType,
        test_count: int = 5,
        baseline_scenarios: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build the prompt for test generation with baseline knowledge.
        
        Args:
            context: Screen and requirements context
            test_type: Type of tests to generate
            test_count: Number of test cases to generate
            baseline_scenarios: Suggested scenarios from baseline knowledge
            
        Returns:
            Complete prompt for LLM
        """
        prompt_parts = [
            f"Based on the following UI screen and requirements context, generate {test_count} {test_type.value} test cases.",
            "",
            context
        ]
        
        # Add baseline scenario suggestions if available
        if baseline_scenarios and self.enable_baseline:
            component_scenarios = baseline_scenarios.get('component_scenarios', [])
            pattern_scenarios = baseline_scenarios.get('pattern_scenarios', [])
            
            if component_scenarios or pattern_scenarios:
                prompt_parts.append("\n### SUGGESTED TEST SCENARIOS (from baseline knowledge):")
                prompt_parts.append("Use these as inspiration, but adapt them to this specific screen context.\n")
            
            # Add component-specific suggestions
            if component_scenarios:
                prompt_parts.append("**Component-Level Test Scenarios:**")
                for comp_entry in component_scenarios[:3]:  # Limit to top 3 component types
                    comp_type = comp_entry.get('component_type', 'component')
                    comp_name = comp_entry.get('component_name', 'component')
                    scenarios = comp_entry.get('scenarios', [])
                    
                    prompt_parts.append(f"\nFor {comp_type} '{comp_name}':")
                    for scenario in scenarios[:3]:  # Top 3 scenarios per component
                        title = scenario.get('title', '')
                        priority = scenario.get('priority', 'medium')
                        steps = scenario.get('steps_template', [])
                        if title:
                            prompt_parts.append(f"  - [{priority.upper()}] {title}")
                            if steps:
                                prompt_parts.append(f"    Steps: {' → '.join(steps[:2])}...")
            
            # Add screen pattern suggestions
            if pattern_scenarios:
                prompt_parts.append("\n**Screen Pattern Test Scenarios:**")
                for scenario in pattern_scenarios[:5]:  # Top 5 pattern scenarios
                    title = scenario.get('title', '')
                    priority = scenario.get('priority', 'medium')
                    category = scenario.get('category', '')
                    if title:
                        prompt_parts.append(f"  - [{priority.upper()}] {title} ({category})")
                        steps = scenario.get('steps_template', [])
                        if steps:
                            prompt_parts.append(f"    Example: {' → '.join(steps[:2])}...")
        
        prompt_parts.append("\nGenerate test cases ONLY in the following strict JSON format (no markdown, no code blocks, only JSON):")
        
        return "\n".join(prompt_parts) + f"""

{{
    "test_cases": [
        {{
            "title": "Brief test case title",
            "description": "Detailed description of what this test verifies",
            "priority": "high",
            "preconditions": ["precondition 1"],
            "test_steps": [
                {{
                    "step_number": 1,
                    "action": "Specific action to perform",
                    "expected_result": "Expected outcome of this step",
                    "test_data": null
                }}
            ],
            "expected_results": ["Final expected result"],
            "tags": ["tag1", "tag2"],
            "requirement_ids": [],
            "confidence_score": 0.85
        }}
    ]
}}

IMPORTANT REQUIREMENTS:
- Return ONLY valid JSON, absolutely no markdown code blocks
- Ensure all strings use double quotes
- No trailing commas
- Generate exactly {test_count} test cases in the array
- Each test case must have: title, description, priority, preconditions, test_steps, expected_results, tags, requirement_ids, confidence_score
- test_steps must be an array of step objects with: step_number, action, expected_result, test_data
- confidence_score must be a number between 0.0 and 1.0"""


    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate_test_cases(
        self,
        screen,  # Can be ScreenData or dict
        test_type: TestCaseType = TestCaseType.FUNCTIONAL,
        requirements: Optional[List[Dict[str, Any]]] = None,
        test_count: int = 5,
        prd_context: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Generate test cases for a screen using Google Gemini with baseline knowledge.
        
        Args:
            screen: Screen data (ScreenData object or dict)
            test_type: Type of tests to generate
            requirements: Optional list of requirements
            test_count: Number of test cases to generate
            prd_context: Optional PRD context text
            
        Returns:
            List of generated test cases
        """
        # Extract baseline scenarios if enabled
        baseline_scenarios = None
        if self.enable_baseline:
            baseline_scenarios = self._extract_baseline_scenarios(screen)
        
        # Build context and prompt with baseline knowledge
        context = self._build_context(screen, requirements, prd_context)
        prompt = self._build_test_generation_prompt(context, test_type, test_count, baseline_scenarios)
        system_prompt = self._build_system_prompt(test_type) + "\n\nIMPORTANT: Respond with ONLY valid JSON, no markdown code blocks."

        # Combine system prompt and user prompt for Gemini
        full_prompt = f"{system_prompt}\\n\\n{prompt}"
        
        generation_config = genai.types.GenerationConfig(
            max_output_tokens=self.max_tokens,
            temperature=self.temperature,
        )

        response = self.model.generate_content(
            contents=full_prompt,
            generation_config=generation_config
        )

        # Extract JSON from response
        response_text = response.text
        
        # Debug output
        print(f"   [DEBUG] Response length: {len(response_text)} chars")
        print(f"   [DEBUG] First 200 chars: {response_text[:200]}")
        
        # Try to parse JSON from response
        try:
            # Remove markdown code blocks if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            # Clean up the response
            response_text = response_text.strip()
            
            # Find JSON boundaries more carefully
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                
                # Try to fix common JSON issues
                # Replace single quotes with double quotes (if not within already quoted strings)
                # Remove trailing commas before closing braces/brackets
                json_str = json_str.replace('\n', ' ')  # Normalize newlines
                
                print(f"   [DEBUG] Extracted JSON length: {len(json_str)}")
                print(f"   [DEBUG] JSON preview: {json_str[:300]}")
                
                try:
                    result = json.loads(json_str)
                    test_cases = result.get("test_cases", [])
                    
                    if not test_cases:
                        print(f"   [DEBUG] No test_cases found in JSON. Keys: {list(result.keys())}")
                        return []
                    
                    # Add test type to each test case
                    for tc in test_cases:
                        tc["test_type"] = test_type.value
                    
                    print(f"   [DEBUG] Successfully parsed {len(test_cases)} test cases")
                    return test_cases
                    
                except json.JSONDecodeError as e:
                    print(f"   [DEBUG] JSON parse error: {e}")
                    print(f"   [DEBUG] Error position: char {e.pos}")
                    print(f"   [DEBUG] Context around error: ...{json_str[max(0, e.pos-100):min(len(json_str), e.pos+100)]}...")
                    
                    # Try to repair incomplete JSON by adding missing closing brackets
                    try:
                        json_str_repaired = json_str.rstrip()
                        
                        # Count unclosed brackets
                        open_braces = json_str_repaired.count('{') - json_str_repaired.count('}')
                        open_brackets = json_str_repaired.count('[') - json_str_repaired.count(']')
                        
                        print(f"   [DEBUG] Attempting repair: {open_braces} unclosed braces, {open_brackets} unclosed brackets")
                        
                        # Add closing brackets
                        json_str_repaired += ']' * open_brackets + '}' * open_braces
                        
                        print(f"   [DEBUG] Repaired JSON length: {len(json_str_repaired)}")
                        
                        result = json.loads(json_str_repaired)
                        test_cases = result.get("test_cases", [])
                        
                        if test_cases:
                            for tc in test_cases:
                                tc["test_type"] = test_type.value
                            print(f"   [DEBUG] Successfully parsed after repair: {len(test_cases)} test cases")
                            return test_cases
                    except Exception as e2:
                        print(f"   [DEBUG] Repair parsing failed: {type(e2).__name__}")
                    
                    # Try to extract individual test cases from the broken JSON
                    try:
                        print(f"   [DEBUG] Attempting to extract individual test cases from malformed JSON...")
                        import re
                        
                        # Find all test case objects
                        test_case_pattern = r'\{[^{}]*"title"[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
                        test_case_matches = re.finditer(test_case_pattern, json_str, re.DOTALL)
                        
                        extracted_cases = []
                        for match in test_case_matches:
                            tc_str = match.group(0)
                            try:
                                tc = json.loads(tc_str)
                                tc["test_type"] = test_type.value
                                extracted_cases.append(tc)
                                print(f"   [DEBUG] Extracted test case: {tc.get('title', 'Unknown')}")
                            except:
                                continue
                        
                        if extracted_cases:
                            print(f"   [DEBUG] Successfully extracted {len(extracted_cases)} test cases from malformed JSON")
                            return extracted_cases
                    except Exception as e3:
                        print(f"   [DEBUG] Individual extraction failed: {type(e3).__name__}")
                    
                    # Last resort: Try to extract the test_cases array and re-wrap it
                    try:
                        print(f"   [DEBUG] Last resort: attempting to extract test_cases array...")
                        
                        # Find the test_cases array
                        array_start = json_str.find('"test_cases"')
                        if array_start >= 0:
                            array_start = json_str.find('[', array_start)
                            if array_start >= 0:
                                # Extract from [ to the end, then repair
                                array_str = json_str[array_start:]
                                
                                # Count and fix brackets
                                open_brackets = array_str.count('[') - array_str.count(']')
                                array_str_fixed = array_str.rstrip() + ']' * open_brackets
                                
                                print(f"   [DEBUG] Trying to parse extracted array: {array_str_fixed[:100]}...")
                                
                                test_cases_raw = json.loads(array_str_fixed)
                                if isinstance(test_cases_raw, list):
                                    for tc in test_cases_raw:
                                        tc["test_type"] = test_type.value
                                    print(f"   [DEBUG] Successfully parsed {len(test_cases_raw)} test cases from array extraction")
                                    return test_cases_raw
                    except Exception as e4:
                        print(f"   [DEBUG] Array extraction failed: {type(e4).__name__}: {e4}")
            else:
                print(f"   [DEBUG] Could not find JSON boundaries. json_start={json_start}, json_end={json_end}")
                
        except Exception as e:
            print(f"   [DEBUG] Unexpected error: {type(e).__name__}: {e}")

        return []

    def generate_comprehensive_tests(
        self,
        screen: ScreenData,
        requirements: Optional[List[Dict[str, Any]]] = None,
        test_types: Optional[List[TestCaseType]] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Generate comprehensive test cases across multiple test types."""
        if test_types is None:
            test_types = [TestCaseType.FUNCTIONAL, TestCaseType.EDGE_CASE]

        all_tests = {}
        
        for test_type in test_types:
            tests = self.generate_test_cases(
                screen=screen,
                test_type=test_type,
                requirements=requirements,
                test_count=3 if test_type == TestCaseType.EDGE_CASE else 5,
            )
            all_tests[test_type.value] = tests

        return all_tests

    def validate_test_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean up a generated test case."""
        validated = {
            "title": test_case.get("title", "Untitled Test Case"),
            "description": test_case.get("description", ""),
            "test_type": test_case.get("test_type", TestCaseType.FUNCTIONAL.value),
            "priority": test_case.get("priority", TestCasePriority.MEDIUM.value),
            "preconditions": test_case.get("preconditions", []),
            "test_steps": [],
            "expected_results": test_case.get("expected_results", []),
            "tags": test_case.get("tags", []),
            "requirement_ids": test_case.get("requirement_ids", []),
            "confidence_score": min(max(test_case.get("confidence_score", 0.7), 0.0), 1.0),
        }

        # Validate test steps
        for i, step in enumerate(test_case.get("test_steps", []), 1):
            validated_step = {
                "step_number": step.get("step_number", i),
                "action": step.get("action", ""),
                "expected_result": step.get("expected_result", ""),
                "test_data": step.get("test_data"),
            }
            if validated_step["action"]:  # Only add non-empty steps
                validated["test_steps"].append(validated_step)

        return validated

    def deduplicate_tests(
        self, test_cases: List[Dict[str, Any]], similarity_threshold: float = 0.8
    ) -> List[Dict[str, Any]]:
        """Remove duplicate or highly similar test cases."""
        if not test_cases:
            return []

        unique_tests = []
        seen_titles = set()

        for tc in test_cases:
            title = tc.get("title", "").lower().strip()
            
            # Simple deduplication based on title similarity
            is_duplicate = False
            for seen in seen_titles:
                # Calculate simple word overlap
                title_words = set(title.split())
                seen_words = set(seen.split())
                if title_words and seen_words:
                    overlap = len(title_words & seen_words) / len(title_words | seen_words)
                    if overlap >= similarity_threshold:
                        is_duplicate = True
                        break

            if not is_duplicate:
                unique_tests.append(tc)
                seen_titles.add(title)

        return unique_tests
