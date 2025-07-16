from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

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

    result = relationship("Result", back_populates="student", uselist=False)

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    question_text = Column(String, index=True)
    options = Column(String)  # Storing options as a JSON string or comma-separated
    correct_answer = Column(String)

class Result(Base):
    __tablename__ = "results"

    id = Column(Integer, primary_key=True, index=True)
    score = Column(Integer, nullable=True)
    time_taken = Column(Integer, nullable=True)  # in seconds
    submitted_at = Column(DateTime, nullable=True)
    quiz_started_at = Column(DateTime, default=datetime.utcnow)
    student_id = Column(Integer, ForeignKey("students.id"))

    student = relationship("Student", back_populates="result") 