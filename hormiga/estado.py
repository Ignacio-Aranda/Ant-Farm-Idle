"""El estado del hormiguero que tiene que sobrevivir a los reinicios (local/estado.json).

Se crea la primera vez que arranca con el reloj de verdad y se vuelve a leer en cada
arranque, para que reiniciar la Pi o el servicio no cambie nada:

- inicio: la fecha de fundación y la semilla, si config.toml no las dice (la fundación
  es el día del primer arranque y la semilla se elige al azar una sola vez).
- colores: el color de cada hormiga que no tiene uno fijo en su sala.
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


def _leer(r):
    try:
        with open(r) as f:
            return json.load(f)
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


def inicio(raiz, falta_fundacion, falta_semilla):
    """La fundación y la semilla del primer arranque (las crea y las guarda si no están)."""
    r = ruta(raiz)
    datos = _leer(r)
    ini = datos.setdefault("inicio", {})
    cambio = False
    if falta_fundacion and "fundacion" not in ini:
        ini["fundacion"] = datetime.date.today().isoformat()
        cambio = True
    if falta_semilla and "semilla" not in ini:
        ini["semilla"] = random.randrange(1, 100000)
        cambio = True
    if cambio:
        _escribir(r, datos)
    return ini.get("fundacion"), ini.get("semilla")


class Estado:
    def __init__(self, raiz, clave):
        """clave: fundación y semilla. Si cambian, el trazado es otro y lo excavado y las
        posiciones empiezan de cero (los colores se conservan)."""
        self.ruta = ruta(raiz)
        datos = _leer(self.ruta)
        self.inicio = datos.get("inicio", {})
        self.colores = dict(datos.get("colores", {}))
        mismo = datos.get("clave") == clave
        self.clave = clave
        obras = datos.get("obras", {}) if mismo else {}
        self.dias = float(obras.get("dias", 0.0))      # tiempo cavando, en días
        self.acabadas = dict(obras.get("acabadas", {}))
        self.posiciones = dict(datos.get("posiciones", {})) if mismo else {}
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
        _escribir(self.ruta, {"inicio": self.inicio, "clave": self.clave, "colores": self.colores,
                              "posiciones": self.posiciones,
                              "obras": {"dias": self.dias, "acabadas": self.acabadas}})
