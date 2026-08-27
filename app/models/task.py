# SQLModel task table definition for SQLite persistence
from sqlmodel import SQLModel, Field
from enum import Enum
from typing import Optional
from datetime import datetime


class TaskStatus(str, Enum):
    """Allowed task status values per ADR-0001"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskTable(SQLModel, table=True):
    """
    SQLite table model for task persistence.
    table=True tells SQLModel to create a database table for this model.
    
    Fields:
    - id: Primary key (auto-increment)
    - title: Task title (indexed for faster lookups)
    - description: Optional task details
    - status: Task status per ADR-0001 workflow
    - due_date: Optional ISO 8601 date string for deadline tracking (Feature 1)
    - tags: Comma-separated tag list for categorization (Feature 2)
    - created_at: Timestamp when task was created
    - updated_at: Timestamp of last update
    """
    __tablename__ = "tasks"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)  # Index for faster lookups
    description: str = ""
    status: TaskStatus = Field(default=TaskStatus.TODO)
    due_date: Optional[str] = Field(default=None, description="ISO 8601 date string (YYYY-MM-DD)")
    tags: str = Field(default="", description="Comma-separated tags for categorization")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
