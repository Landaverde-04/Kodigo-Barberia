from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from .roles import ADMINISTRADOR, BARBERO, CLIENTE, ROLES_NEGOCIO, es_administrador


@transaction.atomic
def asignar_rol(*, actor, usuario, rol):
    """Única asignación de rol/perfil. No reemplaza el formulario de cuentas."""
    if not es_administrador(actor):
        raise PermissionDenied
    if rol not in ROLES_NEGOCIO:
        raise ValidationError('Rol de negocio desconocido.', code='rol_invalido')
    from barbers.models import Barbero
    from appointments.models import EstadoCita

    cuenta = get_user_model().objects.select_for_update().get(pk=usuario.pk)
    perfil = Barbero.objects.select_for_update().filter(usuario=cuenta).first()
    if cuenta.is_superuser and rol != ADMINISTRADOR:
        raise ValidationError('Un superusuario conserva el rol Administrador.', code='superusuario_admin')
    if perfil and (rol != BARBERO or not cuenta.is_active):
        if perfil.citas.filter(estado=EstadoCita.CONFIRMADA).exists():
            raise ValidationError('Resuelve las citas confirmadas antes de desactivar al barbero o cambiar su rol.', code='citas_pendientes')
    grupo, _ = Group.objects.get_or_create(name=rol)
    cuenta.groups.set([grupo])
    if rol == BARBERO:
        perfil, _ = Barbero.objects.get_or_create(usuario=cuenta)
        perfil.activo = cuenta.is_active
        perfil.save(update_fields=['activo', 'fecha_modificacion'])
    elif perfil:
        perfil.activo = False
        perfil.save(update_fields=['activo', 'fecha_modificacion'])
    # El administrador del negocio usa las pantallas del sistema; staff/superuser
    # se administran aparte y no pueden venir del formulario público.
    return cuenta


@transaction.atomic
def registrar_cliente(*, username, password, first_name='', last_name='', email=''):
    """Entrada segura para el futuro formulario público, sin parámetros privilegiados."""
    from django.contrib.auth.password_validation import validate_password
    usuario = get_user_model()(username=username, first_name=first_name, last_name=last_name, email=email)
    validate_password(password, user=usuario)
    usuario.set_password(password)
    usuario.full_clean(exclude=['groups', 'user_permissions'])
    usuario.save()
    grupo, _ = Group.objects.get_or_create(name=CLIENTE)
    usuario.groups.set([grupo])
    return usuario
