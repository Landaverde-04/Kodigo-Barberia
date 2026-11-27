"""Consultas de solo lectura sobre perfiles de barbero."""
from .models import Barbero


def obtener_perfil_de_usuario(usuario):
    """Devuelve el perfil existente del usuario o None; nunca lo crea."""
    return Barbero.objects.select_related('usuario').filter(usuario=usuario).first()


def listar_perfiles():
    """Perfiles registrados para consulta administrativa, con la cuenta asociada."""
    return Barbero.objects.select_related('usuario').all()
