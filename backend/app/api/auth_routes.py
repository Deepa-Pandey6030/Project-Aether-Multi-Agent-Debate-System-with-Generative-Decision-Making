"""
Auth routes for AETHER
POST /auth/signup
POST /auth/login
POST /auth/refresh
POST /auth/logout
GET  /auth/me
"""

from fastapi import APIRouter, HTTPException, Request, status, Depends

from app.core.security import verify_password, create_access_token, decode_refresh_token
from app.models.user import (
    SignupRequest, LoginRequest, TokenResponse,
    RefreshRequest, AccessTokenResponse, UserPublic
)
from app.services.user_store import (
    create_user, get_user_by_email, get_user_by_username,
    update_last_login, to_public,
    create_session, get_session_by_token, revoke_session
)
from app.api.dependencies import get_current_user
from app.models.user import UserInDB

auth_router = APIRouter()


# ---------------------------------------------------------------------------
# Signup
# ---------------------------------------------------------------------------

@auth_router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: Request, body: SignupRequest):
    # Check email uniqueness
    if await get_user_by_email(body.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check username uniqueness
    if await get_user_by_username(body.username):
        raise HTTPException(status_code=400, detail="Username already taken")

    user = await create_user(
        email=body.email,
        username=body.username,
        plain_password=body.password,
    )

    access_token = create_access_token(user.user_id, user.email)
    ip = request.client.host if request.client else None
    raw_refresh, _ = await create_session(
        user_id=user.user_id,
        ip_address=ip,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        user=to_public(user),
    )


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@auth_router.post("/login", response_model=TokenResponse)
async def login(request: Request, body: LoginRequest):
    user = await get_user_by_username(body.username)

    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    await update_last_login(user.user_id)

    access_token = create_access_token(user.user_id, user.email)
    ip = request.client.host if request.client else None
    raw_refresh, _ = await create_session(
        user_id=user.user_id,
        ip_address=ip,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        user=to_public(user),
    )


# ---------------------------------------------------------------------------
# Refresh access token
# ---------------------------------------------------------------------------

@auth_router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_token(body: RefreshRequest):
    # Validate the JWT signature + type first
    payload = decode_refresh_token(body.refresh_token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    # Check the session exists in DB and is not revoked
    session = await get_session_by_token(body.refresh_token)
    if session is None:
        raise HTTPException(status_code=401, detail="Session not found or revoked")

    user_id: str = payload["sub"]
    new_access = create_access_token(user_id, payload.get("email", ""))

    return AccessTokenResponse(access_token=new_access)


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

@auth_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: RefreshRequest):
    """Revoke the refresh token / session."""
    await revoke_session(body.refresh_token)


# ---------------------------------------------------------------------------
# Me
# ---------------------------------------------------------------------------

@auth_router.get("/me", response_model=UserPublic)
async def me(current_user: UserInDB = Depends(get_current_user)):
    return to_public(current_user)