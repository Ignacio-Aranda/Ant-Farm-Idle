"""Carga de la configuración y reloj (real o simulado)."""

import datetime
import math
import os
import time
import unicodedata

from motor.colores import es_color
from motor.sprites import cargar_toml

from . import estado as E
from . import fiestas as F
from . import tiempo as T
from .tierra import ANCHO_MIN, OBRAS, PISOS
from .tiempo import MALAGA

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

POR_DEFECTO = {
    "general": {"fundacion": "2026-01-01", "semilla": 2026},
}

FUNCIONES = ("trabajo", "reuniones", "despacho", "comedor", "agua", "despensa", "museo", "otra")
PAREDES = ("madera", "azulejo", "piedra")
SUELOS = ("madera", "baldosa", "tierra")
SECCIONES = ("general", "ciudad", "tiempo", "horario", "nido", "paisaje", "halloween")
# los números de config.toml: (sección, clave, valor por defecto, entero)
NUMEROS = (("general", "fps_pixel", 20, False), ("general", "texto_aumento", 0, True),
           ("ciudad", "lat", MALAGA[0], False), ("ciudad", "lon", MALAGA[1], False),
           ("tiempo", "cada_minutos", 10, False), ("nido", "entrada", 20, True),
           ("paisaje", "cementerio", 74, False))
DIAS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")


# ------------------------------------------------- lectura con aviso

def _numero(d, clave, defecto, avisos, donde, entero=True, sep=": "):
    """d[clave] como número (también "12" o "36,72"); si no lo es, aviso y el valor por defecto."""
    v = d.get(clave, defecto)
    try:
        if isinstance(v, bool):
            raise ValueError
        n = float(v.strip().replace(",", ".") if isinstance(v, str) else v)
        if not math.isfinite(n):
            raise ValueError
        return int(n) if entero else n
    except (TypeError, ValueError):
        avisos.append("%s%s%s debe ser un número (%s)"
                      % (donde, sep, clave, "no lo tengo en cuenta" if defecto is None else "puse %s" % defecto))
        return defecto


def _texto(d, clave, defecto, avisos, donde):
    """d[clave] como texto (un número también vale); si es otra cosa, aviso y el valor por defecto."""
    v = d.get(clave, defecto)
    if isinstance(v, (str, int, float)) and not isinstance(v, bool) and str(v).strip():
        return str(v).strip()
    avisos.append("%s: %s mal escrito (puse «%s»)" % (donde, clave, defecto))
    return defecto


def _tablas(d, clave, avisos, donde, campo=None):
    """Las [[clave]] de un fichero, como lista de tablas. Una [clave] suelta cuenta como una y,
    con campo, una lista de textos también vale (miembro = ["Ana", "Luis"] son dos nombres)."""
    v = d.get(clave, [])
    if not isinstance(v, list):
        v = [v]
    out = []
    for x in v:
        if isinstance(x, dict):
            out.append(x)
        elif campo and isinstance(x, str) and x.strip():
            out.append({campo: x.strip()})
        else:
            avisos.append("%s: %s mal escrito (%s), usa [[%s]]" % (donde, clave, x, clave))
    return out


def _dia(v):
    """Una fecha "AAAA-MM-DD" (o de TOML) como date, o None si está mal escrita."""
    if isinstance(v, datetime.datetime):
        return v.date()
    if isinstance(v, datetime.date):
        return v
    try:
        return datetime.date.fromisoformat(str(v).strip())
    except ValueError:
        return None


def _fundacion(v):
    """La fundación como date, o None si está mal escrita o es de un año sin sentido (con
    9999-12-31 no se podrían contar los días que vienen)."""
    d = _dia(v)
    return d if d and 1900 <= d.year <= 2999 else None


def _hora(v):
    """"HH:MM" (o una hora de TOML) -> (h, m), o None si está mal escrita o fuera de rango."""
    if isinstance(v, datetime.time):
        return v.hour, v.minute
    try:
        h, m = (int(x) for x in str(v).strip().split(":"))
    except ValueError:
        return None
    return (h, m) if 0 <= h <= 23 and 0 <= m <= 59 else None


