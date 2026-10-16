import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings
from app.services.database import db_manager

logger = logging.getLogger("ecopulse.auth")

security = HTTPBearer(auto_error=False)

DEFAULT_SEED_PASSWORD = "EcoPulse@2026"


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt with salt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception as e:
        logger.warning(f"Password verification error: {e}")
        return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generate a signed JWT access token with expiration."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_user_by_username_or_email(identifier: str) -> Optional[Dict[str, Any]]:
    """Fetch user by username or email from MongoDB Atlas or memory store."""
    clean_id = identifier.strip().lower()

    if db_manager.is_connected and db_manager.users is not None:
        try:
            user = await db_manager.users.find_one(
                {"$or": [{"username": clean_id}, {"email": clean_id}]},
                {"_id": 0}
            )
            if user:
                return user
        except Exception as e:
            logger.warning(f"Database lookup error for user '{identifier}': {e}")

    # Fallback to in-memory store
    users = db_manager.memory_store.get("users", [])
    for u in users:
        if u.get("username", "").lower() == clean_id or u.get("email", "").lower() == clean_id:
            return u
    return None


async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Fetch user by unique user ID."""
    if db_manager.is_connected and db_manager.users is not None:
        try:
            user = await db_manager.users.find_one({"id": user_id}, {"_id": 0})
            if user:
                return user
        except Exception as e:
            logger.warning(f"Database lookup error for user ID '{user_id}': {e}")

    users = db_manager.memory_store.get("users", [])
    for u in users:
        if u.get("id") == user_id:
            return u
    return None


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    """Dependency: Extract, decode JWT, and return active authenticated user."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token payload missing subject.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account associated with this token was not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated. Contact an administrator.",
        )

    return user


async def get_optional_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict[str, Any]]:
    """Optional authentication dependency (does not reject unauthenticated requests)."""
    if not credentials or not credentials.credentials:
        return None
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("sub")
        if user_id:
            return await get_user_by_id(user_id)
    except Exception:
        pass
    return None


def require_role(allowed_roles: List[str]):
    """Role-based authorization dependency factory."""
    async def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = current_user.get("role", "environmental_analyst")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: {', '.join(allowed_roles)} (current: {user_role})."
            )
        return current_user
    return role_checker


# Seed password initialization for in-memory default accounts
def initialize_seed_user_passwords():
    """Ensure in-memory default users have hashed passwords so they can immediately log in."""
    users = db_manager.memory_store.get("users", [])
    hashed_seed_pw = hash_password(DEFAULT_SEED_PASSWORD)
    for u in users:
        if "hashed_password" not in u:
            u["hashed_password"] = hashed_seed_pw
        if "default_location_id" not in u:
            u["default_location_id"] = "station-alpha"
        if "notification_preferences" not in u:
            u["notification_preferences"] = {
                "email_alerts": True,
                "in_app_alerts": True,
                "minimum_severity": "warning",
                "digest_frequency": "instant"
            }


initialize_seed_user_passwords()
