# Pydantic schemas for API request validation and response serialization
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum
from typing import Optional
from datetime import datetime as dt


class TaskStatus(str, Enum):
    """Task status enum for schema validation"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskCreate(BaseModel):
    """Schema for creating a new task (POST request body)"""
    title: str = Field(..., min_length=1, max_length=255, description="Task title")
    description: str = Field(default="", max_length=1000, description="Task description")
    status: Optional[TaskStatus] = Field(default=None, description="Initial task status")
    due_date: Optional[str] = Field(None, description="ISO 8601 date string (YYYY-MM-DD) - Feature 1")
    tags: Optional[str] = Field(None, description="Comma-separated tags (max 10, 1-50 chars each) - Feature 2")
    
    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v):
        """Validate due_date is valid ISO 8601 format"""
        if v is None:
            return v
        try:
            dt.fromisoformat(v)
            return v
        except (ValueError, TypeError):
            raise ValueError('due_date must be ISO 8601 format (YYYY-MM-DD)')
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        """Validate and normalize tags"""
        if not v:
            return ""
        
        # Split and clean
        tag_list = [t.strip() for t in v.split(",") if t.strip()]
        
        # Validate count
        if len(tag_list) > 10:
            raise ValueError('Maximum 10 tags per task')
        
        # Validate each tag length
        for tag in tag_list:
            if len(tag) < 1 or len(tag) > 50:
                raise ValueError(f'Tag "{tag}" must be 1-50 characters')
        
        # Remove duplicates and rejoin
        return ", ".join(sorted(set(tag_list)))


class TaskUpdate(BaseModel):
    """Schema for partial task updates (PATCH/PUT request body)"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[TaskStatus] = Field(None)
    due_date: Optional[str] = Field(None, description="ISO 8601 date string (YYYY-MM-DD) - Feature 1")
    tags: Optional[str] = Field(None, description="Comma-separated tags - Feature 2")
    
    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v):
        """Validate due_date is valid ISO 8601 format"""
        if v is None:
            return v
        try:
            dt.fromisoformat(v)
            return v
        except (ValueError, TypeError):
            raise ValueError('due_date must be ISO 8601 format (YYYY-MM-DD)')
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        """Validate and normalize tags"""
        if not v:
            return ""
        
        tag_list = [t.strip() for t in v.split(",") if t.strip()]
        
        if len(tag_list) > 10:
            raise ValueError('Maximum 10 tags per task')
        
        for tag in tag_list:
            if len(tag) < 1 or len(tag) > 50:
                raise ValueError(f'Tag "{tag}" must be 1-50 characters')
        
        return ", ".join(sorted(set(tag_list)))


class TaskRead(BaseModel):
    """Schema for API responses when returning task data"""
    id: int
    title: str
    description: str
    status: TaskStatus
    due_date: Optional[str] = None
    tags: str = ""
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # Allow creation from SQLModel instances