def _llano(texto):
    """En minúsculas y sin tildes, para comparar nombres ("Diseño" y "diseno" son lo mismo)."""
    t = unicodedata.normalize("NFD", str(texto).strip().lower())
    return "".join(c for c in t if not unicodedata.combining(c))


# ------------------------------------------------------------- carga

def cargar_tipos(carpeta, avisos):
    """Los tipos de sala de tipos/*.toml: función, paredes, suelo y muebles."""
    tipos = {}
    if not os.path.isdir(carpeta):
        return tipos
    for nombre in sorted(os.listdir(carpeta)):
        if not nombre.endswith(".toml") or nombre.startswith("."):
            continue
        clave = os.path.splitext(nombre)[0].lower()
        donde = "tipos/" + nombre
        try:
            d = cargar_toml(os.path.join(carpeta, nombre))
        except Exception as e:
            avisos.append("%s: %s" % (donde, e))
            continue
        funcion = str(d.get("funcion", "otra")).lower()
        if funcion not in FUNCIONES:
            avisos.append("%s: función desconocida «%s»" % (donde, funcion))
            funcion = "otra"
        paredes = str(d.get("paredes", "madera")).strip().lower()
        if paredes not in PAREDES and not (paredes.startswith("#") and es_color(paredes)):
            avisos.append("%s: paredes «%s» no existe (madera, azulejo, piedra o \"#RRGGBB\"; puse madera)"
                          % (donde, d.get("paredes")))
            paredes = "madera"
        suelo = str(d.get("suelo", "madera")).strip().lower()
        if suelo not in SUELOS:
            avisos.append("%s: suelo «%s» no existe (madera, baldosa o tierra; puse madera)" % (donde, suelo))
            suelo = "madera"
        tipos[clave] = {"funcion": funcion, "paredes": paredes, "suelo": suelo, "fichero": donde,
                        "muebles": _tablas(d, "mueble", avisos, donde, "pieza")}
    return tipos


def _sala(d, nombre, tipos, avisos):
    """Una sala de salas/*.toml, con cada valor comprobado (los que están mal, con aviso)."""
    donde = "salas/" + nombre
    tipo = str(d.get("tipo", "trabajo")).lower()
    if tipo not in tipos:
        avisos.append("%s: no existe el tipo «%s» (en tipos/)" % (donde, tipo))
    color = d.get("color", "blanco")
    color = color.strip() if isinstance(color, str) else color
    if color and not es_color(color):
        avisos.append("%s: no existe el color «%s» (puse blanco)" % (donde, color))
        color = "blanco"
    clave_planta = "planta" if "planta" in d or "nivel" not in d else "nivel"
    planta = _numero(d, clave_planta, 2, avisos, donde)
    if not 1 <= planta <= len(PISOS) - 1:
        planta = max(1, min(len(PISOS) - 1, planta))
        avisos.append("%s: la planta va de 1 a %d (puse %d)" % (donde, len(PISOS) - 1, planta))
    ancho = _numero(d, "ancho", 32, avisos, donde)
    if ancho < ANCHO_MIN:
        avisos.append("%s: el ancho mínimo es %d (puse %d)" % (donde, ANCHO_MIN, ANCHO_MIN))
        ancho = ANCHO_MIN
    miembros = []
    for m in _tablas(d, "miembro", avisos, donde, "nombre"):
        m = dict(m)
        m["nombre"] = str(m.get("nombre", "")).strip()
        if not m["nombre"]:
            avisos.append("%s: hay un [[miembro]] sin nombre" % donde)
            continue
        if isinstance(m.get("color"), str):
            m["color"] = m["color"].strip()
        if m.get("color") and not es_color(m["color"]):
            avisos.append("%s: %s: no existe el color «%s»" % (donde, m["nombre"], m["color"]))
            del m["color"]
        if m.get("cumple"):
            try:
                F.dia_mes(m["cumple"])
            except ValueError:
                avisos.append("%s: %s: cumple mal escrito (%s), usa DD-MM" % (donde, m["nombre"], m["cumple"]))
                del m["cumple"]
        miembros.append(m)
    reuniones = []
    dias = {_llano(x): x for x in DIAS}
    for r in _tablas(d, "reunion", avisos, donde):
        que = "%s: reunión «%s»" % (donde, r.get("nombre", "Reunión"))
        hora = _hora(r.get("hora", "10:00"))
        dia = _llano(r.get("dia", "todos"))
        if hora is None:
            avisos.append("%s: hora mal escrita (%s), usa HH:MM, de 00:00 a 23:59" % (que, r.get("hora")))
        elif dia != "todos" and dia not in dias:
            avisos.append("%s: día mal escrito (%s), usa lunes, martes... o todos" % (que, r.get("dia")))
        else:
            reuniones.append(dict(r, hora="%02d:%02d" % hora, dia=dias.get(dia, dia),
                                  minutos=_numero(r, "minutos", 60, avisos, que, entero=False)))
    return {
        "clave": os.path.splitext(nombre)[0].lower(),
        "fichero": donde,
        "nombre": _texto(d, "nombre", os.path.splitext(nombre)[0], avisos, donde),
        "color": color,
        "planta": planta,
        "x": None if d.get("x") is None else _numero(d, "x", None, avisos, donde),
        "ancho": ancho,
        "tipo": tipo,
        "funcion": tipos.get(tipo, {}).get("funcion", "trabajo"),
        "reuniones": reuniones,
        "jefe": bool(d.get("jefe", False)),
        "miembros": miembros,
        "muebles": _tablas(d, "mueble", avisos, donde, "pieza"),
    }


