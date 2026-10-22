"""Tiempo real con OpenWeather (opcional).

Si hay clave, cada pocos minutos se pide el tiempo actual de la ciudad en un hilo
aparte (el hormiguero no se para nunca a esperar a internet). Lo último que llegó
se guarda en local/openweather.json, junto con un pequeño historial de cada día
(si llovió, si hubo tormenta...) para el diario y para saber si hay charcos.
Si no hay clave, no hay internet o los datos son viejos, se usa el clima de respaldo
de hormiga/tiempo.py.

La clave se busca, por orden, en la variable de entorno OPENWEATHER_API_KEY, en el
fichero local/openweather_clave.txt y en [tiempo] clave de config.toml. El servicio de la
Pi no ve las variables de la sesión: allí, el fichero (o OPENWEATHER_API_KEY=... en local/entorno).
"""

import datetime
import json
import math
import os
import threading
import time
import urllib.parse
import urllib.request

from . import tiempo as T

URL = "https://api.openweathermap.org/data/2.5/weather"
VALIDO = 3 * 3600   # segundos que se fían de los últimos datos si no llegan nuevos
FALLOS_AVISO = 3    # peticiones seguidas rechazadas por la clave antes de avisar


def _marca(v):
    """Una marca de tiempo guardada, o None si no lo es o es del futuro (se guardó con el reloj
    adelantado: si no, se fiaría de esos datos, o no pediría otros, hasta esa fecha)."""
    if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) \
            and 0 < v <= time.time() + 60:
        return float(v)
    return None


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


def _minutos_locales(marca, zona=None):
    """Minutos desde medianoche, en la zona horaria de la ciudad si se da (si no, la del ordenador)."""
    t = datetime.datetime.fromtimestamp(marca, T.zona_horaria(zona))
    return t.hour * 60 + t.minute + t.second / 60


class TiempoReal:
    """El tiempo de ahora mismo, con la misma forma que tiempo.TiempoDelDia."""

    terral = False

    def __init__(self, datos, zona=None):
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
        self.sol = (_minutos_locales(s["sunrise"], zona), _minutos_locales(s["sunset"], zona)) \
            if s.get("sunrise") and s.get("sunset") else None

    def lluvia(self, minuto):
        return self._inten if (self.llueve or self.nieve) else 0.0

    def temperatura(self, minuto):
        return self.temp


