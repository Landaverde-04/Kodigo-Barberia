from datetime import timedelta

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_safe

from seguridad.roles import ADMINISTRADOR, rol_requerido

from .forms import FechaPanelForm
from .selectors import (
    citas_del_dia, contar_cuentas_por_rol, distribucion_por_estado, listado_general,
)


@login_required
@permission_required('seguridad.view_usuario', raise_exception=True)
@permission_required('appointments.view_cita', raise_exception=True)
@rol_requerido(ADMINISTRADOR)
@require_safe
def panel(request):
    """Resumen administrativo de solo lectura; la fecha se elige por GET."""
    hoy = timezone.localdate()
    valor = request.GET.get('fecha', '').strip()
    ver_todas = request.GET.get('ver') == 'todas'

    if valor:
        form = FechaPanelForm({'fecha': valor})
        fecha = None
        if form.is_valid():
            fecha = form.cleaned_data['fecha']
    else:
        fecha = hoy
        form = FechaPanelForm(initial={'fecha': fecha.isoformat()})

    if fecha is None:
        cuentas = None
        citas = None
        total_dia = None
        estados = None
    else:
        cuentas = contar_cuentas_por_rol()
        citas = citas_del_dia(fecha)
        total_dia = citas.count()
        estados = distribucion_por_estado(fecha)

    return render(request, 'dashboard/panel.html', {
        'form': form,
        'fecha': fecha,
        'hoy': hoy,
        'anterior': fecha - timedelta(days=1) if fecha else None,
        'siguiente': fecha + timedelta(days=1) if fecha else None,
        'cuentas': cuentas,
        'citas': citas,
        'total_dia': total_dia,
        'estados': estados,
        'listado': listado_general(None if ver_todas else fecha),
        'ver_todas': ver_todas,
    })
