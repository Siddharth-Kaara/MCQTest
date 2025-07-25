from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from datetime import datetime, timezone
import logging
import models, schemas, security

# Configure CRUD module logging
crud_logger = logging.getLogger("crud")

def create_student(db: Session, student: schemas.StudentCreate):
    try:
        crud_logger.info(f"Creating new student: {student.email}")
        hashed_password = security.get_password_hash(student.password)
        db_student = models.Student(
            roll_no=student.roll_no,
            full_name=student.full_name,
            email=student.email,
            hashed_password=hashed_password,
            cgpa=student.cgpa,
            tenth_percentage=student.tenth_percentage,
            twelfth_percentage=student.twelfth_percentage
        )
        db.add(db_student)
        db.commit()
        db.refresh(db_student)
        crud_logger.info(f"Student created successfully - ID: {db_student.id}")
        return db_student
    except Exception as e:
        crud_logger.error(f"Error creating student {student.email}: {str(e)}")
        db.rollback()
        raise

def get_student_by_email(db: Session, email: str):
    """
    Performs a case-insensitive and whitespace-insensitive lookup for a student by email.
    """
    try:
        original_email = email
        search_email = email.lower().strip() if email else ""
        
        crud_logger.info(f"Looking up student by email")
        crud_logger.debug(f"Original email: '{original_email}'")
        crud_logger.debug(f"Search email (normalized): '{search_email}'")
        
        if not search_email:
            crud_logger.warning("Empty email provided for lookup")
            return None
        
        # Perform database query
        student = db.query(models.Student).filter(func.lower(models.Student.email) == search_email).first()
        
        if student:
            crud_logger.info(f"Student found - ID: {student.id}, Email: {student.email}, Name: {student.full_name}")
            crud_logger.debug(f"Student details - Roll: {student.roll_no}, CGPA: {student.cgpa}")
            crud_logger.debug(f"Password hash length: {len(student.hashed_password) if student.hashed_password else 0}")
            crud_logger.debug(f"Session ID: {student.session_id if student.session_id else 'None'}")
        else:
            crud_logger.warning(f"No student found for email: {search_email}")
            
            # Additional debugging: check if there are similar emails
            similar_emails = db.query(models.Student.email).all()
            crud_logger.debug(f"Total students in database: {len(similar_emails)}")
            
            # Check for potential matches (without case sensitivity)
            potential_matches = [email[0] for email in similar_emails if search_email in email[0].lower()]
            if potential_matches:
                crud_logger.debug(f"Potential similar emails found: {potential_matches[:3]}...")  # Limit to first 3
            else:
                crud_logger.debug("No similar emails found in database")
        
        return student
        
    except Exception as e:
        crud_logger.error(f"Database error during email lookup for '{email}': {str(e)}")
        crud_logger.error(f"Error type: {type(e).__name__}")
        raise

def get_questions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Question).options(joinedload(models.Question.correct_answers)).offset(skip).limit(limit).all()

def start_quiz_attempt(db: Session, student_id: int):
    # Use timezone-aware datetime to fix the timezone bug
    utc_now = datetime.now(timezone.utc)
    crud_logger.info(f"Creating quiz attempt with UTC timestamp: {utc_now}")
    
    db_result = models.Result(
        student_id=student_id,
        quiz_started_at=utc_now
    )
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    
    crud_logger.info(f"Quiz attempt created - started_at: {db_result.quiz_started_at}")
    return db_result

def update_student_result(db: Session, result_id: int, score: float, time_taken: int):
    # Lock the row for update to prevent race conditions
    db_result = db.query(models.Result).filter(models.Result.id == result_id).with_for_update().first()

    # After locking, check if the quiz has already been submitted by another request
    if db_result and db_result.submitted_at:
        crud_logger.warning(f"Race condition detected: Quiz for result ID {result_id} was already submitted.")
        return None  # Indicate that the submission was not processed

    if db_result:
        db_result.score = score
        db_result.time_taken = time_taken
        # Use timezone-aware datetime for consistency
        db_result.submitted_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(db_result)
    return db_result

def get_all_students(db: Session, skip: int = 0, limit: int = 1000):
    """Get all students regardless of whether they've taken the quiz or not"""
    return db.query(models.Student).options(joinedload(models.Student.result)).offset(skip).limit(limit).all()

def get_all_students_with_results(db: Session, skip: int = 0, limit: int = 3000):
    """Get all students with their results using LEFT JOIN to include students who haven't taken the quiz"""
    return (db.query(models.Student)
            .outerjoin(models.Result)
            .options(joinedload(models.Student.result))
            .order_by(desc(models.Result.score).nulls_last(), models.Student.full_name)
            .offset(skip)
            .limit(limit)
            .all())
 