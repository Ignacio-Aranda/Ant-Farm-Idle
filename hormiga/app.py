"""Arranque, reloj (real o simulado) y bucle principal."""

import argparse
import datetime
import locale
import os
import random
import sys
import time
import unicodedata

from motor.colores import Fondo, color
from motor.pantalla import PantallaHTML
from motor.sprites import cargar_toml

from . import fiestas as F
from .mundo import Mundo

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

POR_DEFECTO = {
    "general": {"fps": 8, "fundacion": "2026-10-14", "semilla": 2026, "unicode": "auto"},
}


def argumentos(argv=None):
    p = argparse.ArgumentParser(prog="hormiguero", description="Ant Farm Idle para la terminal.")
    p.add_argument("-c", "--config", default=os.path.join(RAIZ, "config.toml"))
    p.add_argument("--salas", default=os.path.join(RAIZ, "salas"))
    p.add_argument("--idos", default=os.path.join(RAIZ, "idos.toml"))
    p.add_argument("--calendario", default=os.path.join(RAIZ, "calendario.toml"))
    p.add_argument("--fecha", help="simular una fecha AAAA-MM-DD")
    p.add_argument("--hora", help="simular una hora HH:MM")
    p.add_argument("--dias", type=float, help="ver el hormiguero N días después de la fundación")
    p.add_argument("--acelerar", type=float, default=1.0,
                   help="el tiempo corre N veces más rápido (p. ej. 3600 = 1 hora por segundo)")
    p.add_argument("--demo", action="store_true",
                   help="modo demostración: semilla aleatoria, un año a toda velocidad y "
                        "pausa de 5 s en cada fecha importante")
    p.add_argument("--seg-dia", type=float, default=4.0,
                   help="en --demo, segundos reales que dura cada día (por defecto 4)")
    p.add_argument("--pausa", type=float, default=5.0, help="en --demo, segundos de pausa")
    p.add_argument("--semilla", type=int, help="semilla del trazado (por defecto la de config.toml)")
    p.add_argument("--captura", metavar="HTML", help="sin terminal: guarda una captura en HTML")
    p.add_argument("--tamano", default="160x62", help="tamaño para --captura")
    p.add_argument("--segundos", type=float, default=10)
    return p.parse_args(argv)


def cargar(args, avisos):
    cfg = {k: dict(v) for k, v in POR_DEFECTO.items()}
    if os.path.exists(args.config):
        try:
            for k, v in cargar_toml(args.config).items():
                if isinstance(v, dict):
                    cfg.setdefault(k, {}).update(v)
                else:
                    cfg[k] = v
        except Exception as e:
            avisos.append("config: %s" % e)
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
            salas.append({
                "clave": os.path.splitext(nombre)[0].lower(),
                "nombre": d.get("nombre", os.path.splitext(nombre)[0]),
                "posicion": d.get("posicion", 99),
                "color": d.get("color", "blanco"),
                "nivel": d.get("nivel", 2),
                "ancho": d.get("ancho", 32),
                "reuniones": d.get("reunion", []),
                "jefe": bool(d.get("jefe", False)),
                "miembros": [m for m in d.get("miembro", []) if m.get("nombre")],
                "muebles": d.get("mueble", []),
            })
    salas.sort(key=lambda s: (s["posicion"], s["clave"]))
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
        return datetime.datetime.now
    base = inicio or datetime.datetime.now()
    t0 = time.monotonic()
    return lambda: base + datetime.timedelta(seconds=(time.monotonic() - t0) * factor)


_CAJAS = {}
for _grupo, _ascii in (("─═━▬", "-"), ("│║┃", "|"), ("┌┐└┘╔╗╚╝╒╕╭╮╰╯├┤┬┴┼╞╡╤╧", "+"),
                       ("▀▄█▌▐▍▓░▒▤▟▙", "#"), ("▪▫•●°", "o"), ("◖", "("), ("◗", ")"),
                       ("›", ">"), ("‹", "<"), ("╱", "/"), ("╲", "\\"), ("‿", "_"),
                       ("▲", "A"), ("♛", "w"), ("✿", "*"), ("◷", "o"), ("≈", "~")):
    for _c in _grupo:
        _CAJAS[ord(_c)] = _ascii


