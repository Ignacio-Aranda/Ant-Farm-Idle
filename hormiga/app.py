"""Carga de la configuración y reloj (real o simulado)."""

import datetime
import os
import time

from motor.sprites import cargar_toml

from . import estado as E
from . import fiestas as F

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

POR_DEFECTO = {
    "general": {"fundacion": "2026-01-01", "semilla": 2026},
}

FUNCIONES = ("trabajo", "reuniones", "despacho", "comedor", "agua", "despensa", "museo", "otra")


def cargar_tipos(carpeta, avisos):
    """Los tipos de sala de tipos/*.toml: función, paredes, suelo y muebles."""
    tipos = {}
    if not os.path.isdir(carpeta):
        return tipos
    for nombre in sorted(os.listdir(carpeta)):
        if not nombre.endswith(".toml"):
            continue
        clave = os.path.splitext(nombre)[0].lower()
        try:
            d = cargar_toml(os.path.join(carpeta, nombre))
        except Exception as e:
            avisos.append("tipos/%s: %s" % (nombre, e))
            continue
        funcion = str(d.get("funcion", "otra")).lower()
        if funcion not in FUNCIONES:
            avisos.append("tipos/%s: función desconocida «%s»" % (nombre, funcion))
            funcion = "otra"
        tipos[clave] = {"funcion": funcion, "paredes": d.get("paredes", "madera"),
                        "suelo": d.get("suelo", "madera"), "muebles": list(d.get("mueble", []))}
    return tipos


def cargar(args, avisos):
    cfg = {k: dict(v) for k, v in POR_DEFECTO.items()}
    general_usuario = {}
    if os.path.exists(args.config):
        try:
            usuario = cargar_toml(args.config)
            general_usuario = usuario.get("general", {})
            for k, v in usuario.items():
                if isinstance(v, dict):
                    cfg.setdefault(k, {}).update(v)
                else:
                    cfg[k] = v
        except Exception as e:
            avisos.append("config: %s" % e)
    # sin fundación o sin semilla en config.toml: las del primer arranque (local/estado.json)
    falta_f, falta_s = "fundacion" not in general_usuario, "semilla" not in general_usuario
    if falta_f or falta_s:
        fundacion, semilla = E.inicio(RAIZ, falta_f, falta_s)
        if falta_f and fundacion:
            cfg["general"]["fundacion"] = fundacion
        if falta_s and semilla:
            cfg["general"]["semilla"] = semilla
    tipos = cargar_tipos(args.tipos, avisos)
    cfg["tipos"] = tipos
    cfg["raiz"] = RAIZ
    salas = []
    if os.path.isdir(args.salas):
        for nombre in sorted(os.listdir(args.salas)):
            if not nombre.endswith(".toml"):
                continue
            try:
                d = cargar_toml(os.path.join(args.salas, nombre))
            except Exception as e:
                avisos.append("%s: %s" % (nombre, e))
                continue
            tipo = str(d.get("tipo", "trabajo")).lower()
            if tipo not in tipos:
                avisos.append("%s: no existe el tipo «%s» (en tipos/)" % (nombre, tipo))
            salas.append({
                "clave": os.path.splitext(nombre)[0].lower(),
                "nombre": d.get("nombre", os.path.splitext(nombre)[0]),
                "color": d.get("color", "blanco"),
                "planta": d.get("planta", d.get("nivel", 2)),
                "x": d.get("x"),
                "ancho": d.get("ancho", 32),
                "tipo": tipo,
                "funcion": tipos.get(tipo, {}).get("funcion", "trabajo"),
                "reuniones": d.get("reunion", []),
                "jefe": bool(d.get("jefe", False)),
                "miembros": [m for m in d.get("miembro", []) if m.get("nombre")],
                "muebles": d.get("mueble", []),
            })
    idos = []
    if os.path.exists(args.idos):
        try:
            idos = [d for d in cargar_toml(args.idos).get("ido", []) if d.get("nombre")]
        except Exception as e:
            avisos.append("idos.toml: %s" % e)
    fiestas = []
    if os.path.exists(args.calendario):
        try:
            fiestas = F.cargar(cargar_toml(args.calendario))
        except Exception as e:
            avisos.append("calendario: %s" % e)
    return cfg, salas, idos, fiestas


def firma(args):
    """Fecha de modificación de los ficheros de gente (para recargar al guardar)."""
    rutas = [args.idos, args.config, args.calendario]
    if os.path.isdir(args.salas):
        rutas += [os.path.join(args.salas, n) for n in sorted(os.listdir(args.salas))]
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
    for k in range(dias):
        d = inicio + datetime.timedelta(days=k)
        cosas = [f.nombre for f in fiestas if f.empieza(d)]
        cumples = [m["nombre"] for s in salas for m in s.get("miembros", []) if F.es_cumple(m, d)]
        if cumples:
            cosas.append("Cumpleaños de " + ", ".join(cumples[:6]) + ("..." if len(cumples) > 6 else ""))
        for i in idos:
            if str(i.get("fecha", "")) == d.isoformat():
                cosas.append("Se va " + i["nombre"])
        if cosas:
            out[d] = " · ".join(cosas)
    return out


def crear_reloj(args, cfg, fiestas=None, salas=None, idos=None):
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
                                           (inicio or datetime.datetime.now()).time())
    if args.hora:
        h, m = (int(v) for v in args.hora.split(":"))
        inicio = (inicio or datetime.datetime.now()).replace(hour=h, minute=m, second=0)
    factor = args.acelerar
    if inicio is None and factor == 1.0:
        def ahora():
            return datetime.datetime.now()
        ahora.real = True   # la hora de verdad: el estado se guarda y las obras cuentan
        return ahora
    base = inicio or datetime.datetime.now()
    t0 = time.monotonic()
    return lambda: base + datetime.timedelta(seconds=(time.monotonic() - t0) * factor)
