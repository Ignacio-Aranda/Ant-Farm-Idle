"""Tiempo real con OpenWeather (opcional).

Si hay clave, cada pocos minutos se pide el tiempo actual de la ciudad en un hilo
aparte (el hormiguero no se para nunca a esperar a internet). Lo último que llegó
se guarda en local/openweather.json, junto con un pequeño historial de cada día
(si llovió, si hubo tormenta...) para el diario y para saber si hay charcos.
Si no hay clave, no hay internet o los datos son viejos, se usa el clima de respaldo
de hormiga/tiempo.py.

La clave se busca, por orden, en la variable de entorno OPENWEATHER_API_KEY, en el
fichero local/openweather_clave.txt y en [tiempo] clave de config.toml.
"""

import datetime
import json
import os
import threading
import time
import urllib.parse
import urllib.request

URL = "https://api.openweathermap.org/data/2.5/weather"
VALIDO = 3 * 3600   # segundos que se fían de los últimos datos si no llegan nuevos


def _intensidad(codigo):
    """Intensidad de lluvia o nieve (0-1) según el código de OpenWeather."""
    if 200 <= codigo < 300:
        return 0.45 if codigo in (230, 231, 232) else 0.85
    if 300 <= codigo < 400:
        return 0.3
    if 500 <= codigo < 600:
        return {500: 0.45, 501: 0.7, 511: 0.6, 520: 0.5, 521: 0.7}.get(codigo, 1.0)
    if 600 <= codigo < 700:
        return {600: 0.4, 601: 0.7, 602: 1.0}.get(codigo, 0.6)
    return 0.0


def _minutos_locales(marca):
    t = datetime.datetime.fromtimestamp(marca)
    return t.hour * 60 + t.minute + t.second / 60


class TiempoReal:
    """El tiempo de ahora mismo, con la misma forma que tiempo.TiempoDelDia."""

    terral = False

    def __init__(self, datos):
        codigo = int(datos["weather"][0]["id"])
        self.codigo = codigo
        self.descripcion = datos["weather"][0].get("description", "")
        self.tormenta = 200 <= codigo < 300
        self.nieve = 600 <= codigo < 700
        self.llueve = 200 <= codigo < 600
        self.calima = codigo in (731, 751, 761)       # polvo o arena en suspensión
        self.niebla = codigo in (701, 741)
        self.nubes = max(0.0, min(1.0, datos.get("clouds", {}).get("all", 0) / 100))
        self.temp = float(datos["main"]["temp"])
        self._inten = _intensidad(codigo)
        s = datos.get("sys", {})
        self.sol = (_minutos_locales(s["sunrise"]), _minutos_locales(s["sunset"])) \
            if s.get("sunrise") and s.get("sunset") else None

    def lluvia(self, minuto):
        return self._inten if (self.llueve or self.nieve) else 0.0

    def temperatura(self, minuto):
        return self.temp


class OpenWeather:
    def __init__(self, clave, lat, lon, carpeta, cada_minutos=10):
        self.clave, self.lat, self.lon = clave, lat, lon
        self.cada = max(5, float(cada_minutos)) * 60
        self.ruta = os.path.join(carpeta, "openweather.json")
        self.cerrojo = threading.Lock()
        self.datos, self.hora = None, 0.0
        self.historial = {}          # "AAAA-MM-DD" -> {"llueve": ..., "tormenta": ..., ...}
        self.ultima_lluvia = None    # marca de tiempo de la última vez que llovía
        self.error = None
        self._leer()
        threading.Thread(target=self._bucle, daemon=True, name="openweather").start()

    # ---------------------------------------------------------------- disco

    def _leer(self):
        try:
            with open(self.ruta) as f:
                d = json.load(f)
            self.datos, self.hora = d.get("datos"), float(d.get("hora", 0))
            self.historial = d.get("historial", {})
            self.ultima_lluvia = d.get("ultima_lluvia")
        except (OSError, ValueError):
            pass

    def _guardar(self):
        try:
            os.makedirs(os.path.dirname(self.ruta), exist_ok=True)
            tmp = self.ruta + ".tmp"
            with open(tmp, "w") as f:
                json.dump({"datos": self.datos, "hora": self.hora, "historial": self.historial,
                           "ultima_lluvia": self.ultima_lluvia}, f)
            os.replace(tmp, self.ruta)
        except OSError:
            pass

    # ---------------------------------------------------------------- red

    def _bucle(self):
        while True:
            if time.time() - self.hora >= self.cada:
                self._pedir()
            time.sleep(30)

    def _pedir(self):
        url = URL + "?" + urllib.parse.urlencode({"lat": self.lat, "lon": self.lon, "appid": self.clave,
                                                   "units": "metric", "lang": "es"})
        try:
            with urllib.request.urlopen(url, timeout=15) as r:
                datos = json.load(r)
            real = TiempoReal(datos)
        except Exception as e:      # sin red, clave mala, respuesta rara...: se sigue con lo que había
            self.error = str(e)
            self.hora = time.time() - self.cada + 120   # reintenta en dos minutos
            return
        ahora = time.time()
        hoy = datetime.date.today().isoformat()
        with self.cerrojo:
            self.datos, self.hora, self.error = datos, ahora, None
            dia = self.historial.setdefault(hoy, {"llueve": False, "tormenta": False, "nieve": False,
                                                  "calima": False, "tmax": real.temp})
            for k in ("llueve", "tormenta", "nieve", "calima"):
                dia[k] = dia[k] or getattr(real, k)
            dia["tmax"] = max(dia.get("tmax", real.temp), real.temp)
            if real.llueve or real.nieve:
                self.ultima_lluvia = ahora
            # sólo se guardan los dos últimos años
            for vieja in sorted(self.historial)[:-730]:
                del self.historial[vieja]
            self._guardar()

    # ---------------------------------------------------------------- consultas

    def actual(self):
        """El tiempo de ahora, o None si no hay datos recientes."""
        with self.cerrojo:
            if self.datos is None or time.time() - self.hora > VALIDO:
                return None
            try:
                return TiempoReal(self.datos)
            except (KeyError, TypeError, ValueError):
                return None

    def llovio_hace(self, horas):
        return self.ultima_lluvia is not None and time.time() - self.ultima_lluvia < horas * 3600

    def dia(self, fecha):
        """Lo que se apuntó de ese día (o None si no se sabe)."""
        return self.historial.get(fecha.isoformat())


def desde_config(cfg, raiz):
    """Crea el cliente si hay clave y [tiempo] no dice lo contrario; si no, None."""
    t = cfg.get("tiempo", {})
    if str(t.get("fuente", "openweather")).lower() != "openweather":
        return None
    clave = os.environ.get("OPENWEATHER_API_KEY", "").strip()
    if not clave:
        try:
            with open(os.path.join(raiz, "local", "openweather_clave.txt")) as f:
                clave = f.read().strip()
        except OSError:
            clave = str(t.get("clave", "")).strip()
    if not clave:
        return None
    ciudad = cfg.get("ciudad", {})
    return OpenWeather(clave, ciudad.get("lat", 36.72), ciudad.get("lon", -4.42),
                       os.path.join(raiz, "local"), t.get("cada_minutos", 10))
