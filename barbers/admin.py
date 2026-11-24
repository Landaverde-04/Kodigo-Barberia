from django.contrib import admin

from .models import Barbero


@admin.register(Barbero)
class BarberoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'activo')
    list_filter = ('activo',)
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name')
    list_select_related = ('usuario',)

    # La asignación de rol y perfil se implementará como una operación única.
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
