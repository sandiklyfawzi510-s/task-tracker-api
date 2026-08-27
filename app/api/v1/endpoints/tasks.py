# Task endpoints implementing CRUD operations per ADR-0001
# Enhanced with Feature 1 (Due Dates) and Feature 2 (Tags)
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import Optional, List
from app.db.session import get_session
from app.models.task import TaskTable
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskRead)
def create_task(
    task_create: TaskCreate,
    session: Session = Depends(get_session)
):
    """
    Create a new task.
    Request body: title (required), description (optional), status (optional, defaults to 'todo'),
                  due_date (optional, ISO 8601), tags (optional, comma-separated)
    Returns: Created task with ID and timestamps
    
    Feature 1: due_date field for deadline tracking
    Feature 2: tags field for task categorization
    """
    return TaskService.create_task(session, task_create)


@router.get("/", response_model=list[TaskRead])
def list_tasks(
    session: Session = Depends(get_session),
    filter: Optional[str] = Query(None, description="Filter type: 'overdue' for Feature 1"),
    tag: Optional[List[str]] = Query(None, description="Filter by tag(s) - AND logic for Feature 2")
):
    """
    List all tasks with optional filtering.
    
    Query Parameters:
    - filter: Optional filter type
      * filter=overdue: Returns only tasks with due_date < today (Feature 1)
    - tag: Optional tag filter (can be repeated)
      * tag=urgent&tag=design: Returns tasks having ALL selected tags (Feature 2)
    
    Returns: Array of all tasks (or filtered subset) in the database
    
    Examples:
    - GET /tasks → All tasks
    - GET /tasks?filter=overdue → Overdue tasks only
    - GET /tasks?tag=urgent → Tasks with 'urgent' tag
    - GET /tasks?tag=urgent&tag=design → Tasks with both 'urgent' AND 'design' tags
    - GET /tasks?filter=overdue&tag=urgent → Overdue tasks with 'urgent' tag
    """
    # Apply status/overdue filter first
    tasks = TaskService.list_tasks_filtered(session, filter)
    
    # Apply tag filter (AND logic)
    tasks = TaskService.list_tasks_by_tag(tasks, tag)
    
    return tasks


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: int, session: Session = Depends(get_session)):
    """
    Get a specific task by ID.
    Returns: Task with matching ID or 404 if not found
    """
    return TaskService.get_task(session, task_id)


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    session: Session = Depends(get_session)
):
    """
    Partially update a task. Only provided fields are updated.
    Status transitions are validated per ADR-0001 transition rules.
    Invalid transitions return 422 Unprocessable Entity and leave task unchanged.
    
    Feature 1: Can update due_date field
    Feature 2: Can update tags field
    """
    return TaskService.update_task(session, task_id, task_update)


@router.delete("/{task_id}")
def delete_task(task_id: int, session: Session = Depends(get_session)):
    """
    Delete a task by ID.
    Returns: 204 No Content on success
    """
    TaskService.delete_task(session, task_id)
    return {"message": "Task deleted successfully"}
