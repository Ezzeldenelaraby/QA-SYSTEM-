from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import AccessMixin

def role_required(allowed_roles):
    """Decorator to require specific roles to access a view."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.shortcuts import redirect
                from django.conf import settings
                return redirect(settings.LOGIN_URL)
            if request.user.is_superuser or request.user.role == 'SUPER_ADMIN' or request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied("You do not have the required role to access this page.")
        return _wrapped_view
    return decorator

class RoleRequiredMixin(AccessMixin):
    """Verify that the current user has one of the allowed roles."""
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.is_superuser or request.user.role == 'SUPER_ADMIN' or request.user.role in self.allowed_roles:
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied("You do not have the required role to access this page.")
