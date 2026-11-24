from django.contrib import admin
from django.urls import path, include

from django.conf import settings

admin.site.site_header = settings.NOMBRE_BARBERIA
admin.site.site_title = settings.NOMBRE_BARBERIA
admin.site.index_title = 'Administración de la barbería'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('seguridad/', include('seguridad.urls')),
]
