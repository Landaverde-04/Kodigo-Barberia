"""Clasificación única de roles del negocio sobre Groups de Django."""
from functools import wraps

from django.core.exceptions import PermissionDenied

CLIENTE = 'Cliente'
BARBERO = 'Barbero'
ADMINISTRADOR = 'Administrador'
ROLES_NEGOCIO = (CLIENTE, BARBERO, ADMINISTRADOR)


def obtener_rol(usuario):
    if not usuario.is_authenticated or not usuario.is_active:
        return None
    if usuario.is_superuser:
        return ADMINISTRADOR
    roles = list(usuario.groups.filter(name__in=ROLES_NEGOCIO).values_list('name', flat=True))
    if len(roles) > 1:
        raise PermissionDenied('La cuenta tiene roles incompatibles. Consulta al administrador.')
    # La ausencia de grupo nunca concede privilegios. El registro explícito asignará Cliente.
    return roles[0] if roles else CLIENTE


def es_administrador(usuario):
    return obtener_rol(usuario) == ADMINISTRADOR


def rol_requerido(*roles):
    def decorar(vista):
        @wraps(vista)
        def protegida(request, *args, **kwargs):
            if obtener_rol(request.user) not in roles:
                raise PermissionDenied
            return vista(request, *args, **kwargs)
        return protegida
    return decorar
