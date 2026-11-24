from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateTimeRangeField, RangeBoundary, RangeOperators
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.functions import Mod
from django.db.models.lookups import Exact

from core.models import ModeloBase
from core.horarios import validar_duracion


class EstadoCita(models.TextChoices):
    CONFIRMADA = 'CONFIRMED', 'Confirmada'
    CANCELADA = 'CANCELLED', 'Cancelada'
    COMPLETADA = 'COMPLETED', 'Completada'


class Cita(ModeloBase):
    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='citas_cliente'
    )
    barbero = models.ForeignKey('barbers.Barbero', on_delete=models.PROTECT, related_name='citas')
    servicio = models.ForeignKey('services.Servicio', on_delete=models.PROTECT, related_name='citas')
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    nombre_servicio_reservado = models.CharField(max_length=100)
    precio_reservado = models.DecimalField(
        max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))]
    )
    duracion_reservada = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), validar_duracion])
    estado = models.CharField(max_length=10, choices=EstadoCita.choices, default=EstadoCita.CONFIRMADA)
    fecha_cancelacion = models.DateTimeField(null=True, blank=True)
    cancelada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name='citas_canceladas',
    )
    motivo_cancelacion = models.TextField(blank=True)
    fecha_finalizacion = models.DateTimeField(null=True, blank=True)
    completada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name='citas_completadas',
    )

    class Meta:
        ordering = ['fecha_inicio', 'pk']
        verbose_name = 'cita'
        verbose_name_plural = 'citas'
        indexes = [
            models.Index(fields=['barbero', 'fecha_inicio'], name='cita_barbero_inicio_idx'),
            models.Index(fields=['cliente', 'fecha_inicio'], name='cita_cliente_inicio_idx'),
        ]
        constraints = [
            models.CheckConstraint(condition=models.Q(fecha_fin__gt=models.F('fecha_inicio')), name='cita_fin_posterior_inicio'),
            models.CheckConstraint(condition=models.Q(precio_reservado__gte=0), name='cita_precio_no_negativo'),
            models.CheckConstraint(condition=models.Q(duracion_reservada__gt=0), name='cita_duracion_positiva'),
            models.CheckConstraint(condition=Exact(Mod('duracion_reservada', 15), models.Value(0)), name='cita_duracion_intervalo'),
            models.CheckConstraint(condition=models.Q(estado__in=EstadoCita.values), name='cita_estado_valido'),
            models.CheckConstraint(
                condition=(
                    models.Q(estado=EstadoCita.CONFIRMADA, fecha_cancelacion__isnull=True,
                             cancelada_por__isnull=True, fecha_finalizacion__isnull=True,
                             completada_por__isnull=True)
                    | models.Q(estado=EstadoCita.CANCELADA, fecha_cancelacion__isnull=False,
                               cancelada_por__isnull=False, fecha_finalizacion__isnull=True,
                               completada_por__isnull=True)
                    | models.Q(estado=EstadoCita.COMPLETADA, fecha_cancelacion__isnull=True,
                               cancelada_por__isnull=True, fecha_finalizacion__isnull=False,
                               completada_por__isnull=False)
                ), name='cita_auditoria_coherente',
            ),
            ExclusionConstraint(
                name='cita_barbero_sin_superposicion',
                expressions=[
                    (models.Func(
                        'fecha_inicio', 'fecha_fin', RangeBoundary(),
                        function='TSTZRANGE', output_field=DateTimeRangeField(),
                    ), RangeOperators.OVERLAPS),
                    ('barbero', RangeOperators.EQUAL),
                ],
                condition=~models.Q(estado=EstadoCita.CANCELADA),
            ),
        ]

    def clean(self):
        super().clean()
        if self.fecha_inicio and self.fecha_fin and self.duracion_reservada:
            if self.fecha_fin - self.fecha_inicio != timedelta(minutes=self.duracion_reservada):
                raise ValidationError({'fecha_fin': 'Debe coincidir con el inicio más la duración reservada.'})

    def __str__(self):
        return f'{self.nombre_servicio_reservado} - {self.fecha_inicio}'
