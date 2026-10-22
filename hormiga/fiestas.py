"""Fiestas y cumpleaños activos en una fecha."""

import datetime

from .tiempo import pascua

# Las que sabe pintar el hormiguero (calendario.toml las explica)
DECORACIONES = ("navidad", "nochevieja", "reyes", "halloween", "difuntos", "andalucia", "espana",
                "semana_santa", "feria", "carnaval", "san_juan", "cruces", "corazones", "libro", "pi",
                "banderines")
GORROS = ("fiesta", "papa_noel", "corona", "capirote", "bruja", "flor", "antifaz")


def _fecha(espec, anio):
    """La fecha de una fiesta ("DD-MM" o "pascua+N") en ese año. Si está mal escrita, también
    con números enormes, ValueError."""
    espec = str(espec).strip().lower().replace(" ", "")
    try:
        if espec.startswith("pascua"):
            resto = espec[6:] or "+0"
            return pascua(anio) + datetime.timedelta(days=int(resto))
        dia, mes = espec.replace("/", "-").split("-")  # formato español: DD-MM (o DD/MM)
        return datetime.date(anio, int(mes), int(dia))
    except OverflowError:
        raise ValueError("fecha fuera de rango: %s" % espec) from None


class Fiesta:
    def __init__(self, d):
        self.nombre = str(d.get("nombre", "Fiesta"))
        self.desde = str(d.get("desde", "01-01"))
        self.hasta = str(d.get("hasta", self.desde))
        self.decoracion = str(d.get("decoracion", "banderines")).strip().lower()
        self.gorro = str(d["gorro"]).strip().lower() if d.get("gorro") else None
        self.mensaje = str(d.get("mensaje", self.nombre))
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
        a, b = self.rango(2028)   # un año bisiesto: así también vale el 29-02
        return (b - a).days


def cargar(datos, avisos=None):
    """Las [[fiesta]] de calendario.toml. Las que están mal escritas se quitan, con un aviso."""
    avisos = [] if avisos is None else avisos
    lista = datos.get("fiesta", [])
    if isinstance(lista, dict):   # [fiesta] en vez de [[fiesta]]: sólo cabe una
        avisos.append("calendario: escribe [[fiesta]], con dos corchetes (con [fiesta] sólo cabe una)")
        lista = [lista]
    out = []
    for d in lista if isinstance(lista, list) else [lista]:
        if not isinstance(d, dict):
            avisos.append("calendario: fiesta mal escrita (%s), usa [[fiesta]]" % d)
            continue
        f = Fiesta(d)
        mal = []
        for espec in dict.fromkeys((f.desde, f.hasta)):
            try:
                _fecha(espec, 2028)
            except ValueError:   # una fecha mal escrita no tumba el hormiguero
                mal.append(espec)
        if mal:
            avisos.append("calendario: «%s»: fecha mal escrita (%s), usa DD-MM o pascua+N"
                          % (f.nombre, ", ".join(mal)))
            continue
        if f.decoracion not in DECORACIONES:
            avisos.append("calendario: «%s»: no existe la decoración «%s»" % (f.nombre, f.decoracion))
        if f.gorro and f.gorro not in GORROS:
            avisos.append("calendario: «%s»: no existe el gorro «%s»" % (f.nombre, f.gorro))
        out.append(f)
    return out


def activas(fiestas, fecha):
    """Fiestas activas, de la más larga a la más corta (la más concreta manda)."""
    act = [f for f in fiestas if f.activa(fecha)]
    act.sort(key=lambda f: -f.duracion())
    return act


def dia_mes(texto):
    """"DD-MM" (formato español) -> (mes, dia). Acepta también "DD/MM", "DD-MM-AAAA" y
    "AAAA-MM-DD". Si no es una fecha que exista (también con números enormes), ValueError."""
    p = [int(v) for v in str(texto).strip().replace("/", "-").split("-")]
    if len(p) == 3:
        p = [p[2], p[1]] if p[0] > 31 else p[:2]   # AAAA-MM-DD o DD-MM-AAAA
    a, b = p
    mes, dia = (b, a) if a <= 31 and b <= 12 else (a, b)  # por si alguien lo puso al revés (MM-DD)
    if not (1 <= mes <= 12 and 1 <= dia <= 31):
        raise ValueError("no existe el día %s" % texto)
    datetime.date(2028, mes, dia)   # que exista (2028 es bisiesto: vale el 29-02)
    return mes, dia


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
