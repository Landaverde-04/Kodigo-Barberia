from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from threading import Barrier

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connections, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from barbers.models import Barbero
from services.models import Servicio

from .models import Cita, EstadoCita


class DatosCitaMixin:
    def preparar_datos(self):
        usuario = get_user_model()
        self.cliente = usuario.objects.create_user(username='cliente_prueba')
        self.cuenta_barbero = usuario.objects.create_user(username='barbero_prueba')
        self.barbero = Barbero.objects.create(usuario=self.cuenta_barbero)
        self.servicio = Servicio.objects.create(nombre='Corte', precio=Decimal('5.00'), duracion_minutos=30)
        self.inicio = timezone.now().replace(second=0, microsecond=0) + timedelta(days=1)

    def datos_cita(self, **cambios):
        datos = {
            'cliente_id': self.cliente.pk, 'barbero_id': self.barbero.pk,
            'servicio_id': self.servicio.pk, 'fecha_inicio': self.inicio,
            'fecha_fin': self.inicio + timedelta(minutes=30),
            'nombre_servicio_reservado': 'Corte', 'precio_reservado': Decimal('5.00'),
            'duracion_reservada': 30,
        }
        datos.update(cambios)
        return datos


class IntegridadCitaTests(DatosCitaMixin, TestCase):
    def setUp(self):
        self.preparar_datos()

    def test_impide_superposicion_parcial_del_mismo_barbero(self):
        Cita.objects.create(**self.datos_cita())
        with self.assertRaises(IntegrityError), transaction.atomic():
            Cita.objects.create(**self.datos_cita(fecha_inicio=self.inicio + timedelta(minutes=15), fecha_fin=self.inicio + timedelta(minutes=45)))

    def test_permite_citas_contiguas(self):
        Cita.objects.create(**self.datos_cita())
        Cita.objects.create(**self.datos_cita(fecha_inicio=self.inicio + timedelta(minutes=30), fecha_fin=self.inicio + timedelta(minutes=60)))
        self.assertEqual(Cita.objects.count(), 2)

    def test_permite_misma_hora_con_barberos_distintos(self):
        cuenta = get_user_model().objects.create_user(username='otro_barbero')
        otro = Barbero.objects.create(usuario=cuenta)
        Cita.objects.create(**self.datos_cita())
        Cita.objects.create(**self.datos_cita(barbero_id=otro.pk))
        self.assertEqual(Cita.objects.count(), 2)

    def test_cancelada_libera_espacio_y_conserva_registro(self):
        Cita.objects.create(**self.datos_cita(
            estado=EstadoCita.CANCELADA, cancelada_por=self.cliente, fecha_cancelacion=timezone.now(),
        ))
        Cita.objects.create(**self.datos_cita())
        self.assertEqual(Cita.objects.count(), 2)

    def test_completada_no_libera_espacio_historico(self):
        Cita.objects.create(**self.datos_cita(
            estado=EstadoCita.COMPLETADA, completada_por=self.cuenta_barbero,
            fecha_finalizacion=timezone.now(),
        ))
        with self.assertRaises(IntegrityError), transaction.atomic():
            Cita.objects.create(**self.datos_cita())

    def test_copia_historica_no_cambia_con_el_catalogo(self):
        cita = Cita.objects.create(**self.datos_cita())
        self.servicio.nombre = 'Corte actualizado'
        self.servicio.precio = Decimal('8.00')
        self.servicio.duracion_minutos = 45
        self.servicio.save()
        cita.refresh_from_db()
        self.assertEqual((cita.nombre_servicio_reservado, cita.precio_reservado, cita.duracion_reservada), ('Corte', Decimal('5.00'), 30))

    def test_no_permite_borrar_relaciones_historicas(self):
        Cita.objects.create(**self.datos_cita())
        for objeto in (self.servicio, self.barbero, self.cliente):
            with self.assertRaises(ProtectedError):
                objeto.delete()

    def test_estado_o_auditoria_invalida_se_rechazan(self):
        for cambios in ({'estado': 'PENDING'}, {'estado': EstadoCita.CANCELADA}, {'estado': EstadoCita.COMPLETADA}):
            with self.assertRaises(IntegrityError), transaction.atomic():
                Cita.objects.create(**self.datos_cita(**cambios))

    def test_validacion_de_fin_coherente_con_duracion(self):
        cita = Cita(**self.datos_cita(fecha_fin=self.inicio + timedelta(minutes=45)))
        with self.assertRaises(ValidationError):
            cita.full_clean()

    def test_precio_duracion_y_orden_fechas_se_protegen_en_bd(self):
        for cambios in ({'precio_reservado': Decimal('-1')}, {'duracion_reservada': 0}, {'duracion_reservada': 17}, {'fecha_fin': self.inicio}):
            with self.assertRaises(IntegrityError), transaction.atomic():
                Cita.objects.create(**self.datos_cita(**cambios))


