import logging
import os
import sys
from sqlalchemy import create_engine, func, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, Session, relationship, declarative_base

# --- Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Hardcoded Database URL for the Azure Test DB
DATABASE_URL = "postgresql+psycopg2://kaaraadmin:Ahimsa0210@mcq-test-db-server.postgres.database.azure.com:5432/postgres"

TEST_USERS = [
    'siddharth.g@kaaratech.com',
    'rohan.s@kaaratech.com'
]

# --- Self-Contained Model Definitions ---
# This avoids importing the main app's config
Base = declarative_base()

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    roll_no = Column(String, unique=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    cgpa = Column(Float)
    tenth_percentage = Column(Float)
    twelfth_percentage = Column(Float)
    result = relationship("Result", back_populates="student", uselist=False, cascade="all, delete-orphan")

class Result(Base):
    __tablename__ = "results"
    id = Column(Integer, primary_key=True, index=True)
    score = Column(Integer, nullable=True)
    time_taken = Column(Integer, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    quiz_started_at = Column(DateTime)
    student_id = Column(Integer, ForeignKey("students.id"))
    student = relationship("Student", back_populates="result")


def get_student_by_email_local(db: Session, email: str):
    """A local, self-contained version of the CRUD function."""
    search_email = email.lower().strip()
    return db.query(Student).filter(func.lower(Student.email) == search_email).first()

def reset_test_users():
    """
    Connects to the specific Azure database and deletes the quiz results
    for the specified test users to allow them to retake the quiz.
    This script is self-contained and does not rely on the app's config.
    """
    logger.info(f"Connecting to the database...")
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db: Session = SessionLocal()
    logger.info("Starting test user reset script...")
    
    try:
        for email in TEST_USERS:
            student = get_student_by_email_local(db, email=email)
            if not student:
                logger.warning(f"User '{email}' not found. Skipping.")
                continue

            if student.result:
                logger.info(f"Found result for {email} (Result ID: {student.result.id}). Deleting...")
                db.delete(student.result)
                db.commit()
                logger.info(f"Successfully deleted quiz data for user: {email}")
            else:
                logger.info(f"No quiz data to delete for user: {email}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        db.rollback()
    finally:
        db.close()
        logger.info("Script finished.")

if __name__ == "__main__":
    reset_test_users()
