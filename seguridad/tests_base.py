from datetime import timedelta
from decimal import Decimal
from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Group, Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from appointments.models import Cita
from barbers.models import Barbero
from services.models import Servicio

from .forms import UsuarioCrearForm
from .roles import ADMINISTRADOR, BARBERO, CLIENTE, obtener_rol
from .services import asignar_rol, registrar_cliente


class RolesTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(username='admin', password='ClaveTemporalDePrueba_2030')
        call_command('preparar_roles', stdout=StringIO())
        self.cliente = registrar_cliente(username='cliente', password='ClaveTemporalDePrueba_2030')

    def test_preparacion_es_idempotente_y_no_crea_cuentas(self):
        total = get_user_model().objects.count()
        call_command('preparar_roles', stdout=StringIO())
        self.assertEqual(Group.objects.count(), 3)
        self.assertEqual(get_user_model().objects.count(), total)
        self.assertEqual(obtener_rol(self.admin), ADMINISTRADOR)

    def test_registro_fuerza_cliente_y_no_admite_privilegios(self):
        self.assertEqual(obtener_rol(self.cliente), CLIENTE)
        self.assertFalse(self.cliente.is_staff or self.cliente.is_superuser)
        with self.assertRaises(TypeError):
            registrar_cliente(username='intruso', password='ClaveTemporalDePrueba_2030', is_superuser=True)
        self.assertFalse(get_user_model().objects.filter(username='intruso').exists())

    def test_registro_valida_password_y_usuario(self):
        with self.assertRaises(ValidationError):
            registrar_cliente(username='otro', password='123')
        self.assertFalse(get_user_model().objects.filter(username='otro').exists())

    def test_cuenta_sin_grupo_es_cliente_y_anonimo_sin_rol(self):
        cuenta = get_user_model().objects.create_user(username='sin_grupo')
        self.assertEqual(obtener_rol(cuenta), CLIENTE)
        self.assertIsNone(obtener_rol(AnonymousUser()))

    def test_asignacion_crea_un_solo_perfil_y_cambia_un_solo_grupo(self):
        for _ in range(2):
            asignar_rol(actor=self.admin, usuario=self.cliente, rol=BARBERO)
        self.assertEqual(Barbero.objects.filter(usuario=self.cliente).count(), 1)
        self.assertEqual(obtener_rol(self.cliente), BARBERO)
        self.assertEqual(self.cliente.groups.count(), 1)

    def test_cliente_no_asigna_roles(self):
        with self.assertRaises(PermissionDenied):
            asignar_rol(actor=self.cliente, usuario=self.cliente, rol=BARBERO)
        self.assertFalse(Barbero.objects.exists())

    def test_roles_ambiguos_se_rechazan(self):
        self.cliente.groups.add(Group.objects.get(name=BARBERO))
        with self.assertRaises(PermissionDenied):
            obtener_rol(self.cliente)

    def test_formulario_administrativo_no_acepta_dos_roles(self):
        form = UsuarioCrearForm(data={
            'username': 'nuevo', 'password1': 'ClaveTemporalDePrueba_2030',
            'password2': 'ClaveTemporalDePrueba_2030', 'is_active': 'on',
            'groups': list(Group.objects.filter(name__in=(CLIENTE, BARBERO)).values_list('pk', flat=True)),
        })
        self.assertFalse(form.is_valid())
        self.assertIn('groups', form.errors)

    def test_barbero_con_citas_no_pierde_rol_y_transaccion_conserva_estado(self):
        asignar_rol(actor=self.admin, usuario=self.cliente, rol=BARBERO)
        perfil = Barbero.objects.get(usuario=self.cliente)
        servicio = Servicio.objects.create(nombre='Corte', precio=5, duracion_minutos=30)
        inicio = timezone.now() + timedelta(days=1)
        Cita.objects.create(cliente=self.admin, barbero=perfil, servicio=servicio,
                            fecha_inicio=inicio, fecha_fin=inicio + timedelta(minutes=30),
                            nombre_servicio_reservado='Corte', precio_reservado=Decimal('5'), duracion_reservada=30)
        with self.assertRaises(ValidationError):
            asignar_rol(actor=self.admin, usuario=self.cliente, rol=CLIENTE)
        self.assertEqual(obtener_rol(self.cliente), BARBERO)
        perfil.refresh_from_db()
        self.assertTrue(perfil.activo)

    def test_permiso_django_sin_rol_admin_no_abre_administracion(self):
        self.cliente.user_permissions.add(Permission.objects.get(codename='view_usuario'))
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get('/seguridad/usuarios/').status_code, 403)

    def test_roles_fijos_no_se_crean_ni_eliminan_por_url(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get('/seguridad/roles/crear/').status_code, 403)
        grupo = Group.objects.get(name=CLIENTE)
        self.assertEqual(self.client.post(f'/seguridad/roles/{grupo.pk}/eliminar/').status_code, 403)
        self.assertTrue(Group.objects.filter(pk=grupo.pk).exists())

    def test_editar_rol_no_permite_renombrarlo(self):
        self.client.force_login(self.admin)
        grupo = Group.objects.get(name=CLIENTE)
        self.client.post(f'/seguridad/roles/{grupo.pk}/editar/', {'name': 'Otro'})
        grupo.refresh_from_db()
        self.assertEqual(grupo.name, CLIENTE)

    def test_editar_cuenta_asigna_perfil_por_la_vista(self):
        self.client.force_login(self.admin)
        response = self.client.post(f'/seguridad/usuarios/{self.cliente.pk}/editar/', {
            'username': self.cliente.username, 'is_active': 'on',
            'groups': [Group.objects.get(name=BARBERO).pk],
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Barbero.objects.filter(usuario=self.cliente, activo=True).exists())

    def test_admin_de_citas_y_barberos_es_solo_consulta(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get('/admin/appointments/cita/add/').status_code, 403)
        self.assertEqual(self.client.get('/admin/barbers/barbero/add/').status_code, 403)

    def test_permiso_malformado_muestra_error_y_no_rompe_pantalla(self):
        self.client.force_login(self.admin)
        grupo = Group.objects.get(name=CLIENTE)
        response = self.client.post(f'/seguridad/roles/{grupo.pk}/editar/', {'permissions': ['texto_invalido']})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)

    def test_desactivar_barbero_con_citas_revierte_cambio_de_cuenta(self):
        asignar_rol(actor=self.admin, usuario=self.cliente, rol=BARBERO)
        perfil = Barbero.objects.get(usuario=self.cliente)
        servicio = Servicio.objects.create(nombre='Corte', precio=5, duracion_minutos=30)
        inicio = timezone.now() + timedelta(days=1)
        Cita.objects.create(cliente=self.admin, barbero=perfil, servicio=servicio,
                            fecha_inicio=inicio, fecha_fin=inicio + timedelta(minutes=30),
                            nombre_servicio_reservado='Corte', precio_reservado=5, duracion_reservada=30)
        self.client.force_login(self.admin)
        response = self.client.post(f'/seguridad/usuarios/{self.cliente.pk}/editar/', {
            'username': self.cliente.username, 'groups': [Group.objects.get(name=BARBERO).pk],
        })
        self.assertEqual(response.status_code, 200)
        self.cliente.refresh_from_db()
        perfil.refresh_from_db()
        self.assertTrue(self.cliente.is_active)
        self.assertTrue(perfil.activo)

    def test_eliminar_usuario_con_perfil_conserva_historico_sin_error(self):
        asignar_rol(actor=self.admin, usuario=self.cliente, rol=BARBERO)
        self.client.force_login(self.admin)
        response = self.client.post(f'/seguridad/usuarios/{self.cliente.pk}/eliminar/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(get_user_model().objects.filter(pk=self.cliente.pk).exists())
