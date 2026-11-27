from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_safe

from seguridad.roles import ADMINISTRADOR, BARBERO, rol_requerido

from .forms import PerfilBarberoForm
from .models import Barbero
from .selectors import listar_perfiles, obtener_perfil_de_usuario


def _guardar_perfil(request, perfil):
    form = PerfilBarberoForm(request.POST, request.FILES, instance=perfil)
    if not form.is_valid():
        return form, False
    if form.changed_data:
        perfil = form.save(commit=False)
        perfil.save(update_fields=[*form.changed_data, 'fecha_modificacion'])
    return form, True


@login_required
@rol_requerido(BARBERO)
@require_http_methods(['GET', 'HEAD', 'POST'])
def mi_perfil(request):
    perfil = obtener_perfil_de_usuario(request.user)
    if perfil is None:
        raise Http404

    if request.method == 'POST':
        form, guardado = _guardar_perfil(request, perfil)
        if guardado:
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('barbers:mi_perfil')
    else:
        form = PerfilBarberoForm(instance=perfil)

    return render(request, 'barbers/mi_perfil.html', {'form': form, 'perfil': perfil})


@login_required
@permission_required('barbers.view_barbero', raise_exception=True)
@rol_requerido(ADMINISTRADOR)
@require_safe
def lista_barberos(request):
    return render(request, 'barbers/lista_barberos.html', {'perfiles': listar_perfiles()})


@login_required
@permission_required('barbers.change_barbero', raise_exception=True)
@rol_requerido(ADMINISTRADOR)
@require_http_methods(['GET', 'HEAD', 'POST'])
def editar_perfil(request, pk):
    perfil = get_object_or_404(Barbero, pk=pk)

    if request.method == 'POST':
        form, guardado = _guardar_perfil(request, perfil)
        if guardado:
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('barbers:lista_barberos')
    else:
        form = PerfilBarberoForm(instance=perfil)

    return render(request, 'barbers/form_perfil.html', {
        'form': form,
        'perfil': perfil,
        'accion': 'Editar',
        'volver_url': reverse('barbers:lista_barberos'),
    })
