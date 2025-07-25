from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Answer(BaseModel):
    question_id: int
    selected_answer: str

class Submission(BaseModel):
    answers: List[Answer] = Field(default_factory=list)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    session_id: Optional[str] = None

class CorrectAnswer(BaseModel):
    answer: str

    class Config:
        from_attributes = True

class Question(BaseModel):
    id: int
    question_text: str
    options: str
    correct_answers: List[CorrectAnswer]

    class Config:
        from_attributes = True

class Result(BaseModel):
    score: Optional[float] = None
    time_taken: Optional[int] = None
    submitted_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class QuizState(BaseModel):
    questions: List[Question]
    quiz_started_at: datetime

class QuizStatus(BaseModel):
    quiz_started_at: datetime
    submitted_at: Optional[datetime] = None

class Student(BaseModel):
    id: int
    roll_no: str
    full_name: str
    email: str
    cgpa: Optional[float] = None
    tenth_percentage: Optional[float] = None
    twelfth_percentage: Optional[float] = None
    result: Optional[Result] = None
    normalized_score: Optional[float] = None
    session_id: Optional[str] = None

    class Config:
        from_attributes = True

class StudentCreate(BaseModel):
    roll_no: str
    full_name: str
    email: str
    password: str
    cgpa: float
    tenth_percentage: float
    twelfth_percentage: float
