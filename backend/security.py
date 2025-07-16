import bcrypt
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from .config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_password(plain_password, hashed_password):
    """Verifies a plain-text password against a hashed one."""
    logging.info("--- Inside security.verify_password ---")
    logging.info(f"Plain password to check: '{plain_password}'")
    logging.info(f"Hashed password from DB: '{hashed_password}'")
    result = bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    logging.info(f"bcrypt.checkpw comparison result: {result}")
    logging.info("------------------------------------")
    return result


def get_password_hash(password):
    """Hashes a plain-text password."""
    # It's important to use encode to convert the string to bytes.
    hashed_bytes = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    # Return the hash as a string to store in the database.
    return hashed_bytes.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt 