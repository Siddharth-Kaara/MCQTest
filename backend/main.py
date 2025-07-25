import logging
import sys
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import List

import crud, models, schemas, security, config
from database import SessionLocal, engine
from config import settings

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('mcq_app.log', mode='a')
    ]
)

# Create loggers for different modules
logger = logging.getLogger(__name__)
auth_logger = logging.getLogger("auth")
api_logger = logging.getLogger("api")

# Log application startup
logger.info("=" * 50)
logger.info("MCQ Test Application Starting Up")
logger.info(f"Environment: {'PRODUCTION' if 'azure' in settings.DATABASE_URL else 'DEVELOPMENT'}")
logger.info(f"Database URL: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'Local DB'}")
logger.info("=" * 50)

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://kaara-mcq-test.azurewebsites.net", "http://localhost:5173", "http://127.0.0.1:5173"],
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
        expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    auth_logger.debug("=" * 30)
    auth_logger.debug("TOKEN VALIDATION ATTEMPT")
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Log token information (without exposing the full token)
        auth_logger.debug(f"Token length: {len(token) if token else 0}")
        auth_logger.debug(f"Token prefix: {token[:20]}..." if token and len(token) > 20 else token)
        
        # Decode JWT token
        auth_logger.debug("Decoding JWT token...")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        email: str = payload.get("sub")
        session_id: str = payload.get("session_id")
        exp: int = payload.get("exp")
        
        auth_logger.debug(f"Token payload - Email: {email}, Session ID: {session_id}")
        auth_logger.debug(f"Token expiration: {datetime.fromtimestamp(exp) if exp else 'None'}")
        
        if email is None or session_id is None:
            auth_logger.warning("Token validation failed: missing email or session_id in payload")
            raise credentials_exception
            
        token_data = schemas.TokenData(email=email, session_id=session_id)
        auth_logger.debug("JWT token decoded successfully")
        
    except JWTError as e:
        auth_logger.warning(f"JWT token validation failed: {str(e)}")
        auth_logger.debug(f"JWT Error type: {type(e).__name__}")
        raise credentials_exception
    except Exception as e:
        auth_logger.error(f"Unexpected error during token decode: {str(e)}")
        raise credentials_exception
    
    # Look up user in database
    auth_logger.debug(f"Looking up user in database for email: {token_data.email}")
    user = crud.get_student_by_email(db, email=token_data.email)
    
    if user is None:
        auth_logger.warning(f"Token validation failed: user not found for email {token_data.email}")
        raise credentials_exception
        
    auth_logger.debug(f"User found - ID: {user.id}, Current session: {user.session_id}")
    
    # Validate session ID
    if user.session_id != token_data.session_id:
        auth_logger.warning(f"Token validation failed: session mismatch")
        auth_logger.debug(f"User session: {user.session_id}, Token session: {token_data.session_id}")
        raise credentials_exception
    
    auth_logger.debug(f"Token validation SUCCESS for user: {user.email}")
    auth_logger.debug("=" * 30)
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
    request_start_time = datetime.now(timezone.utc)
    client_email = form_data.username.strip().lower() if form_data.username else "None"
    
    auth_logger.info("=" * 40)
    auth_logger.info(f"LOGIN ATTEMPT - Email: {client_email}")
    auth_logger.info(f"Request timestamp: {request_start_time}")
    auth_logger.info(f"Password provided: {'Yes' if form_data.password else 'No'}")
    auth_logger.info(f"Password length: {len(form_data.password) if form_data.password else 0}")
    
    try:
        # Step 1: Look up user in database
        auth_logger.info(f"STEP 1: Looking up user in database...")
        user = crud.get_student_by_email(db, email=form_data.username)
        
        if not user:
            auth_logger.warning(f"STEP 1 FAILED: User not found in database for email: {client_email}")
            auth_logger.info("=" * 40)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        auth_logger.info(f"STEP 1 SUCCESS: User found - ID: {user.id}, Name: {user.full_name}, Email: {user.email}")
        
        # Step 2: Verify password
        auth_logger.info(f"STEP 2: Verifying password...")
        password_valid = security.verify_password(form_data.password, user.hashed_password)
        
        if not password_valid:
            auth_logger.warning(f"STEP 2 FAILED: Password verification failed for user: {client_email}")
            auth_logger.info(f"Stored hash length: {len(user.hashed_password) if user.hashed_password else 0}")
            auth_logger.info("=" * 40)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        auth_logger.info(f"STEP 2 SUCCESS: Password verified for user: {client_email}")
        
        # Step 3: Create access token
        auth_logger.info(f"STEP 3: Creating access token...")
        access_token = security.create_access_token(
            data={"sub": user.email}
        )
        auth_logger.info(f"STEP 3 SUCCESS: Access token created with length: {len(access_token)}")
        
        # Step 4: Update session ID
        auth_logger.info(f"STEP 4: Updating user session...")
        payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        session_id = payload.get("session_id")
        user.session_id = session_id
        db.commit()
        auth_logger.info(f"STEP 4 SUCCESS: Session ID updated: {session_id}")
        
        # Calculate and log total processing time
        processing_time = (datetime.now(timezone.utc) - request_start_time).total_seconds()
        auth_logger.info(f"LOGIN SUCCESS for {client_email} - Processing time: {processing_time:.3f}s")
        auth_logger.info("=" * 40)
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        # Re-raise HTTP exceptions (authentication failures)
        raise
    except Exception as e:
        # Log unexpected errors
        auth_logger.error(f"UNEXPECTED ERROR during login for {client_email}: {str(e)}")
        auth_logger.error(f"Error type: {type(e).__name__}")
        auth_logger.info("=" * 40)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during authentication"
        )

