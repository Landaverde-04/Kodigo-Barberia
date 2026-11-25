from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.views.decorators.http import require_safe

from barbers.models import Barbero
from seguridad.roles import BARBERO, obtener_rol
from services.models import Servicio


@require_safe
def portada(request):
    return render(request, 'website/portada.html')


@require_safe
def catalogo_servicios(request):
    servicios = Servicio.objects.filter(activo=True)
    return render(request, 'website/catalogo_servicios.html', {'servicios': servicios})


@require_safe
def catalogo_barberos(request):
    perfiles = Barbero.objects.filter(
        activo=True,
        usuario__is_active=True,
        usuario__is_superuser=False,
        usuario__groups__name=BARBERO,
    ).select_related('usuario')

    barberos = []
    for perfil in perfiles:
        try:
            rol = obtener_rol(perfil.usuario)
        except PermissionDenied:
            continue
        if rol == BARBERO:
            barberos.append({
                'nombre': perfil.usuario.get_full_name(),
                'descripcion': perfil.descripcion,
                'foto': perfil.foto,
            })

    return render(request, 'website/catalogo_barberos.html', {'barberos': barberos})
