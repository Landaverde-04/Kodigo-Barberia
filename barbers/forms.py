from pathlib import Path

from django import forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

from .models import Barbero


class ImagenBarberoField(forms.ImageField):
    extensiones = {
        'JPEG': ('.jpg', '.jpeg'),
        'PNG': ('.png',),
        'WEBP': ('.webp',),
    }
    tamano_maximo = 5_000_000

    def to_python(self, data):
        if isinstance(data, UploadedFile) and data.size > self.tamano_maximo:
            raise ValidationError('La imagen debe pesar como máximo 5 MB.', code='imagen_demasiado_grande')

        imagen = super().to_python(data)
        if imagen:
            extensiones_validas = self.extensiones.get(imagen.image.format, ())
            if Path(imagen.name).suffix.lower() not in extensiones_validas:
                raise ValidationError(
                    'Usa una imagen JPEG, PNG o WebP con la extensión correspondiente.',
                    code='formato_imagen_invalido',
                )
        return imagen


class PerfilBarberoForm(forms.ModelForm):
    foto = ImagenBarberoField(
        label='Foto',
        required=False,
        help_text='Opcional. JPEG, PNG o WebP de hasta 5 MB.',
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/jpeg,image/png,image/webp',
        }),
    )

    class Meta:
        model = Barbero
        fields = ('descripcion', 'foto')
        labels = {'descripcion': 'Descripción'}
        widgets = {
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Cuéntanos brevemente tu experiencia y especialidad.',
            }),
        }
