from django.urls import path

from . import views

app_name = 'barbers'

urlpatterns = [
    path('', views.lista_barberos, name='lista_barberos'),
    path('mi-perfil/', views.mi_perfil, name='mi_perfil'),
    path('agenda/', views.agenda, name='agenda'),
    path('<int:pk>/cancelar/', views.cancelar_cita_barbero, name='cancelar_cita'),
    path('<int:pk>/completar/', views.completar_cita_barbero, name='completar_cita'),
    path('<int:pk>/editar/', views.editar_perfil, name='editar_perfil'),
]
