from django.conf import settings
from django.db import models

from core.models import ModeloBase


class Barbero(ModeloBase):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='perfil_barbero'
    )
    descripcion = models.TextField(blank=True)
    foto = models.ImageField(upload_to='barberos/', blank=True)

    class Meta:
        ordering = ['usuario__first_name', 'usuario__username']
        verbose_name = 'barbero'
        verbose_name_plural = 'barberos'

    def __str__(self):
        return self.usuario.get_full_name() or self.usuario.username
