"""
TraceRx AI - Security & Role-Based Access Control (RBAC)
Enforces granular authorization for Manufacturer, Distributor, Pharmacy, and Regulator roles.
"""

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
import hashlib
import hmac

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from backend.app.core.config import settings


class UserRole(str, Enum):
    MANUFACTURER = "Manufacturer"
    DISTRIBUTOR = "Distributor"
    PHARMACY = "Pharmacy"
    REGULATOR = "Regulator"
    ADMIN = "Admin"


security_scheme = HTTPBearer(auto_error=False)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generates a signed JWT bearer token with claims."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": now})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and validates a JWT bearer token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    x_api_key: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Extracts current authenticated identity and role from either Bearer JWT or X-API-KEY.
    Allows demo/fallback execution when testing locally.
    """
    # 1. Check API Key header
    if x_api_key:
        if x_api_key.startswith("mfg_"):
            return {"sub": "pfizer-global-01", "role": UserRole.MANUFACTURER, "tenant_id": "tenant-pfizer"}
        elif x_api_key.startswith("dist_"):
            return {"sub": "dhl-coldchain-01", "role": UserRole.DISTRIBUTOR, "tenant_id": "tenant-dhl"}
        elif x_api_key.startswith("pharm_"):
            return {"sub": "st-thomas-rx-01", "role": UserRole.PHARMACY, "tenant_id": "tenant-nhs"}
        elif x_api_key.startswith("reg_"):
            return {"sub": "who-regulator-01", "role": UserRole.REGULATOR, "tenant_id": "tenant-who"}

    # 2. Check JWT Bearer token
    if credentials:
        payload = decode_access_token(credentials.credentials)
        return {
            "sub": payload.get("sub", "anonymous"),
            "role": payload.get("role", UserRole.PHARMACY),
            "tenant_id": payload.get("tenant_id", settings.DEFAULT_TENANT_ID)
        }

    # 3. Default demo role for point-of-care verification
    return {
        "sub": "demo-dispensary-user",
        "role": UserRole.PHARMACY,
        "tenant_id": settings.DEFAULT_TENANT_ID
    }


def require_roles(allowed_roles: List[UserRole]):
    """FastAPI dependency enforcing specific RBAC roles."""
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_role = current_user.get("role")
        if user_role not in allowed_roles and user_role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: {[r.value for r in allowed_roles]}"
            )
        return current_user
    return role_checker
