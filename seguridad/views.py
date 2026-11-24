from itertools import groupby

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.models import Group, Permission
from django.db.models import Count
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.core.exceptions import PermissionDenied, ValidationError

from .roles import ADMINISTRADOR, CLIENTE, rol_requerido
from .services import asignar_rol
from django.contrib import messages
from django.urls import reverse_lazy

from .models import Usuario
from .forms import UsuarioCrearForm, UsuarioEditarForm, RolForm, ResetearPasswordForm, APPS_NEGOCIO, PERMISOS_NEGOCIO


_ACCIONES_ES = {
    'add': 'Agregar',
    'change': 'Modificar',
    'delete': 'Eliminar',
    'view': 'Ver',
}


def _permisos_agrupados():
    permisos = Permission.objects.filter(
        PERMISOS_NEGOCIO
    ).select_related('content_type').order_by('content_type__app_label', 'codename')
    resultado = []
    for app_label, grupo in groupby(permisos, key=lambda p: p.content_type.app_label):
        items = []
        for p in grupo:
            accion = p.codename.split('_')[0]
            label = f"{_ACCIONES_ES.get(accion, accion)} {p.content_type.model}"
            items.append({'pk': p.pk, 'label': label})
        resultado.append((app_label, items))
    return resultado


@login_required
@permission_required('seguridad.view_usuario', raise_exception=True)
@rol_requerido(ADMINISTRADOR)
def lista_usuarios(request):
    usuarios = Usuario.objects.all().order_by('username')
    return render(request, 'seguridad/lista_usuarios.html', {'usuarios': usuarios})


@login_required
@permission_required('seguridad.view_usuario', raise_exception=True)
@rol_requerido(ADMINISTRADOR)
def detalle_usuario(request, id):
    usuario = get_object_or_404(Usuario, pk=id)
    return render(request, 'seguridad/detalle_usuario.html', {'usuario': usuario})


@login_required
@permission_required('seguridad.add_usuario', raise_exception=True)
@rol_requerido(ADMINISTRADOR)
def crear_usuario(request):
    if request.method == 'POST':
        form = UsuarioCrearForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    usuario = form.save(commit=False)
                    usuario.debe_cambiar_password = True
                    usuario.save()
                    grupos = form.cleaned_data['groups']
                    asignar_rol(actor=request.user, usuario=usuario, rol=grupos[0].name if grupos else CLIENTE)
                messages.success(request, 'Usuario creado correctamente.')
                return redirect('seguridad:lista_usuarios')
            except ValidationError as error:
                form.add_error(None, error)
    else:
        form = UsuarioCrearForm()
    return render(request, 'seguridad/form_usuario.html', {'form': form, 'accion': 'Crear'})


@login_required
@permission_required('seguridad.change_usuario', raise_exception=True)
@rol_requerido(ADMINISTRADOR)
def editar_usuario(request, id):
    usuario = get_object_or_404(Usuario, pk=id)
    if request.method == 'POST':
        form = UsuarioEditarForm(request.POST, instance=usuario)
        if form.is_valid():
            try:
                with transaction.atomic():
                    usuario = form.save(commit=False)
                    usuario.save()
                    grupos = form.cleaned_data['groups']
                    rol = grupos[0].name if grupos else (ADMINISTRADOR if usuario.is_superuser else CLIENTE)
                    asignar_rol(actor=request.user, usuario=usuario, rol=rol)
                messages.success(request, 'Usuario actualizado correctamente.')
                return redirect('seguridad:lista_usuarios')
            except ValidationError as error:
                form.add_error(None, error)
    else:
        form = UsuarioEditarForm(instance=usuario)
    return render(request, 'seguridad/form_usuario.html', {'form': form, 'accion': 'Editar', 'usuario': usuario})


@login_required
@permission_required('seguridad.delete_usuario', raise_exception=True)
@rol_requerido(ADMINISTRADOR)
def eliminar_usuario(request, id):
    usuario = get_object_or_404(Usuario, pk=id)
    if request.method == 'POST':
        try:
            usuario.delete()
        except ProtectedError:
            messages.error(request, 'La cuenta tiene información asociada. Conserva su historial y desactívala desde la edición de cuenta.')
            return redirect('seguridad:detalle_usuario', id=id)
        messages.success(request, 'Usuario eliminado correctamente.')
        return redirect('seguridad:lista_usuarios')
    return render(request, 'seguridad/eliminar_usuario.html', {'usuario': usuario})


