"""FastAPI dependency functions for Auth0 authentication and authorisation."""

from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.auth0 import get_roles, verify_token

_bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> dict[str, Any]:
    """Validate the Bearer token and return the decoded payload.

    Raises:
        HTTPException 401: if the token is missing or invalid.
    """
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
        roles = get_roles(payload)
        if role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' is required to access this resource",
            )
        return payload

    return _check_role
