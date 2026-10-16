import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.user import (
    UserRegister,
    UserLogin,
    UserUpdateProfile,
    UserChangePassword,
    UserRoleUpdate,
    UserResponse,
    TokenResponse,
)
from app.models.common import generate_uuid, get_current_utc_iso
from app.config import settings
from app.services.database import db_manager
from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    get_user_by_username_or_email,
    get_user_by_id,
    get_current_user,
    require_role,
)

logger = logging.getLogger("ecopulse.routes.auth")

router = APIRouter(prefix="/auth", tags=["Authentication & Access Control"])


def sanitize_user_dict(user: dict) -> dict:
    """Strip sensitive fields like hashed_password before serialization."""
    clean = dict(user)
    clean.pop("hashed_password", None)
    clean.pop("password", None)
    clean.pop("_id", None)
    if "notification_preferences" not in clean:
        clean["notification_preferences"] = {
            "email_alerts": True,
            "in_app_alerts": True,
            "minimum_severity": "warning",
            "digest_frequency": "instant"
        }
    if "default_location_id" not in clean:
        clean["default_location_id"] = "station-alpha"
    return clean


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED, summary="Register New User")
async def register(user_in: UserRegister):
    """Register a new EcoPulse AI platform account with bcrypt password hashing and token issuance."""
    # Check for existing user with same username
    existing_username = await get_user_by_username_or_email(user_in.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{user_in.username}' is already registered."
        )

    # Check for existing email
    existing_email = await get_user_by_username_or_email(user_in.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{user_in.email}' is already associated with an account."
        )

    # Restrict direct registration of admin role from public register endpoint
    # First user or explicit analysts
    assigned_role = user_in.role if user_in.role in ["admin", "environmental_analyst", "field_operator"] else "environmental_analyst"

    user_id = f"usr-{generate_uuid()[:8]}"
    created_at = get_current_utc_iso()
    hashed_pw = hash_password(user_in.password)

    new_user = {
        "id": user_id,
        "username": user_in.username.strip(),
        "email": user_in.email.strip().lower(),
        "full_name": user_in.full_name.strip(),
        "role": assigned_role,
        "hashed_password": hashed_pw,
        "is_active": True,
        "created_at": created_at,
        "default_location_id": user_in.default_location_id or "station-alpha",
        "notification_preferences": {
            "email_alerts": True,
            "in_app_alerts": True,
            "minimum_severity": "warning",
            "digest_frequency": "instant"
        }
    }

    if db_manager.is_connected and db_manager.users is not None:
        try:
            await db_manager.users.insert_one(dict(new_user))
        except Exception as e:
            logger.error(f"Error persisting new user: {e}")
            raise HTTPException(status_code=500, detail="Database error during registration.")
    else:
        db_manager.memory_store["users"].append(new_user)

    # Issue JWT token
    token = create_access_token(data={"sub": user_id, "username": new_user["username"], "role": new_user["role"]})
    clean_user = sanitize_user_dict(new_user)

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": UserResponse(**clean_user),
    }


@router.post("/login", response_model=TokenResponse, summary="User Authentication & Token Generation")
async def login(credentials: UserLogin):
    """Authenticate with username or email and password to receive a JWT access token."""
    user = await get_user_by_username_or_email(credentials.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check password
    hashed_pw = user.get("hashed_password")
    if not hashed_pw or not verify_password(credentials.password, hashed_pw):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact an administrator.",
        )

    token = create_access_token(data={"sub": user["id"], "username": user["username"], "role": user.get("role", "environmental_analyst")})
    clean_user = sanitize_user_dict(user)

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": UserResponse(**clean_user),
    }


