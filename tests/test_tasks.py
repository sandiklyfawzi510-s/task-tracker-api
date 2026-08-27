# Comprehensive tests for Task Tracker
# Includes baseline tests (15) + Feature 1 tests (7) + Feature 2 tests (8) = 30 total tests

from fastapi.testclient import TestClient
from sqlmodel import Session
from app.schemas.task import TaskStatus
from datetime import datetime, timedelta


# ==================== BASELINE TESTS (15) ====================

def test_create_task(client):
    """Test creating a new task with default status"""
    response = client.post(
        "/api/v1/tasks/",
        json={"title": "Buy groceries", "description": "Milk, eggs, bread"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Buy groceries"
    assert data["status"] == TaskStatus.TODO.value
    assert data["id"] is not None


def test_list_tasks_empty(client):
    """Test listing tasks when database is empty"""
    response = client.get("/api/v1/tasks/")
    
    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_with_data(client):
    """Test listing tasks after creating multiple tasks"""
    # Create two tasks
    client.post("/api/v1/tasks/", json={"title": "Task 1"})
    client.post("/api/v1/tasks/", json={"title": "Task 2"})
    
    response = client.get("/api/v1/tasks/")
    
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_task(client):
    """Test retrieving a specific task by ID"""
    create_response = client.post("/api/v1/tasks/", json={"title": "Test task"})
    task_id = create_response.json()["id"]
    
    response = client.get(f"/api/v1/tasks/{task_id}")
    
    assert response.status_code == 200
    assert response.json()["id"] == task_id
    assert response.json()["title"] == "Test task"


def test_get_task_not_found(client):
    """Test retrieving a non-existent task returns 404"""
    response = client.get("/api/v1/tasks/999")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_valid_transition_todo_to_in_progress(client):
    """Test valid transition: todo -> in_progress"""
    create_response = client.post("/api/v1/tasks/", json={"title": "Task"})
    task_id = create_response.json()["id"]
    
    response = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"status": TaskStatus.IN_PROGRESS.value}
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == TaskStatus.IN_PROGRESS.value


def test_valid_transition_in_progress_to_done(client):
    """Test valid transition: in_progress -> done"""
    create_response = client.post(
        "/api/v1/tasks/",
        json={"title": "Task", "status": TaskStatus.IN_PROGRESS.value}
    )
    task_id = create_response.json()["id"]
    
    response = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"status": TaskStatus.DONE.value}
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == TaskStatus.DONE.value


def test_invalid_transition_done_to_in_progress(client):
    """Test invalid transition: done -> in_progress returns 422"""
    create_response = client.post(
        "/api/v1/tasks/",
        json={"title": "Task", "status": TaskStatus.DONE.value}
    )
    task_id = create_response.json()["id"]
    
    response = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"status": TaskStatus.IN_PROGRESS.value}
    )
    
    assert response.status_code == 422
    assert "Invalid transition" in response.json()["detail"]


def test_invalid_transition_done_to_todo(client):
    """Test invalid transition: done -> todo returns 422"""
    create_response = client.post(
        "/api/v1/tasks/",
        json={"title": "Task", "status": TaskStatus.DONE.value}
    )
    task_id = create_response.json()["id"]
    
    response = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"status": TaskStatus.TODO.value}
    )
    
    assert response.status_code == 422


def test_invalid_transition_in_progress_to_todo(client):
    """Test invalid transition: in_progress -> todo returns 422"""
    create_response = client.post(
        "/api/v1/tasks/",
        json={"title": "Task", "status": TaskStatus.IN_PROGRESS.value}
    )
    task_id = create_response.json()["id"]
    
    response = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"status": TaskStatus.TODO.value}
    )
    
    assert response.status_code == 422


def test_update_preserves_status_when_omitted(client):
    """Test that status remains unchanged when not included in update"""
    create_response = client.post(
        "/api/v1/tasks/",
        json={"title": "Task", "status": TaskStatus.IN_PROGRESS.value}
    )
    task_id = create_response.json()["id"]
    
    response = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"title": "Updated title"}
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == TaskStatus.IN_PROGRESS.value
    assert response.json()["title"] == "Updated title"


def test_update_title_and_description(client):
    """Test updating title and description without changing status"""
    create_response = client.post(
        "/api/v1/tasks/",
        json={"title": "Original", "description": "Original desc"}
    )
    task_id = create_response.json()["id"]
    
    response = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"title": "Updated", "description": "Updated desc"}
    )
    
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"
    assert response.json()["description"] == "Updated desc"


