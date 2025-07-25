import csv
import logging
import os
import random
import string
import sys
from sqlalchemy.orm import sessionmaker
from database import engine, SessionLocal
import crud
import schemas
from security import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_password(length=12):
    """Generates a random password."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

def populate_students_from_csv():
    db = SessionLocal()
    try:
        # Construct the absolute path to the CSV file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(script_dir, 'CSV.csv')
        credentials_path = os.path.join(script_dir, 'student_credentials.csv')

        with open(csv_path, 'r', encoding='utf-8-sig') as csv_file, open(credentials_path, 'w', newline='') as new_csv_file:
            csv_reader = csv.DictReader(csv_file)
            fieldnames = ['email', 'password']
            csv_writer = csv.DictWriter(new_csv_file, fieldnames=fieldnames)
            csv_writer.writeheader()

            for row in csv_reader:
                email = row['Personal Email Id'].strip().lower()
                
                # Check if student already exists
                if crud.get_student_by_email(db, email=email):
                    logger.warning(f"Student with email {email} already exists. Skipping.")
                    continue

                password = generate_password()
                
                try:
                    student_data = schemas.StudentCreate(
                        roll_no=row['Roll No'].strip(),
                        full_name=row['Name of Student'].strip(),
                        email=email,
                        password=password,
                        cgpa=float(row['B.Tech(CGPA)']),
                        tenth_percentage=float(row['Class 10 %']),
                        twelfth_percentage=float(row['Class 12th/Diploma %'])
                    )
                    
                    crud.create_student(db=db, student=student_data)
                    csv_writer.writerow({'email': email, 'password': password})
                    logger.info(f"Successfully created student: {email}")

                except (ValueError, KeyError) as e:
                    logger.error(f"Skipping row due to data error for email {email}: {e}. Row: {row}")
                except Exception as e:
                    logger.error(f"An unexpected error occurred for email {email}: {e}")

        # Add test users if not present
        test_users = [
            {"email": "siddharth.g@kaaratech.com", "password": "password", "full_name": "Siddharth G", "roll_no": "101"},
            {"email": "rohan.s@kaaratech.com", "password": "password", "full_name": "Rohan S", "roll_no": "102"},
            {"email": "test1@email.com", "password": "password", "full_name": "Test User 1", "roll_no": "T01"},
            {"email": "test2@email.com", "password": "password", "full_name": "Test User 2", "roll_no": "T02"},
            {"email": "chintan@test.com", "password": "password", "full_name": "Chintan", "roll_no": "T03"},
            {"email": "ashwini@test.com", "password": "password", "full_name": "Ashwini", "roll_no": "T04"},
            {"email": "venu@test.com", "password": "password", "full_name": "Venu", "roll_no": "T05"},
            {"email": "anirudh@test.com", "password": "password", "full_name": "Anirudh", "roll_no": "T06"},
            {"email": "satya@test.com", "password": "password", "full_name": "Satya", "roll_no": "T07"},
            {"email": "ashwini@kaaratech.com", "password": "password", "full_name": "Ashwini K", "roll_no": "T08"},
            {"email": "chintan.singh@kaaratech.com", "password": "password", "full_name": "Chintan S", "roll_no": "T09"},
            {"email": "anirudh.arabolu@kaaratech.com", "password": "password", "full_name": "Anirudh A", "roll_no": "T10"},
            {"email": "venugopal.a@kaaratech.com", "password": "password", "full_name": "Venugopal A", "roll_no": "T11"},
            {"email": "satya.b@kaaratech.com", "password": "password", "full_name": "Satya B", "roll_no": "T12"}
        ]
        for user_data in test_users:
            email = user_data["email"].strip().lower()
            if not crud.get_student_by_email(db, email=email):
                try:
                    student_data = schemas.StudentCreate(
                        roll_no=user_data["roll_no"],
                        full_name=user_data["full_name"],
                        email=email,
                        password=user_data["password"],
                        cgpa=8.0,
                        tenth_percentage=90.0,
                        twelfth_percentage=90.0
                    )
                    crud.create_student(db=db, student=student_data)
                    logger.info(f"Test user created: {email}")
                except Exception as e:
                    logger.error(f"Failed to create test user {email}: {e}")
            else:
                logger.info(f"Test user already exists: {email}")

    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Starting student population script.")
    populate_students_from_csv()
    logger.info("Student population script finished.") 