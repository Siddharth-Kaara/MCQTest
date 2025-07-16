import os
import sys
from sqlalchemy.orm import Session

# Add the project root to the Python path to allow absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend import models, database, security

def init_db():
    """
    Initializes the database for a production environment.
    - Creates all necessary tables based on the models.
    - Ensures the default admin user exists.
    This script is safe to run multiple times.
    """
    print("Connecting to the database and creating tables...")
    # This line ensures that all tables defined in your models are created in the DB.
    database.Base.metadata.create_all(bind=database.engine)
    print("Tables created or already exist.")

    db = database.SessionLocal()
    try:
        # Check if the admin user already exists to avoid creating duplicates.
        if db.query(models.Student).filter(models.Student.email == "admin@kaaratech.com").count() == 0:
            print("Admin user not found, creating one...")
            hashed_password = security.get_password_hash("Ahimsa0210")
            admin_user = models.Student(
                email="admin@kaaratech.com",
                hashed_password=hashed_password,
                full_name="Admin User",
                roll_no="N/A",
                cgpa=0,
                tenth_percentage=0,
                twelfth_percentage=0,
            )
            db.add(admin_user)
            db.commit()
            print("Admin user created successfully.")
        else:
            print("Admin user already exists. No action needed.")

    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
    finally:
        print("Closing database session.")
        db.close()

if __name__ == "__main__":
    init_db()
    print("Database initialization check completed.") 