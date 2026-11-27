from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode
from django.views.decorators.http import require_POST, require_http_methods, require_safe

from appointments.forms import CancelarCitaForm
from appointments.models import Cita, EstadoCita
from appointments.selectors import obtener_agenda_barbero
from appointments.services import cancelar_cita, completar_cita
from seguridad.roles import ADMINISTRADOR, BARBERO, rol_requerido

from .forms import FechaAgendaForm, PerfilBarberoForm
from .models import Barbero
from .selectors import listar_perfiles, obtener_perfil_de_usuario


def _mensajes(error):
    return error.messages if hasattr(error, 'messages') else [str(error)]


def _cita_para_fecha(pk):
    return Cita.objects.filter(pk=pk).only('fecha_inicio').first()


def _url_agenda(request, cita=None):
    """Vuelve a la fecha que se estaba viendo, con una fecha segura de respaldo."""
    valor = (request.GET.get('fecha') or '').strip()
    fecha = None
    if valor:
        form = FechaAgendaForm({'fecha': valor})
        if form.is_valid():
            fecha = form.cleaned_data['fecha']
    if fecha is None and cita is not None:
        fecha = timezone.localtime(cita.fecha_inicio).date()
    if fecha is None:
        fecha = timezone.localdate()
    consulta = urlencode({'fecha': fecha.isoformat()})
    return f"{reverse('barbers:agenda')}?{consulta}"


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
@permission_required('appointments.view_cita', raise_exception=True)
@rol_requerido(BARBERO)
@require_safe
def agenda(request):
    """Agenda privada del barbero autenticado; la fecha se elige por GET."""
    valor = request.GET.get('fecha', '').strip()
    hoy = timezone.localdate()

    if valor:
        form = FechaAgendaForm({'fecha': valor})
        fecha = None
        citas = None
        if form.is_valid():
            fecha = form.cleaned_data['fecha']
            citas = obtener_agenda_barbero(actor=request.user, fecha=fecha)
    else:
        fecha = hoy
        form = FechaAgendaForm(initial={'fecha': fecha.isoformat()})
        citas = obtener_agenda_barbero(actor=request.user, fecha=fecha)

    return render(request, 'barbers/agenda.html', {
        'form': form,
        'form_cancelar': CancelarCitaForm(auto_id=False),
        'fecha': fecha,
        'citas': citas,
        'anterior': fecha - timedelta(days=1) if fecha else None,
        'siguiente': fecha + timedelta(days=1) if fecha else None,
        'hoy': hoy,
        'estado_confirmada': EstadoCita.CONFIRMADA,
        'perfil': obtener_perfil_de_usuario(request.user),
    })


@login_required
@permission_required('appointments.change_cita', raise_exception=True)
@rol_requerido(BARBERO)
@require_POST
def cancelar_cita_barbero(request, pk):
    """Cancela una cita propia mediante el servicio compartido de Samuel."""
    form = CancelarCitaForm(request.POST)
    if not form.is_valid():
        for errores in form.errors.values():
            for mensaje in errores:
                messages.error(request, mensaje)
        return redirect(_url_agenda(request, _cita_para_fecha(pk)))

    try:
        cita = cancelar_cita(
            actor=request.user, cita_id=pk, motivo=form.cleaned_data['motivo'],
        )
    except (Cita.DoesNotExist, PermissionDenied):
        # No revelar si una cita ajena existe.
        raise Http404 from None
    except ValidationError as error:
        for mensaje in _mensajes(error):
            messages.error(request, mensaje)
        cita = _cita_para_fecha(pk)
        return redirect(_url_agenda(request, cita))

    messages.success(request, 'La cita fue cancelada.')
    return redirect(_url_agenda(request, cita))


@login_required
@permission_required('appointments.change_cita', raise_exception=True)
@rol_requerido(BARBERO)
@require_POST
def completar_cita_barbero(request, pk):
    """Finaliza una cita propia mediante el servicio compartido de Samuel."""
    try:
        cita = completar_cita(actor=request.user, cita_id=pk)
    except (Cita.DoesNotExist, PermissionDenied):
        # No revelar si una cita ajena existe.
        raise Http404 from None
    except ValidationError as error:
        for mensaje in _mensajes(error):
            messages.error(request, mensaje)
        cita = _cita_para_fecha(pk)
        return redirect(_url_agenda(request, cita))

    messages.success(request, 'La cita fue completada.')
    return redirect(_url_agenda(request, cita))


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

    return render(request, 'barbers/editar_perfil.html', {
        'form': form,
        'perfil': perfil,
        'volver_url': reverse('barbers:lista_barberos'),
    })