def _repetidos(salas, idos, avisos):
    """Cada hormiga va por su nombre: si dos personas se llaman igual, la segunda lleva también
    el de su sala ("Ana (Diseño)"). Y avisa de quien está en una sala y en idos.toml sin fecha."""
    vistos = {}
    for s in salas:
        miembros = []
        for m in s["miembros"]:
            n = m["nombre"]
            if n.lower() in vistos:
                otro = "%s (%s)" % (n, s["nombre"])
                if otro.lower() in vistos:
                    avisos.append("%s: «%s» está repetido; sale una sola vez" % (s["fichero"], n))
                    continue
                donde = [vistos[n.lower()]] + ([s["fichero"]] if s["fichero"] != vistos[n.lower()] else [])
                avisos.append("hay dos «%s» (en %s): la segunda sale como «%s»"
                              % (n, " y en ".join(donde), otro))
                m = dict(m, nombre=otro)
            vistos[m["nombre"].lower()] = s["fichero"]
            miembros.append(m)
        s["miembros"] = miembros
    for d in idos:
        n = str(d["nombre"]).strip()
        if not d.get("fecha") and n.lower() in vistos:
            avisos.append("«%s» está en %s y en idos.toml sin fecha (ya se fue), así que no sale; "
                          "si son dos personas, cambia un nombre" % (n, vistos[n.lower()]))


def _convocadas(salas, avisos):
    """A quién convoca cada [[reunion]]: "todos", la clave de una sala (vale también su nombre:
    "diseno" o "Diseño") o una lista de nombres (vale uno suelto). Si no es nadie, se quita
    con un aviso (las que un día no convocan a nadie que esté, las avisa el hormiguero)."""
    sala_de = {_llano(s["nombre"]): s["clave"] for s in salas}
    sala_de.update({_llano(s["clave"]): s["clave"] for s in salas})
    gente = {_llano(m["nombre"]): m["nombre"] for s in salas for m in s["miembros"]}
    for s in salas:
        buenas = []
        for r in s["reuniones"]:
            quien = r.get("quien", "todos")
            if not isinstance(quien, list) and _llano(quien) == "todos":
                quien = "todos"
            elif not isinstance(quien, list) and _llano(quien) in sala_de:
                quien = sala_de[_llano(quien)]
            else:
                nombres = []
                if quien == []:
                    avisos.append("%s: reunión «%s»: quien está vacío, así que no convoca a nadie"
                                  % (s["fichero"], r.get("nombre", "Reunión")))
                for n in (quien if isinstance(quien, list) else [quien]):
                    if _llano(n) in gente:
                        nombres.append(gente[_llano(n)])
                    else:
                        avisos.append("%s: reunión «%s»: «%s» no es %snadie del hormiguero"
                                      % (s["fichero"], r.get("nombre", "Reunión"), n,
                                         "" if isinstance(quien, list) else "ninguna sala ni "))
                if not nombres:
                    continue
                quien = nombres
            buenas.append(dict(r, quien=quien))
        s["reuniones"] = buenas


