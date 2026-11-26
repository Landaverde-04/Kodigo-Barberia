from datetime import datetime, timedelta

from django import forms
from django.db.models import Count, Q
from django.utils import timezone

from barbers.models import Barbero
from core.horarios import calcular_fin_validado
from seguridad.roles import BARBERO, ROLES_NEGOCIO
from services.models import Servicio

from .services import MAX_MOTIVO


class BarberoChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.usuario.get_full_name() or obj.usuario.username


class ServicioChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f'{obj.nombre} — ${obj.precio} · {obj.duracion_minutos} min'


def barberos_habilitados():
    """Mismo criterio que services.barbero_habilitado: un único rol de negocio, Barbero."""
    return (
        Barbero.objects.filter(activo=True, usuario__is_active=True, usuario__is_superuser=False)
        .annotate(roles=Count('usuario__groups', filter=Q(usuario__groups__name__in=ROLES_NEGOCIO), distinct=True))
        .filter(roles=1, usuario__groups__name=BARBERO)
        .select_related('usuario').distinct()
    )


class BuscarHorarioForm(forms.Form):
    """Paso 1: servicio, barbero y fecha. Solo ofrece recursos habilitados."""
    servicio = ServicioChoiceField(
        queryset=Servicio.objects.filter(activo=True), empty_label='Elige un servicio',
        error_messages={'required': 'Elige un servicio.', 'invalid_choice': 'El servicio elegido no está disponible.'},
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    barbero = BarberoChoiceField(
        queryset=Barbero.objects.none(), empty_label='Elige un barbero',
        error_messages={'required': 'Elige un barbero.', 'invalid_choice': 'El barbero elegido no está disponible.'},
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    fecha = forms.DateField(
        error_messages={'required': 'Elige una fecha.', 'invalid': 'Escribe una fecha válida.'},
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['barbero'].queryset = barberos_habilitados()
        self.fields['fecha'].widget.attrs['min'] = timezone.localdate().isoformat()

    def clean_fecha(self):
        fecha = self.cleaned_data['fecha']
        if fecha < timezone.localdate():
            raise forms.ValidationError('Elige una fecha de hoy en adelante.', code='fecha_pasada')
        return fecha


class ConfirmarReservaForm(BuscarHorarioForm):
    """Paso 2: añade el inicio elegido. Precio, duración y cliente nunca llegan del navegador."""
    fecha = None
    inicio = forms.CharField(error_messages={'required': 'Elige una hora disponible.'})

    def clean_inicio(self):
        valor = self.cleaned_data['inicio'].strip()
        try:
            inicio = datetime.fromisoformat(valor)
            if timezone.is_naive(inicio):
                inicio = timezone.make_aware(inicio, timezone.get_default_timezone())
            # Descarta fechas en los extremos del calendario que desbordan al convertir zonas.
            timezone.localtime(inicio) + timedelta(days=1)
        except (ValueError, OverflowError):
            raise forms.ValidationError('La hora elegida no es válida.', code='inicio_invalido') from None
        return inicio

    def clean(self):
        datos = super().clean()
        servicio, inicio = datos.get('servicio'), datos.get('inicio')
        if servicio and inicio:
            # El resumen no ofrece horas pasadas, cerradas o desalineadas; la reserva revalida igual.
            datos['fin'] = calcular_fin_validado(inicio, servicio.duracion_minutos)
        return datos


class CancelarCitaForm(forms.Form):
    motivo = forms.CharField(
        required=False, max_length=MAX_MOTIVO,
        error_messages={'max_length': f'El motivo admite como máximo {MAX_MOTIVO} caracteres.'},
        widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'maxlength': MAX_MOTIVO,
                                     'placeholder': 'Motivo (opcional)'}),
    )
