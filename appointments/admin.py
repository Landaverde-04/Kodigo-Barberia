from django.contrib import admin

from .models import Cita


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    """Solo consulta: las escrituras deberán pasar por los servicios de Samuel."""
    list_display = ('id', 'cliente', 'barbero', 'nombre_servicio_reservado', 'fecha_inicio', 'estado')
    list_filter = ('estado', 'barbero')
    search_fields = ('cliente__username', 'nombre_servicio_reservado')
    list_select_related = ('cliente', 'barbero__usuario')
    date_hierarchy = 'fecha_inicio'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
