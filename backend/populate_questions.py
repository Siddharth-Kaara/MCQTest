import logging
import os
import re
import sys
from sqlalchemy import create_engine, func, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, Session, relationship, declarative_base

# --- Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Hardcoded Database URL for the Azure Test DB
DATABASE_URL = "postgresql+psycopg2://kaaraadmin:Ahimsa0210@mcq-test-db-server.postgres.database.azure.com:5432/postgres"

# --- Self-Contained Model Definitions ---
Base = declarative_base()

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    question_text = Column(String, index=True)
    options = Column(String)
    correct_answers = relationship("CorrectAnswer", back_populates="question")

class CorrectAnswer(Base):
    __tablename__ = "correct_answers"
    id = Column(Integer, primary_key=True, index=True)
    answer = Column(String, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    question = relationship("Question", back_populates="correct_answers")

def populate_questions():
    """
    Reads questions from a text file, parses them, and populates the questions table in the database.
    """
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Clear existing questions and answers to ensure a clean slate
        logger.info("Clearing existing questions and answers from the database...")
        db.query(CorrectAnswer).delete()
        db.query(Question).delete()
        db.commit()
        logger.info("Database cleared successfully.")
        
        # Fix the file path - script is run from project root, not backend directory
        with open('backend/questions.txt', 'r', encoding='utf-8') as f:
            content = f.read()

        # Split the content by sections
        sections = re.split(r'_{2,}', content)
        for section in sections:
            if not section.strip():
                continue

            # Split each section into questions
            questions = re.split(r'\n(?=\d+\.)', section)
            for q_text in questions:
                if not q_text.strip():
                    continue

                # Extract the question, options, and answer
                match = re.search(r'(\d+)\.\s*(.*?)\n(.*?)\n✅ Answer: (.*)', q_text, re.DOTALL)
                if match:
                    q_number, question, options_str, answer = match.groups()
                    
                    # Format the options string, removing the leading characters (e.g., "A. ", "B) ")
                    cleaned_options = [re.sub(r'^[A-Z][.)]\s*', '', opt.strip()) for opt in options_str.strip().split('\n')]
                    options = "||".join(cleaned_options)

                    # Check if the question already exists
                    if db.query(Question).filter(Question.question_text == question.strip()).count() == 0:
                        db_question = Question(
                            question_text=question.strip(),
                            options=options
                        )
                        db.add(db_question)
                        db.commit()
                        db.refresh(db_question)

                        # Handle multiple answers separated by commas
                        answers = [a.strip() for a in answer.split(',')]
                        for ans in answers:
                            db_answer = CorrectAnswer(answer=ans, question_id=db_question.id)
                            db.add(db_answer)
                        
                        db.commit()
                        logger.info(f"Added question: {question.strip()}")
                    else:
                        logger.warning(f"Question already exists: {question.strip()}")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    populate_questions()
