"""Evaluator service for assessing tests against PRD requirements."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple

import re

try:
    import google.generativeai as genai
except Exception:
    genai = None

from app.config import get_settings

settings = get_settings()


class ModelAdapter:
    """Base class for model adapters."""

    def generate_evaluation(self, prompt: str) -> Dict[str, Any]:
        raise NotImplementedError()


class PremiumAdapter(ModelAdapter):
    """Adapter that uses a configured LLM for evaluation."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or os.getenv("PREMIUM_GEMINI_API_KEY") or settings.gemini_api_key
        self.model_name = model_name or settings.llm_model

        if not genai or not self.api_key:
            raise RuntimeError("PremiumAdapter requires the Google Generative AI SDK and an API key")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)

    def generate_evaluation(self, prompt: str) -> Dict[str, Any]:
        generation_config = genai.types.GenerationConfig(max_output_tokens=settings.llm_max_tokens,
                                                         temperature=settings.llm_temperature)

        response = self.model.generate_content(contents=prompt, generation_config=generation_config)
        text = response.text if hasattr(response, "text") else str(response)

        # Try to extract JSON
        try:
            # strip markdown blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            # locate JSON object
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = text[start:end]
                return json.loads(json_str)
        except Exception:
            pass

        # If parsing failed, return raw text
        return {"raw": text}