def _revisar_config(cfg, avisos):
    """Los números de config.toml (también escritos como texto), las obras de [nido] y la zona horaria."""
    for seccion, clave, defecto, entero in NUMEROS:
        s = cfg.get(seccion, {})
        if clave in s:
            s[clave] = _numero(s, clave, defecto, avisos, "config: [%s]" % seccion, entero, " ")
    nido = cfg.get("nido", {})
    if "obras" in nido and not isinstance(nido["obras"], list):
        avisos.append("config: [nido] obras debe ser una lista, p. ej. [\"despensa\", \"museo\"] "
                      "(puse las de siempre)")
        del nido["obras"]
    if "obras" in nido:
        obras = [str(n).strip() for n in nido["obras"] if isinstance(n, str) and n.strip()]
        if len(obras) < len(nido["obras"]):
            avisos.append("config: [nido] obras: cada obra es un nombre entre comillas")
        nido["obras"] = obras
    claves = [n.lower() for n in nido["obras"]] if "obras" in nido else [o["clave"] for o in OBRAS]
    for n in claves:
        if n not in cfg["tipos"]:
            avisos.append("config: [nido] la obra «%s» no tiene tipo en tipos/ (será una sala vacía)" % n)
    ciudad = cfg.get("ciudad", {})
    zona = str(ciudad.pop("zona_horaria", "")).strip()
    if zona and T.zona_horaria(zona) is None:
        avisos.append("config: [ciudad] zona_horaria «%s» no existe (p. ej. \"Europe/Madrid\"; "
                      "uso la del ordenador)" % zona)
    elif zona:
        ciudad["zona_horaria"] = zona


def guarda_estado(args):
    """¿Se escribe en local/ (fundación, semilla, lo excavado...)? Sólo con el reloj de verdad:
    nunca en la demo, con --fecha, --hora, --dias o --acelerar, al hacer capturas o medir, ni
    desde herramientas/ (que ponen args.sin_estado)."""
    return not (getattr(args, "sin_estado", False) or args.demo or args.fecha or args.hora
                or args.dias is not None or args.acelerar != 1.0
                or getattr(args, "captura", None) or getattr(args, "medir", False))


