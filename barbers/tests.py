from datetime import datetime, time as hora_dia, timedelta
from decimal import Decimal
from io import BytesIO, StringIO
from tempfile import TemporaryDirectory

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from appointments.services import cancelar_cita, reservar_cita
from seguridad.roles import ADMINISTRADOR, BARBERO, CLIENTE
from seguridad.services import asignar_rol, registrar_cliente
from services.models import Servicio

from .models import Barbero
from .selectors import listar_perfiles, obtener_perfil_de_usuario


class PerfilesBarberoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('preparar_roles', stdout=StringIO())
        usuarios = get_user_model().objects

        cls.admin = usuarios.create_user(username='admin_perfiles')
        cls.admin.groups.add(Group.objects.get(name=ADMINISTRADOR))

        cls.barbero = usuarios.create_user(
            username='barbero_perfil', first_name='Ana', last_name='Morales',
        )
        cls.barbero.groups.add(Group.objects.get(name=BARBERO))
        cls.perfil = Barbero.objects.create(
            usuario=cls.barbero, descripcion='Cortes clasicos',
        )

        cls.otro = usuarios.create_user(username='otro_barbero')
        cls.otro.groups.add(Group.objects.get(name=BARBERO))
        cls.otro_perfil = Barbero.objects.create(usuario=cls.otro)

        cls.cliente = usuarios.create_user(username='cliente_perfil')
        cls.cliente.groups.add(Group.objects.get(name=CLIENTE))

    def test_visitante_es_redirigido_a_login(self):
        rutas = (
            reverse('barbers:mi_perfil'),
            reverse('barbers:lista_barberos'),
            reverse('barbers:editar_perfil', args=[self.perfil.pk]),
        )
        for ruta in rutas:
            with self.subTest(ruta=ruta):
                self.assertRedirects(
                    self.client.get(ruta), f"{reverse('seguridad:login')}?next={ruta}",
                )

    def test_cliente_no_puede_ver_ni_escribir_perfiles(self):
        self.client.force_login(self.cliente)

        self.assertEqual(self.client.get(reverse('barbers:mi_perfil')).status_code, 403)
        self.assertEqual(self.client.get(reverse('barbers:lista_barberos')).status_code, 403)
        self.assertEqual(
            self.client.get(reverse('barbers:editar_perfil', args=[self.perfil.pk])).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(reverse('barbers:mi_perfil'), {'descripcion': 'intruso'}).status_code,
            403,
        )

        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.descripcion, 'Cortes clasicos')
        self.assertFalse(Barbero.objects.filter(usuario=self.cliente).exists())
        self.assertEqual(list(self.cliente.groups.values_list('name', flat=True)), [CLIENTE])

    def test_barbero_edita_solo_su_perfil(self):
        self.client.force_login(self.barbero)
        url = reverse('barbers:mi_perfil')

        respuesta = self.client.get(url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertTemplateUsed(respuesta, 'barbers/mi_perfil.html')
        self.assertTemplateUsed(respuesta, 'core/base.html')
        self.assertContains(respuesta, 'Cortes clasicos')
        self.assertContains(respuesta, 'Ana Morales')
        self.assertNotContains(respuesta, self.otro.username)

        self.assertRedirects(
            self.client.post(url, {'descripcion': 'Especialista en barba'}), url,
        )
        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.descripcion, 'Especialista en barba')
        self.assertEqual(self.perfil.usuario_id, self.barbero.pk)
        self.assertTrue(self.perfil.activo)
        self.assertEqual(list(self.barbero.groups.values_list('name', flat=True)), [BARBERO])

    def test_barbero_no_puede_editar_otro_perfil_ni_enviar_un_pk(self):
        self.client.force_login(self.barbero)
        ajena = reverse('barbers:editar_perfil', args=[self.otro_perfil.pk])

        self.assertEqual(self.client.get(ajena).status_code, 403)
        self.assertEqual(
            self.client.post(ajena, {'descripcion': 'cambio ajeno'}).status_code, 403,
        )
        self.client.post(
            reverse('barbers:mi_perfil'),
            {'descripcion': 'cambio propio', 'pk': self.otro_perfil.pk},
        )

        self.otro_perfil.refresh_from_db()
        self.assertEqual(self.otro_perfil.descripcion, '')
        self.assertEqual(self.otro_perfil.usuario_id, self.otro.pk)

    def test_administrador_lista_y_edita_un_perfil_existente(self):
        self.client.force_login(self.admin)

        self.assertContains(
            self.client.get(reverse('barbers:lista_barberos')), 'Ana Morales',
        )
        url = reverse('barbers:editar_perfil', args=[self.otro_perfil.pk])
        respuesta = self.client.get(url)
        self.assertTemplateUsed(respuesta, 'barbers/editar_perfil.html')
        self.assertTemplateUsed(respuesta, 'core/base.html')
        self.assertContains(respuesta, 'Editar perfil')
        self.assertContains(respuesta, 'Panel de gestión')

        self.assertRedirects(
            self.client.post(url, {'descripcion': 'Perfil editado por admin'}),
            reverse('barbers:lista_barberos'),
        )
        self.otro_perfil.refresh_from_db()
        self.assertEqual(self.otro_perfil.descripcion, 'Perfil editado por admin')
        self.assertEqual(self.otro_perfil.usuario_id, self.otro.pk)
        self.assertTrue(self.otro_perfil.activo)

    def test_barbero_sube_y_quita_la_foto(self):
        self.client.force_login(self.barbero)
        url = reverse('barbers:mi_perfil')
        imagen = BytesIO()
        Image.new('RGB', (12, 12)).save(imagen, format='PNG')
        archivo = SimpleUploadedFile('ana.png', imagen.getvalue(), content_type='image/png')

        with TemporaryDirectory() as directorio, self.settings(MEDIA_ROOT=directorio):
            self.assertRedirects(
                self.client.post(url, {'descripcion': 'Con foto', 'foto': archivo}), url,
            )
            self.perfil.refresh_from_db()
            self.assertTrue(self.perfil.foto.storage.exists(self.perfil.foto.name))
            self.assertContains(self.client.get(url), self.perfil.foto.url)

            self.assertRedirects(
                self.client.post(url, {'descripcion': 'Con foto', 'foto-clear': 'on'}), url,
            )
            self.perfil.refresh_from_db()
            self.assertFalse(self.perfil.foto)

    def test_foto_rechaza_formato_y_tamano(self):
        self.client.force_login(self.barbero)
        imagen = BytesIO()
        Image.new('RGB', (12, 12)).save(imagen, format='GIF')
        casos = (
            (
                'ana.gif', imagen.getvalue(),
                'Usa una imagen JPEG, PNG o WebP con la extensión correspondiente.',
            ),
            (
                'grande.png', b'x' * 5_000_001,
                'La imagen debe pesar como máximo 5 MB.',
            ),
        )
        for nombre, contenido, mensaje in casos:
            with self.subTest(archivo=nombre):
                archivo = SimpleUploadedFile(nombre, contenido)
                respuesta = self.client.post(
                    reverse('barbers:mi_perfil'),
                    {'descripcion': 'Sin cambio', 'foto': archivo},
                )
                self.assertFormError(respuesta.context['form'], 'foto', mensaje)
                self.assertContains(respuesta, mensaje)

        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.descripcion, 'Cortes clasicos')
        self.assertFalse(self.perfil.foto)

    def test_perfil_sin_foto_muestra_un_mensaje_util(self):
        self.client.force_login(self.barbero)

        self.assertContains(self.client.get(reverse('barbers:mi_perfil')), 'Sin foto')

    def test_post_sin_csrf_es_rechazado(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.barbero)

        self.assertEqual(
            cliente.post(
                reverse('barbers:mi_perfil'), {'descripcion': 'sin csrf'},
            ).status_code,
            403,
        )
        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.descripcion, 'Cortes clasicos')

    def test_consultas_devuelven_solo_perfiles_existentes(self):
        self.assertEqual(obtener_perfil_de_usuario(self.barbero), self.perfil)
        self.assertIsNone(obtener_perfil_de_usuario(self.cliente))
        self.assertIn(self.perfil, listar_perfiles())
        self.assertIn(self.otro_perfil, listar_perfiles())

    def test_admin_de_barbero_sigue_en_modo_consulta(self):
        peticion = RequestFactory().get('/admin/')
        peticion.user = self.admin
        modelo_admin = admin.site._registry[Barbero]

        self.assertFalse(modelo_admin.has_add_permission(peticion))
        self.assertFalse(modelo_admin.has_change_permission(peticion, self.perfil))
        self.assertFalse(modelo_admin.has_delete_permission(peticion, self.perfil))