@app.get("/admin/results/", response_model=List[schemas.Student])
def read_results(skip: int = 0, limit: int = 3000, current_user: schemas.Student = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    students_from_db = crud.get_all_students_with_results(db, skip=skip, limit=limit)
    
    for student in students_from_db:
        if student.result and student.result.time_taken is not None and student.cgpa is not None and student.tenth_percentage is not None and student.twelfth_percentage is not None:
            max_time = 20 * 60
            time_penalty = max(0, (student.result.time_taken - (max_time * 0.25)) / (max_time * 0.75))
            speed_score = (1 - time_penalty) * 100
            academic_score = (student.cgpa * 10 + student.tenth_percentage + student.twelfth_percentage) / 3
            quiz_score = (student.result.score / 25) * 100
            normalized_score = (quiz_score * 0.5) + (academic_score * 0.3) + (speed_score * 0.2)
            student.normalized_score = round(normalized_score, 2)
            
    return students_from_db

@app.get("/questions/", response_model=schemas.QuizState)
def read_questions(current_user: schemas.Student = Depends(get_current_user), db: Session = Depends(get_db)):
    api_logger.info("=" * 40)
    api_logger.info(f"QUESTIONS REQUEST for user: {current_user.email}")
    
    try:
        # Check if the user has already completed the quiz
        if current_user.result and current_user.result.submitted_at:
            api_logger.warning(f"User {current_user.email} already completed quiz")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already completed the quiz.",
            )
        
        # If this is the first time, start the timer by creating a result entry
        if not current_user.result:
            api_logger.info("Starting new quiz attempt for user")
            crud.start_quiz_attempt(db, student_id=current_user.id)
            db.refresh(current_user)  # Refresh to get the new result relationship
            api_logger.info(f"Quiz attempt started at: {current_user.result.quiz_started_at}")
        else:
            # Check if the quiz has expired
            time_now = datetime.now(timezone.utc)
            time_started = current_user.result.quiz_started_at
            if time_started.tzinfo is None:
                time_started = time_started.replace(tzinfo=timezone.utc)

            if (time_now - time_started).total_seconds() > (20 * 60):
                api_logger.warning(f"User {current_user.email} tried to access an expired quiz.")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Your quiz session has expired.",
                )

        api_logger.info("Fetching questions from database...")
        questions_orm = crud.get_questions(db)
        api_logger.info(f"Retrieved {len(questions_orm)} questions from database")
        
        # Convert SQLAlchemy objects to Pydantic objects
        api_logger.debug("Converting SQLAlchemy objects to Pydantic schemas...")
        questions_pydantic = [schemas.Question.model_validate(q) for q in questions_orm]
        api_logger.info("Successfully converted questions to Pydantic schemas")
        
        # Ensure quiz_started_at is timezone-aware
        quiz_started_at = current_user.result.quiz_started_at
        if quiz_started_at.tzinfo is None:
            # If stored time is naive, assume it's UTC and make it timezone-aware
            quiz_started_at = quiz_started_at.replace(tzinfo=timezone.utc)
            api_logger.warning(f"Fixed timezone-naive quiz start time: {quiz_started_at}")
        
        api_logger.info(f"Sending quiz_started_at to frontend: {quiz_started_at}")
        api_logger.info(f"ISO format: {quiz_started_at.isoformat()}")
        
        quiz_state = schemas.QuizState(
            questions=questions_pydantic,
            quiz_started_at=quiz_started_at
        )
        
        api_logger.info("QUESTIONS REQUEST SUCCESS")
        api_logger.info("=" * 40)
        return quiz_state
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        api_logger.error(f"QUESTIONS REQUEST FAILED: {str(e)}")
        api_logger.error(f"Error type: {type(e).__name__}")
        api_logger.info("=" * 40)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load quiz questions"
        )

