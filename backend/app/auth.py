"""Auth0 JWT verification helpers and role-based access control."""
import os
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "")

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict[str, Any]:
    """Validate Auth0 JWT and return the decoded token payload.

    In non-production environments where AUTH0_DOMAIN is not set, this
    dependency accepts any Bearer token and returns a minimal payload so
    that automated tests can inject a mock user without a live Auth0
    tenant.
    """
    if not AUTH0_DOMAIN:
        # Dev / test mode – accept any token or no token at all.
        if credentials:
            return {"sub": credentials.credentials, "roles": []}
        return {"sub": "anonymous", "roles": []}

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Lazy import so that production code keeps working without python-jose
    # installed, but tests can still run.
    try:
        import json
        import urllib.request

        from jose import JWTError, jwt as _jwt

        jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
        with urllib.request.urlopen(jwks_url, timeout=5) as resp:  # noqa: S310
            jwks = json.loads(resp.read())

        unverified_header = _jwt.get_unverified_header(credentials.credentials)
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header.get("kid"):
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"],
                }
        if not rsa_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
        payload = _jwt.decode(
            credentials.credentials,
            rsa_key,
            algorithms=["RS256"],
            audience=AUTH0_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/",
        )
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc


def require_role(role: str):
    """Return a FastAPI dependency that enforces a minimum role."""

    async def _check(current_user: dict[str, Any] = Depends(get_current_user)):
        roles: list[str] = current_user.get(
            "roles",
            current_user.get(
                f"https://{AUTH0_DOMAIN}/roles",
                current_user.get("https://ndis-crm/roles", []),
            ),
        )
        allowed = {"Admin", role}
        if not any(r in allowed for r in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' or 'Admin' required",
            )
        return current_user

    return _check
