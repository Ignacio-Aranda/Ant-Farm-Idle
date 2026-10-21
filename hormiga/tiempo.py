"""Calendario, sol y clima de Málaga. Todo se calcula a partir de la fecha,
sin internet: el mismo día siempre tiene el mismo tiempo.

Fuentes:
- Clima: AEMET, valores normales 1981-2010, Málaga Aeropuerto (6155A).
- Sol: tabla de salida/puesta del sol en Málaga (día 1 de cada mes).
"""

import datetime
import math
import random

# Media de días con lluvia (>= 1 mm) por mes, enero..diciembre (AEMET).
DIAS_LLUVIA = [5.8, 4.8, 4.0, 4.5, 3.1, 0.8, 0.1, 0.5, 2.1, 4.4, 5.6, 6.6]
# Precipitación media mensual en mm (para la intensidad).
LLUVIA_MM = [69, 60, 52, 44, 20, 6, 0, 6, 20, 57, 100, 100]
# Temperatura media mensual en ºC (AEMET).
TEMP_MEDIA = [12.1, 12.9, 14.7, 16.3, 19.3, 23.0, 25.5, 26.0, 23.5, 19.5, 15.7, 13.2]
# Oscilación aproximada entre la mínima y la máxima del día.
OSCILACION = [9, 9, 9, 9, 9, 9, 9, 9, 8, 8, 8, 9]
# Nubosidad típica (0 despejado - 1 cubierto), estimada a partir de los días de lluvia.
NUBES = [0.40, 0.38, 0.35, 0.35, 0.25, 0.12, 0.05, 0.08, 0.18, 0.32, 0.40, 0.45]

# Salida y puesta del sol el día 1 de cada mes, en hora OFICIAL de Málaga.
_SOL_OFICIAL = [(8, 32, 18, 12), (8, 22, 18, 42), (7, 52, 19, 12), (8, 7, 20, 40),
                (7, 26, 21, 6), (7, 2, 21, 32), (7, 3, 21, 42), (7, 23, 21, 27),
                (7, 49, 20, 50), (8, 13, 20, 5), (7, 41, 18, 24), (8, 12, 18, 3)]


def _ultimo_domingo(anio, mes):
    d = datetime.date(anio, mes + 1, 1) - datetime.timedelta(days=1) if mes < 12 \
        else datetime.date(anio, 12, 31)
    return d - datetime.timedelta(days=(d.weekday() + 1) % 7)


def horario_verano(fecha):
    """Hora de verano en España: del último domingo de marzo al último de octubre."""
    return _ultimo_domingo(fecha.year, 3) <= fecha < _ultimo_domingo(fecha.year, 10)


def _sol_estandar(mes):
    """Tabla en hora de invierno (sin el +1 de verano) para poder interpolar."""
    h1, m1, h2, m2 = _SOL_OFICIAL[mes - 1]
    ajuste = 60 if 4 <= mes <= 10 else 0  # del 1 de abril al 1 de octubre ya es verano
    return h1 * 60 + m1 - ajuste, h2 * 60 + m2 - ajuste


def sol(fecha):
    """(amanecer, anochecer) en minutos desde medianoche, hora oficial."""
    ini = datetime.date(fecha.year, fecha.month, 1)
    sig = datetime.date(fecha.year + (fecha.month == 12), fecha.month % 12 + 1, 1)
    t = (fecha - ini).days / (sig - ini).days
    a1, p1 = _sol_estandar(fecha.month)
    a2, p2 = _sol_estandar(sig.month)
    a = a1 + (a2 - a1) * t
    p = p1 + (p2 - p1) * t
    if horario_verano(fecha):
        a, p = a + 60, p + 60
    return a, p


