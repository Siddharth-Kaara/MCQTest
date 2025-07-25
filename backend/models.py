from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base

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
    session_id = Column(String, nullable=True)

    result = relationship("Result", back_populates="student", uselist=False)

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    question_text = Column(String, index=True)
    options = Column(String)  # Storing options as a JSON string or comma-separated
    
    correct_answers = relationship("CorrectAnswer", back_populates="question")

class CorrectAnswer(Base):
    __tablename__ = "correct_answers"

    id = Column(Integer, primary_key=True, index=True)
    answer = Column(String, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))

    question = relationship("Question", back_populates="correct_answers")

class Result(Base):
    __tablename__ = "results"

    id = Column(Integer, primary_key=True, index=True)
    score = Column(Float, nullable=True)  # Changed from Integer to Float for decimal scoring
    time_taken = Column(Integer, nullable=True)  # in seconds
    submitted_at = Column(DateTime, nullable=True)
    # Use timezone-aware datetime as default - this ensures proper timezone handling
    quiz_started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    student_id = Column(Integer, ForeignKey("students.id"))

    student = relationship("Student", back_populates="result")
 