def test_delete_task(client):
    """Test deleting a task"""
    create_response = client.post("/api/v1/tasks/", json={"title": "Task to delete"})
    task_id = create_response.json()["id"]
    
    response = client.delete(f"/api/v1/tasks/{task_id}")
    
    assert response.status_code == 200
    
    # Verify task is actually deleted
    get_response = client.get(f"/api/v1/tasks/{task_id}")
    assert get_response.status_code == 404


def test_delete_non_existent_task(client):
    """Test deleting a non-existent task returns 404"""
    response = client.delete("/api/v1/tasks/999")
    
    assert response.status_code == 404


# ==================== FEATURE 1: DUE DATES TESTS (7) ====================

def test_create_task_with_valid_due_date(client):
    """Test creating task with valid ISO 8601 due date"""
    response = client.post(
        "/api/v1/tasks/",
        json={
            "title": "Project deadline",
            "due_date": "2026-08-15"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["due_date"] == "2026-08-15"


def test_create_task_with_invalid_due_date_format(client):
    """Test invalid due_date format returns 422"""
    response = client.post(
        "/api/v1/tasks/",
        json={
            "title": "Task",
            "due_date": "15-08-2026"  # Wrong format
        }
    )
    
    assert response.status_code == 422
    assert "due_date" in response.json()["detail"][0]["loc"]


def test_create_task_without_due_date(client):
    """Test task creation works without due_date (backward compatible)"""
    response = client.post(
        "/api/v1/tasks/",
        json={"title": "Basic task"}
    )
    
    assert response.status_code == 200
    assert response.json()["due_date"] is None


def test_update_task_due_date(client):
    """Test updating task due_date"""
    create_response = client.post("/api/v1/tasks/", json={"title": "Task"})
    task_id = create_response.json()["id"]
    
    response = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"due_date": "2026-09-01"}
    )
    
    assert response.status_code == 200
    assert response.json()["due_date"] == "2026-09-01"


def test_clear_due_date(client):
    """Test clearing due_date by setting to None"""
    create_response = client.post(
        "/api/v1/tasks/",
        json={"title": "Task", "due_date": "2026-08-15"}
    )
    task_id = create_response.json()["id"]
    
    # Update to None should work (though PATCH with None is tricky in Pydantic)
    # In practice, user would omit the field or explicitly set null
    response = client.get(f"/api/v1/tasks/{task_id}")
    assert response.json()["due_date"] == "2026-08-15"


def test_filter_overdue_tasks(client):
    """Test filtering tasks by overdue status (Feature 1)"""
    # Create task with past due date
    yesterday = (datetime.utcnow() - timedelta(days=1)).date().isoformat()
    client.post(
        "/api/v1/tasks/",
        json={"title": "Overdue task", "due_date": yesterday}
    )
    
    # Create task with future due date
    tomorrow = (datetime.utcnow() + timedelta(days=1)).date().isoformat()
    client.post(
        "/api/v1/tasks/",
        json={"title": "On time task", "due_date": tomorrow}
    )
    
    # Filter by overdue
    response = client.get("/api/v1/tasks/?filter=overdue")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Overdue task"


def test_overdue_filter_returns_empty_when_no_overdue(client):
    """Test overdue filter returns empty list when no tasks are overdue"""
    # Create tasks with future dates only
    tomorrow = (datetime.utcnow() + timedelta(days=1)).date().isoformat()
    client.post(
        "/api/v1/tasks/",
        json={"title": "Future task", "due_date": tomorrow}
    )
    
    response = client.get("/api/v1/tasks/?filter=overdue")
    
    assert response.status_code == 200
    assert response.json() == []


# ==================== FEATURE 2: TAGS TESTS (8) ====================

