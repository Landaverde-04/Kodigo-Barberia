from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Servicio


class ServicioTests(TestCase):
    def test_precio_negativo_y_duracion_cero_no_se_guardan(self):
        for precio, duracion in ((Decimal('-1'), 30), (Decimal('5'), 0), (Decimal('5'), 17)):
            with self.assertRaises(IntegrityError), transaction.atomic():
                Servicio.objects.create(nombre='Invalido', precio=precio, duracion_minutos=duracion)

    def test_imagen_es_opcional_y_se_puede_desactivar(self):
        servicio = Servicio(nombre='Corte', precio=Decimal('5'), duracion_minutos=30)
        servicio.full_clean()
        servicio.save()
        servicio.activo = False
        servicio.save()
        self.assertTrue(Servicio.objects.filter(pk=servicio.pk, activo=False).exists())
