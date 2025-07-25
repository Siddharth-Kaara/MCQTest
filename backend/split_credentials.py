import csv
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration ---
SOURCE_FILE_NAME = 'student_credentials_real.csv'
CHUNK_SIZE = 500

def split_csv():
    """
    Reads a large CSV file and splits it into smaller chunks of a specified size.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    source_path = os.path.join(script_dir, SOURCE_FILE_NAME)
    
    try:
        with open(source_path, 'r', newline='') as file:
            reader = csv.reader(file)
            header = next(reader)  # Read the header row
            students = list(reader)
        
        if not students:
            logger.warning(f"The source file '{SOURCE_FILE_NAME}' is empty. No splitting needed.")
            return

        logger.info(f"Found {len(students)} students in '{SOURCE_FILE_NAME}'. Splitting into chunks of {CHUNK_SIZE}.")

        # Split the list of students into chunks
        for i, chunk_start in enumerate(range(0, len(students), CHUNK_SIZE)):
            chunk_end = chunk_start + CHUNK_SIZE
            chunk = students[chunk_start:chunk_end]
            
            # Define the output file name
            output_file_name = f'student_credentials_part_{i + 1}.csv'
            output_path = os.path.join(script_dir, output_file_name)
            
            logger.info(f"Writing {len(chunk)} students to '{output_file_name}'...")
            
            # Write the chunk to a new CSV file
            with open(output_path, 'w', newline='') as outfile:
                writer = csv.writer(outfile)
                writer.writerow(header)  # Write the header
                writer.writerows(chunk)  # Write the student data
            
            logger.info(f"Successfully created '{output_file_name}'.")

    except FileNotFoundError:
        logger.error(f"Error: The source file '{SOURCE_FILE_NAME}' was not found in the '{script_dir}' directory.")
    except StopIteration:
        logger.error(f"Error: The source file '{SOURCE_FILE_NAME}' is empty or contains only a header.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    logger.info("Starting CSV splitting script...")
    split_csv()
    logger.info("CSV splitting script finished.") 