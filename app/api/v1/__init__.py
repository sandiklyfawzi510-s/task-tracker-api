# API v1 router registration point
from fastapi import APIRouter
from app.api.v1.endpoints import health, tasks

# Create main v1 router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router)
api_router.include_router(tasks.router)
