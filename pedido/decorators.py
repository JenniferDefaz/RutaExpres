from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def rol_requerido(*roles):
    """Decorator that checks if logged-in user has one of the specified roles."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url='login')
        def wrapper(request, *args, **kwargs):
            if hasattr(request.user, 'perfil') and request.user.perfil.rol in roles:
                return view_func(request, *args, **kwargs)
            messages.error(request, 'No tiene permisos para acceder a esta sección.')
            return redirect('inicio')
        return wrapper
    return decorator

def secretario_requerido(view_func):
    return rol_requerido('SECRETARIO')(view_func)

def despachador_requerido(view_func):
    return rol_requerido('DESPACHADOR')(view_func)

def cliente_requerido(view_func):
    return rol_requerido('CLIENTE')(view_func)
