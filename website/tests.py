from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from services.models import Servicio


class CatalogoServiciosTests(TestCase):
    def test_visitante_ve_servicios_activos_con_o_sin_imagen(self):
        Servicio.objects.create(
            nombre='Corte clásico', descripcion='Acabado con tijera',
            precio=Decimal('12.50'), duracion_minutos=30,
        )
        Servicio.objects.create(
            nombre='Perfilado', precio=Decimal('8.00'), duracion_minutos=15,
            imagen='servicios/perfilado.webp',
        )
        Servicio.objects.create(
            nombre='Servicio retirado', precio=Decimal('5.00'),
            duracion_minutos=15, activo=False,
        )

        respuesta = self.client.get(reverse('website:catalogo_servicios'))

        self.assertContains(respuesta, 'Corte clásico')
        self.assertContains(respuesta, 'Acabado con tijera')
        self.assertContains(respuesta, '12,50 USD')
        self.assertContains(respuesta, '30 min')
        self.assertContains(respuesta, '/media/servicios/perfilado.webp')
        self.assertContains(respuesta, 'Sin imagen')
        self.assertNotContains(respuesta, 'Servicio retirado')

    def test_catalogo_vacio_muestra_un_mensaje(self):
        respuesta = self.client.get(reverse('website:catalogo_servicios'))

        self.assertContains(respuesta, 'Por ahora no hay servicios disponibles.')
