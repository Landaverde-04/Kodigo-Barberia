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
