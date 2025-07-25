import bcrypt
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from config import settings
import uuid

# Configure security module logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
security_logger = logging.getLogger("security")

def verify_password(plain_password, hashed_password):
    """Verifies a plain-text password against a hashed one."""
    try:
        security_logger.debug(f"Password verification attempt")
        security_logger.debug(f"Plain password length: {len(plain_password) if plain_password else 0}")
        security_logger.debug(f"Hashed password length: {len(hashed_password) if hashed_password else 0}")
        
        if not plain_password or not hashed_password:
            security_logger.warning("Password verification failed: missing password or hash")
            return False
            
        # Perform password verification
        result = bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        
        if result:
            security_logger.info("Password verification: SUCCESS")
        else:
            security_logger.warning("Password verification: FAILED - passwords do not match")
            
        return result
        
    except Exception as e:
        security_logger.error(f"Password verification ERROR: {str(e)}")
        security_logger.error(f"Error type: {type(e).__name__}")
        return False


def get_password_hash(password):
    """Hashes a plain-text password."""
    try:
        security_logger.debug(f"Hashing password of length: {len(password) if password else 0}")
        
        if not password:
            security_logger.error("Password hashing failed: empty password provided")
            raise ValueError("Password cannot be empty")
            
        # It's important to use encode to convert the string to bytes.
        hashed_bytes = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        hashed_string = hashed_bytes.decode('utf-8')
        
        security_logger.info(f"Password hashed successfully - hash length: {len(hashed_string)}")
        
        # Return the hash as a string to store in the database.
        return hashed_string
        
    except Exception as e:
        security_logger.error(f"Password hashing ERROR: {str(e)}")
        security_logger.error(f"Error type: {type(e).__name__}")
        raise


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Creates a JWT access token with session management."""
    try:
        security_logger.info("Creating access token...")
        security_logger.debug(f"Token data keys: {list(data.keys())}")
        
        to_encode = data.copy()
        
        # Calculate expiration time
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
            security_logger.debug(f"Using custom expiration delta: {expires_delta}")
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            security_logger.debug(f"Using default expiration: {settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutes")
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        to_encode.update({"exp": expire, "session_id": session_id})
        
        security_logger.info(f"Token expiration: {expire}")
        security_logger.info(f"Session ID generated: {session_id}")
        
        # Encode JWT
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        security_logger.info(f"JWT token created successfully - length: {len(encoded_jwt)}")
        security_logger.debug(f"Token algorithm: {settings.ALGORITHM}")
        
        return encoded_jwt
        
    except Exception as e:
        security_logger.error(f"Token creation ERROR: {str(e)}")
        security_logger.error(f"Error type: {type(e).__name__}")
        raise


def verify_token(token: str):
    """Verifies a JWT token and returns the payload."""
    try:
        security_logger.debug("Verifying JWT token...")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        security_logger.info("Token verification successful")
        return payload
    except JWTError as e:
        security_logger.warning(f"Token verification failed: {str(e)}")
        raise
    except Exception as e:
        security_logger.error(f"Unexpected error during token verification: {str(e)}")
        raise
 