class ConcurrenciaCitaTests(DatosCitaMixin, TransactionTestCase):
    def setUp(self):
        self.preparar_datos()

    def test_dos_inserciones_concurrentes_solo_crean_una_cita(self):
        barrera = Barrier(2)
        datos = self.datos_cita()

        def insertar():
            try:
                barrera.wait(timeout=10)
                with transaction.atomic():
                    Cita.objects.create(**datos)
                return 'creada'
            except IntegrityError:
                return 'ocupada'
            finally:
                connections['default'].close()

        with ThreadPoolExecutor(max_workers=2) as ejecutor:
            resultados = list(ejecutor.map(lambda _: insertar(), range(2)))
        self.assertCountEqual(resultados, ['creada', 'ocupada'])
        self.assertEqual(Cita.objects.count(), 1)


# ---------------------------------------------------------------------------
# Servicios, selectores y vistas de citas (Samuel)
# ---------------------------------------------------------------------------
from datetime import datetime, time as hora_dia
from io import StringIO
from unittest import mock

from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.urls import reverse

from seguridad.roles import BARBERO
from seguridad.services import asignar_rol, registrar_cliente

from .selectors import obtener_agenda_barbero, obtener_citas_cliente, obtener_horarios_disponibles
from .services import cancelar_cita, completar_cita, reservar_cita

CLAVE = 'ClaveTemporalDePrueba_2030'


def dia_laboral_futuro(dias=2):
    fecha = timezone.localdate() + timedelta(days=dias)
    while fecha.weekday() == 6:
        fecha += timedelta(days=1)
    return fecha


def instante(fecha, hora, minuto=0):
    return timezone.make_aware(datetime.combine(fecha, hora_dia(hora, minuto)))


class EscenarioCitasMixin:
    def preparar_escenario(self):
        usuario = get_user_model()
        self.admin = usuario.objects.create_superuser(username='admin_citas', password=CLAVE)
        call_command('preparar_roles', stdout=StringIO())
        self.cliente = registrar_cliente(username='ana', password=CLAVE, first_name='Ana')
        self.otro_cliente = registrar_cliente(username='beto', password=CLAVE)
        self.cuenta_barbero = registrar_cliente(username='carlos', password=CLAVE, first_name='Carlos')
        self.barbero = asignar_rol(actor=self.admin, usuario=self.cuenta_barbero, rol=BARBERO).perfil_barbero
        self.cuenta_otro_barbero = registrar_cliente(username='dario', password=CLAVE)
        self.otro_barbero = asignar_rol(actor=self.admin, usuario=self.cuenta_otro_barbero, rol=BARBERO).perfil_barbero
        self.servicio = Servicio.objects.create(nombre='Corte de pelo', precio=Decimal('5.00'), duracion_minutos=30)
        self.fecha = dia_laboral_futuro()
        self.inicio = instante(self.fecha, 9)

    def reservar(self, inicio=None, actor=None, **cambios):
        datos = {'actor': actor or self.cliente, 'servicio_id': self.servicio.pk,
                 'barbero_id': self.barbero.pk, 'fecha_inicio': inicio or self.inicio}
        datos.update(cambios)
        return reservar_cita(**datos)

    def assertCodigo(self, codigo, funcion, *args, **kwargs):
        with self.assertRaises(ValidationError) as contexto:
            funcion(*args, **kwargs)
        self.assertEqual(contexto.exception.code, codigo)


