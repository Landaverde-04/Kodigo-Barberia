from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST, require_safe

from seguridad.roles import ADMINISTRADOR, rol_requerido

from .forms import ServicioForm
from .models import Servicio


@login_required
@permission_required('services.view_servicio', raise_exception=True)
@rol_requerido(ADMINISTRADOR)
@require_safe
def lista_servicios(request):
    return render(request, 'services/lista_servicios.html', {'servicios': Servicio.objects.all()})


@login_required
@permission_required('services.add_servicio', raise_exception=True)
@rol_requerido(ADMINISTRADOR)
@require_http_methods(['GET', 'HEAD', 'POST'])
def crear_servicio(request):
    if request.method == 'POST':
        form = ServicioForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Servicio creado correctamente.')
            return redirect('services:lista_servicios')
    else:
        form = ServicioForm()

    return render(request, 'services/form_servicio.html', {'form': form})


@login_required
@permission_required('services.change_servicio', raise_exception=True)
@rol_requerido(ADMINISTRADOR)
@require_http_methods(['GET', 'HEAD', 'POST'])
def editar_servicio(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    if request.method == 'POST':
        form = ServicioForm(request.POST, request.FILES, instance=servicio)
        if form.is_valid():
            if form.changed_data:
                # Editar los datos del catálogo no debe sobrescribir su estado de publicación.
                servicio = form.save(commit=False)
                servicio.save(update_fields=[*form.changed_data, 'fecha_modificacion'])
            messages.success(request, 'Servicio actualizado correctamente.')
            return redirect('services:lista_servicios')
    else:
        form = ServicioForm(instance=servicio)

    return render(request, 'services/form_servicio.html', {'form': form, 'servicio': servicio})


@login_required
@permission_required('services.change_servicio', raise_exception=True)
@rol_requerido(ADMINISTRADOR)
@require_POST
def cambiar_estado_servicio(request, pk, activo):
    with transaction.atomic():
        servicio = get_object_or_404(Servicio.objects.select_for_update(), pk=pk)
        if servicio.activo != activo:
            servicio.activo = activo
            servicio.save(update_fields=['activo', 'fecha_modificacion'])

    messages.success(request, 'Servicio activado.' if activo else 'Servicio desactivado.')
    return redirect('services:lista_servicios')
