"""Auth0 authentication package.

Re-exports the core FastAPI dependencies so that code can import directly
from ``app.auth`` without needing to know the internal module layout:

    from app.auth import get_current_user, require_role
"""

from app.auth.dependencies import get_current_user, require_role

__all__ = ["get_current_user", "require_role"]
