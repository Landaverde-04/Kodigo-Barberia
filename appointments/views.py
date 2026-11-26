from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode
from django.views.decorators.http import require_http_methods, require_POST, require_safe

from seguridad.roles import CLIENTE, rol_requerido

from .forms import BuscarHorarioForm, CancelarCitaForm, ConfirmarReservaForm
from .models import Cita, EstadoCita
from .selectors import obtener_citas_cliente, obtener_horarios_disponibles
from .services import cancelar_cita, reservar_cita


def _mensajes(error):
    return error.messages if hasattr(error, 'messages') else [str(error)]


@login_required
@permission_required('appointments.view_cita', raise_exception=True)
@rol_requerido(CLIENTE)
@require_safe
def mis_citas(request):
    citas = obtener_citas_cliente(actor=request.user)
    ahora = timezone.now()
    proximas = citas.filter(estado=EstadoCita.CONFIRMADA, fecha_fin__gt=ahora)
    historial = citas.exclude(pk__in=proximas.values('pk')).order_by('-fecha_inicio', '-pk')
    return render(request, 'appointments/mis_citas.html', {
        'proximas': proximas, 'historial': historial, 'ahora': ahora,
        'form_cancelar': CancelarCitaForm(),
    })


@login_required
@permission_required('appointments.add_cita', raise_exception=True)
@rol_requerido(CLIENTE)
@require_safe
def reservar(request):
    """Paso 1: elegir servicio, barbero y fecha; muestra los horarios libres."""
    form = BuscarHorarioForm(request.GET or None)
    horarios = None
    if form.is_bound and form.is_valid():
        horarios = obtener_horarios_disponibles(
            servicio_id=form.cleaned_data['servicio'].pk,
            barbero_id=form.cleaned_data['barbero'].pk,
            fecha=form.cleaned_data['fecha'],
        )
    return render(request, 'appointments/reservar.html', {'form': form, 'horarios': horarios})


@login_required
@permission_required('appointments.add_cita', raise_exception=True)
@rol_requerido(CLIENTE)
@require_http_methods(['GET', 'HEAD', 'POST'])
def confirmar_reserva(request):
    """Paso 2: resumen con datos del servidor (GET) y reserva definitiva (POST)."""
    datos = request.POST if request.method == 'POST' else request.GET
    form = ConfirmarReservaForm(datos)
    if not form.is_valid():
        for errores in form.errors.values():
            for error in errores:
                messages.error(request, error)
        return redirect('appointments:reservar')

    servicio = form.cleaned_data['servicio']
    barbero = form.cleaned_data['barbero']
    inicio = form.cleaned_data['inicio']

    if request.method == 'POST':
        try:
            cita = reservar_cita(
                actor=request.user, servicio_id=servicio.pk, barbero_id=barbero.pk, fecha_inicio=inicio,
            )
        except ValidationError as error:
            # El horario pudo ocuparse desde que se mostró: volver a las opciones actualizadas.
            for mensaje in _mensajes(error):
                messages.error(request, mensaje)
            consulta = urlencode({
                'servicio': servicio.pk, 'barbero': barbero.pk,
                'fecha': timezone.localtime(inicio).date().isoformat(),
            })
            return redirect(f"{reverse('appointments:reservar')}?{consulta}")
        messages.success(request, 'Tu cita quedó confirmada.')
        return redirect('appointments:detalle_cita', pk=cita.pk)

    return render(request, 'appointments/confirmar.html', {
        'servicio': servicio, 'barbero': barbero, 'inicio': inicio,
        'fin': form.cleaned_data['fin'],
        'inicio_valor': timezone.localtime(inicio).strftime('%Y-%m-%dT%H:%M'),
    })


@login_required
@permission_required('appointments.view_cita', raise_exception=True)
@rol_requerido(CLIENTE)
@require_safe
def detalle_cita(request, pk):
    cita = get_object_or_404(obtener_citas_cliente(actor=request.user), pk=pk)
    return render(request, 'appointments/detalle.html', {
        'cita': cita, 'puede_cancelar': cita.estado == EstadoCita.CONFIRMADA and cita.fecha_inicio > timezone.now(),
        'form_cancelar': CancelarCitaForm(),
    })


@login_required
@permission_required('appointments.change_cita', raise_exception=True)
@rol_requerido(CLIENTE)
@require_POST
def cancelar(request, pk):
    form = CancelarCitaForm(request.POST)
    if not form.is_valid():
        for errores in form.errors.values():
            for error in errores:
                messages.error(request, error)
        return redirect('appointments:detalle_cita', pk=pk)
    try:
        cancelar_cita(actor=request.user, cita_id=pk, motivo=form.cleaned_data['motivo'])
    except Cita.DoesNotExist:
        raise Http404 from None
    except PermissionDenied:
        # No revelar si la cita ajena existe.
        raise Http404 from None
    except ValidationError as error:
        for mensaje in _mensajes(error):
            messages.error(request, mensaje)
        return redirect('appointments:detalle_cita', pk=pk)
    messages.success(request, 'La cita fue cancelada.')
    return redirect('appointments:mis_citas')
