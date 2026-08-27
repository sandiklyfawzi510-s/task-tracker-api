# Tests for health check endpoint
from fastapi.testclient import TestClient


def test_health_check(client):
    """Test that health check endpoint returns 200 and correct response structure"""
    response = client.get("/api/v1/health")
    
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert "message" in response.json()
