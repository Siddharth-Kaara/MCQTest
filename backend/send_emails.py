import csv
import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Email Configuration (Hardcoded) ---
EMAIL_HOST = 'smtp-relay.brevo.com'
EMAIL_PORT = 587
EMAIL_USER = '931427001@smtp-brevo.com'
EMAIL_PASSWORD = 'NfQgh1t57mRxFLWM' # IMPORTANT: Replace with your Brevo SMTP Key

# --- Email Content ---
SENDER_EMAIL = 'admin@kaaratech.com' # The "From" address shown to recipients
QUIZ_LINK = "https://kaara-mcq-test.azurewebsites.net/"
SENDER_NAME = "Kaara Info Systems"
SUBJECT = "Your Credentials for the Kaara Info Systems MCQ Assessment"

def create_email_body(email, password):
    """Creates the HTML content for the email."""
    return f"""
    <html>
    <head>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Exo+2:wght@700&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 20px auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }}
            .header {{ 
                font-family: 'Exo 2', sans-serif; 
                mso-font-alt: 'Arial'; /* Specific fallback for Microsoft Outlook */
                font-size: 24px; 
                font-weight: bold; 
                color: #c00; 
                margin-bottom: 20px; 
            }}
            .credentials {{ background-color: #f9f9f9; padding: 15px; border: 1px solid #eee; border-radius: 4px; }}
            .footer {{ margin-top: 20px; font-size: 12px; color: #777; }}
            a {{ color: #c00; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">Kaara Info Systems MCQ Assessment</div>
            <p>Dear Student,</p>
            <p>Here are your credentials for the online MCQ assessment. Please use the following details to log in.</p>
            
            <div class="credentials">
                <p><strong>Link:</strong> <a href="{QUIZ_LINK}">{QUIZ_LINK}</a></p>
                <p><strong>Username:</strong> {email}</p>
                <p><strong>Password:</strong> {password}</p>
            </div>

            <p>Please ensure you have a stable internet connection before you begin. <b>The quiz is strictly timed for 20 minutes, and you must submit your answers before the timer runs out.</b></p>
            <p>Good luck!</p>

            <div class="footer">
                <p>Best regards,<br>The Kaara Team</p>
                <p>If you have any issues, please contact the assessment administrator.</p>
            </div>
        </div>
    </body>
    </html>
    """

def send_emails():
    """Reads credentials from CSV and sends an email to each student."""
    if not all([EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD]):
        logger.error("Email configuration is incomplete.")
        return

    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(script_dir, 'student_credentials_test.csv')
        
        with open(csv_path, 'r') as file:
            reader = csv.DictReader(file)
            # Make the field names lowercase and strip whitespace to handle variations
            reader.fieldnames = [field.strip().lower() for field in reader.fieldnames]
            
            students = list(reader)
            if not students:
                logger.warning("The credentials file is empty. No emails to send.")
                return

        logger.info(f"Found {len(students)} students to email.")
        
        # Connect to the SMTP server
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        logger.info("Successfully connected to the SMTP server.")

        for student in students:
            try:
                # Strip whitespace from values to handle dirty data
                recipient_email = student.get('email', '').strip()
                password = student.get('password', '').strip()

                if not recipient_email or not password:
                    logger.warning(f"Skipping row with missing data or only whitespace: {student}")
                    continue

                msg = MIMEMultipart('alternative')
                msg['Subject'] = SUBJECT
                msg['From'] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
                msg['To'] = recipient_email

                body = create_email_body(recipient_email, password)
                msg.attach(MIMEText(body, 'html'))

                server.sendmail(EMAIL_USER, recipient_email, msg.as_string())
                logger.info(f"Successfully sent email to {recipient_email}")

            except KeyError as e:
                logger.error(f"CSV file is missing expected column: {e}. Please ensure it has 'email' and 'password' columns.")
                break # Stop processing if the CSV format is wrong
            except Exception as e:
                logger.error(f"Failed to send email to {student.get('email', 'unknown')}: {e}")

    except FileNotFoundError:
        logger.error(f"Error: The file 'student_credentials.csv' was not found in the '{script_dir}' directory.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
    finally:
        if 'server' in locals() and server:
            server.quit()
            logger.info("SMTP server connection closed.")

if __name__ == "__main__":
    logger.info("Starting email sending script...")
    send_emails()
    logger.info("Email sending script finished.") 