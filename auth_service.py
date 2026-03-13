from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from config import (
    ACCESS_TOKEN_MINUTES,
    AUTH_CLIENT_ID,
    AUTH_CLIENT_SECRET,
    JWT_ALGORITHM,
    JWT_SECRET,
    REFRESH_TOKEN_DAYS,
)
from schemas import (
    RefreshTokenResponse,
    TokenRefreshRequest,
    TokenRequest,
    TokenResponse,
)

bearer_scheme = HTTPBearer(auto_error=False)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _build_token(payload: Dict[str, Any], expires_delta: timedelta) -> str:
    if not JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT secret is not configured on the server.",
        )
    to_encode = payload.copy()
    to_encode["exp"] = int((_utc_now() + expires_delta).timestamp())
    to_encode["iat"] = int(_utc_now().timestamp())
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),) -> Dict[str, Any]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
        )

    if not JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT secret is not configured on the server.",
        )

    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid JWT token: {exc}",
        )

    return payload


def issue_token(body: TokenRequest) -> TokenResponse:
    if not AUTH_CLIENT_ID or not AUTH_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Auth client credentials are not configured on the server.",
        )

    if body.client_id != AUTH_CLIENT_ID or body.client_secret != AUTH_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client credentials.",
        )

    access_payload = {
        "sub": body.client_id,
        "typ": "access",
    }
    refresh_payload = {
        "sub": body.client_id,
        "typ": "refresh",
    }

    access_token = _build_token(access_payload, timedelta(minutes=ACCESS_TOKEN_MINUTES))
    refresh_token = _build_token(refresh_payload, timedelta(days=REFRESH_TOKEN_DAYS))

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_MINUTES * 60,
        refresh_token=refresh_token,
    )


def refresh_access_token(body: TokenRefreshRequest) -> RefreshTokenResponse:
    if not JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT secret is not configured on the server.",
        )

    try:
        payload = jwt.decode(body.refresh_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid refresh token: {exc}",
        )

    if payload.get("typ") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Provided token is not a refresh token.",
        )

    new_access_payload = {
        "sub": payload.get("sub"),
        "typ": "access",
    }
    new_access_token = _build_token(new_access_payload, timedelta(minutes=ACCESS_TOKEN_MINUTES))

    return RefreshTokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_MINUTES * 60,
    )
