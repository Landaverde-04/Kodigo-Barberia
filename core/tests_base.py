from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from .horarios import calcular_fin_validado, validar_duracion


class HorarioTests(SimpleTestCase):
    def setUp(self):
        self.zona = ZoneInfo('America/El_Salvador')
        self.ahora = datetime(2030, 1, 1, tzinfo=self.zona)

    def hora(self, dia, hora, minuto=0, segundo=0):
        return datetime(2030, 1, dia, hora, minuto, segundo, tzinfo=self.zona)

    def test_cita_puede_terminar_exactamente_al_cierre(self):
        fin = calcular_fin_validado(self.hora(2, 16, 45), 15, ahora=self.ahora)
        self.assertEqual(fin, self.hora(2, 17))

    def test_rechaza_intervalo_fuera_de_horario(self):
        for inicio, duracion in ((self.hora(2, 7, 45), 30), (self.hora(2, 16, 45), 30), (self.hora(2, 17), 15)):
            with self.assertRaises(ValidationError):
                calcular_fin_validado(inicio, duracion, ahora=self.ahora)

    def test_domingo_cerrado_y_sabado_abierto(self):
        calcular_fin_validado(self.hora(5, 8), 30, ahora=self.ahora)
        with self.assertRaises(ValidationError):
            calcular_fin_validado(self.hora(6, 8), 30, ahora=self.ahora)

    def test_rechaza_inicio_desalineado_o_con_segundos(self):
        for inicio in (self.hora(2, 8, 5), self.hora(2, 8, 0, 1)):
            with self.assertRaises(ValidationError):
                calcular_fin_validado(inicio, 30, ahora=self.ahora)

    def test_rechaza_pasado_y_fecha_sin_zona(self):
        for inicio in (self.ahora, self.ahora.replace(tzinfo=None)):
            with self.assertRaises(ValidationError):
                calcular_fin_validado(inicio, 30, ahora=self.ahora)

    def test_convierte_instante_utc_a_horario_local(self):
        inicio = self.hora(2, 8).astimezone(ZoneInfo('UTC'))
        self.assertEqual(calcular_fin_validado(inicio, 30, ahora=self.ahora), inicio + timedelta(minutes=30))

    def test_duracion_debe_ser_multiplo_positivo_de_quince(self):
        for valor in (0, -15, 17):
            with self.assertRaises(ValidationError):
                validar_duracion(valor)