def a_ascii(t):
    t = t.translate(_CAJAS)
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()


def sin_terminal(args):
    avisos = []
    cfg, salas, idos, fiestas = cargar(args, avisos)
    w, h = (int(v) for v in args.tamano.lower().split("x"))
    p = PantallaHTML(w, h)
    reloj = crear_reloj(args, cfg)
    simulado = [reloj()]
    fps = float(cfg["general"]["fps"])
    m = Mundo(cfg, salas, idos, fiestas, p, lambda: simulado[0], avisos)
    t0 = time.perf_counter()
    pasos = int(args.segundos * fps)
    for _ in range(pasos):
        simulado[0] += datetime.timedelta(seconds=args.acelerar / fps)
        m.paso(1 / fps)
    m.dibujar()
    print("%.2f ms/fotograma" % ((time.perf_counter() - t0) / max(1, pasos) * 1000))
    for a in avisos:
        print("aviso:", a)
    with open(args.captura, "w", encoding="utf-8") as f:
        f.write(p.a_html("Hormiguero"))


def _bucle(scr, args):
    import curses
    from motor.pantalla import PantallaCurses
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    scr.nodelay(True)
    scr.keypad(True)
    avisos = []
    cfg, salas, idos, fiestas = cargar(args, avisos)
    if args.semilla is not None:
        cfg["general"]["semilla"] = args.semilla
    elif args.demo:
        cfg["general"]["semilla"] = random.randrange(1, 100000)
    p = PantallaCurses(scr)
    uni = str(cfg["general"].get("unicode", "auto")).lower()
    unicode_ok = uni in ("si", "sí", "true") or (uni == "auto" and "UTF" in locale.getpreferredencoding(False).upper())
    if not unicode_ok:
        poner = p.poner
        p.poner = lambda y, x, t, fg, f: poner(y, x, t if t.isascii() else a_ascii(t), fg, f)
    reloj = crear_reloj(args, cfg, fiestas, salas, idos)
    m = Mundo(cfg, salas, idos, fiestas, p, reloj, avisos)
    m.unicode = unicode_ok
    if args.demo:
        m.contexto_cada = 0.25
        m.demo_texto = "DEMO · semilla %s · un día cada %g s" % (cfg["general"]["semilla"], args.seg_dia)
    fps = max(2.0, float(cfg["general"]["fps"]))
    anterior = time.monotonic()
    fondo_cielo = None
    huella = firma(args)
    revisado = time.monotonic()
    while True:
        ahora = time.monotonic()
        dt = min(0.5, ahora - anterior)
        anterior = ahora
        k = scr.getch()
        while k != -1:
            if k in (ord("q"), ord("Q")):
                return
            if k == curses.KEY_RESIZE:
                curses.update_lines_cols()
                p.actualizar_tamano()
                m.construir()
            k = scr.getch()
        if ahora - revisado > 3:
            revisado = ahora
            nueva = firma(args)
            if nueva != huella:
                huella = nueva
                avisos.clear()
                cfg2, salas, idos, fiestas = cargar(args, avisos)
                m.fiestas = fiestas
                m.cargar_gente(salas, idos)
                m.actualizar_contexto(forzar=True)
        if args.demo:
            m.pausa_texto = reloj.texto if reloj.en_pausa() else None
        m.paso(dt)
        if m.fondo_cielo != fondo_cielo:
            fondo_cielo = m.fondo_cielo
            scr.clear()
        m.dibujar()
        if avisos:
            p.poner(0, 0, (" Avisos: " + "; ".join(avisos))[:p.ancho - 1], color("negro"), Fondo(229, 3))
        p.mostrar()
        espera = 1 / fps - (time.monotonic() - ahora)
        if espera > 0:
            time.sleep(espera)


def main(argv=None):
    args = argumentos(argv)
    if args.captura:
        sin_terminal(args)
        return
    locale.setlocale(locale.LC_ALL, "")
    os.environ.setdefault("ESCDELAY", "25")
    import curses
    try:
        curses.wrapper(_bucle, args)
    except KeyboardInterrupt:
        pass
