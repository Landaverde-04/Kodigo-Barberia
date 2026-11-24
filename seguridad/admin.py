from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Consulta de cuentas; editar roles desde las pantallas coordinadas de seguridad."""
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.unregister(Group)


@admin.register(Group)
class GrupoConsultaAdmin(admin.ModelAdmin):
    """Los grupos fijos se gestionan mediante seguridad y preparar_roles."""
    list_display = ('name',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
