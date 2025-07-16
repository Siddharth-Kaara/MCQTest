import sys
import os
from sqlalchemy.orm import Session

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend import crud, security, database

def verify_credentials(email: str, password: str):
    """
    Verifies a student's credentials against the database.
    """
    print(f"Attempting to verify credentials for: {email}")
    db = database.SessionLocal()
    
    student = crud.get_student_by_email(db, email=email)
    
    if not student:
        print("RESULT: FAILURE - Student email not found in the database.")
        db.close()
        return

    print(f"Found student: {student.full_name}")
    print("Verifying password...")

    if security.verify_password(password, student.hashed_password):
        print("\n================================")
        print("RESULT: SUCCESS - Password is correct.")
        print("================================")
    else:
        print("\n================================")
        print("RESULT: FAILURE - Password does NOT match.")
        print("================================")
        
    db.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python verify_student.py <email> \"<password>\"")
        print("Please provide the email and password as arguments.")
        print("NOTE: It is important to wrap the password in double quotes.")
        sys.exit(1)

    user_email = sys.argv[1]
    user_password = sys.argv[2]
    
    verify_credentials(user_email, user_password) 