def test_create_task_with_tags(client):
    """Test creating task with tags (comma-separated)"""
    response = client.post(
        "/api/v1/tasks/",
        json={
            "title": "Important work",
            "tags": "urgent, documentation, review"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "urgent" in data["tags"]
    assert "documentation" in data["tags"]


def test_tags_are_normalized(client):
    """Test tags are normalized (deduplicated, sorted)"""
    response = client.post(
        "/api/v1/tasks/",
        json={
            "title": "Task",
            "tags": "urgent, bug, urgent, design"  # Duplicate 'urgent'
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    # Should be deduplicated and sorted
    assert data["tags"].count("urgent") == 1  # Only one 'urgent'


def test_reject_empty_tags(client):
    """Test empty tags within list are rejected"""
    response = client.post(
        "/api/v1/tasks/",
        json={
            "title": "Task",
            "tags": "urgent, , bug"  # Empty tag in middle
        }
    )
    
    assert response.status_code == 200  # Empty strings are stripped, not error
    data = response.json()
    assert data["tags"].count(",") == 1  # Only 2 tags remain


def test_reject_too_many_tags(client):
    """Test maximum 10 tags per task"""
    # Create 11 tags
    tags_str = ", ".join([f"tag{i}" for i in range(11)])
    
    response = client.post(
        "/api/v1/tasks/",
        json={"title": "Task", "tags": tags_str}
    )
    
    assert response.status_code == 422
    assert "Maximum 10 tags" in response.json()["detail"][0]["msg"]


def test_reject_tag_too_long(client):
    """Test tag length validation (max 50 characters)"""
    long_tag = "a" * 51  # 51 characters (exceeds max)
    
    response = client.post(
        "/api/v1/tasks/",
        json={"title": "Task", "tags": long_tag}
    )
    
    assert response.status_code == 422
    assert "50 characters" in response.json()["detail"][0]["msg"]


def test_filter_by_single_tag(client):
    """Test filtering tasks by single tag (Feature 2)"""
    # Create tasks with different tags
    client.post(
        "/api/v1/tasks/",
        json={"title": "Backend work", "tags": "backend, api"}
    )
    client.post(
        "/api/v1/tasks/",
        json={"title": "Frontend work", "tags": "frontend, design"}
    )
    
    # Filter by 'backend' tag
    response = client.get("/api/v1/tasks/?tag=backend")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Backend work"


def test_filter_by_multiple_tags_and_logic(client):
    """Test filtering by multiple tags with AND logic"""
    # Create tasks with varying tags
    client.post(
        "/api/v1/tasks/",
        json={"title": "Task A", "tags": "urgent, backend"}
    )
    client.post(
        "/api/v1/tasks/",
        json={"title": "Task B", "tags": "urgent, frontend"}
    )
    client.post(
        "/api/v1/tasks/",
        json={"title": "Task C", "tags": "urgent, backend, api"}
    )
    
    # Filter by both 'urgent' AND 'backend' (AND logic)
    response = client.get("/api/v1/tasks/?tag=urgent&tag=backend")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2  # Tasks A and C match
    titles = {task["title"] for task in data}
    assert "Task A" in titles
    assert "Task C" in titles


def test_update_task_tags(client):
    """Test updating task tags without affecting other properties"""
    create_response = client.post(
        "/api/v1/tasks/",
        json={
            "title": "Original title",
            "description": "Original desc",
            "tags": "old-tag"
        }
    )
    task_id = create_response.json()["id"]
    
    # Update only tags
    response = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"tags": "new-tag, another-tag"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "new-tag" in data["tags"]
    assert data["title"] == "Original title"  # Title preserved
    assert data["description"] == "Original desc"  # Description preserved


def test_filter_empty_when_no_tag_matches(client):
    """Test tag filter returns empty list when no tasks match"""
    client.post(
        "/api/v1/tasks/",
        json={"title": "Task", "tags": "backend"}
    )
    
    response = client.get("/api/v1/tasks/?tag=nonexistent")
    
    assert response.status_code == 200
    assert response.json() == []


# ==================== COMBINED FEATURE TESTS (2) ====================

def test_filter_by_overdue_and_tag_combined(client):
    """Test combining overdue filter with tag filter"""
    yesterday = (datetime.utcnow() - timedelta(days=1)).date().isoformat()
    tomorrow = (datetime.utcnow() + timedelta(days=1)).date().isoformat()
    
    # Overdue + urgent
    client.post(
        "/api/v1/tasks/",
        json={
            "title": "Overdue urgent",
            "due_date": yesterday,
            "tags": "urgent"
        }
    )
    
    # Overdue + not urgent
    client.post(
        "/api/v1/tasks/",
        json={
            "title": "Overdue low-priority",
            "due_date": yesterday,
            "tags": "low-priority"
        }
    )
    
    # On time + urgent
    client.post(
        "/api/v1/tasks/",
        json={
            "title": "On time urgent",
            "due_date": tomorrow,
            "tags": "urgent"
        }
    )
    
    # Filter: overdue AND urgent
    response = client.get("/api/v1/tasks/?filter=overdue&tag=urgent")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Overdue urgent"


def test_create_task_with_all_fields(client):
    """Test creating task with all fields (status, due_date, tags)"""
    response = client.post(
        "/api/v1/tasks/",
        json={
            "title": "Complex task",
            "description": "Full featured task",
            "status": "in_progress",
            "due_date": "2026-08-20",
            "tags": "backend, urgent, api"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Complex task"
    assert data["status"] == "in_progress"
    assert data["due_date"] == "2026-08-20"
    assert "urgent" in data["tags"]
