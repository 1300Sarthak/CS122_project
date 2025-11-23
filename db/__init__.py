from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from db.models import Base
import os

# Database file path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'budget.db')

# Create engine
engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)

# Create session factory
SessionLocal = scoped_session(sessionmaker(bind=engine, autocommit=False, autoflush=False))


def init_db():
    """Initialize database and create tables."""
    Base.metadata.create_all(bind=engine)


def get_session():
    """Get a database session."""
    return SessionLocal()


def close_session():
    """Close the current session."""
    SessionLocal.remove()