class ReservaServiceTests(EscenarioCitasMixin, TestCase):
    def setUp(self):
        self.preparar_escenario()

    def test_reserva_valida_confirma_y_copia_datos_del_servidor(self):
        cita = self.reservar()
        self.assertEqual(cita.estado, EstadoCita.CONFIRMADA)
        self.assertEqual(cita.cliente, self.cliente)
        self.assertEqual(cita.fecha_fin, self.inicio + timedelta(minutes=30))
        self.assertEqual((cita.nombre_servicio_reservado, cita.precio_reservado, cita.duracion_reservada),
                         ('Corte de pelo', Decimal('5.00'), 30))

    def test_rechaza_fecha_pasada_domingo_desalineada_y_despues_del_cierre(self):
        pasado = instante(timezone.localdate() - timedelta(days=1), 9)
        domingo = self.fecha + timedelta(days=(6 - self.fecha.weekday()))
        self.assertCodigo('inicio_pasado', self.reservar, pasado)
        self.assertCodigo('dia_cerrado', self.reservar, instante(domingo, 9))
        self.assertCodigo('inicio_desalineado', self.reservar, instante(self.fecha, 9, 5))
        self.assertCodigo('fuera_horario', self.reservar, instante(self.fecha, 16, 45))
        self.assertCodigo('fuera_horario', self.reservar, instante(self.fecha, 7, 45))
        self.assertFalse(Cita.objects.exists())

    def test_rechaza_servicio_barbero_o_cuenta_inactivos(self):
        self.servicio.activo = False
        self.servicio.save()
        self.assertCodigo('servicio_no_disponible', self.reservar)
        self.servicio.activo = True
        self.servicio.save()

        self.barbero.activo = False
        self.barbero.save()
        self.assertCodigo('barbero_no_disponible', self.reservar)
        self.barbero.activo = True
        self.barbero.save()

        self.cuenta_barbero.is_active = False
        self.cuenta_barbero.save()
        self.assertCodigo('barbero_no_disponible', self.reservar)
        self.assertCodigo('barbero_no_disponible', self.reservar, barbero_id=999999)
        self.assertFalse(Cita.objects.exists())

    def test_solo_un_cliente_puede_reservar(self):
        for actor in (self.cuenta_barbero, self.admin):
            with self.assertRaises(PermissionDenied):
                self.reservar(actor=actor)
        self.assertFalse(Cita.objects.exists())

    def test_superposicion_parcial_y_total_se_rechaza(self):
        self.reservar()
        self.assertCodigo('horario_ocupado', self.reservar, self.inicio, actor=self.otro_cliente)
        self.assertCodigo('horario_ocupado', self.reservar, self.inicio + timedelta(minutes=15))
        self.assertCodigo('horario_ocupado', self.reservar, self.inicio - timedelta(minutes=15))
        self.assertEqual(Cita.objects.count(), 1)

    def test_contiguas_otro_barbero_y_cancelada_permitidas(self):
        cita = self.reservar()
        self.reservar(self.inicio + timedelta(minutes=30))
        self.reservar(self.inicio - timedelta(minutes=30))
        self.reservar(self.inicio, barbero_id=self.otro_barbero.pk)
        cancelar_cita(actor=self.cliente, cita_id=cita.pk)
        self.reservar(self.inicio, actor=self.otro_cliente)
        self.assertEqual(Cita.objects.exclude(estado=EstadoCita.CANCELADA).count(), 4)

    def test_snapshots_no_cambian_al_editar_el_catalogo(self):
        cita = self.reservar()
        self.servicio.nombre = 'Corte premium'
        self.servicio.precio = Decimal('9.00')
        self.servicio.duracion_minutos = 45
        self.servicio.save()
        cita.refresh_from_db()
        self.assertEqual((cita.nombre_servicio_reservado, cita.precio_reservado, cita.duracion_reservada, cita.fecha_fin),
                         ('Corte de pelo', Decimal('5.00'), 30, self.inicio + timedelta(minutes=30)))


