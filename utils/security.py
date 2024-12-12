from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status, FastAPI
from fastapi.security import OAuth2PasswordBearer
import os
import secrets
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# JWT Configuration
SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY", "your-secret-key-for-testing"
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="v1/auth/token")

# JWT settings
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(
    data: Dict, expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, SECRET_KEY, algorithm=ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """Verify a JWT token and return the user_id if valid"""
    try:
        payload = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except JWTError:
        return None


def generate_user_secret() -> str:
    """Generate a secure random user secret"""
    return secrets.token_urlsafe(32)


def hash_user_secret(user_secret: str) -> str:
    """Hash a user secret using bcrypt"""
    # Convert the user_secret to bytes and generate a salt
    password = user_secret.encode('utf-8')
    salt = bcrypt.gensalt()
    # Hash the password
    hashed = bcrypt.hashpw(password, salt)
    # Return the hash as a string
    return hashed.decode('utf-8')


def verify_user_secret(plain_secret: str, hashed_secret: str) -> bool:
    """Verify a user secret against its hash using bcrypt"""
    try:
        # Convert strings to bytes for bcrypt
        password = plain_secret.encode('utf-8')
        stored_hash = hashed_secret.encode('utf-8')
        # Check if the password matches
        return bcrypt.checkpw(password, stored_hash)
    except Exception:
        return False


def hash_secret(secret: str) -> str:
    """Hash a secret using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(secret.encode(), salt).decode()


def verify_secret(plain_secret: str, hashed_secret: str) -> bool:
    """Verify a secret against its hash"""
    return bcrypt.checkpw(
        plain_secret.encode(), hashed_secret.encode()
    )


def create_access_token_jwt(
    data: Dict, expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> Dict:
    """Decode a JWT token"""
    try:
        payload = jwt.decode(
            token, JWT_SECRET, algorithms=[JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> Dict:
    """Get the current user from the JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_token(token)
        user_id = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
        return {"user_id": user_id}
    except jwt.JWTError:
        raise credentials_exception
