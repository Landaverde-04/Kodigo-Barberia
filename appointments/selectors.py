"""Consultas reutilizables de citas (docs/CONTRATOS.md). Solo lectura.

La disponibilidad es informativa: reservar_cita vuelve a validar todo al guardar.
"""
from datetime import datetime, timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from barbers.models import Barbero
from core.horarios import HORA_APERTURA, HORA_CIERRE, INTERVALO_MINUTOS, calcular_fin_validado
from seguridad.roles import BARBERO, obtener_rol
from services.models import Servicio

from .models import Cita, EstadoCita
from .services import barbero_habilitado


def _limites_del_dia(fecha):
    """Apertura y cierre del día como instantes con la zona horaria del negocio."""
    zona = timezone.get_default_timezone()
    apertura = timezone.make_aware(datetime.combine(fecha, HORA_APERTURA), zona)
    cierre = timezone.make_aware(datetime.combine(fecha, HORA_CIERRE), zona)
    return apertura, cierre


def obtener_horarios_disponibles(*, servicio_id, barbero_id, fecha):
    """Inicios libres (datetime con zona, ordenados) para el servicio y barbero en esa fecha.

    Devuelve una lista vacía si el servicio o el barbero no están habilitados,
    si el día está cerrado o si ya no quedan horarios futuros.
    """
    servicio = Servicio.objects.filter(pk=servicio_id, activo=True).first()
    barbero = Barbero.objects.select_related('usuario').filter(pk=barbero_id).first()
    if servicio is None or barbero is None or not barbero_habilitado(barbero):
        return []

    apertura, cierre = _limites_del_dia(fecha)
    ocupados = list(
        Cita.objects.filter(barbero_id=barbero.pk, fecha_inicio__lt=cierre, fecha_fin__gt=apertura)
        .exclude(estado=EstadoCita.CANCELADA)
        .values_list('fecha_inicio', 'fecha_fin')
    )
    ahora = timezone.now()
    duracion = timedelta(minutes=servicio.duracion_minutos)
    paso = timedelta(minutes=INTERVALO_MINUTOS)

    disponibles = []
    inicio = apertura
    while inicio + duracion <= cierre:
        try:
            fin = calcular_fin_validado(inicio, servicio.duracion_minutos, ahora=ahora)
        except ValidationError:
            # Pasado, domingo u otra regla del horario común: no se ofrece.
            fin = None
        if fin and not any(ocupado_inicio < fin and ocupado_fin > inicio for ocupado_inicio, ocupado_fin in ocupados):
            disponibles.append(inicio)
        inicio += paso
    return disponibles


def obtener_agenda_barbero(*, actor, fecha):
    """Citas (todos los estados) del barbero autenticado que empiezan en esa fecha."""
    if obtener_rol(actor) != BARBERO:
        raise PermissionDenied('Solo un barbero puede consultar su agenda.')
    apertura, _ = _limites_del_dia(fecha)
    siguiente = apertura + timedelta(days=1)
    return (
        Cita.objects.filter(barbero__usuario=actor, fecha_inicio__gte=apertura, fecha_inicio__lt=siguiente)
        .select_related('cliente', 'servicio', 'barbero__usuario')
        .order_by('fecha_inicio', 'pk')
    )


def obtener_citas_cliente(*, actor):
    """Todas las citas reservadas por el actor como cliente."""
    if obtener_rol(actor) is None:
        raise PermissionDenied
    return (
        Cita.objects.filter(cliente=actor)
        .select_related('barbero__usuario', 'servicio')
        .order_by('fecha_inicio', 'pk')
    )