class TransicionesCitaTests(EscenarioCitasMixin, TestCase):
    def setUp(self):
        self.preparar_escenario()
        self.cita = self.reservar()

    def en(self, momento):
        return mock.patch('django.utils.timezone.now', return_value=momento)

    def test_cliente_cancela_su_cita_antes_del_inicio_con_auditoria(self):
        cita = cancelar_cita(actor=self.cliente, cita_id=self.cita.pk, motivo='  No puedo asistir  ')
        cita.refresh_from_db()
        self.assertEqual(cita.estado, EstadoCita.CANCELADA)
        self.assertEqual(cita.cancelada_por, self.cliente)
        self.assertIsNotNone(cita.fecha_cancelacion)
        self.assertEqual(cita.motivo_cancelacion, 'No puedo asistir')

    def test_cliente_no_cancela_cita_ajena_ni_despues_del_inicio(self):
        with self.assertRaises(PermissionDenied):
            cancelar_cita(actor=self.otro_cliente, cita_id=self.cita.pk)
        with self.en(self.inicio):
            self.assertCodigo('cancelacion_fuera_de_plazo', cancelar_cita, actor=self.cliente, cita_id=self.cita.pk)
        self.cita.refresh_from_db()
        self.assertEqual(self.cita.estado, EstadoCita.CONFIRMADA)

    def test_barbero_asignado_y_admin_cancelan_aunque_este_atrasada(self):
        otra = self.reservar(self.inicio + timedelta(hours=1))
        with self.en(self.inicio + timedelta(hours=3)):
            self.assertEqual(cancelar_cita(actor=self.cuenta_barbero, cita_id=self.cita.pk).estado, EstadoCita.CANCELADA)
            self.assertEqual(cancelar_cita(actor=self.admin, cita_id=otra.pk).cancelada_por, self.admin)

    def test_otro_barbero_no_cancela_ni_completa(self):
        with self.en(self.cita.fecha_fin):
            for funcion in (cancelar_cita, completar_cita):
                with self.assertRaises(PermissionDenied):
                    funcion(actor=self.cuenta_otro_barbero, cita_id=self.cita.pk)

    def test_completar_solo_desde_el_fin_por_barbero_o_admin(self):
        with self.en(self.cita.fecha_fin - timedelta(minutes=1)):
            self.assertCodigo('finalizacion_anticipada', completar_cita, actor=self.cuenta_barbero, cita_id=self.cita.pk)
        with self.en(self.cita.fecha_fin):
            with self.assertRaises(PermissionDenied):
                completar_cita(actor=self.cliente, cita_id=self.cita.pk)
            cita = completar_cita(actor=self.cuenta_barbero, cita_id=self.cita.pk)
        self.assertEqual((cita.estado, cita.completada_por), (EstadoCita.COMPLETADA, self.cuenta_barbero))
        otra = self.reservar(self.inicio + timedelta(hours=1))
        with self.en(otra.fecha_fin):
            self.assertEqual(completar_cita(actor=self.admin, cita_id=otra.pk).estado, EstadoCita.COMPLETADA)

    def test_estados_terminales_no_cambian(self):
        cancelar_cita(actor=self.cliente, cita_id=self.cita.pk)
        self.assertCodigo('transicion_invalida', cancelar_cita, actor=self.admin, cita_id=self.cita.pk)
        with self.en(self.cita.fecha_fin):
            self.assertCodigo('transicion_invalida', completar_cita, actor=self.admin, cita_id=self.cita.pk)
        otra = self.reservar(self.inicio + timedelta(hours=1))
        with self.en(otra.fecha_fin):
            completar_cita(actor=self.cuenta_barbero, cita_id=otra.pk)
            self.assertCodigo('transicion_invalida', cancelar_cita, actor=self.cuenta_barbero, cita_id=otra.pk)

    def test_cita_inexistente_no_es_exito(self):
        with self.assertRaises(Cita.DoesNotExist):
            cancelar_cita(actor=self.cliente, cita_id=999999)
        with self.assertRaises(Cita.DoesNotExist):
            completar_cita(actor=self.admin, cita_id=999999)


