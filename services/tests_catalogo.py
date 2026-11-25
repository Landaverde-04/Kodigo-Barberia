from datetime import timedelta
from decimal import Decimal
from io import BytesIO, StringIO
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from appointments.models import Cita
from barbers.models import Barbero
from seguridad.roles import ADMINISTRADOR, CLIENTE

from .models import Servicio


class AdministracionCatalogoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('preparar_roles', stdout=StringIO())
        usuarios = get_user_model().objects
        cls.administrador = usuarios.create_user(username='administrador_catalogo')
        cls.administrador.groups.add(Group.objects.get(name=ADMINISTRADOR))
        cls.cliente = usuarios.create_user(username='cliente_catalogo')
        cls.cliente.groups.add(Group.objects.get(name=CLIENTE))
        cls.servicio = Servicio.objects.create(
            nombre='Corte', precio=Decimal('10.00'), duracion_minutos=30,
        )

    def setUp(self):
        self.lista = reverse('services:lista_servicios')
        self.crear = reverse('services:crear_servicio')
        self.editar = reverse('services:editar_servicio', args=[self.servicio.pk])
        self.desactivar = reverse('services:desactivar_servicio', args=[self.servicio.pk])
        self.activar = reverse('services:activar_servicio', args=[self.servicio.pk])
        self.datos = {
            'nombre': 'Corte y barba',
            'descripcion': 'Arreglo de barba y corte',
            'precio': '12.50',
            'duracion_minutos': 45,
        }

    def test_visitante_redirigido_y_cliente_con_permisos_rechazado(self):
        self.assertRedirects(
            self.client.get(self.lista), f"{reverse('seguridad:login')}?next={self.lista}",
        )
        permisos = Permission.objects.filter(content_type__app_label='services')
        self.cliente.user_permissions.add(*permisos)
        self.client.force_login(self.cliente)

        for ruta in (self.lista, self.crear, self.editar):
            with self.subTest(ruta=ruta):
                self.assertEqual(self.client.get(ruta).status_code, 403)
        for ruta in (self.crear, self.editar, self.desactivar, self.activar):
            with self.subTest(ruta=ruta):
                self.assertEqual(self.client.post(ruta, self.datos).status_code, 403)

        self.assertEqual(Servicio.objects.count(), 1)
        self.servicio.refresh_from_db()
        self.assertEqual(self.servicio.nombre, 'Corte')
        self.assertTrue(self.servicio.activo)

    def test_rol_administrador_sin_permiso_es_rechazado(self):
        grupo = Group.objects.get(name=ADMINISTRADOR)
        permiso = Permission.objects.get(content_type__app_label='services', codename='add_servicio')
        grupo.permissions.remove(permiso)
        self.client.force_login(self.administrador)

        self.assertEqual(self.client.post(self.crear, self.datos).status_code, 403)

    def test_administrador_lista_y_crea_un_servicio(self):
        self.client.force_login(self.administrador)
        Servicio.objects.create(nombre='Retirado', precio=5, duracion_minutos=15, activo=False)

        respuesta = self.client.get(self.lista)
        self.assertContains(respuesta, 'Corte')
        self.assertContains(respuesta, 'Retirado')
        self.assertContains(self.client.get(self.crear), 'Nuevo servicio')

        respuesta = self.client.post(self.crear, self.datos, follow=True)

        self.assertRedirects(respuesta, self.lista)
        self.assertContains(respuesta, 'Servicio creado correctamente.')
        servicio = Servicio.objects.get(nombre='Corte y barba')
        self.assertEqual(servicio.precio, Decimal('12.50'))
        self.assertEqual(servicio.duracion_minutos, 45)
        self.assertTrue(servicio.activo)

    def test_precio_negativo_y_duracion_fuera_de_intervalo_muestran_errores(self):
        self.client.force_login(self.administrador)
        datos = {**self.datos, 'precio': '-1.00', 'duracion_minutos': 17}

        respuesta = self.client.post(self.crear, datos)

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('precio', respuesta.context['form'].errors)
        self.assertContains(respuesta, 'La duración debe ser positiva y múltiplo de 15 minutos.')
        self.assertEqual(Servicio.objects.count(), 1)

    def test_administrador_puede_subir_y_quitar_la_imagen(self):
        self.client.force_login(self.administrador)
        imagen = BytesIO()
        Image.new('RGB', (12, 12)).save(imagen, format='PNG')
        archivo = SimpleUploadedFile('corte.png', imagen.getvalue(), content_type='image/png')

        with TemporaryDirectory() as directorio, self.settings(MEDIA_ROOT=directorio):
            self.assertRedirects(
                self.client.post(self.editar, {**self.datos, 'imagen': archivo}), self.lista,
            )
            self.servicio.refresh_from_db()
            self.assertTrue(self.servicio.imagen.storage.exists(self.servicio.imagen.name))
            self.assertContains(
                self.client.get(reverse('website:catalogo_servicios')), self.servicio.imagen.url,
            )

            self.assertRedirects(
                self.client.post(self.editar, {**self.datos, 'imagen-clear': 'on'}), self.lista,
            )
            self.servicio.refresh_from_db()
            self.assertFalse(self.servicio.imagen)

    def test_imagen_rechaza_archivos_grandes_o_de_otro_formato(self):
        self.client.force_login(self.administrador)
        imagen = BytesIO()
        Image.new('RGB', (12, 12)).save(imagen, format='GIF')
        mensaje_formato = 'Usa una imagen JPEG, PNG o WebP con la extensión correspondiente.'
        casos = (
            ('grande.png', b'x' * 5_000_001, 'La imagen debe pesar como máximo 5 MB.'),
            ('corte.gif', imagen.getvalue(), mensaje_formato),
            ('disfraz.png', imagen.getvalue(), mensaje_formato),
        )
        for nombre, contenido, mensaje in casos:
            with self.subTest(archivo=nombre):
                archivo = SimpleUploadedFile(nombre, contenido)
                respuesta = self.client.post(self.crear, {**self.datos, 'imagen': archivo})
                self.assertFormError(respuesta.context['form'], 'imagen', mensaje)
                self.assertContains(respuesta, mensaje)
        self.assertEqual(Servicio.objects.count(), 1)

    def test_estado_solo_cambia_con_post_y_csrf(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.administrador)

        self.assertEqual(cliente.get(self.desactivar).status_code, 405)
        self.assertEqual(cliente.post(self.desactivar).status_code, 403)
        self.servicio.refresh_from_db()
        self.assertTrue(self.servicio.activo)

        cliente.get(self.lista)
        csrf = cliente.cookies['csrftoken'].value
        respuesta = cliente.post(self.desactivar, {'csrfmiddlewaretoken': csrf}, follow=True)

        self.assertRedirects(respuesta, self.lista)
        self.assertContains(respuesta, 'Servicio desactivado.')
        self.servicio.refresh_from_db()
        self.assertFalse(self.servicio.activo)
        self.assertRedirects(
            cliente.post(self.desactivar, {'csrfmiddlewaretoken': csrf}), self.lista,
        )
        self.servicio.refresh_from_db()
        self.assertFalse(self.servicio.activo)
        self.assertNotContains(
            cliente.get(reverse('website:catalogo_servicios')), self.servicio.nombre,
        )
        self.assertRedirects(
            cliente.post(self.activar, {'csrfmiddlewaretoken': csrf}), self.lista,
        )
        self.assertContains(
            cliente.get(reverse('website:catalogo_servicios')), self.servicio.nombre,
        )

    def test_editar_y_desactivar_preservan_los_datos_de_la_cita(self):
        usuario = get_user_model().objects.create_user(username='barbero_catalogo')
        barbero = Barbero.objects.create(usuario=usuario)
        inicio = timezone.now()
        fin = inicio + timedelta(minutes=self.servicio.duracion_minutos)
        cita = Cita.objects.create(
            cliente=self.cliente, barbero=barbero, servicio=self.servicio,
            fecha_inicio=inicio, fecha_fin=fin,
            nombre_servicio_reservado=self.servicio.nombre,
            precio_reservado=self.servicio.precio,
            duracion_reservada=self.servicio.duracion_minutos,
        )
        self.client.force_login(self.administrador)

        self.assertContains(self.client.get(self.editar), 'Editar servicio')
        self.assertRedirects(self.client.post(self.editar, self.datos), self.lista)
        self.assertRedirects(self.client.post(self.desactivar), self.lista)

        self.servicio.refresh_from_db()
        self.assertEqual(self.servicio.nombre, 'Corte y barba')
        self.assertEqual(self.servicio.precio, Decimal('12.50'))
        self.assertEqual(self.servicio.duracion_minutos, 45)
        self.assertFalse(self.servicio.activo)
        cita.refresh_from_db()
        self.assertEqual(cita.nombre_servicio_reservado, 'Corte')
        self.assertEqual(cita.precio_reservado, Decimal('10.00'))
        self.assertEqual(cita.duracion_reservada, 30)
        self.assertEqual(cita.fecha_inicio, inicio)
        self.assertEqual(cita.fecha_fin, fin)
