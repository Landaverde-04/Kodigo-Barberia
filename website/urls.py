from django.urls import path

from . import views

app_name = 'website'

urlpatterns = [
    path('servicios/', views.catalogo_servicios, name='catalogo_servicios'),
]