class OpenWeather:
    def __init__(self, clave, lat, lon, carpeta, cada_minutos=10, zona=None):
        self.clave, self.lat, self.lon, self.zona = clave, lat, lon, zona
        self.cada = max(5, float(cada_minutos)) * 60
        self.ruta = os.path.join(carpeta, "openweather.json")
        self.cerrojo = threading.Lock()
        self.datos, self.hora = None, 0.0   # los últimos datos buenos y cuándo llegaron
        self.historial = {}          # "AAAA-MM-DD" -> {"llueve": ..., "tormenta": ..., ...}
        self.ultima_lluvia = None    # marca de tiempo de la última vez que llovía
        self.ultima_nieve = None
        self.error = None
        self.fallos = 0              # peticiones seguidas que ha rechazado OpenWeather (clave mala...)
        self._leer()
        self.proximo = self.hora + self.cada   # cuándo toca pedirlos otra vez
        threading.Thread(target=self._bucle, daemon=True, name="openweather").start()

    # ---------------------------------------------------------------- disco

    def _leer(self):
        """Lo guardado en openweather.json. Lo que no tiene la forma de siempre (el fichero editado
        a mano o dañado) es como si no estuviera."""
        try:
            with open(self.ruta, encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, ValueError):
            return
        if not isinstance(d, dict):
            return
        hora = _marca(d.get("hora"))
        if isinstance(d.get("datos"), dict) and hora is not None:
            self.datos, self.hora = d["datos"], hora
        historial = d.get("historial")
        if isinstance(historial, dict):
            self.historial = {k: v for k, v in historial.items() if isinstance(v, dict)}
        self.ultima_lluvia = _marca(d.get("ultima_lluvia"))
        self.ultima_nieve = _marca(d.get("ultima_nieve"))

    def _guardar(self):
        try:
            os.makedirs(os.path.dirname(self.ruta), exist_ok=True)
            tmp = self.ruta + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"datos": self.datos, "hora": self.hora, "historial": self.historial,
                           "ultima_lluvia": self.ultima_lluvia, "ultima_nieve": self.ultima_nieve}, f)
            os.replace(tmp, self.ruta)
        except OSError:
            pass

    # ---------------------------------------------------------------- red

    def _bucle(self):
        while True:
            ahora = time.time()
            # si el reloj ha ido hacia atrás, el próximo quedaría muy lejos: toca ya
            if ahora >= self.proximo or self.proximo - ahora > max(self.cada, 120) + 60:
                self._pedir()
            time.sleep(30)

    def _pedir(self):
        url = URL + "?" + urllib.parse.urlencode({"lat": self.lat, "lon": self.lon, "appid": self.clave,
                                                   "units": "metric", "lang": "es"})
        try:
            with urllib.request.urlopen(url, timeout=15) as r:
                datos = json.load(r)
            real = TiempoReal(datos, self.zona)
        except Exception as e:      # sin red, clave mala, respuesta rara...: se sigue con lo que había
            self.error = str(e)
            # la clave mal copiada o aún sin activar (401) o una petición que no vale: se avisa
            codigo = getattr(e, "code", None)
            self.fallos = self.fallos + 1 if codigo in (400, 401, 403, 404) else 0
            # reintenta en dos minutos; los datos de antes conservan su hora (y caducan a su tiempo)
            self.proximo = time.time() + 120
            return
        ahora = time.time()
        self.proximo = ahora + self.cada
        hoy = T.ahora(self.zona).date().isoformat()
        with self.cerrojo:
            self.datos, self.hora, self.error, self.fallos = datos, ahora, None, 0
            dia = self.historial.setdefault(hoy, {"llueve": False, "tormenta": False, "nieve": False,
                                                  "calima": False, "tmax": real.temp})
            for k in ("llueve", "tormenta", "nieve", "calima"):
                dia[k] = bool(dia.get(k)) or getattr(real, k)
            tmax = dia.get("tmax")
            dia["tmax"] = max(tmax, real.temp) if isinstance(tmax, (int, float)) else real.temp
            if real.llueve or real.nieve:
                self.ultima_lluvia = ahora
            if real.nieve:
                self.ultima_nieve = ahora
            # sólo se guardan los dos últimos años
            for vieja in sorted(self.historial)[:-730]:
                del self.historial[vieja]
            self._guardar()

    # ---------------------------------------------------------------- consultas

    def actual(self):
        """El tiempo de ahora, o None si no hay datos recientes."""
        with self.cerrojo:
            if self.datos is None or not 0 <= time.time() - self.hora <= VALIDO:
                return None
            try:
                return TiempoReal(self.datos, self.zona)
            except (KeyError, TypeError, ValueError, IndexError, AttributeError):   # datos con otra forma
                return None

    def llovio_hace(self, horas):
        return self.ultima_lluvia is not None and time.time() - self.ultima_lluvia < horas * 3600

    def nevo_hace(self, horas):
        return self.ultima_nieve is not None and time.time() - self.ultima_nieve < horas * 3600

    def dia(self, fecha):
        """Lo que se apuntó de ese día (o None si no se sabe)."""
        return self.historial.get(fecha.isoformat())

    def aviso(self):
        """Un aviso si OpenWeather lleva varias peticiones seguidas rechazando la clave (o None)."""
        if self.fallos < FALLOS_AVISO:
            return None
        return ("tiempo: OpenWeather no acepta la clave (%s): mira que esté bien copiada (las nuevas "
                "tardan unas horas en funcionar); mientras, uso el tiempo estadístico" % self.error)


def desde_config(cfg, raiz):
    """Crea el cliente si hay clave y [tiempo] no dice lo contrario; si no, None."""
    t = cfg.get("tiempo", {})
    if str(t.get("fuente", "openweather")).lower() != "openweather":
        return None
    clave = os.environ.get("OPENWEATHER_API_KEY", "").strip()
    if not clave:
        try:   # utf-8-sig: también si el Bloc de notas la guardó «con BOM»
            with open(os.path.join(raiz, "local", "openweather_clave.txt"), encoding="utf-8-sig") as f:
                clave = f.read().strip()
        except (OSError, ValueError):
            clave = ""
    if not clave:   # ni en el entorno ni en el fichero (o está vacío): la de config.toml
        clave = str(t.get("clave", "")).strip()
    if not clave:
        return None
    ciudad = cfg.get("ciudad", {})
    return OpenWeather(clave, ciudad.get("lat", 36.72), ciudad.get("lon", -4.42),
                       os.path.join(raiz, "local"), t.get("cada_minutos", 10), ciudad.get("zona_horaria"))
