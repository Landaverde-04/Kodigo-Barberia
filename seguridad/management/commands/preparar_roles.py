from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from seguridad.roles import ADMINISTRADOR, BARBERO, CLIENTE, ROLES_NEGOCIO


class Command(BaseCommand):
    help = 'Inicializa los tres grupos y sus permisos de forma idempotente, sin crear contraseñas.'

    @transaction.atomic
    def handle(self, *args, **options):
        usuarios = list(get_user_model().objects.prefetch_related('groups').all())
        for usuario in usuarios:
            nombres = set(usuario.groups.values_list('name', flat=True))
            if not usuario.is_superuser and (len(nombres & set(ROLES_NEGOCIO)) > 1 or nombres - set(ROLES_NEGOCIO)):
                raise CommandError(f'La cuenta {usuario.username} tiene grupos heredados o ambiguos. Coordina su revisión antes de inicializar.')

        apps = ('seguridad', 'services', 'barbers', 'appointments')
        for nombre in ROLES_NEGOCIO:
            grupo, _ = Group.objects.get_or_create(name=nombre)
            if nombre == ADMINISTRADOR:
                permisos = Permission.objects.filter(content_type__app_label__in=apps)
                permisos = permisos | Permission.objects.filter(content_type__app_label='auth', codename__in=('view_group', 'change_group'))
            elif nombre == BARBERO:
                permisos = Permission.objects.filter(content_type__app_label='appointments', codename__in=('view_cita', 'change_cita'))
            else:
                permisos = Permission.objects.filter(content_type__app_label='appointments', codename__in=('view_cita', 'add_cita', 'change_cita'))
            grupo.permissions.set(permisos)

        for usuario in usuarios:
            if usuario.is_superuser:
                usuario.groups.set([Group.objects.get(name=ADMINISTRADOR)])
            elif not usuario.groups.exists():
                usuario.groups.set([Group.objects.get(name=CLIENTE)])
        self.stdout.write(self.style.SUCCESS('Roles preparados: Cliente, Barbero y Administrador. No se crearon cuentas.'))
