# Database session initialization and dependency injection for SQLModel
from sqlmodel import SQLModel, create_engine, Session
from app.core.config import settings

# Create SQLite engine with check_same_thread=False for testing flexibility
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    echo=False  # Set to True for SQL debug logging
)


def create_db_and_tables():
    """Create all database tables at application startup"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependency injection function to provide a database session to endpoints"""
    with Session(engine) as session:
        yield session
