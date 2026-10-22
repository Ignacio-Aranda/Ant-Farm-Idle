"""Sprites hechos con caracteres y una máscara de color, como tramos (la simulación los usa
para saber cuánto ocupa cada cosa), y la lectura de los ficheros TOML."""

import re

from . import colores

try:
    import tomllib
except ImportError:  # Python < 3.11
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None


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


# Los errores de TOML más comunes, en español: (principio del mensaje de tomllib, explicación)
ERRORES_TOML = (
    ("Invalid value", "un valor mal escrito (¿falta una comilla, o son comillas curvas “ ”?)"),
    ("Cannot declare", "la sección %s está repetida (escríbela una sola vez)"),
    ("Cannot mutate immutable namespace", "la sección %s ya estaba escrita de otra forma más arriba"),
    ("Cannot overwrite a value", "una clave está repetida"),
    ("Illegal character '\\n'", "falta cerrar unas comillas"),
    ("Unclosed array", "falta cerrar una lista con «]»"),
    ("Unclosed inline table", "falta cerrar una tabla con «}»"),
    ("Expected newline or end of document after a statement",
     "sobra algo detrás del valor (¿faltan comillas, o es un número con coma? usa punto: 36.72)"),
    ("Expected ']' at the end of a table declaration", "falta el «]» de la sección"),
    ("Expected '=' after a key in a key/value pair", "falta el «=» detrás de la clave"),
    ("Unescaped '\\' in a string", "una «\\» dentro de comillas (escríbela doble, «\\\\»)"),
)


def explicar_error_toml(e):
    """El mensaje de un error de tomllib en español, con la línea en que está."""
    texto = str(e)
    m = re.match(r"(.*?)\s*\((?:at line (\d+), column \d+|at end of document)\)\s*$", texto, re.S)
    que, linea = (m.group(1), m.group(2)) if m else (texto, None)
    donde = "en la línea %s" % linea if linea else "al final del fichero"
    for principio, explicacion in ERRORES_TOML:
        if que.startswith(principio):
            if "%s" in explicacion:
                sec = re.search(r"\(([^)]*)\)", que)
                nombres = re.findall(r"'([^']*)'", sec.group(1)) if sec else []
                explicacion = explicacion % ("[%s]" % ".".join(nombres) if nombres else "")
            return "no se puede leer, %s: %s" % (donde, explicacion)
    return "no se puede leer, %s: %s" % (donde, que)


def cargar_toml(ruta):
    """Un fichero TOML. Vale también guardado «con BOM» o en ANSI (Latin-1), como los deja a
    veces el Bloc de notas de Windows. Si está mal escrito, ValueError con el error en español."""
    if tomllib is None:
        raise RuntimeError("Hace falta Python 3.11+ (o el paquete tomli) para leer TOML")
    with open(ruta, "rb") as f:
        datos = f.read()
    if datos.startswith(b"\xef\xbb\xbf"):
        datos = datos[3:]
    try:
        texto = datos.decode("utf-8")
    except UnicodeDecodeError:
        texto = datos.decode("cp1252", errors="replace")
    try:
        return tomllib.loads(texto)
    except tomllib.TOMLDecodeError as e:
        raise ValueError(explicar_error_toml(e)) from None
