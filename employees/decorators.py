from django.core.exceptions import PermissionDenied
from functools import wraps

def superadmin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_superuser or (hasattr(request.user, 'profil') and request.user.profil.is_superadmin):
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return _wrapped_view

def dept_admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_superuser or (hasattr(request.user, 'profil') and request.user.profil.is_dept_admin):
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return _wrapped_view

def rh_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_superuser or (hasattr(request.user, 'profil') and request.user.profil.is_rh):
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return _wrapped_view

def manager_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_superuser or (hasattr(request.user, 'profil') and (request.user.profil.is_manager or request.user.profil.is_superadmin or request.user.profil.is_rh)):
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return _wrapped_view
