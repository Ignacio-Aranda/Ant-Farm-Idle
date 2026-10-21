"""Fiestas y cumpleaños activos en una fecha."""

import datetime

from .tiempo import pascua


def _fecha(espec, anio):
    espec = str(espec).strip().lower()
    if espec.startswith("pascua"):
        resto = espec[6:].strip() or "+0"
        return pascua(anio) + datetime.timedelta(days=int(resto))
    dia, mes = espec.split("-")  # formato español: DD-MM
    return datetime.date(anio, int(mes), int(dia))


class Fiesta:
    def __init__(self, d):
        self.nombre = d.get("nombre", "Fiesta")
        self.desde = str(d.get("desde", "01-01"))
        self.hasta = str(d.get("hasta", self.desde))
        self.decoracion = d.get("decoracion", "banderines")
        self.gorro = d.get("gorro")
        self.mensaje = d.get("mensaje", self.nombre)
        self.lugar = d.get("lugar", "")

    def rango(self, anio):
        a = _fecha(self.desde, anio)
        b = _fecha(self.hasta, anio)
        if b < a:  # cruza el año
            b = _fecha(self.hasta, anio + 1)
        return a, b

    def activa(self, fecha):
        for anio in (fecha.year - 1, fecha.year):
            try:
                a, b = self.rango(anio)
            except ValueError:
                continue
            if a <= fecha <= b:
                return True
        return False

    def empieza(self, fecha):
        try:
            return self.rango(fecha.year)[0] == fecha
        except ValueError:
            return False

    def duracion(self):
        a, b = self.rango(2026)
        return (b - a).days


def cargar(datos):
    out = []
    for d in datos.get("fiesta", []):
        try:
            f = Fiesta(d)
            f.rango(2026)
            out.append(f)
        except Exception:  # una fecha mal escrita no tumba el hormiguero
            continue
    return out


def activas(fiestas, fecha):
    """Fiestas activas, de la más larga a la más corta (la más concreta manda)."""
    act = [f for f in fiestas if f.activa(fecha)]
    act.sort(key=lambda f: -f.duracion())
    return act


def dia_mes(texto):
    """"DD-MM" (formato español) -> (mes, dia). Acepta también "DD/MM"."""
    a, b = (int(v) for v in str(texto).replace("/", "-").split("-")[-2:])
    if a <= 31 and b <= 12:
        return b, a
    return a, b  # por si alguien lo puso al revés (MM-DD) y no hay duda


def es_cumple(persona, fecha):
    c = persona.get("cumple")
    if not c:
        return False
    try:
        mes, dia = dia_mes(c)
    except ValueError:
        return False
    if (mes, dia) == (2, 29) and fecha.month == 2 and fecha.day == 28:
        try:
            datetime.date(fecha.year, 2, 29)
        except ValueError:
            return True  # los del 29 de febrero lo celebran el 28 en años no bisiestos
    return (fecha.month, fecha.day) == (mes, dia)
