import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# --- Use an absolute path for the database file ---
# This ensures the app and init_db.py use the same database
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATABASE_URL = f"sqlite:///{os.path.join(PROJECT_ROOT, 'mcq_test.db')}"
# ----------------------------------------------------

engine = create_engine(
    settings.DATABASE_URL, 
    # For SQLite, connect_args is needed. It's ignored by other databases.
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base() 