class SelectoresCitaTests(EscenarioCitasMixin, TestCase):
    def setUp(self):
        self.preparar_escenario()

    def horarios(self, **cambios):
        datos = {'servicio_id': self.servicio.pk, 'barbero_id': self.barbero.pk, 'fecha': self.fecha}
        datos.update(cambios)
        return obtener_horarios_disponibles(**datos)

    def test_horarios_del_dia_completo_alineados_y_dentro_del_cierre(self):
        horarios = self.horarios()
        self.assertEqual(horarios[0], instante(self.fecha, 8))
        self.assertEqual(horarios[-1], instante(self.fecha, 16, 30))
        self.assertEqual(len(horarios), 35)
        self.assertEqual(horarios, sorted(horarios))

    def test_excluye_ocupados_y_permite_contiguos_y_cancelados(self):
        cita = self.reservar()
        horarios = self.horarios()
        for ocupado in (instante(self.fecha, 8, 45), instante(self.fecha, 9), instante(self.fecha, 9, 15)):
            self.assertNotIn(ocupado, horarios)
        self.assertIn(instante(self.fecha, 8, 30), horarios)
        self.assertIn(instante(self.fecha, 9, 30), horarios)
        self.assertIn(instante(self.fecha, 9), self.horarios(barbero_id=self.otro_barbero.pk))
        cancelar_cita(actor=self.cliente, cita_id=cita.pk)
        self.assertIn(instante(self.fecha, 9), self.horarios())

    def test_dia_cerrado_pasado_o_recursos_inactivos_no_ofrecen_horarios(self):
        domingo = self.fecha + timedelta(days=(6 - self.fecha.weekday()))
        self.assertEqual(self.horarios(fecha=domingo), [])
        self.assertEqual(self.horarios(fecha=timezone.localdate() - timedelta(days=1)), [])
        self.barbero.activo = False
        self.barbero.save()
        self.assertEqual(self.horarios(), [])
        self.assertEqual(self.horarios(barbero_id=999999), [])

    def test_agenda_y_listados_limitados_al_actor(self):
        propia = self.reservar()
        self.reservar(self.inicio, barbero_id=self.otro_barbero.pk, actor=self.otro_cliente)
        self.assertEqual(list(obtener_agenda_barbero(actor=self.cuenta_barbero, fecha=self.fecha)), [propia])
        self.assertEqual(list(obtener_citas_cliente(actor=self.cliente)), [propia])
        with self.assertRaises(PermissionDenied):
            obtener_agenda_barbero(actor=self.cliente, fecha=self.fecha)


