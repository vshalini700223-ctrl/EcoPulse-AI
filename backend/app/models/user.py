from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from app.models.common import generate_uuid, get_current_utc_iso


class NotificationPreferences(BaseModel):
    email_alerts: bool = Field(default=True, description="Enable email alert dispatch")
    in_app_alerts: bool = Field(default=True, description="Enable in-app alert banner & notifications")
    minimum_severity: str = Field(default="warning", description="Minimum alert severity: critical, warning, info")
    digest_frequency: str = Field(default="instant", description="Delivery frequency: instant, daily, weekly")


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="User email address")
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name")
    role: str = Field(default="environmental_analyst", description="Role: admin, environmental_analyst, field_operator")
    default_location_id: Optional[str] = Field(default="station-alpha", description="Default monitoring location ID")


class UserCreate(UserBase):
    """Backwards-compatible user creation schema."""
    password: Optional[str] = Field(default=None, min_length=6, description="User password")


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Unique username (alphanumeric and underscores)")
    email: EmailStr = Field(..., description="Valid work/personal email address")
    password: str = Field(..., min_length=6, max_length=100, description="Secure account password")
    full_name: str = Field(..., min_length=2, max_length=100, description="Full display name")
    role: Optional[str] = Field(default="environmental_analyst", description="Role: admin, environmental_analyst, field_operator")
    default_location_id: Optional[str] = Field(default="station-alpha", description="Default station ID")


class UserLogin(BaseModel):
    username: str = Field(..., description="Username or email address")
    password: str = Field(..., description="Account password")


class UserUpdateProfile(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    email: Optional[EmailStr] = Field(default=None)
    default_location_id: Optional[str] = Field(default=None)
    notification_preferences: Optional[NotificationPreferences] = Field(default=None)


class UserChangePassword(BaseModel):
    current_password: str = Field(..., description="Existing account password")
    new_password: str = Field(..., min_length=6, max_length=100, description="New secure password")


class UserRoleUpdate(BaseModel):
    role: str = Field(..., description="Role: admin, environmental_analyst, field_operator")


class UserResponse(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool = True
    created_at: str = Field(default_factory=get_current_utc_iso)
    default_location_id: Optional[str] = "station-alpha"
    notification_preferences: Optional[Dict[str, Any]] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
