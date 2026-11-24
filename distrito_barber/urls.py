from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = settings.NOMBRE_BARBERIA
admin.site.site_title = settings.NOMBRE_BARBERIA
admin.site.index_title = 'Administración de la barbería'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('seguridad/', include('seguridad.urls')),
    path('servicios/', include('services.urls')),
    path('barberos/', include('barbers.urls')),
    path('citas/', include('appointments.urls')),
    path('web/', include('website.urls')),
    path('panel/', include('dashboard.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
