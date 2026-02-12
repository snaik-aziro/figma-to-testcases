"""Pydantic schemas for API request/response models."""

from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field

from app.models.database import TestCaseType, TestCasePriority, ProcessingStatus


# ============= Project Schemas =============

class ProjectCreate(BaseModel):
    """Schema for creating a new project."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    figma_file_id: Optional[str] = None


class ProjectResponse(BaseModel):
    """Schema for project response."""

    id: int
    name: str
    description: Optional[str]
    figma_file_id: Optional[str]
    status: ProcessingStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============= Figma Schemas =============

class FigmaFileRequest(BaseModel):
    """Schema for Figma file processing request."""

    file_id: str = Field(..., description="Figma file ID or URL")


class ComponentData(BaseModel):
    """Schema for extracted component data."""

    node_id: str
    name: str
    component_type: str
    relevance_score: Optional[float] = None
    properties: Optional[dict] = None
    position: Optional[dict] = None
    children: Optional[List["ComponentData"]] = None


class ScreenData(BaseModel):
    """Schema for extracted screen data."""

    node_id: str
    name: str
    screen_type: Optional[str] = None
    components: List[ComponentData] = []
    metadata: Optional[dict] = None


class FigmaExtractionResponse(BaseModel):
    """Schema for Figma extraction response."""

    file_id: str
    file_name: str
    screens: List[ScreenData]
    total_screens: int
    total_components: int


# ============= Document Schemas =============

class DocumentUploadResponse(BaseModel):
    """Schema for document upload response."""

    id: int
    filename: str
    file_type: str
    content_preview: Optional[str] = None
    requirements_count: int

    class Config:
        from_attributes = True


class RequirementResponse(BaseModel):
    """Schema for requirement response."""

    id: int
    requirement_id: Optional[str]
    title: str
    description: Optional[str]
    category: Optional[str]
    priority: TestCasePriority
    acceptance_criteria: Optional[List[str]] = None

    class Config:
        from_attributes = True


# ============= Test Case Schemas =============

class TestStep(BaseModel):
    """Schema for a test step."""

    step_number: int
    action: str
    expected_result: str
    test_data: Optional[str] = None


class TestCaseCreate(BaseModel):
    """Schema for creating a test case."""

    title: str
    description: Optional[str] = None
    test_type: TestCaseType = TestCaseType.FUNCTIONAL
    priority: TestCasePriority = TestCasePriority.MEDIUM
    preconditions: Optional[List[str]] = None
    test_steps: List[TestStep]
    expected_results: List[str]
    test_data: Optional[dict] = None
    tags: Optional[List[str]] = None


class TestCaseResponse(BaseModel):
    """Schema for test case response."""

    id: int
    test_id: str
    title: str
    description: Optional[str]
    test_type: TestCaseType
    priority: TestCasePriority
    preconditions: Optional[List[str]]
    test_steps: List[dict]
    expected_results: List[str]
    test_data: Optional[dict]
    tags: Optional[List[str]]
    confidence_score: Optional[float]
    screen_name: Optional[str] = None
    requirement_ids: List[str] = []
    created_at: datetime

    class Config:
        from_attributes = True


class TestGenerationRequest(BaseModel):
    """Schema for test generation request."""

    project_id: int
    screen_ids: Optional[List[int]] = None  # If None, generate for all screens
    test_types: Optional[List[TestCaseType]] = None  # If None, generate all types
    include_requirements: bool = True


class TestGenerationResponse(BaseModel):
    """Schema for test generation response."""

    project_id: int
    total_test_cases: int
    test_cases_by_type: dict
    generation_time_seconds: float
    coverage_summary: dict


# ============= Traceability Schemas =============

class TraceabilityItem(BaseModel):
    """Schema for traceability matrix item."""

    requirement_id: str
    requirement_title: str
    test_case_ids: List[str]
    coverage_status: str  # covered, partial, uncovered


class TraceabilityMatrix(BaseModel):
    """Schema for traceability matrix response."""

    project_id: int
    total_requirements: int
    covered_requirements: int
    coverage_percentage: float
    items: List[TraceabilityItem]


# ============= Health Check =============

class HealthCheck(BaseModel):
    """Schema for health check response."""

    status: str = "healthy"
    version: str = "0.1.0"
    database: str = "connected"
    figma_api: str = "available"
    llm_api: str = "available"


# Forward reference resolution
ComponentData.model_rebuild()
