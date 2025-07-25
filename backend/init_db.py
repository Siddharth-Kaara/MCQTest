import csv
import logging
import os
import random
import string
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

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    question_text = Column(String, index=True)
    options = Column(String)
    correct_answers = relationship("CorrectAnswer", back_populates="question", cascade="all, delete-orphan")

class CorrectAnswer(Base):
    __tablename__ = "correct_answers"
    id = Column(Integer, primary_key=True, index=True)
    answer = Column(String, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    question = relationship("Question", back_populates="correct_answers")

def generate_password(length=12):
    """Generates a random password."""
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for i in range(length))

def get_password_hash(password):
    """Hashes a plain-text password."""
    import bcrypt
    hashed_bytes = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed_bytes.decode('utf-8')

def init_db():
    """
    Initializes the database by dropping all existing tables and recreating them.
    This is a DESTRUCTIVE operation and will result in data loss.
    """
    engine = create_engine(DATABASE_URL)
    
    print("!!! WARNING: THIS IS A DESTRUCTIVE OPERATION AND WILL DELETE ALL EXISTING DATA. !!!")
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Tables dropped.")

    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created.")

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Create the admin user
        print("Creating admin user...")
        hashed_password = get_password_hash("Ahimsa0210")
        admin_user = Student(
            email="admin@kaaratech.com",
            hashed_password=hashed_password,
            full_name="Admin User",
            roll_no="N/A",
            cgpa=0,
            tenth_percentage=0,
            twelfth_percentage=0,
            session_id=None
        )
        db.add(admin_user)
        db.commit()
        print("Admin user created successfully.")

        # Create users from CSV
        try:
            # Construct the absolute path to the CSV file
            script_dir = os.path.dirname(os.path.abspath(__file__))
            csv_path = os.path.join(script_dir, 'CSV.csv')
            credentials_path = os.path.join(script_dir, 'student_credentials.csv')

            with open(csv_path, 'r') as csv_file, open(credentials_path, 'w', newline='') as new_csv_file:
                csv_reader = csv.DictReader(csv_file)
                fieldnames = ['email', 'password']
                csv_writer = csv.DictWriter(new_csv_file, fieldnames=fieldnames)
                csv_writer.writeheader()

                for row in csv_reader:
                    email = row['Personal Email Id']
                    if db.query(Student).filter(Student.email == email).count() == 0:
                        password = generate_password()
                        hashed_password = get_password_hash(password)
                        student = Student(
                            email=email,
                            hashed_password=hashed_password,
                            full_name=row['Name of Student'],
                            roll_no=row['Roll No'],
                            cgpa=float(row['B.Tech(CGPA)']),
                            tenth_percentage=float(row['Class 10 %']),
                            twelfth_percentage=float(row['Class 12th/Diploma %'])
                        )
                        db.add(student)
                        db.commit()
                        csv_writer.writerow({'email': email, 'password': password})
                        logger.info(f"Created user: {email}")
                    else:
                        logger.warning(f"User {email} already exists. Skipping.")
        except FileNotFoundError:
            logger.warning("CSV.csv not found. Skipping bulk user creation.")

        # Create specific test users if they don't exist
        test_users = [
            {"email": "siddharth.g@kaaratech.com", "password": "password", "full_name": "Siddharth G", "roll_no": "101"},
            {"email": "rohan.s@kaaratech.com", "password": "password", "full_name": "Rohan S", "roll_no": "102"}
        ]

        for user_data in test_users:
            if db.query(Student).filter(Student.email == user_data["email"]).count() == 0:
                print(f"Creating test user: {user_data['email']}")
                hashed_password = get_password_hash(user_data["password"])
                test_user = Student(
                    email=user_data["email"],
                    hashed_password=hashed_password,
                    full_name=user_data["full_name"],
                    roll_no=user_data["roll_no"],
                    cgpa=8.0,
                    tenth_percentage=90,
                    twelfth_percentage=90,
                    session_id=None
                )
                db.add(test_user)
                db.commit()
                print(f"Test user {user_data['email']} created successfully.")
            else:
                print(f"Test user {user_data['email']} already exists.")

    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
    finally:
        print("Closing database session.")
        db.close()

if __name__ == "__main__":
    init_db()
    print("Database initialization check completed.")
