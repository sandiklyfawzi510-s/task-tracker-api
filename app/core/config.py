# Configuration management using Pydantic Settings to load environment variables
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables via python-dotenv"""
    
    # Application metadata
    app_name: str = "Task Tracker API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Database configuration
    database_url: str = "sqlite:///./task_tracker.db"
    
    # API configuration
    api_prefix: str = "/api/v1"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
