from functools import wraps

from flask import abort
from flask_login import current_user

from app.models.admin_user import Role


def roles_required(minimum_role: str):
    """Require the logged-in AdminUser to have at least `minimum_role`
    (superadmin > admin > viewer). Must be combined with @login_required
    (or applied to a view already behind one)."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if not current_user.has_role_at_least(minimum_role):
                abort(403)
            return view_func(*args, **kwargs)

        return wrapped

    return decorator


__all__ = ["roles_required", "Role"]
