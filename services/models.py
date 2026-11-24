from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.functions import Mod
from django.db.models.lookups import Exact

from core.models import ModeloBase
from core.horarios import validar_duracion


class Servicio(ModeloBase):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(
        max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))]
    )
    duracion_minutos = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), validar_duracion])
    imagen = models.ImageField(upload_to='servicios/', blank=True)

    class Meta:
        ordering = ['nombre', 'pk']
        verbose_name = 'servicio'
        verbose_name_plural = 'servicios'
        constraints = [
            models.CheckConstraint(condition=models.Q(precio__gte=0), name='servicio_precio_no_negativo'),
            models.CheckConstraint(condition=models.Q(duracion_minutos__gt=0), name='servicio_duracion_positiva'),
            models.CheckConstraint(condition=Exact(Mod('duracion_minutos', 15), models.Value(0)), name='servicio_duracion_intervalo'),
        ]

    def __str__(self):
        return self.nombre
