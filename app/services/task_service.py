# Task service layer implementing transition validation per ADR-0001
from sqlmodel import Session, select
from app.models.task import TaskTable, TaskStatus
from app.schemas.task import TaskCreate, TaskUpdate
from fastapi import HTTPException
from datetime import datetime
from typing import Optional, List


# Transition map per ADR-0001: allowed status transitions
ALLOWED_TRANSITIONS = {
    TaskStatus.TODO: {TaskStatus.TODO, TaskStatus.IN_PROGRESS},
    TaskStatus.IN_PROGRESS: {TaskStatus.IN_PROGRESS, TaskStatus.DONE},
    TaskStatus.DONE: {TaskStatus.DONE},
}


class TaskService:
    """Service layer for task business logic including status transition validation"""
    
    @staticmethod
    def create_task(session: Session, task_create: TaskCreate) -> TaskTable:
        """Create a new task in the database"""
        db_task = TaskTable(
            title=task_create.title,
            description=task_create.description,
            status=task_create.status or TaskStatus.TODO,
            due_date=task_create.due_date,  # Feature 1: Due dates
            tags=task_create.tags or ""  # Feature 2: Tags
        )
        session.add(db_task)
        session.commit()
        session.refresh(db_task)
        return db_task
    
    @staticmethod
    def get_task(session: Session, task_id: int) -> TaskTable:
        """Retrieve a task by ID, raise 404 if not found"""
        task = session.get(TaskTable, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task
    
    @staticmethod
    def list_tasks(session: Session) -> list[TaskTable]:
        """Retrieve all tasks from the database"""
        statement = select(TaskTable)
        return session.exec(statement).all()
    
    @staticmethod
    def is_overdue(due_date: Optional[str]) -> bool:
        """
        Check if a task is overdue (due_date < today).
        Feature 1: Overdue detection for filtering.
        """
        if not due_date:
            return False
        try:
            due_dt = datetime.fromisoformat(due_date)
            return due_dt.date() < datetime.utcnow().date()
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def list_tasks_filtered(session: Session, filter_type: Optional[str] = None) -> list[TaskTable]:
        """
        List tasks with optional filtering.
        Feature 1: Supports filter='overdue' to show only overdue tasks.
        """
        tasks = TaskService.list_tasks(session)
        
        if filter_type == "overdue":
            return [t for t in tasks if TaskService.is_overdue(t.due_date)]
        
        return tasks
    
    @staticmethod
    def list_tasks_by_tag(tasks: list[TaskTable], tag_filters: Optional[List[str]] = None) -> list[TaskTable]:
        """
        Filter tasks by tags using AND logic.
        Feature 2: Task must have ALL selected tags to be included.
        """
        if not tag_filters:
            return tasks
        
        filtered = []
        for task in tasks:
            # Parse task tags
            task_tags = {t.strip() for t in task.tags.split(",") if t.strip()}
            
            # Check if task has all selected tags (AND logic)
            if all(tag in task_tags for tag in tag_filters):
                filtered.append(task)
        
        return filtered
    
    @staticmethod
    def validate_transition(current_status: TaskStatus, new_status: TaskStatus) -> bool:
        """
        Validate if a status transition is allowed per ADR-0001.
        Returns True if valid, raises HTTPException if invalid.
        """
        if new_status not in ALLOWED_TRANSITIONS[current_status]:
            allowed = ", ".join([s.value for s in ALLOWED_TRANSITIONS[current_status]])
            raise HTTPException(
                status_code=422,
                detail=f"Invalid transition from '{current_status.value}' to '{new_status.value}'. Allowed transitions: {allowed}"
            )
        return True
    
    @staticmethod
    def update_task(session: Session, task_id: int, task_update: TaskUpdate) -> TaskTable:
        """
        Update a task with validation. If status transition is invalid,
        raise 422 error before applying any changes (atomic validation).
        """
        db_task = TaskService.get_task(session, task_id)
        
        # Validate status transition first (before any mutations)
        if task_update.status and task_update.status != db_task.status:
            TaskService.validate_transition(db_task.status, task_update.status)
        
        # Apply updates after validation succeeds
        if task_update.title is not None:
            db_task.title = task_update.title
        if task_update.description is not None:
            db_task.description = task_update.description
        if task_update.status is not None:
            db_task.status = task_update.status
        if task_update.due_date is not None:  # Feature 1: Allow due_date update
            db_task.due_date = task_update.due_date
        if task_update.tags is not None:  # Feature 2: Allow tags update
            db_task.tags = task_update.tags
        
        session.add(db_task)
        session.commit()
        session.refresh(db_task)
        return db_task
    
    @staticmethod
    def delete_task(session: Session, task_id: int) -> None:
        """Delete a task from the database"""
        db_task = TaskService.get_task(session, task_id)
        session.delete(db_task)
        session.commit()
