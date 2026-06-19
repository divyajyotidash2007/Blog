from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

# FastAPI dependency — reads the Bearer token from the Authorization header
bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(github_username: str, avatar_url: str, name: str) -> str:
    """Create a signed JWT token containing the user's GitHub profile."""
    payload = {
        "sub": github_username,          # subject — who this token belongs to
        "avatar_url": avatar_url,
        "name": name,
        "is_admin": github_username == settings.ADMIN_GITHUB_USERNAME,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and verify a JWT token. Raises HTTPException if invalid or expired."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """FastAPI dependency — returns the decoded token payload if the token is valid."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return decode_access_token(credentials.credentials)


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """FastAPI dependency — only allows the admin user through."""
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
