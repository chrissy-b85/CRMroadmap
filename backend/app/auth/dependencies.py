"""FastAPI dependency functions for Auth0 authentication and authorisation."""

from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.auth0 import AUTH0_DOMAIN, get_roles, verify_token

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> dict[str, Any]:
    """Validate the Bearer token and return the decoded payload.

    In environments where AUTH0_DOMAIN is not set (e.g. tests), any token
    or no token is accepted and a minimal dev payload is returned.

    Raises:
        HTTPException 401: if the token is missing or invalid in production.
    """
    if not AUTH0_DOMAIN:
        if credentials:
            return {"sub": credentials.credentials, "roles": []}
        return {"sub": "anonymous", "roles": []}

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await verify_token(credentials.credentials)


def require_role(role: str):
    """Return a FastAPI dependency that enforces the given role.

    Usage::

        @router.get("/admin", dependencies=[Depends(require_role("Admin"))])
        async def admin_endpoint(): ...

    Raises:
        HTTPException 403: if the authenticated user does not hold the role.
    """

    async def _check_role(
        payload: dict[str, Any] = Depends(get_current_user),
    ) -> dict[str, Any]:
        roles = get_roles(payload) if AUTH0_DOMAIN else payload.get("roles", [])
        allowed = {"Admin", role}
        if not any(r in allowed for r in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' or 'Admin' required",
            )
        return payload

    return _check_role
