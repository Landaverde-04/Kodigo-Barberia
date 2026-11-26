from django.urls import path

from . import views

app_name = 'appointments'

urlpatterns = [
    path('', views.mis_citas, name='mis_citas'),
    path('reservar/', views.reservar, name='reservar'),
    path('reservar/confirmar/', views.confirmar_reserva, name='confirmar_reserva'),
    path('<int:pk>/', views.detalle_cita, name='detalle_cita'),
    path('<int:pk>/cancelar/', views.cancelar, name='cancelar_cita'),
]