CLAVE_AGENDA = 'ClaveAgendaTemporal_2030'


class AgendaBarberoTests(TestCase):
    @staticmethod
    def dia_laboral_futuro():
        fecha = timezone.localdate() + timedelta(days=1)
        while fecha.weekday() == 6:
            fecha += timedelta(days=1)
        return fecha

    @staticmethod
    def instante(fecha, hora, minuto=0):
        return timezone.make_aware(datetime.combine(fecha, hora_dia(hora, minuto)))

    @classmethod
    def setUpTestData(cls):
        call_command('preparar_roles', stdout=StringIO())
        usuarios = get_user_model().objects
        cls.admin = usuarios.create_superuser(username='admin_agenda', password=CLAVE_AGENDA)
        cls.cliente = registrar_cliente(
            username='cliente_agenda', password=CLAVE_AGENDA, first_name='Clara',
        )
        cls.otro_cliente = registrar_cliente(
            username='otro_cliente_agenda', password=CLAVE_AGENDA, first_name='Diego',
        )
        cls.usuario_barbero = registrar_cliente(
            username='barbero_agenda', password=CLAVE_AGENDA, first_name='Ana',
        )
        cls.perfil = asignar_rol(
            actor=cls.admin, usuario=cls.usuario_barbero, rol=BARBERO,
        ).perfil_barbero
        cls.usuario_otro = registrar_cliente(
            username='otro_barbero_agenda', password=CLAVE_AGENDA,
        )
        cls.otro_perfil = asignar_rol(
            actor=cls.admin, usuario=cls.usuario_otro, rol=BARBERO,
        ).perfil_barbero
        cls.servicio = Servicio.objects.create(
            nombre='Corte agenda', precio=Decimal('5.00'), duracion_minutos=30,
        )
        cls.fecha = cls.dia_laboral_futuro()
        cls.inicio = cls.instante(cls.fecha, 9)
        cls.cita_propia = reservar_cita(
            actor=cls.cliente, servicio_id=cls.servicio.pk,
            barbero_id=cls.perfil.pk, fecha_inicio=cls.inicio,
        )
        reservar_cita(
            actor=cls.otro_cliente, servicio_id=cls.servicio.pk,
            barbero_id=cls.otro_perfil.pk, fecha_inicio=cls.inicio,
        )

    def test_acceso_privado_por_rol(self):
        url = reverse('barbers:agenda')
        self.assertRedirects(self.client.get(url), f"{reverse('seguridad:login')}?next={url}")

        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(url).status_code, 403)

        self.client.force_login(self.usuario_barbero)
        respuesta = self.client.get(url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertTemplateUsed(respuesta, 'barbers/agenda.html')
        self.assertTemplateUsed(respuesta, 'core/base.html')

    def test_sin_fecha_usa_hoy(self):
        self.client.force_login(self.usuario_barbero)

        respuesta = self.client.get(reverse('barbers:agenda'))

        self.assertEqual(respuesta.context['fecha'], timezone.localdate())
        self.assertContains(respuesta, timezone.localdate().isoformat())

    def test_fecha_valida_solo_citas_propias_ordenadas(self):
        segunda = reservar_cita(
            actor=self.cliente, servicio_id=self.servicio.pk,
            barbero_id=self.perfil.pk, fecha_inicio=self.instante(self.fecha, 10, 30),
        )
        self.client.force_login(self.usuario_barbero)

        respuesta = self.client.get(reverse('barbers:agenda'), {
            'fecha': self.fecha.isoformat(), 'barbero_id': self.otro_perfil.pk,
        })

        self.assertEqual(list(respuesta.context['citas']), [self.cita_propia, segunda])
        self.assertContains(respuesta, 'Clara')
        self.assertContains(respuesta, 'Corte agenda')
        self.assertContains(respuesta, '30 min')
        self.assertContains(respuesta, 'Confirmada')
        self.assertNotContains(respuesta, 'Diego')

    def test_muestra_snapshots_no_catalogo_actual(self):
        self.servicio.nombre = 'Corte actualizado'
        self.servicio.duracion_minutos = 45
        self.servicio.precio = Decimal('9.00')
        self.servicio.save()
        self.client.force_login(self.usuario_barbero)

        respuesta = self.client.get(reverse('barbers:agenda'), {'fecha': self.fecha.isoformat()})

        self.assertContains(respuesta, 'Corte agenda')
        self.assertContains(respuesta, '30 min')
        self.assertNotContains(respuesta, 'Corte actualizado')
        self.assertNotContains(respuesta, '45 min')

    def test_fecha_invalida_muestra_error_comprensible(self):
        self.client.force_login(self.usuario_barbero)

        for valor in ('no-es-fecha', '2026-13-45', '01/02/2026', '2026-1-2'):
            with self.subTest(valor=valor):
                respuesta = self.client.get(reverse('barbers:agenda'), {'fecha': valor})
                self.assertEqual(respuesta.status_code, 200)
                self.assertContains(respuesta, 'Escribe una fecha válida en formato AAAA-MM-DD')
                self.assertIsNone(respuesta.context['citas'])
                self.assertNotContains(respuesta, 'No hay citas para esta fecha.')

    def test_navegacion_a_fechas_anteriores_y_posteriores(self):
        self.client.force_login(self.usuario_barbero)

        respuesta = self.client.get(reverse('barbers:agenda'), {'fecha': self.fecha.isoformat()})

        self.assertContains(respuesta, f"?fecha={(self.fecha - timedelta(days=1)).isoformat()}")
        self.assertContains(respuesta, f"?fecha={(self.fecha + timedelta(days=1)).isoformat()}")
        self.assertContains(respuesta, 'Anterior')
        self.assertContains(respuesta, 'Siguiente')
        self.assertContains(respuesta, 'Hoy')

    def test_fecha_sin_citas_muestra_mensaje(self):
        self.client.force_login(self.usuario_barbero)

        respuesta = self.client.get(
            reverse('barbers:agenda'),
            {'fecha': (self.fecha + timedelta(days=2)).isoformat()},
        )

        self.assertContains(respuesta, 'No hay citas para esta fecha.')

    def test_cita_cancelada_conserva_registro_y_estado(self):
        cancelar_cita(actor=self.usuario_barbero, cita_id=self.cita_propia.pk)
        self.client.force_login(self.usuario_barbero)

        respuesta = self.client.get(reverse('barbers:agenda'), {'fecha': self.fecha.isoformat()})

        self.assertContains(respuesta, 'Corte agenda')
        self.assertContains(respuesta, 'Cancelada')

    def test_post_no_esta_permitido(self):
        self.client.force_login(self.usuario_barbero)

        self.assertEqual(self.client.post(reverse('barbers:agenda')).status_code, 405)

    def test_barbero_sin_perfil_muestra_aviso(self):
        cuenta = get_user_model().objects.create_user(username='barbero_sin_perfil_agenda')
        cuenta.groups.add(Group.objects.get(name=BARBERO))
        self.client.force_login(cuenta)

        respuesta = self.client.get(reverse('barbers:agenda'), {'fecha': self.fecha.isoformat()})

        self.assertContains(respuesta, 'no tiene un perfil de barbero asignado')
        self.assertEqual(list(respuesta.context['citas']), [])