@router.get("/me", response_model=UserResponse, summary="Get Current Authenticated User Profile")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Retrieve full profile of currently authenticated user via JWT Bearer token."""
    clean = sanitize_user_dict(current_user)
    return UserResponse(**clean)


@router.put("/profile", response_model=UserResponse, summary="Update User Profile & Settings")
async def update_profile(
    profile_in: UserUpdateProfile,
    current_user: dict = Depends(get_current_user),
):
    """Update profile details, default station, and notification preferences."""
    user_id = current_user["id"]
    updates = {}

    if profile_in.full_name is not None:
        updates["full_name"] = profile_in.full_name.strip()
    if profile_in.email is not None:
        updates["email"] = profile_in.email.strip().lower()
    if profile_in.default_location_id is not None:
        updates["default_location_id"] = profile_in.default_location_id
    if profile_in.notification_preferences is not None:
        updates["notification_preferences"] = profile_in.notification_preferences.model_dump()

    if not updates:
        return UserResponse(**sanitize_user_dict(current_user))

    if db_manager.is_connected and db_manager.users is not None:
        try:
            await db_manager.users.update_one({"id": user_id}, {"$set": updates})
            updated_user = await db_manager.users.find_one({"id": user_id}, {"_id": 0})
            return UserResponse(**sanitize_user_dict(updated_user))
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            raise HTTPException(status_code=500, detail="Database error during profile update.")

    # In-memory store fallback
    for u in db_manager.memory_store.get("users", []):
        if u.get("id") == user_id:
            u.update(updates)
            return UserResponse(**sanitize_user_dict(u))

    raise HTTPException(status_code=404, detail="User account not found.")


@router.post("/change-password", summary="Change Account Password")
async def change_password(
    pwd_in: UserChangePassword,
    current_user: dict = Depends(get_current_user),
):
    """Safely change user password after verifying existing credentials."""
    user_id = current_user["id"]
    hashed_pw = current_user.get("hashed_password")

    if not hashed_pw or not verify_password(pwd_in.current_password, hashed_pw):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password verification failed. Please check your existing password.",
        )

    new_hashed = hash_password(pwd_in.new_password)

    if db_manager.is_connected and db_manager.users is not None:
        try:
            await db_manager.users.update_one({"id": user_id}, {"$set": {"hashed_password": new_hashed}})
        except Exception as e:
            logger.error(f"Error updating password: {e}")
            raise HTTPException(status_code=500, detail="Database error updating password.")
    else:
        for u in db_manager.memory_store.get("users", []):
            if u.get("id") == user_id:
                u["hashed_password"] = new_hashed
                break

    return {"message": "Password updated successfully."}


@router.get("/users", response_model=List[UserResponse], summary="List Platform Users (Admin Only)")
async def list_users(admin_user: dict = Depends(require_role(["admin"]))):
    """Admin-restricted endpoint to list all platform users and roles."""
    if db_manager.is_connected and db_manager.users is not None:
        try:
            cursor = db_manager.users.find({}, {"_id": 0, "hashed_password": 0}).sort("created_at", -1)
            users = await cursor.to_list(length=100)
            return [UserResponse(**sanitize_user_dict(u)) for u in users]
        except Exception as e:
            logger.error(f"Error fetching users: {e}")
            raise HTTPException(status_code=500, detail="Database error retrieving users.")

    users = db_manager.memory_store.get("users", [])
    return [UserResponse(**sanitize_user_dict(u)) for u in users]


@router.put("/users/{user_id}/role", response_model=UserResponse, summary="Modify User Role (Admin Only)")
async def modify_user_role(
    user_id: str,
    role_in: UserRoleUpdate,
    admin_user: dict = Depends(require_role(["admin"])),
):
    """Admin-restricted endpoint to update a user's role."""
    valid_roles = ["admin", "environmental_analyst", "field_operator"]
    if role_in.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}."
        )

    if db_manager.is_connected and db_manager.users is not None:
        try:
            res = await db_manager.users.find_one_and_update(
                {"id": user_id},
                {"$set": {"role": role_in.role}},
                return_document=True,
                projection={"_id": 0, "hashed_password": 0}
            )
            if not res:
                raise HTTPException(status_code=404, detail="User not found.")
            return UserResponse(**sanitize_user_dict(res))
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error modifying role: {e}")
            raise HTTPException(status_code=500, detail="Database error updating role.")

    for u in db_manager.memory_store.get("users", []):
        if u.get("id") == user_id:
            u["role"] = role_in.role
            return UserResponse(**sanitize_user_dict(u))

    raise HTTPException(status_code=404, detail="User not found.")
