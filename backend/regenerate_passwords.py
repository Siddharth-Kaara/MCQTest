import csv
import logging
import os
import random
import string
from sqlalchemy.orm import Session
from database import SessionLocal
import crud
import models
from security import get_password_hash

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_password(length=12):
    """Generates a new random password."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def regenerate_passwords():
    """
    Fetches all students, regenerates their passwords, updates the database,
    and creates a new student_credentials.csv file.
    """
    db = SessionLocal()

    # Define users to exclude from the password reset
    excluded_emails = {
        'admin@kaaratech.com',
        'siddharth.g@kaaratech.com',
        'rohan.s@kaaratech.com',
        'test1@email.com',
        'test2@email.com',
        'chintan@test.com',
        'ashwini@test.com',
        'venu@test.com',
        'anirudh@test.com',
        'satya@test.com',
        'ashwini@kaaratech.com',
        'chintan.singh@kaaratech.com',
        'anirudh.arabolu@kaaratech.com',
        'venugopal.a@kaaratech.com',
        'satya.b@kaaratech.com'
    }
    
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        credentials_path = os.path.join(script_dir, 'student_credentials.csv')
        
        logger.info(f"Creating new credentials file at: {credentials_path}")

        with open(credentials_path, 'w', newline='') as csvfile:
            fieldnames = ['email', 'password']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            # Fetch all students from the database
            # Using a large limit to get all students, assuming less than 3000.
            # For a larger dataset, pagination would be needed.
            all_students = crud.get_all_students(db, limit=3000)
            logger.info(f"Found {len(all_students)} total students in the database.")
            
            students_to_update = [s for s in all_students if s.email not in excluded_emails]
            logger.info(f"Found {len(students_to_update)} students to update (after exclusions).")

            for student in students_to_update:
                new_password = generate_password()
                student.hashed_password = get_password_hash(new_password)
                writer.writerow({'email': student.email, 'password': new_password})
                logger.info(f"Generated new password for: {student.email}")

            # Commit all changes to the database at once
            db.commit()
            logger.info("Successfully updated all student passwords in the database.")

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()
        logger.info("Database session closed.")

if __name__ == "__main__":
    logger.info("Starting password regeneration script...")
    regenerate_passwords()
    logger.info("Password regeneration script finished.") 