def cargar(args, avisos):
    """config.toml, tipos/, salas/, idos.toml y calendario.toml. Lo que está mal no tumba el
    hormiguero: se avisa (en la franja amarilla) y se usa el valor por defecto."""
    fallo = False   # config.toml no se ha podido leer: no se sabe si traía fundación y semilla
    for opcion, ruta, defecto in (("-c", args.config, "config.toml"), ("--salas", args.salas, "salas"),
                                  ("--tipos", args.tipos, "tipos"), ("--idos", args.idos, "idos.toml"),
                                  ("--calendario", args.calendario, "calendario.toml")):
        if not os.path.exists(ruta) and os.path.abspath(ruta) != os.path.join(RAIZ, defecto):
            avisos.append("%s: no encuentro %s" % (opcion, ruta))
            fallo = fallo or opcion == "-c"
    cfg = {k: dict(v) for k, v in POR_DEFECTO.items()}
    general_usuario = {}
    if os.path.exists(args.config):
        try:
            usuario = cargar_toml(args.config)
            general_usuario = usuario.get("general", {})
            for k, v in usuario.items():
                if isinstance(v, dict):
                    cfg.setdefault(k, {}).update(v)
                elif k in SECCIONES:
                    avisos.append("config: %s tiene que ser una sección, [%s]" % (k, k))
                else:
                    cfg[k] = v
        except Exception as e:
            avisos.append("config: %s" % e)
            fallo = True
    if not isinstance(general_usuario, dict):
        general_usuario, fallo = {}, True
    # sin fundación o sin semilla en config.toml: las del primer arranque (local/estado.json),
    # que sólo se apuntan con el reloj de verdad. Si config.toml no se ha podido leer, las del
    # hormiguero de verdad (las del primer arranque o, si no las hay, las del último que se
    # guardó): una errata no cambia de hormiguero
    falta_f, falta_s = "fundacion" not in general_usuario, "semilla" not in general_usuario
    mal_f = not falta_f and _fundacion(general_usuario["fundacion"]) is None
    if mal_f:   # se usa la del primer arranque si la hay (sin crearla), o la de por defecto
        avisos.append("config: fundacion mal escrita (%s), usa AAAA-MM-DD (de 1900 a 2999)"
                      % general_usuario["fundacion"])
    if falta_f or falta_s or mal_f:
        hoy = T.ahora(cfg.get("ciudad", {}).get("zona_horaria")).date()
        previo = E.de_verdad(RAIZ) if fallo else None
        fundacion, semilla = previo or E.inicio(RAIZ, falta_f, falta_s, guarda_estado(args) and not fallo, hoy)
        if (falta_f or mal_f) and fundacion:
            cfg["general"]["fundacion"] = fundacion
        if falta_s and semilla is not None:
            cfg["general"]["semilla"] = semilla
    fundacion = _fundacion(cfg["general"]["fundacion"]) or _dia(POR_DEFECTO["general"]["fundacion"])
    cfg["general"]["fundacion"] = fundacion.isoformat()
    tipos = cargar_tipos(args.tipos, avisos)
    cfg["tipos"] = tipos
    cfg["raiz"] = RAIZ
    _revisar_config(cfg, avisos)
    salas = []
    if os.path.isdir(args.salas):
        for nombre in sorted(os.listdir(args.salas)):
            if not nombre.endswith(".toml") or nombre.startswith("."):
                continue
            try:
                d = cargar_toml(os.path.join(args.salas, nombre))
            except Exception as e:
                avisos.append("salas/%s: %s" % (nombre, e))
                continue
            salas.append(_sala(d, nombre, tipos, avisos))
    idos = []
    if os.path.exists(args.idos):
        try:
            datos = cargar_toml(args.idos)
        except Exception as e:
            avisos.append("idos.toml: %s" % e)
        else:
            for d in _tablas(datos, "ido", avisos, "idos.toml", "nombre"):
                if str(d.get("nombre", "")).strip():
                    idos.append(dict(d, nombre=str(d["nombre"]).strip()))
    _repetidos(salas, idos, avisos)
    _convocadas(salas, avisos)
    fiestas = []
    if os.path.exists(args.calendario):
        try:
            fiestas = F.cargar(cargar_toml(args.calendario), avisos)
        except Exception as e:
            avisos.append("calendario: %s" % e)
    return cfg, salas, idos, fiestas


def firma(args):
    """Fecha de modificación de los ficheros de gente (para recargar al guardar)."""
    rutas = [args.idos, args.config, args.calendario]
    if os.path.isdir(args.salas):   # sólo los .toml (no los .swp ni los ocultos de los editores)
        rutas += [os.path.join(args.salas, n) for n in sorted(os.listdir(args.salas))
                  if n.endswith(".toml") and not n.startswith(".")]
    out = []
    for r in rutas:
        try:
            out.append((r, os.path.getmtime(r)))
        except OSError:
            pass
    return tuple(out)