def pascua(anio):
    """Domingo de Resurrección (algoritmo anónimo gregoriano)."""
    a = anio % 19
    b, c = divmod(anio, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = ((h + l - 7 * m + 114) % 31) + 1
    return datetime.date(anio, mes, dia)


ESTACIONES = ["invierno", "primavera", "verano", "otoño"]


def estacion(fecha):
    """Estación astronómica (fechas aproximadas)."""
    md = (fecha.month, fecha.day)
    if md >= (12, 21) or md < (3, 20):
        return "invierno"
    if md < (6, 21):
        return "primavera"
    if md < (9, 23):
        return "verano"
    return "otoño"


class TiempoDelDia:
    """El tiempo de un día concreto en Málaga (determinista)."""

    def __init__(self, fecha, semilla=0):
        self.fecha = fecha
        rng = random.Random("%s-%s" % (semilla, fecha.isoformat()))
        mes = fecha.month - 1
        dias_mes = 31
        prob = DIAS_LLUVIA[mes] / dias_mes
        # Los días de lluvia suelen ir seguidos: si ayer llovió, más probable.
        ayer = random.Random("%s-%s" % (semilla, (fecha - datetime.timedelta(1)).isoformat()))
        if ayer.random() < prob:
            prob = min(0.9, prob * 2.2)
        self.llueve = rng.random() < prob
        self.lluvias = []  # (inicio_min, fin_min, intensidad 0-1)
        if self.llueve:
            for _ in range(rng.choice([1, 1, 1, 2])):
                ini = rng.uniform(0, 22 * 60)
                dur = rng.uniform(1.5, 7) * 60
                inten = min(1.0, rng.uniform(0.2, 0.7) + LLUVIA_MM[mes] / 400)
                self.lluvias.append((ini, min(24 * 60, ini + dur), inten))
        self.tormenta = self.llueve and mes in (8, 9, 10, 11, 0) and rng.random() < 0.3
        self.nubes = min(1.0, max(0.0, NUBES[mes] + rng.uniform(-0.25, 0.3)
                                  + (0.4 if self.llueve else 0)))
        # Calima (polvo del Sáhara) y terral (viento caliente de tierra adentro)
        self.calima = mes in (1, 2, 5, 6, 7) and rng.random() < 0.04 and not self.llueve
        self.terral = mes in (5, 6, 7) and rng.random() < 0.10 and not self.llueve
        self.variacion = rng.uniform(-2.5, 2.5) + (5 if self.terral else 0) - (2 if self.llueve else 0)

    def lluvia(self, minuto):
        """Intensidad de lluvia (0 = nada) en un minuto del día."""
        for ini, fin, inten in self.lluvias:
            if ini <= minuto <= fin:
                # empieza y acaba suave
                borde = min(minuto - ini, fin - minuto) / 30
                return inten * min(1.0, 0.3 + borde)
        return 0.0

    def temperatura(self, minuto):
        mes = self.fecha.month - 1
        media = TEMP_MEDIA[mes] + self.variacion
        # mínima hacia las 7:00, máxima hacia las 16:00
        fase = math.cos((minuto / 60 - 16) / 24 * 2 * math.pi)
        return media + fase * OSCILACION[mes] / 2


_CACHE = {}


def tiempo_del_dia(fecha, semilla=0):
    clave = (fecha, semilla)
    t = _CACHE.get(clave)
    if t is None:
        if len(_CACHE) > 50:
            _CACHE.clear()
        t = _CACHE[clave] = TiempoDelDia(fecha, semilla)
    return t


def llovio_hace(ahora, horas, semilla=0):
    """¿Ha llovido en las últimas 'horas'? (para charcos, setas y caracoles)"""
    for h in range(0, int(horas) + 1):
        t = ahora - datetime.timedelta(hours=h)
        if tiempo_del_dia(t.date(), semilla).lluvia(t.hour * 60 + t.minute) > 0:
            return True
    return False


def fase_lunar(fecha):
    """0 = nueva, 0.5 = llena."""
    ref = datetime.date(2000, 1, 6)
    return ((fecha - ref).days % 29.530588) / 29.530588
