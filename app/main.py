# Main FastAPI application setup and configuration
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import create_db_and_tables
from app.api.v1 import api_router

# Create FastAPI application instance with metadata
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A RESTful API for managing tasks with status workflow validation"
)

# Configure CORS to allow frontend requests from any origin (suitable for local development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables at startup
@app.on_event("startup")
def on_startup():
    """Initialize database tables when application starts"""
    create_db_and_tables()

# Include all v1 API routes with prefix /api/v1
app.include_router(api_router, prefix=settings.api_prefix)
