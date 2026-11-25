from django.shortcuts import render
from django.views.decorators.http import require_safe

from services.models import Servicio


@require_safe
def portada(request):
    return render(request, 'website/portada.html')


@require_safe
def catalogo_servicios(request):
    servicios = Servicio.objects.filter(activo=True)
    return render(request, 'website/catalogo_servicios.html', {'servicios': servicios})