class FallbackAdapter(ModelAdapter):
    """Heuristic evaluator producing coarse-grained metrics."""

    def _tokenize(self, text: str) -> List[str]:
        words = re.findall(r"\w+", (text or "").lower())
        return [w for w in words if len(w) > 1]

    def _extract_requirements_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Heuristically extract requirements from raw PRD text."""
        if not text:
            return []

        lines = [l.strip() for l in text.splitlines() if l.strip()]
        reqs: List[Dict[str, Any]] = []
        counter = 1

        # Patterns for numbered, bullet, and 'requirement' prefixed lines
        num_re = re.compile(r'^(?:\d+\.|\d+\))\s+(.*)')
        bullet_re = re.compile(r'^[\-\*\u2022]\s+(.*)')
        reqword_re = re.compile(r'^(?:requirement|req|r\-|req\:?)\b[:\s-]*\s*(.*)', re.I)

        for ln in lines:
            m = num_re.match(ln)
            if m:
                title = m.group(1).strip()
            else:
                m = bullet_re.match(ln)
                if m:
                    title = m.group(1).strip()
                else:
                    m = reqword_re.match(ln)
                    if m:
                        title = m.group(1).strip()
                    else:
                        # Keep longer sentences that look like a single requirement
                        if len(ln.split()) >= 6 and len(ln.split()) <= 40:
                            title = ln
                        else:
                            continue

            reqs.append({"requirement_id": f"REQ-{counter}", "title": title})
            counter += 1

            # Limit to reasonable number to avoid noise
            if counter > 200:
                break

        return reqs

    def _overlap_score(self, a: str, b: str) -> float:
        aw = set(self._tokenize(a))
        bw = set(self._tokenize(b))
        if not aw or not bw:
            return 0.0
        return len(aw & bw) / len(aw | bw)

    def generate_evaluation(self, prd: Dict[str, Any], tests: Dict[str, Any], screen: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        requirements = prd.get("requirements") or prd.get("reqs") or prd.get("items") or []
        # Infer requirements from PRD raw text when structured list missing
        if not requirements:
            raw_text = prd.get('full_text') or prd.get('text') or prd.get('body') or prd.get('content') or None
            if not raw_text and isinstance(prd, str):
                raw_text = prd
            if raw_text:
                inferred = self._extract_requirements_from_text(raw_text)
                if inferred:
                    requirements = inferred
        test_cases = tests.get("test_cases") or tests.get("tests") or []

        # If a specific screen is provided, prioritize tests for that screen
        screen_name = None
        if screen:
            screen_name = screen.get('name') or screen.get('screen')
            # Prefer tests that have an explicit source marker
            filtered = [tc for tc in test_cases if (tc.get('_source_screen') == screen_name or tc.get('screen') == screen_name)]
            if filtered:
                test_cases = filtered

        # Build compact textual representation of the selected screen
        screen_text = ""
        if screen:
            parts = []
            try:
                sname = screen.get('name') or screen.get('screen')
                if sname:
                    parts.append(sname)
            except Exception:
                pass
            try:
                comps = screen.get('components') or []
                def _collect_names(cs):
                    for c in cs:
                        if isinstance(c, dict):
                            n = c.get('name')
                            if n:
                                parts.append(n)
                            children = c.get('children') or []
                            if children:
                                _collect_names(children)
                _collect_names(comps)
            except Exception:
                pass
            screen_text = " ".join(parts)

        # Filter requirements to those relevant to the screen when possible
        relevant_requirements: List[Dict[str, Any]] = []
        if requirements and screen_text:
            for req in requirements:
                req_text = (req.get('title') or req.get('description') or req.get('text') or '')
                if not req_text:
                    continue
                overlap = self._overlap_score(req_text, screen_text)
                if overlap >= 0.03:
                    relevant_requirements.append(req)
        else:
            relevant_requirements = list(requirements)

        # Map requirement id -> matched tests
        per_requirement = []
        matched_req_count = 0

        # Precompute title/text tokens
        for req in relevant_requirements:
            req_id = req.get("requirement_id") or req.get("id") or req.get("req_id")
            req_text = (req.get("title") or req.get("description") or req.get("text") or "")

            # Find candidate tests by explicit requirement_ids or by overlap
            matched = []
            for tc in test_cases:
                tc_id = tc.get("id") or tc.get("title")
                if req_id and req_id in (tc.get("requirement_ids") or []):
                    score = 1.0
                    matched.append((tc_id, score))
                    continue

                # fallback: similarity between requirement text and test title+description
                tc_text = " ".join(filter(None, [tc.get("title", ""), tc.get("description", "")]))
                score = self._overlap_score(req_text, tc_text)
                # boost score if this test is explicitly from the same screen
                if screen_name and (tc.get('_source_screen') == screen_name or tc.get('screen') == screen_name):
                    score = min(1.0, score + 0.25)
                if score > 0.05:  # tiny threshold to consider
                    matched.append((tc_id, score))

            relevance = max([s for _, s in matched], default=0.0)
            correctness = 0.0
            notes = []
            if matched:
                matched_req_count += 1
                # basic correctness: each matched test should have steps + expected
                for tc_id, sc in matched:
                    tc = next((t for t in test_cases if (t.get("id") or t.get("title")) == tc_id), None)
                    if not tc:
                        continue
                    has_steps = bool(tc.get("test_steps"))
                    has_expected = bool(tc.get("expected_results")) or any(s.get("expected_result") for s in tc.get("test_steps", []))
                    correctness += (0.5 if has_steps else 0.0) + (0.5 if has_expected else 0.0)

            # normalize correctness
            if matched:
                correctness = min(correctness / (len(matched) * 1.0), 1.0)

            per_requirement.append({
                "id": req_id,
                "text": req_text,
                "matched_tests": [m[0] for m in matched],
                "scores": {"relevance": round(relevance, 3), "correctness": round(correctness, 3)},
                "notes": notes,
            })

        # Metrics
        total_reqs = len(relevant_requirements) or 1
        coverage = matched_req_count / total_reqs

        # Redundancy
        titles = [ (tc.get("title") or "").strip().lower() for tc in test_cases ]
        dup_count = len(titles) - len(set(titles))
        redundancy = dup_count / (len(titles) or 1)

        # Average relevance & correctness
        avg_relevance = sum(r["scores"]["relevance"] for r in per_requirement) / (len(per_requirement) or 1)
        avg_correctness = sum(r["scores"]["correctness"] for r in per_requirement) / (len(per_requirement) or 1)

        # Completeness
        completeness_scores = []
        clarity_scores = []
        for tc in test_cases:
            score = 0.0
            if tc.get("preconditions"):
                score += 0.33
            if tc.get("test_steps"):
                score += 0.34
            if tc.get("expected_results"):
                score += 0.33
            completeness_scores.append(score)

            # clarity: length heuristics
            title = tc.get("title", "")
            desc = tc.get("description", "")
            clarity = 0.0
            if 5 < len(title.split()) < 20:
                clarity += 0.5
            if 10 < len(desc.split()) < 200:
                clarity += 0.5
            clarity_scores.append(clarity)

        completeness = sum(completeness_scores) / (len(completeness_scores) or 1)
        clarity = sum(clarity_scores) / (len(clarity_scores) or 1)

        issues: List[Dict[str, Any]] = []
        # Flag tests with no steps
        for tc in test_cases:
            if not tc.get("test_steps"):
                issues.append({"severity": "medium", "message": "Test has no steps", "test_title": tc.get("title")})
            if not tc.get("expected_results") and not any(s.get("expected_result") for s in tc.get("test_steps", [])):
                issues.append({"severity": "high", "message": "Test missing expected results", "test_title": tc.get("title")})

        evaluation = {
            "metrics": {
                "coverage": round(coverage, 3),
                "relevance": round(avg_relevance, 3),
                "correctness": round(avg_correctness, 3),
                "completeness": round(completeness, 3),
                "redundancy": round(redundancy, 3),
                "clarity": round(clarity, 3),
            },
            "per_requirement": per_requirement,
            "issues": issues,
            "summary": f"Evaluated {len(test_cases)} tests for {len(relevant_requirements)} relevant requirements (from {len(requirements)} total).",
            "raw": {},
        }

        return evaluation


class Evaluator:
    """Public evaluator service. Chooses adapter and returns evaluation JSON."""

    def __init__(self, adapter: Optional[ModelAdapter] = None):
        self.adapter = adapter

    @classmethod
    def with_premium(cls) -> "Evaluator":
        try:
            adapter = PremiumAdapter()
            return cls(adapter=adapter)
        except Exception:
            # propagate so caller knows premium isn't available
            raise

    @classmethod
    def with_fallback(cls) -> "Evaluator":
        return cls(adapter=FallbackAdapter())

    def evaluate(self, prd: Dict[str, Any], tests: Dict[str, Any], screen: Optional[Dict[str, Any]] = None, prefer_premium: bool = True) -> Dict[str, Any]:
        """Evaluate provided PRD and tests.

        If prefer_premium is True, try the premium adapter first and fall back to heuristics.
        """
        if prefer_premium:
            try:
                adapter = self.adapter or PremiumAdapter()
                # Build a compact prompt that requests JSON evaluation
                prompt = self._build_prompt(prd, tests, screen=screen)
                result = adapter.generate_evaluation(prompt)
                # If premium returns raw text, try to wrap into expected structure
                if not isinstance(result, dict) or ("metrics" not in result and "raw" in result):
                    # Fall back to heuristic parsing
                    return FallbackAdapter().generate_evaluation(prd, tests, screen=screen)
                return result
            except Exception:
                # fallback
                return FallbackAdapter().generate_evaluation(prd, tests, screen=screen)

        # Direct heuristic
        return FallbackAdapter().generate_evaluation(prd, tests, screen=screen)

    def _build_prompt(self, prd: Dict[str, Any], tests: Dict[str, Any], screen: Optional[Dict[str, Any]] = None) -> str:
        # Detailed natural-language prompt with a clear expected JSON schema.
        instructions = (
            "You are a QA evaluation assistant. Given a PRD (requirements) document and a set of generated test cases plus an optional selected screen, "
            "produce a JSON evaluation with a strong focus on a compact and reliable `metrics` object.\n"
            "REQUIRED OUTPUT: Return valid JSON only. The top-level object must include at least a `metrics` object with the numeric scores below.\n"
            "METRICS (0.0-1.0): coverage, relevance, correctness, completeness, redundancy, clarity.\n"
            "OPTIONAL: per_requirement array and issues array are allowed but not required. If the model includes them they should follow the schema.\n"
            "When given a `screen`, prioritize judging tests for that screen and restrict requirement matching to requirements relevant to that screen.\n"
            "Return ONLY valid JSON. Do NOT include commentary or markdown.\n"
        )

        schema_example = {
            "metrics": {
                "coverage": 0.85,
                "relevance": 0.78,
                "correctness": 0.72,
                "completeness": 0.64,
                "redundancy": 0.10,
                "clarity": 0.80
            }}
        # Compose the prompt including compact PRD and tests to stay under token limits.
        prd_preview = prd
        test_preview = tests

        # Truncate large fields to avoid token overflow
        try:
            prd_text = json.dumps(prd_preview)[:6000]
        except Exception:
            prd_text = str(prd_preview)[:6000]

        try:
            tests_text = json.dumps(test_preview)[:6000]
        except Exception:
            tests_text = str(test_preview)[:6000]

        screen_text = ""
        if screen:
            try:
                screen_text = json.dumps(screen)[:2000]
            except Exception:
                screen_text = str(screen)[:2000]

        prompt_parts = [
            instructions,
            "EXAMPLES: The LLM must return JSON exactly matching the schema format. Example (for guidance):",
            json.dumps(schema_example, indent=2),
            "\nPRD (truncated):",
            prd_text,
            "\nGENERATED TEST CASES (truncated):",
            tests_text,
            "\nSELECTED SCREEN (truncated):",
            screen_text,
            "\nReturn the evaluation JSON now."
        ]

        return "\n".join(prompt_parts)


__all__ = ["Evaluator", "PremiumAdapter", "FallbackAdapter", "ModelAdapter"]
