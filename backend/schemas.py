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

class Question(BaseModel):
    id: int
    question_text: str
    options: str

    class Config:
        orm_mode = True

class Result(BaseModel):
    score: Optional[int] = None
    time_taken: Optional[int] = None
    submitted_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class Student(BaseModel):
    id: int
    roll_no: str
    full_name: str
    email: str
    cgpa: Optional[float] = None
    tenth_percentage: Optional[float] = None
    twelfth_percentage: Optional[float] = None
    result: Optional[Result] = None

    class Config:
        from_attributes = True

class StudentCreate(Student):
    password: str 