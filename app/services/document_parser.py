"""Document parser for extracting requirements from PDF and DOCX files."""

import re
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

from PyPDF2 import PdfReader
from docx import Document as DocxDocument

from app.schemas import RequirementResponse
from app.models.database import TestCasePriority


class DocumentParser:
    """Parser for extracting requirements from documents."""

    def __init__(self):
        self.requirement_patterns = [
            # Common requirement ID patterns
            r"(?:REQ|RQ|R|FR|NFR|BR|SR|US|USER STORY)[-_]?\s*\d+",
            r"\d+\.\d+(?:\.\d+)*",  # Numbered sections like 1.1, 1.1.1
        ]

        self.priority_keywords = {
            TestCasePriority.CRITICAL: ["critical", "must", "mandatory", "essential", "required"],
            TestCasePriority.HIGH: ["high", "important", "should", "significant"],
            TestCasePriority.MEDIUM: ["medium", "normal", "could", "desirable"],
            TestCasePriority.LOW: ["low", "nice to have", "optional", "may"],
        }

    def parse_pdf(self, file_path: str) -> Dict[str, Any]:
        """Parse PDF file and extract content."""
        reader = PdfReader(file_path)
        full_text = ""
        pages_content = []

        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            full_text += page_text + "\n"
            pages_content.append({
                "page_number": page_num + 1,
                "content": page_text
            })

        return {
            "full_text": full_text,
            "pages": pages_content,
            "total_pages": len(reader.pages),
            "file_type": "pdf"
        }

    def parse_docx(self, file_path: str) -> Dict[str, Any]:
        """Parse DOCX file and extract content."""
        doc = DocxDocument(file_path)
        full_text = ""
        sections = []
        current_section = {"heading": None, "content": []}

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            # Check if this is a heading
            if para.style.name.startswith("Heading"):
                if current_section["content"]:
                    sections.append(current_section)
                current_section = {"heading": text, "content": []}
            else:
                current_section["content"].append(text)
            
            full_text += text + "\n"

        # Add last section
        if current_section["content"]:
            sections.append(current_section)

        return {
            "full_text": full_text,
            "sections": sections,
            "total_sections": len(sections),
            "file_type": "docx"
        }

    def parse_json(self, file_path: str) -> Dict[str, Any]:
        """Parse JSON file containing pre-parsed PRD data."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # If JSON already has the expected structure, return it
        if isinstance(data, dict):
            # Extract full_text if available, otherwise create from content
            full_text = data.get('full_text', '')
            
            # If no full_text but has sections/content, construct it
            if not full_text:
                if 'sections' in data:
                    full_text = "\n\n".join(
                        f"{s.get('heading', '')}\n{' '.join(s.get('content', []))}"
                        for s in data.get('sections', [])
                    )
                elif 'content' in data:
                    full_text = data.get('content')
                elif 'text' in data:
                    full_text = data.get('text')
                else:
                    # Fallback: stringify the entire JSON
                    full_text = json.dumps(data, indent=2)
            
            result = {
                "full_text": full_text,
                "file_type": "json",
                **data  # Include all original data
            }
            
            return result
        else:
            # If JSON is not a dict, treat it as text
            return {
                "full_text": json.dumps(data, indent=2),
                "file_type": "json"
            }
    
    def parse_text(self, content: str) -> Dict[str, Any]:
        """Parse raw text content."""
        lines = content.split("\n")
        sections = []
        current_section = {"heading": None, "content": []}

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Heuristic: Lines that are short and end without punctuation might be headings
            if len(line) < 100 and not line.endswith((".", ",", ";", ":")):
                if current_section["content"]:
                    sections.append(current_section)
                current_section = {"heading": line, "content": []}
            else:
                current_section["content"].append(line)

        if current_section["content"]:
            sections.append(current_section)

        return {
            "full_text": content,
            "sections": sections,
            "total_sections": len(sections),
            "file_type": "text"
        }

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """Parse file based on extension."""
        path = Path(file_path)
        extension = path.suffix.lower()

        if extension == ".pdf":
            return self.parse_pdf(file_path)
        elif extension in [".docx", ".doc"]:
            return self.parse_docx(file_path)
        elif extension == ".json":
            return self.parse_json(file_path)
        elif extension in [".txt", ".md"]:
            with open(file_path, "r", encoding="utf-8") as f:
                return self.parse_text(f.read())
        else:
            raise ValueError(f"Unsupported file format: {extension}")

    def _detect_priority(self, text: str) -> TestCasePriority:
        """Detect priority from text content."""
        text_lower = text.lower()
        for priority, keywords in self.priority_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return priority
        return TestCasePriority.MEDIUM

    def _extract_acceptance_criteria(self, text: str) -> List[str]:
        """Extract acceptance criteria from text."""
        criteria = []
        
        # Look for common acceptance criteria patterns
        patterns = [
            r"(?:Given|When|Then)\s+.+",  # BDD format
            r"(?:AC|Acceptance Criteria)[\s:]+(.+)",
            r"(?:Should|Must|Shall)\s+.+",
            r"(?:•|●|-|\*|\d+\.)\s*(.+)",  # Bullet points
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                if isinstance(matches[0], str):
                    criteria.extend(matches)
                else:
                    criteria.extend([m[0] if isinstance(m, tuple) else m for m in matches])

        return list(set(criteria))[:10]  # Limit and deduplicate

    def _categorize_requirement(self, text: str) -> str:
        """Categorize requirement based on content."""
        text_lower = text.lower()
        
        categories = {
            "authentication": ["login", "logout", "password", "auth", "sign in", "sign up", "register"],
            "user_interface": ["display", "show", "ui", "screen", "button", "input", "form"],
            "data_validation": ["valid", "invalid", "format", "required", "optional", "error"],
            "navigation": ["navigate", "redirect", "link", "menu", "tab", "page"],
            "security": ["secure", "encrypt", "permission", "access", "role"],
            "performance": ["fast", "load", "response time", "performance"],
            "integration": ["api", "integrate", "connect", "sync", "external"],
            "notification": ["notify", "alert", "email", "message", "notification"],
            "search": ["search", "filter", "sort", "find"],
            "payment": ["pay", "payment", "checkout", "cart", "order"],
        }

        for category, keywords in categories.items():
            if any(kw in text_lower for kw in keywords):
                return category

        return "general"

    def extract_requirements(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract structured requirements from parsed document data."""
        requirements = []
        full_text = parsed_data.get("full_text", "")
        sections = parsed_data.get("sections", [])

        req_counter = 1

        # Process sections
        for section in sections:
            heading = section.get("heading", "")
            content = " ".join(section.get("content", []))

            if not content:
                continue

            # Look for requirement IDs in content
            found_req_id = None
            for pattern in self.requirement_patterns:
                match = re.search(pattern, heading + " " + content, re.IGNORECASE)
                if match:
                    found_req_id = match.group()
                    break

            # Create requirement entry
            if heading or len(content) > 50:  # Only process meaningful content
                requirement = {
                    "requirement_id": found_req_id or f"REQ-{req_counter:03d}",
                    "title": heading if heading else content[:100] + "..." if len(content) > 100 else content,
                    "description": content,
                    "category": self._categorize_requirement(heading + " " + content),
                    "priority": self._detect_priority(heading + " " + content),
                    "acceptance_criteria": self._extract_acceptance_criteria(content),
                }
                requirements.append(requirement)
                req_counter += 1

        # If no sections found, try to extract from full text
        if not requirements and full_text:
            # Split by common delimiters
            paragraphs = re.split(r"\n\s*\n", full_text)
            for para in paragraphs:
                para = para.strip()
                if len(para) > 50:  # Meaningful content
                    requirements.append({
                        "requirement_id": f"REQ-{req_counter:03d}",
                        "title": para[:100] + "..." if len(para) > 100 else para,
                        "description": para,
                        "category": self._categorize_requirement(para),
                        "priority": self._detect_priority(para),
                        "acceptance_criteria": self._extract_acceptance_criteria(para),
                    })
                    req_counter += 1

        return requirements

    def get_document_summary(self, parsed_data: Dict[str, Any]) -> str:
        """Generate a summary of the document for context."""
        full_text = parsed_data.get("full_text", "")
        
        # Take first 2000 characters as preview/summary
        summary = full_text[:2000]
        if len(full_text) > 2000:
            summary += "..."
        
        return summary
