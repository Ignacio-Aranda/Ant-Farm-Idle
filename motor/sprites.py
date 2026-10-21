"""Sprites: de arte ASCII + máscara de color a tramos listos para pintar."""

import os
import sys

from . import colores

try:
    import tomllib
except ImportError:  # Python < 3.11
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

ESPEJO = str.maketrans("()[]{}<>/\\", ")(][}{><\\/")


def lineas(arte):
    """Normaliza un dibujo: lista de líneas sin líneas vacías al principio/final."""
    if isinstance(arte, (list, tuple)):
        ls = list(arte)
    else:
        ls = str(arte).replace("\t", "    ").split("\n")
    if len(ls) > 1 and not ls[0].strip():
        ls.pop(0)  # el salto de línea tras las comillas
    while ls and not ls[-1].strip():
        ls.pop()
    return [l.rstrip() for l in ls]


def mascara_lineas(mascara, n):
    """Como lineas() pero respetando las filas vacías (deben cuadrar con el arte)."""
    if not mascara:
        return [""] * n
    if isinstance(mascara, (list, tuple)):
        return (list(mascara) + [""] * n)[:max(n, len(mascara))]
    ls = str(mascara).split("\n")
    if ls and not ls[0].strip():
        ls.pop(0)
    while len(ls) > n and not ls[-1].strip():
        ls.pop()
    return ls + [""] * (n - len(ls))


def espejar(arte, mascara):
    """Da la vuelta a un dibujo. Las palabras (IRPF, nombres...) siguen leyéndose bien."""
    w = max((len(l) for l in arte), default=0)
    nuevo_a, nuevo_m = [], []
    for i, linea in enumerate(arte):
        m = mascara[i] if i < len(mascara) else ""
        ra = list(linea.ljust(w)[::-1].translate(ESPEJO))
        rm = list(m.ljust(w)[:w][::-1])
        j = 0
        while j < w:
            if ra[j].isalnum() or ra[j] == "%":
                k = j
                while k < w and (ra[k].isalnum() or ra[k] == "%"):
                    k += 1
                if k - j >= 2:
                    ra[j:k] = ra[j:k][::-1]
                    rm[j:k] = rm[j:k][::-1]
                j = k
            else:
                j += 1
        nuevo_a.append("".join(ra).rstrip())
        nuevo_m.append("".join(rm))
    return nuevo_a, nuevo_m


class Cuadro:
    """Un fotograma: lista de tramos (dy, dx, texto, Color)."""
    __slots__ = ("ancho", "alto", "tramos")

    def __init__(self, ancho, alto, tramos):
        self.ancho, self.alto, self.tramos = ancho, alto, tramos


def construir(arte, mascara=None, pintor=None, solido=True, defecto="blanco"):
    """arte: lista de líneas. Espacios a la izquierda/derecha y '?' son
    transparentes; los espacios interiores tapan lo de detrás si solido=True."""
    if pintor is None:
        c = colores.color(defecto)
        pintor = lambda _m: c  # noqa: E731
    if mascara is None:
        mascara = [""] * len(arte)
    tramos = []
    for dy, linea in enumerate(arte):
        m = mascara[dy] if dy < len(mascara) else ""
        ini = len(linea) - len(linea.lstrip(" "))
        fin = len(linea.rstrip(" "))
        buf, x0, actual = [], ini, None
        for x in range(ini, fin):
            ch = linea[x]
            if ch == "?" or (ch == " " and not solido):
                if buf and actual is not None:
                    tramos.append((dy, x0, "".join(buf), actual))
                buf, actual = [], None
                continue
            if ch == " ":
                if not buf:
                    x0 = x
                buf.append(ch)
                continue
            col = pintor(m[x] if x < len(m) else " ")
            if buf and actual is not None and col != actual:
                tramos.append((dy, x0, "".join(buf), actual))
                buf = []
            if not buf:
                x0 = x
            buf.append(ch)
            actual = col
        if buf and actual is not None:
            tramos.append((dy, x0, "".join(buf), actual))
    ancho = max((len(l) for l in arte), default=0)
    return Cuadro(ancho, len(arte), tramos)


