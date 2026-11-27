from django.urls import path

from . import views

app_name = 'barbers'

urlpatterns = [
    path('', views.lista_barberos, name='lista_barberos'),
    path('mi-perfil/', views.mi_perfil, name='mi_perfil'),
    path('<int:pk>/editar/', views.editar_perfil, name='editar_perfil'),
]