class RelojDemo:
    """El tiempo vuela, pero se para unos segundos en las fechas importantes."""

    def __init__(self, inicio, seg_dia, importantes, pausa):
        self.sim = inicio
        self.factor = 86400.0 / max(0.2, seg_dia)
        self.importantes = importantes
        self.pausa = pausa
        self.ultimo = time.monotonic()
        self.pausa_hasta = 0.0
        self.vistos = set()
        self.texto = None
        self._comprobar(inicio.date(), time.monotonic())

    def _comprobar(self, dia, ahora):
        if dia in self.importantes and dia not in self.vistos:
            self.vistos.add(dia)
            self.sim = datetime.datetime.combine(dia, datetime.time(12, 0))
            self.pausa_hasta = ahora + self.pausa
            self.texto = self.importantes[dia]
            return True
        return False

    def en_pausa(self):
        return time.monotonic() < self.pausa_hasta

    def __call__(self):
        ahora = time.monotonic()
        dt = ahora - self.ultimo
        self.ultimo = ahora
        if ahora < self.pausa_hasta:
            return self.sim
        nuevo = self.sim + datetime.timedelta(seconds=dt * self.factor)
        dia = self.sim.date()
        while dia < nuevo.date():
            dia += datetime.timedelta(days=1)
            if self._comprobar(dia, ahora):
                return self.sim
        self.sim = nuevo
        return self.sim


def fechas_importantes(inicio, fiestas, salas, idos, dias=400):
    out = {}
    # cuándo se va cada uno (sin fecha, o mal escrita: ya se fue)
    bajas = [(str(i["nombre"]).lower(), _dia(i.get("fecha")) or inicio) for i in idos]
    for k in range(dias):
        d = inicio + datetime.timedelta(days=k)
        cosas = [f.nombre for f in fiestas if f.empieza(d)]
        # cumpleaños sólo de quien ese día está en el hormiguero (ya ha llegado y no se ha ido)
        idos_ya = {n for n, f in bajas if f <= d}
        cumples = [m["nombre"] for s in salas for m in s.get("miembros", [])
                   if F.es_cumple(m, d) and (_dia(m.get("alta")) or d) <= d
                   and m["nombre"].lower() not in idos_ya]
        if cumples:
            cosas.append("Cumpleaños de " + ", ".join(cumples[:6]) + ("..." if len(cumples) > 6 else ""))
        for i in idos:
            if str(i.get("fecha", "")) == d.isoformat():
                cosas.append("Se va " + i["nombre"])
        if cosas:
            out[d] = " · ".join(cosas)
    return out


def crear_reloj(args, cfg, fiestas=None, salas=None, idos=None):
    """La hora del hormiguero: la de verdad (en la zona horaria de la ciudad, si se da) o una
    simulada (--demo, --fecha, --hora, --dias, --acelerar)."""
    zona = cfg.get("ciudad", {}).get("zona_horaria")
    if args.demo:
        inicio = datetime.date.fromisoformat(str(cfg["general"]["fundacion"]))
        if args.fecha:
            inicio = datetime.date.fromisoformat(args.fecha)
        imp = fechas_importantes(inicio, fiestas or [], salas or [], idos or [])
        return RelojDemo(datetime.datetime.combine(inicio, datetime.time(9, 0)),
                         args.seg_dia, imp, args.pausa)
    inicio = None
    if args.dias is not None:
        f = datetime.date.fromisoformat(str(cfg["general"]["fundacion"]))
        inicio = datetime.datetime.combine(f, datetime.time(12)) + datetime.timedelta(days=args.dias)
    if args.fecha:
        inicio = datetime.datetime.combine(datetime.date.fromisoformat(args.fecha),
                                           (inicio or T.ahora(zona)).time())
    if args.hora:
        h, m = (int(v) for v in args.hora.split(":"))
        inicio = (inicio or T.ahora(zona)).replace(hour=h, minute=m, second=0)
    factor = args.acelerar
    if inicio is None and factor == 1.0:
        def ahora():
            return T.ahora(zona)
        ahora.real = guarda_estado(args)   # la hora de verdad: el estado se guarda y las obras cuentan
        return ahora
    base = inicio or T.ahora(zona)
    t0 = time.monotonic()
    return lambda: base + datetime.timedelta(seconds=(time.monotonic() - t0) * factor)
