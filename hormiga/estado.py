"""El estado del hormiguero que tiene que sobrevivir a los reinicios (local/estado.json).

Sólo se escribe con el reloj de verdad (nunca en la demo, con --fecha, --hora, --dias o
--acelerar, al hacer capturas o medir, ni desde herramientas/) y se vuelve a leer en cada
arranque, para que reiniciar la Pi o el servicio no cambie nada:

- inicio: la fecha de fundación y la semilla, si config.toml no las dice (la fundación
  es el día del primer arranque y la semilla se elige al azar una sola vez).
- colores: el color de cada hormiga que no tiene uno fijo en su sala.
- hormigueros: lo de cada hormiguero, por su clave (fundación y semilla), para que una
  prueba con otra semilla o una errata en config.toml no toquen el de verdad:
  - posiciones: dónde estaba cada hormiga, para que siga en el mismo sitio.
  - obras: con [nido] cavar = "encendido", las obras sólo avanzan mientras el hormiguero
    está en marcha. Se guarda cuánto llevan cavando (en días) y qué día del hormiguero
    se terminó cada obra (para el diario). Una semana apagado, una semana sin obras.
"""

import datetime
import json
import os
import random
import time

GUARDAR_CADA = 60          # segundos
SALTO_MAXIMO = 300         # si el reloj salta más que esto (suspensión, cambio de hora...), no cuenta


def ruta(raiz):
    return os.path.join(raiz, "local", "estado.json")


def _tabla(v):
    return v if isinstance(v, dict) else {}


def _leer(r):
    try:
        with open(r) as f:
            return _tabla(json.load(f))
    except (OSError, ValueError):
        return {}


def _escribir(r, datos):
    try:
        os.makedirs(os.path.dirname(r), exist_ok=True)
        tmp = r + ".tmp"
        with open(tmp, "w") as f:
            json.dump(datos, f, ensure_ascii=False, indent=1)
        os.replace(tmp, r)
    except OSError:
        pass


def _hormigueros(datos):
    """Lo guardado de cada hormiguero, por su clave, del primero al último que se guardó
    (también el del formato antiguo: uno solo, con su "clave" en la raíz)."""
    hs = {k: v for k, v in _tabla(datos.get("hormigueros")).items() if isinstance(v, dict)}
    viejo = datos.get("clave")
    if isinstance(viejo, str) and viejo not in hs:
        hs[viejo] = {"obras": _tabla(datos.get("obras")), "posiciones": _tabla(datos.get("posiciones"))}
    return hs


def inicio(raiz, falta_fundacion, falta_semilla, guardar=True, hoy=None):
    """La fundación y la semilla del primer arranque. Las que faltan se crean (hoy y una al
    azar) y, con guardar (sólo con el reloj de verdad), se apuntan; si no, valen para esta vez."""
    r = ruta(raiz)
    datos = _leer(r)
    ini = dict(_tabla(datos.get("inicio")))
    cambio = False
    if falta_fundacion and "fundacion" not in ini:
        ini["fundacion"] = (hoy or datetime.date.today()).isoformat()
        cambio = True
    if falta_semilla and "semilla" not in ini:
        ini["semilla"] = random.randrange(1, 100000)
        cambio = True
    if cambio and guardar:
        datos["inicio"] = ini
        _escribir(r, datos)
    return ini.get("fundacion"), ini.get("semilla")


def de_verdad(raiz):
    """La fundación y la semilla del hormiguero de verdad, para cuando config.toml no se puede
    leer: las del primer arranque si están las dos (una prueba con --semilla 7 no las cambia)
    y, si no, las del último hormiguero que se guardó (o None)."""
    ini = _tabla(_leer(ruta(raiz)).get("inicio"))
    if "fundacion" in ini and "semilla" in ini:
        return ini["fundacion"], ini["semilla"]
    return ultimo(raiz)


def ultimo(raiz):
    """La fundación y la semilla del último hormiguero que se guardó, o None si no hay."""
    for clave, h in reversed(list(_hormigueros(_leer(ruta(raiz))).items())):
        if "fundacion" in h and "semilla" in h:
            return h["fundacion"], h["semilla"]
        if clave[10:11] == "-" and clave[11:]:   # formato antiguo: sólo la clave, "AAAA-MM-DD-semilla"
            s = clave[11:]
            return clave[:10], int(s) if s.lstrip("-").isdigit() else s
    return None


class Estado:
    def __init__(self, raiz, fundacion, semilla):
        """Lo guardado del hormiguero con esta fundación y esta semilla. Con otras el trazado es
        otro: tiene su propia entrada, que empieza de cero sin tocar las demás (los colores son
        de todos)."""
        self.ruta = ruta(raiz)
        datos = _leer(self.ruta)
        self.inicio = _tabla(datos.get("inicio"))
        self.colores = dict(_tabla(datos.get("colores")))
        self.fundacion, self.semilla = str(fundacion), semilla
        self.clave = "%s-%s" % (fundacion, semilla)
        mio = _hormigueros(datos).get(self.clave, {})
        obras = _tabla(mio.get("obras"))
        self.dias = float(obras.get("dias", 0.0))      # tiempo cavando, en días
        self.acabadas = dict(_tabla(obras.get("acabadas")))
        self.posiciones = dict(_tabla(mio.get("posiciones")))
        self._ultimo = None
        self._guardado = time.monotonic()

    def avanzar(self, ahora):
        """Suma a las obras el tiempo pasado desde la última vez (ahora: la hora de verdad)."""
        if self._ultimo is not None:
            seg = (ahora - self._ultimo).total_seconds()
            if 0 < seg <= SALTO_MAXIMO:
                self.dias += seg / 86400
        self._ultimo = ahora

    def acabar(self, obra, dia):
        """Apunta el día en que se terminó una obra (sólo la primera vez)."""
        if obra not in self.acabadas:
            self.acabadas[obra] = int(dia)
            return True
        return False

    def color(self, nombre, usados, paleta):
        """El color de siempre de esta hormiga; si es nueva, el menos usado de la paleta."""
        c = self.colores.get(nombre)
        if c is None:
            c = min(paleta, key=lambda p: (usados.count(p), paleta.index(p)))
            self.colores[nombre] = c
        return c

    def toca_guardar(self):
        return time.monotonic() - self._guardado > GUARDAR_CADA

    def guardar(self, hormigas=None):
        self._guardado = time.monotonic()
        if hormigas is not None:
            self.posiciones = {h.nombre: [h.x, h.y] for h in hormigas if not getattr(h, "esqueleto", False)}
        # se vuelve a leer, para no pisar lo que haya guardado otro hormiguero entretanto
        datos = _leer(self.ruta)
        hs = _hormigueros(datos)
        hs.pop(self.clave, None)   # el último que se guarda va al final
        hs[self.clave] = {"fundacion": self.fundacion, "semilla": self.semilla,
                          "obras": {"dias": self.dias, "acabadas": self.acabadas},
                          "posiciones": self.posiciones}
        colores = dict(_tabla(datos.get("colores")))
        colores.update(self.colores)
        _escribir(self.ruta, {"inicio": _tabla(datos.get("inicio")) or self.inicio, "colores": colores,
                              "hormigueros": hs})