@app.get("/quiz-status", response_model=schemas.QuizStatus)
def get_quiz_status(current_user: schemas.Student = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Provides the current status of the user's quiz, primarily for timer synchronization.
    This is a lightweight endpoint to be called periodically by the frontend.
    """
    api_logger.debug(f"Quiz status requested for user: {current_user.email}")
    if not current_user.result:
        # This case should ideally not be hit if the quiz has started.
        api_logger.warning(f"User {current_user.email} requested quiz status without a result entry.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz has not been started yet.",
        )

    quiz_started_at = current_user.result.quiz_started_at
    if quiz_started_at.tzinfo is None:
        quiz_started_at = quiz_started_at.replace(tzinfo=timezone.utc)

    status_data = schemas.QuizStatus(
        quiz_started_at=quiz_started_at,
        submitted_at=current_user.result.submitted_at
    )
    api_logger.debug(f"Quiz status sent for {current_user.email}: started_at={status_data.quiz_started_at}")
    return status_data


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

    # Server-side time validation with proper timezone handling
    time_now = datetime.now(timezone.utc)
    time_started = current_user.result.quiz_started_at
    
    if time_started.tzinfo is None:
        # If stored time is naive, assume it's UTC and make it timezone-aware
        time_started = time_started.replace(tzinfo=timezone.utc)
        logging.warning(f"Fixed timezone-naive start time: {time_started}")
    
    # Now safe to calculate time difference
    time_taken = (time_now - time_started).total_seconds()
    
    # Add timezone debugging logs
    logging.info(f"Time validation - Now: {time_now}, Started: {time_started}")
    logging.info(f"Time calculation - Elapsed seconds: {time_taken}")
    logging.info(f"Timezone info - Now: {time_now.tzinfo}, Started: {time_started.tzinfo}")
    
    # Allow a 60-second grace period for network latency and auto-submit timing
    if time_taken > (20 * 60 + 120):
        logging.warning(f"Time limit exceeded for user {current_user.email} - elapsed: {time_taken}s, limit: {20*60}s")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Time limit exceeded. Your quiz session has expired and your submission could not be recorded.",
        )

    questions = crud.get_questions(db)
    question_map = {q.id: [ans.answer for ans in q.correct_answers] for q in questions}
    
    score = 0
    for answer in submission.answers:
        if answer.question_id in question_map:
            correct_answers = question_map[answer.question_id]
            if answer.selected_answer in correct_answers:
                if len(correct_answers) > 1:
                    score += 0.5
                else:
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

# Mount static assets (CSS, JS files) from the assets directory
app.mount("/assets", StaticFiles(directory="frontend/assets"), name="assets")

# Serve favicon and other static files
@app.get("/logo.svg")
async def get_favicon():
    try:
        return FileResponse("frontend/logo.svg")
    except FileNotFoundError:
        # Return a simple SVG if the file doesn't exist
        from fastapi.responses import Response
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polygon points="10,8 16,12 10,16 10,8"/></svg>"""
        return Response(content=svg_content, media_type="image/svg+xml")

@app.get("/vite.svg")
async def get_vite_favicon():
    try:
        return FileResponse("frontend/vite.svg")
    except FileNotFoundError:
        # Return a simple SVG if the file doesn't exist
        from fastapi.responses import Response
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polygon points="10,8 16,12 10,16 10,8"/></svg>"""
        return Response(content=svg_content, media_type="image/svg+xml")

# Debug endpoint to test timezone handling
@app.get("/debug/timezone")
def debug_timezone():
    """Debug endpoint to test timezone handling"""
    now_naive = datetime.utcnow()  # Old way (timezone-naive)
    now_aware = datetime.now(timezone.utc)  # New way (timezone-aware)
    
    return {
        "naive_utc": now_naive,
        "aware_utc": now_aware,
        "naive_iso": now_naive.isoformat(),
        "aware_iso": now_aware.isoformat(),
        "timezone_info": {
            "naive_tzinfo": str(now_naive.tzinfo),
            "aware_tzinfo": str(now_aware.tzinfo)
        }
    }

# Test endpoint to reset user quiz attempts (for testing only)
@app.post("/debug/reset-quiz/{email}")
def reset_user_quiz(email: str, db: Session = Depends(get_db)):
    """Reset a user's quiz attempt for testing purposes"""
    api_logger.info(f"RESET REQUEST for user: {email}")
    
    try:
        # Find user
        user = crud.get_student_by_email(db, email=email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Delete existing result if any
        if user.result:
            db.delete(user.result)
            db.commit()
            api_logger.info(f"Reset quiz attempt for user: {email}")
            return {"message": f"Quiz attempt reset for {email}"}
        else:
            return {"message": f"No quiz attempt found for {email}"}
    
    except Exception as e:
        api_logger.error(f"Error resetting quiz for {email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reset quiz")

# SPA catch-all route - serve index.html for all non-API routes
@app.get("/{full_path:path}")
async def serve_spa(request: Request, full_path: str):
    # Don't interfere with API routes
    if full_path.startswith("token") or full_path.startswith("admin") or full_path.startswith("questions") or full_path.startswith("submit") or full_path.startswith("debug"):
        raise HTTPException(status_code=404, detail="Not found")
    
    # Serve index.html for all other routes (SPA routing)
    return FileResponse("frontend/index.html")
 