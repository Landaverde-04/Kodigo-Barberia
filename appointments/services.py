"""Única capa de escritura de citas (docs/CONTRATOS.md).

Códigos de ValidationError estables que pueden consultar otras apps:

- servicio_no_disponible: el servicio no existe para reservar o está inactivo.
- barbero_no_disponible: el perfil o la cuenta del barbero no están habilitados.
- horario_ocupado: el intervalo se cruza con otra cita no cancelada del barbero.
- transicion_invalida: la cita ya no está CONFIRMED.
- cancelacion_fuera_de_plazo: el cliente intenta cancelar después del inicio.
- finalizacion_anticipada: se intenta completar antes de fecha_fin.
- motivo_largo: el motivo de cancelación supera MAX_MOTIVO caracteres.
- Además se propagan los códigos de core.horarios.calcular_fin_validado:
  zona_horaria_requerida, inicio_pasado, dia_cerrado, fuera_horario,
  inicio_desalineado y duracion_invalida.

Un ID de cita inexistente lanza Cita.DoesNotExist (la vista responde 404).
Un actor sin permiso recibe PermissionDenied.
"""
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from barbers.models import Barbero
from core.horarios import calcular_fin_validado
from seguridad.roles import ADMINISTRADOR, BARBERO, CLIENTE, obtener_rol
from services.models import Servicio

from .models import Cita, EstadoCita

RESTRICCION_SUPERPOSICION = 'cita_barbero_sin_superposicion'
MAX_MOTIVO = 500
MENSAJE_OCUPADO = 'Ese horario ya no está disponible con el barbero elegido. Elige otra hora.'


def _rol_seguro(usuario):
    """Rol del usuario; una cuenta con roles ambiguos no se considera habilitada."""
    try:
        return obtener_rol(usuario)
    except PermissionDenied:
        return None


def barbero_habilitado(barbero):
    """Perfil activo, cuenta activa y rol Barbero. Requiere barbero.usuario cargado."""
    return barbero.activo and barbero.usuario.is_active and _rol_seguro(barbero.usuario) == BARBERO


def hay_superposicion(*, barbero_id, fecha_inicio, fecha_fin, excluir_id=None):
    """Intersección estricta: contiguas permitidas; CANCELLED no bloquea."""
    citas = Cita.objects.filter(
        barbero_id=barbero_id, fecha_inicio__lt=fecha_fin, fecha_fin__gt=fecha_inicio,
    ).exclude(estado=EstadoCita.CANCELADA)
    if excluir_id is not None:
        citas = citas.exclude(pk=excluir_id)
    return citas.exists()


def _es_error_superposicion(error):
    causa = error.__cause__
    diag = getattr(causa, 'diag', None)
    return getattr(diag, 'constraint_name', None) == RESTRICCION_SUPERPOSICION


def reservar_cita(*, actor, servicio_id, barbero_id, fecha_inicio):
    """Crea una cita CONFIRMED para el cliente autenticado (actor)."""
    if _rol_seguro(actor) != CLIENTE:
        raise PermissionDenied('Solo una cuenta de cliente puede reservar citas.')
    try:
        return _reservar_en_transaccion(
            actor=actor, servicio_id=servicio_id, barbero_id=barbero_id, fecha_inicio=fecha_inicio,
        )
    except IntegrityError as error:
        # El bloque atomic ya se revirtió; aquí solo se traduce el error.
        if _es_error_superposicion(error):
            raise ValidationError(MENSAJE_OCUPADO, code='horario_ocupado') from None
        raise


