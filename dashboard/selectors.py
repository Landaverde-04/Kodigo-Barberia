"""Consultas de solo lectura para el panel administrativo.

El panel no crea tablas ni escribe citas: solo presenta datos derivados de
seguridad.Usuario, barbers.Barbero y appointments.Cita.
"""
from datetime import datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.utils import timezone

from appointments.models import Cita, EstadoCita
from seguridad.roles import ADMINISTRADOR, BARBERO, CLIENTE, obtener_rol

CLAVES_ROL = {CLIENTE: 'cliente', BARBERO: 'barbero', ADMINISTRADOR: 'administrador'}


def contar_cuentas_por_rol():
    """Totales globales por rol de negocio; cuentas ambiguas van aparte."""
    conteos = {'cliente': 0, 'barbero': 0, 'administrador': 0, 'por_revisar': 0}
    usuarios = get_user_model().objects.prefetch_related('groups').all()
    for usuario in usuarios:
        try:
            rol = obtener_rol(usuario)
        except PermissionDenied:
            conteos['por_revisar'] += 1
            continue
        clave = CLAVES_ROL.get(rol)
        if clave:
            conteos[clave] += 1
    return conteos


def _rango_local(fecha):
    """Inicio y fin del día en la zona horaria del negocio, nunca en UTC."""
    zona = timezone.get_default_timezone()
    inicio_local = datetime.combine(fecha, time.min)
    fin_local = inicio_local + timedelta(days=1)
    return timezone.make_aware(inicio_local, zona), timezone.make_aware(fin_local, zona)


def citas_del_dia(fecha):
    """Citas que empiezan en esa fecha local, ordenadas por inicio y pk."""
    inicio, fin = _rango_local(fecha)
    return (
        Cita.objects.filter(fecha_inicio__gte=inicio, fecha_inicio__lt=fin)
        .select_related('cliente', 'barbero__usuario', 'servicio')
        .order_by('fecha_inicio', 'pk')
    )


def distribucion_por_estado(fecha):
    """Cantidad de citas del día por cada estado aprobado, incluidos los ceros."""
    inicio, fin = _rango_local(fecha)
    totales = dict(
        Cita.objects.filter(fecha_inicio__gte=inicio, fecha_inicio__lt=fin)
        .values('estado').annotate(total=Count('pk'))
        .values_list('estado', 'total')
    )
    return [
        {'codigo': codigo, 'nombre': nombre, 'total': totales.get(codigo, 0)}
        for codigo, nombre in EstadoCita.choices
    ]


def listado_general(fecha=None):
    """Todas las citas; con fecha, solo las de ese día local."""
    citas = Cita.objects.select_related('cliente', 'barbero__usuario', 'servicio')
    if fecha is not None:
        inicio, fin = _rango_local(fecha)
        citas = citas.filter(fecha_inicio__gte=inicio, fecha_inicio__lt=fin)
    return citas.order_by('fecha_inicio', 'pk')
