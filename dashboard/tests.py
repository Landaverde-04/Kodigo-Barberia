from datetime import datetime, time as hora_dia, timedelta, timezone as zona_utc
from decimal import Decimal
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from appointments.models import Cita
from appointments.services import cancelar_cita, completar_cita, reservar_cita
from seguridad.roles import BARBERO, CLIENTE
from seguridad.services import asignar_rol, registrar_cliente
from services.models import Servicio

from .selectors import citas_del_dia, contar_cuentas_por_rol, distribucion_por_estado


class PanelAdministrativoTests(TestCase):
    CLAVE = 'ClavePanelTemporal_2030'

    @staticmethod
    def dia_laboral_futuro(desde=None):
        fecha = (desde or timezone.localdate()) + timedelta(days=1)
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

        cls.admin = usuarios.create_superuser(username='admin_panel', password=cls.CLAVE)
        cls.cliente = registrar_cliente(
            username='cliente_panel', password=cls.CLAVE, first_name='Clara',
        )
        cls.otro_cliente = registrar_cliente(username='otro_cliente_panel', password=cls.CLAVE)
        cls.usuario_barbero = registrar_cliente(username='barbero_panel', password=cls.CLAVE)
        cls.perfil = asignar_rol(
            actor=cls.admin, usuario=cls.usuario_barbero, rol=BARBERO,
        ).perfil_barbero
        cls.usuario_otro = registrar_cliente(username='otro_barbero_panel', password=cls.CLAVE)
        cls.otro_perfil = asignar_rol(
            actor=cls.admin, usuario=cls.usuario_otro, rol=BARBERO,
        ).perfil_barbero
        cls.ambiguo = usuarios.create_user(username='ambiguo_panel')
        cls.ambiguo.groups.add(Group.objects.get(name=CLIENTE), Group.objects.get(name=BARBERO))

        cls.servicio = Servicio.objects.create(
            nombre='Corte panel', precio=Decimal('5.00'), duracion_minutos=30,
        )
        cls.fecha = cls.dia_laboral_futuro()
        cls.otra_fecha = cls.dia_laboral_futuro(desde=cls.fecha)

        cls.cita_confirmada = reservar_cita(
            actor=cls.cliente, servicio_id=cls.servicio.pk,
            barbero_id=cls.perfil.pk, fecha_inicio=cls.instante(cls.fecha, 9),
        )
        cls.cita_cancelada = reservar_cita(
            actor=cls.cliente, servicio_id=cls.servicio.pk,
            barbero_id=cls.perfil.pk, fecha_inicio=cls.instante(cls.fecha, 10, 30),
        )
        cancelar_cita(actor=cls.admin, cita_id=cls.cita_cancelada.pk, motivo='Prueba del panel')
        cls.cita_completada = reservar_cita(
            actor=cls.otro_cliente, servicio_id=cls.servicio.pk,
            barbero_id=cls.perfil.pk, fecha_inicio=cls.instante(cls.fecha, 11),
        )
        with mock.patch('django.utils.timezone.now', return_value=cls.cita_completada.fecha_fin):
            completar_cita(actor=cls.admin, cita_id=cls.cita_completada.pk)
        cls.cita_otra_fecha = reservar_cita(
            actor=cls.cliente, servicio_id=cls.servicio.pk,
            barbero_id=cls.perfil.pk, fecha_inicio=cls.instante(cls.otra_fecha, 9),
        )

    def test_acceso_solo_para_administrador(self):
        url = reverse('dashboard:panel')
        self.assertRedirects(self.client.get(url), f"{reverse('seguridad:login')}?next={url}")

        for usuario in (self.cliente, self.usuario_barbero):
            with self.subTest(usuario=usuario.username):
                self.client.force_login(usuario)
                self.assertEqual(self.client.get(url).status_code, 403)

        self.client.force_login(self.admin)
        respuesta = self.client.get(url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertTemplateUsed(respuesta, 'dashboard/panel.html')
        self.assertTemplateUsed(respuesta, 'core/base.html')

    def test_cuentas_totales_por_rol_y_ambiguas(self):
        self.assertEqual(contar_cuentas_por_rol(), {
            'cliente': 2, 'barbero': 2, 'administrador': 1, 'por_revisar': 1,
        })

        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('dashboard:panel'))
        self.assertEqual(respuesta.context['cuentas']['cliente'], 2)
        self.assertEqual(respuesta.context['cuentas']['barbero'], 2)
        self.assertEqual(respuesta.context['cuentas']['por_revisar'], 1)
        self.assertContains(respuesta, 'Cuentas por revisar')

    def test_conteo_y_distribucion_son_de_la_fecha_elegida(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('dashboard:panel'), {'fecha': self.fecha.isoformat()})

        self.assertEqual(respuesta.context['total_dia'], 3)
        self.assertEqual(list(respuesta.context['citas']), [
            self.cita_confirmada, self.cita_cancelada, self.cita_completada,
        ])
        self.assertEqual(
            [(estado['nombre'], estado['total']) for estado in respuesta.context['estados']],
            [('Confirmada', 1), ('Cancelada', 1), ('Completada', 1)],
        )
        self.assertContains(respuesta, 'Confirmada')
        self.assertContains(respuesta, 'Cancelada')
        self.assertContains(respuesta, 'Completada')

    def test_el_dia_se_cuenta_en_hora_local_no_en_utc(self):
        inicio = self.instante(self.fecha, 20)
        cita_nocturna = Cita.objects.create(
            cliente=self.cliente, barbero=self.perfil, servicio=self.servicio,
            fecha_inicio=inicio, fecha_fin=inicio + timedelta(minutes=30),
            nombre_servicio_reservado='Corte nocturno', precio_reservado=Decimal('5.00'),
            duracion_reservada=30,
        )
        self.assertEqual(timezone.localtime(inicio).date(), self.fecha)
        self.assertEqual(
            inicio.astimezone(zona_utc.utc).date(), self.fecha + timedelta(days=1),
        )

        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('dashboard:panel'), {'fecha': self.fecha.isoformat()})

        self.assertEqual(respuesta.context['total_dia'], 4)
        self.assertIn(cita_nocturna, list(respuesta.context['citas']))

    def test_listado_general_acepta_filtro_opcional(self):
        self.client.force_login(self.admin)
        url = reverse('dashboard:panel')

        con_filtro = self.client.get(url, {'fecha': self.fecha.isoformat()})
        self.assertEqual(list(con_filtro.context['listado']), [
            self.cita_confirmada, self.cita_cancelada, self.cita_completada,
        ])

        sin_filtro = self.client.get(url, {
            'fecha': self.fecha.isoformat(), 'ver': 'todas',
        })
        self.assertEqual(list(sin_filtro.context['listado']), [
            self.cita_confirmada, self.cita_cancelada, self.cita_completada,
            self.cita_otra_fecha,
        ])
        self.assertContains(sin_filtro, 'Se muestran todas las fechas.')

    def test_fecha_sin_citas_muestra_mensaje_y_ceros(self):
        fecha_vacia = self.fecha + timedelta(days=60)
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('dashboard:panel'), {'fecha': fecha_vacia.isoformat()})

        self.assertEqual(respuesta.context['total_dia'], 0)
        self.assertEqual([estado['total'] for estado in respuesta.context['estados']], [0, 0, 0])
        self.assertContains(respuesta, 'No hay citas para esta fecha.')

    def test_fecha_invalida_muestra_error_sin_conteos_parciales(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('dashboard:panel'), {'fecha': '30/11/2026'})

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Escribe una fecha válida en formato AAAA-MM-DD')
        self.assertIsNone(respuesta.context['cuentas'])
        self.assertIsNone(respuesta.context['citas'])
        self.assertIsNone(respuesta.context['estados'])

    def test_solo_se_admite_get_y_no_se_muestran_ingresos(self):
        self.client.force_login(self.admin)
        url = reverse('dashboard:panel')

        self.assertEqual(self.client.post(url).status_code, 405)

        respuesta = self.client.get(url)
        for texto in ('Ingresos', 'Pagos', 'Ventas'):
            with self.subTest(texto=texto):
                self.assertNotContains(respuesta, texto)

    def test_selectors_devuelven_solo_la_fecha_local_pedida(self):
        self.assertEqual(len(list(citas_del_dia(self.fecha))), 3)
        self.assertEqual(len(list(citas_del_dia(self.otra_fecha))), 1)
        self.assertEqual(
            [estado['total'] for estado in distribucion_por_estado(self.otra_fecha)], [1, 0, 0],
        )
