"""Auth0 JWT token verification middleware."""

import asyncio
import os
from typing import Any

import httpx
from jose import JWTError, jwt
from fastapi import HTTPException, status

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "")

if not AUTH0_DOMAIN:
    raise RuntimeError("AUTH0_DOMAIN environment variable is not set")
if not AUTH0_AUDIENCE:
    raise RuntimeError("AUTH0_AUDIENCE environment variable is not set")

_jwks_cache: dict[str, Any] | None = None
_jwks_lock = asyncio.Lock()


async def _get_jwks() -> dict[str, Any]:
    """Fetch the JWKS from the Auth0 tenant (cached per process startup)."""
    global _jwks_cache
    async with _jwks_lock:
        if _jwks_cache is None:
            url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                _jwks_cache = response.json()
    return _jwks_cache


async def verify_token(token: str) -> dict[str, Any]:
    """Verify an RS256 JWT issued by Auth0 and return its decoded payload.

    Raises:
        HTTPException 401: if the token is invalid, expired, or cannot be verified.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError:
        raise credentials_exception

    jwks = await _get_jwks()
    rsa_key: dict[str, Any] = {}
    for key in jwks.get("keys", []):
        if key.get("kid") == unverified_header.get("kid"):
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"],
            }
            break

    if not rsa_key:
        raise credentials_exception

    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=AUTH0_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/",
        )
    except JWTError:
        raise credentials_exception

    return payload


def get_roles(payload: dict[str, Any]) -> list[str]:
    """Extract roles from the Auth0 token payload.

    Auth0 adds roles under the ``https://`` namespace claim when the
    'Add Roles to Access Token' action/rule is configured.
    """
    namespace = "https://ndis-crm.com/"
    return payload.get(f"{namespace}roles", [])


def get_permissions(payload: dict[str, Any]) -> list[str]:
    """Extract permissions (scopes) from the Auth0 token payload."""
    return payload.get("permissions", [])
