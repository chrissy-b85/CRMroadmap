"""Auth package – re-export public API for backwards-compatible imports."""

from app.auth.dependencies import get_current_user, require_role

__all__ = ["get_current_user", "require_role"]
