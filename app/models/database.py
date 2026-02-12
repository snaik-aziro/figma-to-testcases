"""Database models for the QA Test Generator."""

from datetime import datetime
from typing import Optional
from enum import Enum as PyEnum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    Enum,
    Boolean,
    Float,
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class TestCaseType(str, PyEnum):
    """Test case type enumeration."""

    FUNCTIONAL = "functional"
    VISUAL = "visual"
    ACCESSIBILITY = "accessibility"
    EDGE_CASE = "edge_case"
    INTEGRATION = "integration"


class TestCasePriority(str, PyEnum):
    """Test case priority enumeration."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ProcessingStatus(str, PyEnum):
    """Processing status enumeration."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Project(Base):
    """Project model representing a test generation project."""

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    figma_file_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING)

    # Relationships
    screens = relationship("Screen", back_populates="project", cascade="all, delete-orphan")
    requirements = relationship("Requirement", back_populates="project", cascade="all, delete-orphan")
    test_cases = relationship("TestCase", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")


class Screen(Base):
    """Screen model representing a Figma screen/frame."""

    __tablename__ = "screens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    figma_node_id = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    screen_type = Column(String(100), nullable=True)
    components_data = Column(JSON, nullable=True)  # Extracted component tree
    screen_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="screens")
    components = relationship("Component", back_populates="screen", cascade="all, delete-orphan")
    test_cases = relationship("TestCase", back_populates="screen")


class Component(Base):
    """Component model representing a UI component from Figma."""

    __tablename__ = "components"

    id = Column(Integer, primary_key=True, autoincrement=True)
    screen_id = Column(Integer, ForeignKey("screens.id"), nullable=False)
    figma_node_id = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    component_type = Column(String(100), nullable=False)  # button, input, text, etc.
    properties = Column(JSON, nullable=True)  # Component properties
    position = Column(JSON, nullable=True)  # x, y, width, height
    parent_id = Column(Integer, ForeignKey("components.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    screen = relationship("Screen", back_populates="components")
    children = relationship("Component", backref="parent", remote_side=[id])


class Document(Base):
    """Document model representing uploaded requirement documents."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, docx
    content = Column(Text, nullable=True)  # Extracted text content
    parsed_data = Column(JSON, nullable=True)  # Structured parsed content
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="documents")
    requirements = relationship("Requirement", back_populates="document")


class Requirement(Base):
    """Requirement model representing extracted requirements."""

    __tablename__ = "requirements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    requirement_id = Column(String(100), nullable=True)  # REQ-001, etc.
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    priority = Column(Enum(TestCasePriority), default=TestCasePriority.MEDIUM)
    acceptance_criteria = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="requirements")
    document = relationship("Document", back_populates="requirements")
    test_cases = relationship(
        "TestCase", secondary="test_case_requirements", back_populates="requirements"
    )


class TestCase(Base):
    """Test case model representing generated test cases."""

    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    screen_id = Column(Integer, ForeignKey("screens.id"), nullable=True)
    test_id = Column(String(100), nullable=False)  # TC-001, etc.
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    test_type = Column(Enum(TestCaseType), default=TestCaseType.FUNCTIONAL)
    priority = Column(Enum(TestCasePriority), default=TestCasePriority.MEDIUM)
    preconditions = Column(JSON, nullable=True)
    test_steps = Column(JSON, nullable=False)  # List of steps
    expected_results = Column(JSON, nullable=False)
    test_data = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)
    confidence__score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="test_cases")
    screen = relationship("Screen", back_populates="test_cases")
    requirements = relationship(
        "Requirement", secondary="test_case_requirements", back_populates="test_cases"
    )


class TestCaseRequirement(Base):
    """Association table for test case and requirement many-to-many relationship."""

    __tablename__ = "test_case_requirements"

    test_case_id = Column(Integer, ForeignKey("test_cases.id"), primary_key=True)
    requirement_id = Column(Integer, ForeignKey("requirements.id"), primary_key=True)
