from django.urls import path

from . import views

app_name = 'services'

urlpatterns = [
    path('', views.lista_servicios, name='lista_servicios'),
    path('crear/', views.crear_servicio, name='crear_servicio'),
    path('<int:pk>/editar/', views.editar_servicio, name='editar_servicio'),
    path('<int:pk>/activar/', views.cambiar_estado_servicio, {'activo': True}, name='activar_servicio'),
    path('<int:pk>/desactivar/', views.cambiar_estado_servicio, {'activo': False}, name='desactivar_servicio'),
]
