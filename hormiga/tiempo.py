"""Calendario, sol y clima. El sol se calcula con la latitud y la longitud de la ciudad;
el tiempo, si no hay datos reales de OpenWeather (hormiga/clima_real.py), sale de un
modelo estadístico: el mismo día siempre tiene el mismo tiempo.

Fuentes:
- Sol: aproximación de la NOAA (ecuación del tiempo y declinación solar).
- Clima de respaldo: AEMET, valores normales 1981-2010, Málaga Aeropuerto (6155A).
"""

import datetime
import math
import random

# Clima de respaldo (Málaga). Media de días con lluvia (>= 1 mm) por mes, enero..diciembre.
DIAS_LLUVIA = [5.8, 4.8, 4.0, 4.5, 3.1, 0.8, 0.1, 0.5, 2.1, 4.4, 5.6, 6.6]
# Precipitación media mensual en mm (para la intensidad).
LLUVIA_MM = [69, 60, 52, 44, 20, 6, 0, 6, 20, 57, 100, 100]
# Temperatura media mensual en ºC.
TEMP_MEDIA = [12.1, 12.9, 14.7, 16.3, 19.3, 23.0, 25.5, 26.0, 23.5, 19.5, 15.7, 13.2]
# Oscilación aproximada entre la mínima y la máxima del día.
OSCILACION = [9, 9, 9, 9, 9, 9, 9, 9, 8, 8, 8, 9]
# Nubosidad típica (0 despejado - 1 cubierto), estimada a partir de los días de lluvia.
NUBES = [0.40, 0.38, 0.35, 0.35, 0.25, 0.12, 0.05, 0.08, 0.18, 0.32, 0.40, 0.45]

MALAGA = (36.72, -4.42)


def zona_horaria(nombre):
    """La zona horaria con ese nombre (p. ej. "Europe/Madrid"), o None si no se da o no existe."""
    if not nombre:
        return None
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(str(nombre).strip())
    except Exception:
        return None


def ahora(zona=None):
    """La hora de ahora (sin zona): la de la ciudad si se da su zona horaria, o la del ordenador."""
    return datetime.datetime.now(zona_horaria(zona)).replace(tzinfo=None)


def desfase_horario(fecha, zona=None):
    """Minutos de diferencia con UTC ese día (con horario de verano), en la zona de la
    ciudad si se da (p. ej. "Europe/Madrid") o en la del ordenador si no."""
    mediodia = datetime.datetime(fecha.year, fecha.month, fecha.day, 12)
    z = zona_horaria(zona)
    if z:
        return mediodia.replace(tzinfo=z).utcoffset().total_seconds() / 60
    return mediodia.astimezone().utcoffset().total_seconds() / 60


def sol(fecha, lat=MALAGA[0], lon=MALAGA[1], zona=None):
    """(amanecer, anochecer) en minutos desde medianoche, en hora local."""
    g = 2 * math.pi / 365 * (fecha.timetuple().tm_yday - 1)
    ecuacion = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g)
                         - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    decl = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g)
            + 0.000907 * math.sin(2 * g) - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    la = math.radians(lat)
    cos_h = math.cos(math.radians(90.833)) / (math.cos(la) * math.cos(decl)) - math.tan(la) * math.tan(decl)
    if cos_h <= -1:
        return 0, 24 * 60          # sol de medianoche
    if cos_h >= 1:
        return 12 * 60, 12 * 60    # noche polar
    h = math.degrees(math.acos(cos_h))
    desfase = desfase_horario(fecha, zona)
    return (720 - 4 * (lon + h) - ecuacion + desfase, 720 - 4 * (lon - h) - ecuacion + desfase)


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


def estacion(fecha, sur=False):
    """Estación astronómica (fechas aproximadas). En el hemisferio sur, al revés."""
    md = (fecha.month, fecha.day)
    if md >= (12, 21) or md < (3, 20):
        e = 0
    elif md < (6, 21):
        e = 1
    elif md < (9, 23):
        e = 2
    else:
        e = 3
    return ESTACIONES[(e + 2) % 4 if sur else e]


class TiempoDelDia:
    """El tiempo de un día concreto según el clima de respaldo (determinista)."""

    nieve = False

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


class TiempoForzado:
    """Un tiempo fijo elegido a mano (--tiempo), para probar o hacer capturas."""

    TIPOS = ("despejado", "nublado", "lluvia", "tormenta", "nieve", "calima")
    terral = False

    def __init__(self, tipo, temperatura=None):
        self.tipo = tipo
        self.llueve = tipo in ("lluvia", "tormenta")
        self.tormenta = tipo == "tormenta"
        self.nieve = tipo == "nieve"
        self.calima = tipo == "calima"
        self.nubes = {"despejado": 0.05, "calima": 0.1}.get(tipo, 0.9)
        self.temp = temperatura if temperatura is not None else {"nieve": -1.0}.get(tipo, 15.0)
        self.sol = None

    def lluvia(self, minuto):
        return {"lluvia": 0.6, "tormenta": 0.9, "nieve": 0.6}.get(self.tipo, 0.0)

    def temperatura(self, minuto):
        return self.temp


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
