"""Horario único aprobado. Cambiarlo requiere acuerdo del equipo."""
from datetime import time, timedelta

from django.core.exceptions import ValidationError
from django.utils import timezone

DIAS_LABORALES = (0, 1, 2, 3, 4, 5)  # Lunes=0; domingo cerrado.
HORA_APERTURA = time(8, 0)
HORA_CIERRE = time(17, 0)
INTERVALO_MINUTOS = 15


def validar_duracion(valor):
    if valor <= 0 or valor % INTERVALO_MINUTOS:
        raise ValidationError('La duración debe ser positiva y múltiplo de 15 minutos.', code='duracion_invalida')


def calcular_fin_validado(fecha_inicio, duracion_minutos, *, ahora=None):
    """Valida el horario de una reserva nueva y devuelve su fin con zona horaria."""
    validar_duracion(duracion_minutos)
    if timezone.is_naive(fecha_inicio):
        raise ValidationError('La fecha debe incluir zona horaria.', code='zona_horaria_requerida')
    if fecha_inicio <= (ahora if ahora is not None else timezone.now()):
        raise ValidationError('La cita debe comenzar en el futuro.', code='inicio_pasado')
    inicio_local = timezone.localtime(fecha_inicio)
    fin = fecha_inicio + timedelta(minutes=duracion_minutos)
    fin_local = timezone.localtime(fin)
    if inicio_local.weekday() not in DIAS_LABORALES:
        raise ValidationError('La barbería no atiende los domingos.', code='dia_cerrado')
    if (inicio_local.time() < HORA_APERTURA or inicio_local.date() != fin_local.date()
            or fin_local.time() > HORA_CIERRE):
        raise ValidationError('La cita completa debe estar entre las 08:00 y las 17:00.', code='fuera_horario')
    minutos = inicio_local.hour * 60 + inicio_local.minute - HORA_APERTURA.hour * 60
    if inicio_local.second or inicio_local.microsecond or minutos % INTERVALO_MINUTOS:
        raise ValidationError('El inicio debe estar alineado a intervalos de 15 minutos.', code='inicio_desalineado')
    return fin