def pintor_aleatorio(rng, paleta, defecto="blanco", ojo="W"):
    """Asigna un color al azar a cada dígito 1-9 de la máscara (4 = ojo)."""
    asign = {str(d): rng.choice(paleta) for d in range(1, 10)}
    asign["4"] = colores.color(ojo)
    base = colores.color(defecto)
    cache = {}

    def pintor(m):
        c = cache.get(m)
        if c is None:
            if m in asign:
                c = asign[m]
            elif m.strip() and m.lower() in colores.CODIGOS:
                c = colores.color(m)
            else:
                c = base
            cache[m] = c
        return c
    return pintor


def pintor_fijo(defecto="blanco", extra=None):
    """Máscara con códigos de letra; dígitos según 'extra' {dígito: color}."""
    base = colores.color(defecto)
    extra = {k: colores.color(v) for k, v in (extra or {}).items()}

    def pintor(m):
        if m in extra:
            return extra[m]
        if m.strip() and m.lower() in colores.CODIGOS:
            return colores.color(m)
        return base
    return pintor


class Plantilla:
    """Dibujo con sus dos direcciones (y varios fotogramas opcionales)."""

    def __init__(self, nombre, arte, mascara=None, mira="derecha",
                 arte_otro=None, mascara_otro=None, peso=1.0, grupo="",
                 solido=True, defecto="blanco"):
        self.nombre, self.peso, self.grupo = nombre, float(peso), grupo
        self.solido, self.defecto = solido, defecto
        varios = isinstance(arte, list) and arte and "\n" in str(arte[0])
        artes = arte if varios else [arte]
        masks = mascara if varios and isinstance(mascara, list) else [mascara] * len(artes)
        uno = []
        for a, m in zip(artes, masks):
            al = lineas(a)
            uno.append((al, mascara_lineas(m, len(al))))
        if arte_otro:
            ao = lineas(arte_otro)
            otro = [(ao, mascara_lineas(mascara_otro, len(ao)))]
        else:
            otro = [espejar(a, m) for a, m in uno]
        if mira == "izquierda":
            self.izq, self.der = uno, otro
        else:
            self.der, self.izq = uno, otro
        self.ancho = max(len(l) for a, _ in uno for l in a)
        self.alto = max(len(a) for a, _ in uno)

    def cuadros(self, derecha, pintor):
        fuente = self.der if derecha else self.izq
        return [construir(a, m, pintor, self.solido) for a, m in fuente]


def cargar_toml(ruta):
    if tomllib is None:
        raise RuntimeError("Hace falta Python 3.11+ (o el paquete tomli) para leer TOML")
    with open(ruta, "rb") as f:
        return tomllib.load(f)


def cargar_peces(carpeta, avisos=None):
    """Lee todos los [[pez]] de los .toml de la carpeta de sprites."""
    peces = []
    if not os.path.isdir(carpeta):
        return peces
    for nombre in sorted(os.listdir(carpeta)):
        if not nombre.endswith(".toml"):
            continue
        ruta = os.path.join(carpeta, nombre)
        try:
            datos = cargar_toml(ruta)
        except Exception as e:  # el acuario no debe morir por un sprite roto
            if avisos is not None:
                avisos.append("%s: %s" % (nombre, e))
            continue
        for d in datos.get("pez", []):
            if not d.get("activo", True):
                continue
            try:
                peces.append(Plantilla(
                    d.get("nombre", "pez"), d["arte"], d.get("mascara"),
                    d.get("mira", "derecha"), d.get("arte_otro"),
                    d.get("mascara_otro"), d.get("peso", 1),
                    d.get("grupo", os.path.splitext(nombre)[0]),
                    d.get("solido", True), d.get("color", "blanco")))
            except Exception as e:
                if avisos is not None:
                    avisos.append("%s (%s): %s" % (nombre, d.get("nombre"), e))
    return peces


if __name__ == "__main__":  # pequeña ayuda: ver los peces de un fichero
    for p in cargar_peces(sys.argv[1] if len(sys.argv) > 1 else "sprites"):
        print(p.nombre, p.grupo)
        for a, _ in (p.der[0], p.izq[0]):
            print("\n".join(a))
        print()
