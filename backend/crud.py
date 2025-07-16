from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import datetime
from . import models, schemas

def get_student_by_email(db: Session, email: str):
    """
    Performs a case-insensitive and whitespace-insensitive lookup for a student by email.
    """
    search_email = email.lower().strip()
    return db.query(models.Student).filter(func.lower(models.Student.email) == search_email).first()

def get_questions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Question).offset(skip).limit(limit).all()

def start_quiz_attempt(db: Session, student_id: int):
    db_result = models.Result(
        student_id=student_id,
        quiz_started_at=datetime.utcnow()
    )
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return db_result

def update_student_result(db: Session, result_id: int, score: int, time_taken: int):
    db_result = db.query(models.Result).filter(models.Result.id == result_id).first()
    if db_result:
        db_result.score = score
        db_result.time_taken = time_taken
        db_result.submitted_at = datetime.utcnow()
        db.commit()
        db.refresh(db_result)
    return db_result

def get_all_students_with_results(db: Session):
    return db.query(models.Student).options(joinedload(models.Student.result)).all() 