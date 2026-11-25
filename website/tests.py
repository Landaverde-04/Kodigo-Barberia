from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from barbers.models import Barbero
from seguridad.roles import BARBERO, CLIENTE
from services.models import Servicio


class CatalogoServiciosTests(TestCase):
    def test_visitante_ve_servicios_activos_con_o_sin_imagen(self):
        Servicio.objects.create(
            nombre='Corte clásico', descripcion='Acabado con tijera',
            precio=Decimal('12.50'), duracion_minutos=30,
        )
        Servicio.objects.create(
            nombre='Perfilado', precio=Decimal('8.00'), duracion_minutos=15,
            imagen='servicios/perfilado.webp',
        )
        Servicio.objects.create(
            nombre='Servicio retirado', precio=Decimal('5.00'),
            duracion_minutos=15, activo=False,
        )

        respuesta = self.client.get(reverse('website:catalogo_servicios'))

        self.assertContains(respuesta, 'Corte clásico')
        self.assertContains(respuesta, 'Acabado con tijera')
        self.assertContains(respuesta, '12,50 USD')
        self.assertContains(respuesta, '30 min')
        self.assertContains(respuesta, '/media/servicios/perfilado.webp')
        self.assertContains(respuesta, 'Sin imagen')
        self.assertNotContains(respuesta, 'Servicio retirado')

    def test_catalogo_vacio_muestra_un_mensaje(self):
        respuesta = self.client.get(reverse('website:catalogo_servicios'))

        self.assertContains(respuesta, 'Por ahora no hay servicios disponibles.')


class SitioPublicoTests(TestCase):
    def test_portada_publica_enlaza_catalogos_e_inicio_de_sesion(self):
        respuesta = self.client.get(reverse('website:portada'))

        self.assertContains(respuesta, 'Distrito Barber')
        for nombre in ('website:catalogo_servicios', 'website:catalogo_barberos', 'seguridad:login'):
            self.assertContains(respuesta, f'href="{reverse(nombre)}"')
        self.assertNotContains(respuesta, 'Panel de gestión')


class CatalogoBarberosTests(TestCase):
    def test_perfiles_publicos_excluyen_cuentas_y_roles_inhabilitados(self):
        grupo_barbero = Group.objects.create(name=BARBERO)
        grupo_cliente = Group.objects.create(name=CLIENTE)
        usuarios = get_user_model().objects
        visible = usuarios.create_user(
            username='cuenta_privada', first_name='Ana', last_name='Morales',
            email='ana.privado@example.com',
        )
        visible.groups.add(grupo_barbero)
        Barbero.objects.create(
            usuario=visible, descripcion='Especialista en cortes clásicos', foto='barberos/ana.webp',
        )
        sin_nombre = usuarios.create_user(username='cuenta_sin_nombre')
        sin_nombre.groups.add(grupo_barbero)
        Barbero.objects.create(usuario=sin_nombre)
        cuenta_inactiva = usuarios.create_user(
            username='inactivo', first_name='Cuenta inactiva', is_active=False,
        )
        cuenta_inactiva.groups.add(grupo_barbero)
        Barbero.objects.create(usuario=cuenta_inactiva)
        perfil_inactivo = usuarios.create_user(username='retirado', first_name='Perfil retirado')
        perfil_inactivo.groups.add(grupo_barbero)
        Barbero.objects.create(usuario=perfil_inactivo, activo=False)
        cliente = usuarios.create_user(username='cliente', first_name='Perfil cliente')
        cliente.groups.add(grupo_cliente)
        Barbero.objects.create(usuario=cliente)
        ambiguo = usuarios.create_user(username='ambiguo', first_name='Perfil ambiguo')
        ambiguo.groups.add(grupo_barbero, grupo_cliente)
        Barbero.objects.create(usuario=ambiguo)
        administrador = usuarios.create_superuser(username='admin', first_name='Perfil administrador')
        administrador.groups.add(grupo_barbero)
        Barbero.objects.create(usuario=administrador)

        respuesta = self.client.get(reverse('website:catalogo_barberos'))

        self.assertContains(respuesta, 'Ana Morales')
        self.assertContains(respuesta, 'Especialista en cortes clásicos')
        self.assertContains(respuesta, '/media/barberos/ana.webp')
        self.assertContains(respuesta, 'Barbero del equipo')
        for texto in (
            'cuenta_privada', 'cuenta_sin_nombre', 'ana.privado@example.com', 'Cuenta inactiva',
            'Perfil retirado', 'Perfil cliente', 'Perfil ambiguo', 'Perfil administrador',
        ):
            self.assertNotContains(respuesta, texto)

    def test_catalogo_sin_perfiles_muestra_un_mensaje(self):
        respuesta = self.client.get(reverse('website:catalogo_barberos'))

        self.assertContains(respuesta, 'Por ahora no hay perfiles de barberos publicados.')