# --- Roles ---

@login_required
@permission_required('auth.view_group', raise_exception=True)
@rol_requerido(ADMINISTRADOR)
def lista_roles(request):
    roles = Group.objects.filter(name__in=(CLIENTE, 'Barbero', ADMINISTRADOR)).annotate(total_usuarios=Count('user')).order_by('name')
    return render(request, 'seguridad/lista_roles.html', {'roles': roles})


@login_required
@permission_required('auth.add_group', raise_exception=True)
@rol_requerido(ADMINISTRADOR)
def crear_rol(request):
    raise PermissionDenied('Los tres roles del negocio son fijos. Usa preparar_roles para inicializarlos.')

@login_required
@permission_required('auth.change_group', raise_exception=True)
@rol_requerido(ADMINISTRADOR)
def editar_rol(request, id):
    rol = get_object_or_404(Group, pk=id, name__in=(CLIENTE, 'Barbero', ADMINISTRADOR))
    if request.method == 'POST':
        form = RolForm(request.POST, instance=rol)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rol actualizado correctamente.')
            return redirect('seguridad:lista_roles')
        permisos_seleccionados = set(int(pk) for pk in request.POST.getlist('permissions') if str(pk).isdigit())
    else:
        form = RolForm(instance=rol)
        permisos_seleccionados = set(rol.permissions.values_list('pk', flat=True))
    return render(request, 'seguridad/form_rol.html', {
        'form': form,
        'accion': 'Editar',
        'rol': rol,
        'permisos_agrupados': _permisos_agrupados(),
        'permisos_seleccionados': permisos_seleccionados,
    })


@login_required
@permission_required('auth.delete_group', raise_exception=True)
@rol_requerido(ADMINISTRADOR)
def eliminar_rol(request, id):
    raise PermissionDenied('Los tres roles del negocio son fijos. Usa preparar_roles para inicializarlos.')

@login_required
@permission_required('auth.change_group', raise_exception=True)
@rol_requerido(ADMINISTRADOR)
def usuarios_rol(request, id):
    rol = get_object_or_404(Group, pk=id, name__in=(CLIENTE, 'Barbero', ADMINISTRADOR))
    if request.method == 'POST':
        messages.info(request, 'Cambia el rol desde la edición de la cuenta para mantener coherente su perfil de barbero.')
        return redirect('seguridad:lista_usuarios')

    usuarios_con_rol = rol.user_set.all().order_by('username')
    usuarios_sin_rol = Usuario.objects.exclude(groups=rol).order_by('username')
    return render(request, 'seguridad/usuarios_rol.html', {
        'rol': rol,
        'usuarios_con_rol': usuarios_con_rol,
        'usuarios_sin_rol': usuarios_sin_rol,
    })


# --- Reseteo de contraseña por administrador ---

@login_required
@permission_required('seguridad.change_usuario', raise_exception=True)
@rol_requerido(ADMINISTRADOR)
def resetear_password(request, id):
    usuario = get_object_or_404(Usuario, pk=id)
    if request.method == 'POST':
        form = ResetearPasswordForm(request.POST)
        if form.is_valid():
            usuario.set_password(form.cleaned_data['password1'])
            usuario.debe_cambiar_password = True
            usuario.save()
            messages.success(
                request,
                f'Contraseña de {usuario.username} restablecida. '
                'El usuario deberá cambiarla en su próximo acceso.'
            )
            return redirect('seguridad:detalle_usuario', id=id)
    else:
        form = ResetearPasswordForm()
    return render(request, 'seguridad/resetear_password.html', {'form': form, 'usuario': usuario})


# --- Perfil propio ---

@login_required
def mi_perfil(request):
    return render(request, 'seguridad/mi_perfil.html')


class CambiarPasswordView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'seguridad/cambiar_password.html'
    success_url = reverse_lazy('seguridad:mi_perfil')

    def form_valid(self, form):
        self.request.user.debe_cambiar_password = False
        self.request.user.save(update_fields=['debe_cambiar_password'])
        messages.success(self.request, 'Contraseña actualizada correctamente.')
        return super().form_valid(form)