class VistasCitaTests(EscenarioCitasMixin, TestCase):
    def setUp(self):
        self.preparar_escenario()
        self.client.force_login(self.cliente)

    def datos_post(self, **cambios):
        datos = {'servicio': self.servicio.pk, 'barbero': self.barbero.pk,
                 'inicio': timezone.localtime(self.inicio).strftime('%Y-%m-%dT%H:%M')}
        datos.update(cambios)
        return datos

    def test_flujo_completo_buscar_revisar_y_confirmar(self):
        respuesta = self.client.get(reverse('appointments:reservar'), {
            'servicio': self.servicio.pk, 'barbero': self.barbero.pk, 'fecha': self.fecha.isoformat()})
        self.assertContains(respuesta, '09:00 AM')
        respuesta = self.client.get(reverse('appointments:confirmar_reserva'), self.datos_post())
        self.assertContains(respuesta, 'Corte de pelo')
        self.assertContains(respuesta, '5,00 USD')
        respuesta = self.client.post(reverse('appointments:confirmar_reserva'), self.datos_post())
        cita = Cita.objects.get()
        self.assertRedirects(respuesta, reverse('appointments:detalle_cita', args=[cita.pk]))
        self.assertContains(self.client.get(reverse('appointments:mis_citas')), 'Corte de pelo')

    def test_datos_manipulados_no_se_aceptan(self):
        self.client.post(reverse('appointments:confirmar_reserva'), self.datos_post(
            precio_reservado='0.01', duracion_reservada='15', cliente=self.otro_cliente.pk,
            cliente_id=self.otro_cliente.pk, estado=EstadoCita.COMPLETADA))
        cita = Cita.objects.get()
        self.assertEqual((cita.cliente, cita.precio_reservado, cita.duracion_reservada, cita.estado),
                         (self.cliente, Decimal('5.00'), 30, EstadoCita.CONFIRMADA))
        for invalido in ('no-es-fecha', ''):
            respuesta = self.client.post(reverse('appointments:confirmar_reserva'), self.datos_post(inicio=invalido))
            self.assertRedirects(respuesta, reverse('appointments:reservar'))
        self.assertEqual(Cita.objects.count(), 1)

    def test_horario_ocupado_vuelve_a_opciones_sin_anunciar_exito(self):
        self.reservar(actor=self.otro_cliente)
        respuesta = self.client.post(reverse('appointments:confirmar_reserva'), self.datos_post(), follow=True)
        self.assertContains(respuesta, 'ya no está disponible')
        self.assertNotContains(respuesta, 'quedó confirmada')
        self.assertEqual(Cita.objects.count(), 1)

    def test_cliente_no_ve_ni_cancela_cita_ajena(self):
        ajena = self.reservar(actor=self.otro_cliente)
        self.assertEqual(self.client.get(reverse('appointments:detalle_cita', args=[ajena.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('appointments:cancelar_cita', args=[ajena.pk])).status_code, 404)
        self.assertNotContains(self.client.get(reverse('appointments:mis_citas')), 'Corte de pelo')
        ajena.refresh_from_db()
        self.assertEqual(ajena.estado, EstadoCita.CONFIRMADA)

    def test_cancelar_exige_post_y_funciona_con_post(self):
        cita = self.reservar()
        url = reverse('appointments:cancelar_cita', args=[cita.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertRedirects(self.client.post(url, {'motivo': 'Viaje'}), reverse('appointments:mis_citas'))
        cita.refresh_from_db()
        self.assertEqual((cita.estado, cita.motivo_cancelacion), (EstadoCita.CANCELADA, 'Viaje'))

    def test_motivo_demasiado_largo_se_rechaza(self):
        cita = self.reservar()
        self.client.post(reverse('appointments:cancelar_cita', args=[cita.pk]), {'motivo': 'x' * 501})
        cita.refresh_from_db()
        self.assertEqual(cita.estado, EstadoCita.CONFIRMADA)

    def test_anonimo_y_barbero_no_acceden(self):
        self.client.force_login(self.cuenta_barbero)
        self.assertEqual(self.client.get(reverse('appointments:reservar')).status_code, 403)
        self.client.logout()
        respuesta = self.client.get(reverse('appointments:mis_citas'))
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn('/seguridad/login/', respuesta['Location'])


class ConcurrenciaReservaTests(EscenarioCitasMixin, TransactionTestCase):
    def setUp(self):
        self.preparar_escenario()

    def test_dos_reservas_simultaneas_un_exito_y_un_error_comprensible(self):
        barrera = Barrier(2)

        def intentar(actor):
            try:
                barrera.wait(timeout=10)
                self.reservar(actor=actor)
                return 'creada'
            except ValidationError as error:
                return error.code
            finally:
                connections['default'].close()

        with ThreadPoolExecutor(max_workers=2) as ejecutor:
            resultados = list(ejecutor.map(intentar, (self.cliente, self.otro_cliente)))
        self.assertCountEqual(resultados, ['creada', 'horario_ocupado'])
        self.assertEqual(Cita.objects.count(), 1)


class EntradasManipuladasTests(EscenarioCitasMixin, TestCase):
    """Casos detectados por la revisión de validación de entradas."""
    def setUp(self):
        self.preparar_escenario()
        self.client.force_login(self.cliente)
        self.url = reverse('appointments:confirmar_reserva')

    def datos(self, inicio):
        return {'servicio': self.servicio.pk, 'barbero': self.barbero.pk, 'inicio': inicio}

    def test_fechas_extremas_redirigen_con_mensaje_y_no_dan_error_500(self):
        for inicio in ('9999-12-31T23:00', '0001-01-01T00:00+14:00'):
            for metodo in (self.client.get, self.client.post):
                respuesta = metodo(self.url, self.datos(inicio))
                self.assertRedirects(respuesta, reverse('appointments:reservar'))
        self.assertFalse(Cita.objects.exists())

    def test_resumen_no_ofrece_domingo_pasado_ni_horas_desalineadas(self):
        domingo = self.fecha + timedelta(days=(6 - self.fecha.weekday()))
        ayer = timezone.localdate() - timedelta(days=1)
        for inicio in (f'{domingo}T09:00', f'{ayer}T09:00', f'{self.fecha}T03:00', f'{self.fecha}T09:05'):
            self.assertRedirects(self.client.get(self.url, self.datos(inicio)), reverse('appointments:reservar'))

    def test_servicio_rechaza_motivo_demasiado_largo(self):
        cita = self.reservar()
        self.assertCodigo('motivo_largo', cancelar_cita, actor=self.cliente, cita_id=cita.pk, motivo='x' * 501)
        cita.refresh_from_db()
        self.assertEqual(cita.estado, EstadoCita.CONFIRMADA)

    def test_lista_de_barberos_excluye_cuentas_con_roles_ambiguos(self):
        from django.contrib.auth.models import Group
        from seguridad.roles import CLIENTE
        from .forms import barberos_habilitados
        self.cuenta_otro_barbero.groups.add(Group.objects.get(name=CLIENTE))
        self.assertEqual(list(barberos_habilitados()), [self.barbero])