@transaction.atomic
def _reservar_en_transaccion(*, actor, servicio_id, barbero_id, fecha_inicio):
    # Orden de bloqueo acordado: Usuario del barbero, Barbero y Servicio.
    usuario_barbero_id = Barbero.objects.filter(pk=barbero_id).values_list('usuario_id', flat=True).first()
    if usuario_barbero_id is None:
        raise ValidationError('El barbero elegido no está disponible.', code='barbero_no_disponible')
    usuario_barbero = get_user_model().objects.select_for_update().get(pk=usuario_barbero_id)
    barbero = Barbero.objects.select_for_update().filter(pk=barbero_id, usuario_id=usuario_barbero.pk).first()
    servicio = Servicio.objects.select_for_update().filter(pk=servicio_id).first()

    if barbero is None:
        raise ValidationError('El barbero elegido no está disponible.', code='barbero_no_disponible')
    barbero.usuario = usuario_barbero
    if not barbero_habilitado(barbero):
        raise ValidationError('El barbero elegido no está disponible.', code='barbero_no_disponible')
    if servicio is None or not servicio.activo:
        raise ValidationError('El servicio elegido no está disponible.', code='servicio_no_disponible')

    # Precio, duración y nombre salen del servidor, nunca del formulario.
    fecha_fin = calcular_fin_validado(fecha_inicio, servicio.duracion_minutos)
    if hay_superposicion(barbero_id=barbero.pk, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin):
        raise ValidationError(MENSAJE_OCUPADO, code='horario_ocupado')

    cita = Cita(
        cliente=actor, barbero=barbero, servicio=servicio,
        fecha_inicio=fecha_inicio, fecha_fin=fecha_fin,
        nombre_servicio_reservado=servicio.nombre,
        precio_reservado=servicio.precio,
        duracion_reservada=servicio.duracion_minutos,
        estado=EstadoCita.CONFIRMADA,
    )
    # La exclusión la verifica PostgreSQL al guardar (también con concurrencia).
    cita.full_clean(validate_constraints=False)
    cita.save()
    return cita


def _es_barbero_asignado(actor, rol, cita):
    return rol == BARBERO and cita.barbero.usuario_id == actor.pk


@transaction.atomic
def cancelar_cita(*, actor, cita_id, motivo=''):
    """Cliente propietario antes del inicio; barbero asignado o administrador si está CONFIRMED."""
    cita = Cita.objects.select_for_update(of=('self',)).select_related('barbero').get(pk=cita_id)
    rol = _rol_seguro(actor)
    ahora = timezone.now()
    motivo = (motivo or '').strip()

    if rol == ADMINISTRADOR or _es_barbero_asignado(actor, rol, cita):
        limite_cliente = False
    elif rol == CLIENTE and cita.cliente_id == actor.pk:
        limite_cliente = True
    else:
        raise PermissionDenied('No puedes cancelar esta cita.')

    if cita.estado != EstadoCita.CONFIRMADA:
        raise ValidationError('Solo se pueden cancelar citas confirmadas.', code='transicion_invalida')
    if limite_cliente and ahora >= cita.fecha_inicio:
        raise ValidationError('La cita ya comenzó; no puede cancelarse desde tu cuenta.', code='cancelacion_fuera_de_plazo')
    if len(motivo) > MAX_MOTIVO:
        raise ValidationError(f'El motivo admite como máximo {MAX_MOTIVO} caracteres.', code='motivo_largo')

    cita.estado = EstadoCita.CANCELADA
    cita.fecha_cancelacion = ahora
    cita.cancelada_por = actor
    cita.motivo_cancelacion = motivo
    cita.save(update_fields=[
        'estado', 'fecha_cancelacion', 'cancelada_por', 'motivo_cancelacion', 'fecha_modificacion',
    ])
    return cita


@transaction.atomic
def completar_cita(*, actor, cita_id):
    """Barbero asignado o administrador, a partir de fecha_fin."""
    cita = Cita.objects.select_for_update(of=('self',)).select_related('barbero').get(pk=cita_id)
    rol = _rol_seguro(actor)
    ahora = timezone.now()

    if not (rol == ADMINISTRADOR or _es_barbero_asignado(actor, rol, cita)):
        raise PermissionDenied('No puedes completar esta cita.')
    if cita.estado != EstadoCita.CONFIRMADA:
        raise ValidationError('Solo se pueden completar citas confirmadas.', code='transicion_invalida')
    if ahora < cita.fecha_fin:
        raise ValidationError('La cita se puede completar cuando llegue su hora de fin.', code='finalizacion_anticipada')

    cita.estado = EstadoCita.COMPLETADA
    cita.fecha_finalizacion = ahora
    cita.completada_por = actor
    cita.save(update_fields=['estado', 'fecha_finalizacion', 'completada_por', 'fecha_modificacion'])
    return cita
