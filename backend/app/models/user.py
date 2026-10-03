"""
Pydantic models for User and Session
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum


class UserPlan(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class UserInDB(BaseModel):
    """Full user document as stored in MongoDB"""
    user_id: str
    email: str
    username: str
    hashed_password: str
    is_active: bool = True
    is_verified: bool = False
    plan: UserPlan = UserPlan.FREE
    debates_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None


class UserPublic(BaseModel):
    """Safe user object returned to the client — no password"""
    user_id: str
    email: str
    username: str
    is_active: bool
    plan: UserPlan
    debates_count: int
    created_at: datetime


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

class SessionInDB(BaseModel):
    """Refresh token session stored in MongoDB"""
    session_id: str
    user_id: str
    refresh_token: str           # store the raw JWT (it is already signed)
    device_info: Optional[str] = None
    ip_address: Optional[str] = None
    is_revoked: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime


# ---------------------------------------------------------------------------
# Auth request / response schemas
# ---------------------------------------------------------------------------

class SignupRequest(BaseModel):
    email: str
    username: str = Field(..., min_length=3, max_length=30)
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    username: str          # login with username
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserPublic


class RefreshRequest(BaseModel):
    refresh_token: str


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"