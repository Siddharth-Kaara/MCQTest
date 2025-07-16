import logging

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import List

from . import crud, models, schemas, security, config
from .database import SessionLocal, engine
from .config import settings

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = crud.get_student_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_admin_user(current_user: schemas.Student = Depends(get_current_user)):
    if current_user.email != "admin@kaaratech.com":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource.",
        )
    return current_user

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    # --- TEMPORARY DEBUGGING ---
    logging.info("--- Inside /token endpoint ---")
    logging.info(f"Received username: '{form_data.username}'")
    logging.info(f"Received password: '{form_data.password}'")
    # ---------------------------
    
    user = crud.get_student_by_email(db, email=form_data.username)

    if not user or not security.verify_password(form_data.password, user.hashed_password):
        logging.warning("User not found or password incorrect.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = security.create_access_token(
        data={"sub": user.email}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/admin/results/", response_model=List[schemas.Student])
def read_results(current_user: schemas.Student = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    logging.info("--- Inside /admin/results/ endpoint ---")
    students_from_db = crud.get_all_students_with_results(db)
    logging.info(f"Found {len(students_from_db)} students in total from CRUD.")

    # Limit logging to the first 10 students for readability
    students_to_log = students_from_db[:10]
    logging.info(f"Displaying logs for the first {len(students_to_log)} students:")

    for student in students_to_log:
        student_data = {
            "email": student.email,
            "cgpa": student.cgpa,
            "10th": student.tenth_percentage,
            "12th": student.twelfth_percentage,
            "result": None
        }
        if student.result:
            student_data["result"] = {
                "id": student.result.id,
                "score": student.result.score,
                "submitted_at": student.result.submitted_at,
            }
        logging.info(f"  - Student Data: {student_data}")

    return students_from_db

@app.get("/questions/", response_model=List[schemas.Question])
def read_questions(current_user: schemas.Student = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check if the user has already completed the quiz
    if current_user.result and current_user.result.submitted_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already completed the quiz.",
        )
    
    # If this is the first time, start the timer by creating a result entry
    if not current_user.result:
        crud.start_quiz_attempt(db, student_id=current_user.id)
        db.refresh(current_user)  # Refresh to get the new result relationship

    questions = crud.get_questions(db)
    return questions

@app.post("/submit")
def submit_quiz(
    submission: schemas.Submission,
    current_user: schemas.Student = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Ensure user has started the quiz but not submitted
    if not current_user.result or current_user.result.submitted_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot submit this quiz.",
        )

    # Server-side time validation
    time_now = datetime.utcnow()
    time_started = current_user.result.quiz_started_at
    time_taken = (time_now - time_started).total_seconds()
    
    # Allow a 30-second grace period for network latency
    if time_taken > (20 * 60 + 30):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Time limit exceeded. Your submission was not recorded.",
        )

    questions = crud.get_questions(db)
    question_map = {q.id: q.correct_answer for q in questions}
    
    score = 0
    for answer in submission.answers:
        if answer.question_id in question_map:
            correct_answer = question_map[answer.question_id]
            # Handle multiple correct answers (e.g., "A, C")
            correct_options = {opt.strip() for opt in correct_answer.split(',')}
            
            # Assuming selected_answer is a single character e.g., "A"
            if answer.selected_answer in correct_options:
                score += 1

    logging.info(f"Submitting quiz for user: {current_user.email} (ID: {current_user.id})")
    logging.info(f"Calculated score: {score}")
    logging.info(f"Time taken: {int(time_taken)}")
    logging.info(f"Updating result with ID: {current_user.result.id}")

    updated_result = crud.update_student_result(
        db=db,
        result_id=current_user.result.id,
        score=score,
        time_taken=int(time_taken)
    )

    logging.info(f"CRUD update_student_result returned: {updated_result}")
    if updated_result:
        logging.info(f"Result score after update: {updated_result.score}")
        logging.info(f"Result submitted_at after update: {updated_result.submitted_at}")


    return {"message": "Quiz submitted successfully!", "score": score}

@app.get("/")
def read_root():
    return {"message": "Welcome to the MCQ Test API"} 