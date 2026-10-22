"""Bucle principal de la versión gráfica.

    python3 hormiguero_pixel.py            # pantalla completa
    python3 hormiguero_pixel.py --ventana  # en una ventana
    python3 hormiguero_pixel.py --demo     # un año a toda velocidad

Teclas: q / Esc salir, f pantalla completa, i info de rendimiento.
"""

import argparse
import datetime
import os
import random
import signal
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class PantallaNula:
    """La simulación necesita saber el tamaño "en celdas": 160x64 (640x512 píxeles)."""

    def __init__(self, ancho=160, alto=64):
        self.ancho, self.alto = ancho, alto


def tus_datos(nombre):
    """local/<nombre> si existe (tus datos, fuera de git); si no, el de ejemplo del repositorio."""
    propio = os.path.join(RAIZ, "local", nombre)
    return propio if os.path.exists(propio) else os.path.join(RAIZ, nombre)


# los mensajes de argparse que salen en inglés, en español
INGLES = (("unrecognized arguments", "no conozco estas opciones"), ("expected one argument", "falta su valor"),
          ("invalid choice", "no vale"), ("choose from", "elige entre"), ("invalid float value", "no es un número"),
          ("invalid int value", "no es un número entero"), ("argument ", "opción "),
          ("the following arguments are required", "faltan estas opciones"), ("ignored explicit argument",
                                                                                "esta opción no lleva valor"))


class Formato(argparse.HelpFormatter):
    def add_usage(self, usage, actions, groups, prefix=None):
        return super().add_usage(usage, actions, groups, "uso: ")


class Opciones(argparse.ArgumentParser):
    """argparse, con la ayuda y los errores en español."""

    def __init__(self, **k):
        super().__init__(formatter_class=Formato, add_help=False, **k)
        self._optionals.title = "opciones"
        self.add_argument("-h", "--help", action="help", help="enseña esta ayuda y sale")

    def error(self, mensaje):
        for ingles, espanol in INGLES:
            mensaje = mensaje.replace(ingles, espanol)
        self.print_usage(sys.stderr)
        self.exit(2, "%s: error: %s\n" % (self.prog, mensaje))


def _fecha(texto):
    try:
        return datetime.date.fromisoformat(texto.strip()).isoformat()
    except ValueError:
        raise argparse.ArgumentTypeError("«%s» no es una fecha: escríbela así, 2026-12-24" % texto) from None


def _hora(texto):
    try:
        h, m = (int(v) for v in texto.strip().split(":"))
    except ValueError:
        h = m = -1
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise argparse.ArgumentTypeError("«%s» no es una hora: escríbela así, 21:00 (de 00:00 a 23:59)" % texto)
    return "%02d:%02d" % (h, m)


def _numero(texto):
    try:
        return float(texto)
    except ValueError:
        raise argparse.ArgumentTypeError("«%s» no es un número (los decimales, con punto: 0.5)" % texto) from None


def _entero(texto):
    try:
        return int(texto)
    except ValueError:
        raise argparse.ArgumentTypeError("«%s» no es un número entero" % texto) from None


def argumentos(argv=None):
    p = Opciones(prog="hormiguero_pixel", description="Ant Farm Idle: un hormiguero en pixel art.")
    p.add_argument("-c", "--config", default=tus_datos("config.toml"), metavar="RUTA",
                   help="fichero de configuración (por defecto, local/config.toml o config.toml)")
    p.add_argument("--salas", default=tus_datos("salas"), metavar="RUTA", help="carpeta de las salas")
    p.add_argument("--tipos", default=tus_datos("tipos"), metavar="RUTA", help="carpeta de los tipos de sala")
    p.add_argument("--idos", default=tus_datos("idos.toml"), metavar="RUTA", help="fichero de los que se fueron")
    p.add_argument("--calendario", default=tus_datos("calendario.toml"), metavar="RUTA",
                   help="fichero de las fiestas")
    p.add_argument("--fecha", type=_fecha, metavar="AAAA-MM-DD", help="empieza ese día")
    p.add_argument("--hora", type=_hora, metavar="HH:MM", help="empieza a esa hora")
    p.add_argument("--dias", type=_numero, metavar="N", help="empieza N días después de la fundación")
    p.add_argument("--acelerar", type=_numero, default=1.0, metavar="N", help="el reloj va N veces más deprisa")
    p.add_argument("--demo", action="store_true", help="un año entero a toda velocidad")
    p.add_argument("--seg-dia", type=_numero, default=4.0, metavar="N",
                   help="en la demo, segundos que dura cada día (como mínimo 0.2)")
    p.add_argument("--pausa", type=_numero, default=5.0, metavar="N",
                   help="en la demo, segundos que se para en cada fecha importante")
    p.add_argument("--semilla", type=_entero, metavar="N", help="otra semilla: otra colocación de salas y túneles")
    p.add_argument("--tiempo", choices=("despejado", "nublado", "lluvia", "tormenta", "nieve", "calima"),
                   help="forzar el tiempo (para probar o hacer capturas)")
    p.add_argument("--fps", type=_numero, default=None, metavar="N",
                   help="fotogramas por segundo (por defecto, fps_pixel de config.toml)")
    p.add_argument("--ventana", action="store_true", help="en ventana en vez de pantalla completa")
    p.add_argument("--captura", metavar="PNG", help="sin pantalla: simula y guarda una imagen")
    p.add_argument("--segundos", type=_numero, default=10, metavar="N",
                   help="con --captura o --medir, segundos que se simulan")
    p.add_argument("--medir", action="store_true", help="sin pantalla: mide cuánto tarda cada fotograma")
    return p.parse_args(argv)


def cargar(A, args, avisos):
    """Lee los ficheros (hormiga.app.cargar) y avisa de los muebles que no existen. Apunta en
    cada tipo las columnas que necesitan sus muebles (las obras no se estrechan más)."""
    from . import muebles as MU
    cfg, salas, idos, fiestas = A.cargar(args, avisos)
    for t in cfg["tipos"].values():
        MU.revisar(t["muebles"], t["fichero"], avisos)
        piezas = [str(mu.get("pieza", "")).lower() for mu in t["muebles"]]
        t["ancho_minimo"] = max([MU.ancho_minimo(p) for p in piezas if p in MU.PIEZAS], default=0)
    for s in salas:
        MU.revisar(s["muebles"], s["fichero"], avisos)
    return cfg, salas, idos, fiestas


def preparar(args):
    sys.path.insert(0, RAIZ)
    from hormiga import app as A
    avisos = []
    cfg, salas, idos, fiestas = cargar(A, args, avisos)
    if args.semilla is not None:
        cfg["general"]["semilla"] = args.semilla
    elif args.demo:
        cfg["general"]["semilla"] = random.randrange(1, 100000)
    from .base import ajustar_textos
    ajustar_textos(cfg)
    if getattr(args, "tiempo", None):
        cfg["tiempo_forzado"] = args.tiempo
    return A, cfg, salas, idos, fiestas, avisos


def iniciar_pygame():
    """Sólo la pantalla y las letras. pygame.init() arranca también el sonido (PulseAudio), que no
    se usa y puede dejar el proceso colgado al salir con sus hilos abiertos."""
    import pygame
    pygame.display.init()
    pygame.font.init()


def memoria_maxima_mb():
    """La memoria máxima que ha usado el proceso, en MB, o None si no se puede saber (el módulo
    resource sólo existe en Linux y macOS: en Windows no se enseña)."""
    try:
        import resource
    except ImportError:
        return None
    maximo = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # en macOS viene en bytes; en Linux, en KB
    return maximo / (1024 * 1024) if sys.platform == "darwin" else maximo / 1024


def sin_pantalla(args):
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    import pygame
    A, cfg, salas, idos, fiestas, avisos = preparar(args)
    iniciar_pygame()
    pantalla = pygame.display.set_mode((640, 512))
    from hormiga.mundo import Mundo
    from .render import Render
    reloj = A.crear_reloj(args, cfg, fiestas, salas, idos)
    simulado = [reloj()]
    fps = args.fps or 20.0
    m = Mundo(cfg, salas, idos, fiestas, PantallaNula(), lambda: simulado[0], avisos)
    r = Render(m, pantalla)
    pasos = int(args.segundos * fps)
    t_sim = t_dib = 0.0
    for i in range(pasos):
        simulado[0] += datetime.timedelta(seconds=args.acelerar / fps)
        t0 = time.perf_counter()
        m.paso(1 / fps)
        t1 = time.perf_counter()
        if args.medir or i == pasos - 1 or i % 20 == 0:
            r.dibujar()
        t2 = time.perf_counter()
        t_sim += t1 - t0
        t_dib += t2 - t1
    if args.medir:
        print("simulación %.2f ms · dibujo %.2f ms por fotograma (%d fotogramas)"
              % (t_sim / pasos * 1000, t_dib / pasos * 1000, pasos))
        mb = memoria_maxima_mb()
        if mb is not None:
            print("memoria máxima: %.1f MB" % mb)
    if args.captura:
        grande = pygame.transform.scale(pantalla, (1280, 1024))
        pygame.image.save(grande, args.captura)
        print("captura guardada en", args.captura)
    for a in m.todos_los_avisos():
        print("aviso:", a)


def firma(args):
    from hormiga import app as A
    return A.firma(args)


def para_reiniciar(args, salas):
    """Lo que sólo se aplica al reiniciar: config.toml y tipos/ tal como están escritos (sin los
    comentarios) y, de cada sala, su nombre, color, planta, x, ancho y tipo."""
    from motor.sprites import cargar_toml

    def leer(ruta):
        try:
            return cargar_toml(ruta)
        except Exception as e:   # también si no existe
            return str(e)
    tipos = {}
    if os.path.isdir(args.tipos):
        tipos = {n: leer(os.path.join(args.tipos, n)) for n in sorted(os.listdir(args.tipos))
                 if n.endswith(".toml") and not n.startswith(".")}
    plano = {s["fichero"]: tuple(s.get(k) for k in ("nombre", "color", "planta", "x", "ancho", "tipo"))
             for s in salas}
    return leer(args.config), tipos, plano


def avisos_de_reinicio(antes, ahora):
    """Avisos de lo que ha cambiado en los ficheros y no se ve hasta reiniciar (si no, al quitarse
    el aviso de una errata parecería que ya está arreglada)."""
    (cfg0, tipos0, plano0), (cfg1, tipos1, plano1) = antes, ahora
    out = []
    if cfg1 != cfg0:
        out.append("config.toml ha cambiado: reinicia el hormiguero para aplicarlo")
    if tipos1 != tipos0:
        out.append("tipos/ ha cambiado: reinicia el hormiguero para aplicarlo")
    for f in sorted(set(plano0) | set(plano1)):
        if f not in plano0:
            out.append("%s es nueva: la sala sale al reiniciar el hormiguero (su gente, mientras, en otra)" % f)
        elif f not in plano1:
            out.append("%s ya no está: su sala se quita al reiniciar el hormiguero" % f)
        elif plano0[f] != plano1[f]:
            out.append("%s: el nombre, el color, la planta, x, el ancho y el tipo de la sala se aplican al "
                       "reiniciar el hormiguero" % f)
    return out


def con_pantalla(args):
    import pygame
    A, cfg, salas, idos, fiestas, avisos = preparar(args)
    iniciar_pygame()
    pygame.mouse.set_visible(False)
    flags = pygame.SCALED
    if not args.ventana:
        flags |= pygame.FULLSCREEN
    try:
        pantalla = pygame.display.set_mode((640, 512), flags, vsync=1)
    except (pygame.error, TypeError):
        pantalla = pygame.display.set_mode((640, 512), flags)
    pygame.display.set_caption("Ant Farm Idle")
    from hormiga.mundo import Mundo
    from .render import Render
    reloj = A.crear_reloj(args, cfg, fiestas, salas, idos)
    inicial = para_reiniciar(args, salas)
    m = Mundo(cfg, salas, idos, fiestas, PantallaNula(), reloj, avisos)
    if args.demo:
        m.contexto_cada = 0.25
        m.demo_texto = "DEMO · semilla %s · un día cada %g s" % (cfg["general"]["semilla"], max(0.2, args.seg_dia))
    r = Render(m, pantalla)
    fps = args.fps or float(cfg["general"].get("fps_pixel", 20))
    clock = pygame.time.Clock()
    huella = firma(args)
    revisado = time.monotonic()
    info = False
    medias = [0.0, 0.0]
    try:
        while True:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    return
                if ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_q, pygame.K_ESCAPE):
                        return
                    if ev.key == pygame.K_f:
                        pygame.display.toggle_fullscreen()
                    if ev.key == pygame.K_i:
                        info = not info
            dt = min(0.25, clock.tick(fps) / 1000.0)
            ahora = time.monotonic()
            if ahora - revisado > 3:
                revisado = ahora
                nueva = firma(args)
                if nueva != huella:
                    huella = nueva
                    # se rehacen los avisos de los ficheros (y, al repintar las salas, los de sus
                    # muebles); los del trazado se quedan. Lo que sólo vale al reiniciar, se avisa
                    nuevos = []
                    try:
                        _cfg, salas, idos, fiestas = cargar(A, args, nuevos)
                        m.avisos_carga = nuevos + avisos_de_reinicio(inicial, para_reiniciar(args, salas))
                        m.fiestas = fiestas
                        m.cargar_gente(salas, idos)
                        m.actualizar_contexto(forzar=True)
                    except Exception as e:   # sigue con lo que tenía
                        m.avisos_carga.append("no he podido recargar los ficheros: %s" % e)
                    r.recargado()
            if args.demo:
                m.pausa_texto = reloj.texto if reloj.en_pausa() else None
            t0 = time.perf_counter()
            m.paso(dt)
            t1 = time.perf_counter()
            avisos = m.todos_los_avisos()
            r.bajar_pancarta = 14 if avisos else 0   # el mensaje del cielo, debajo de la franja
            r.dibujar()
            t2 = time.perf_counter()
            medias[0] = medias[0] * 0.95 + (t1 - t0) * 50
            medias[1] = medias[1] * 0.95 + (t2 - t1) * 50
            y = 44   # debajo de la fecha: la franja de avisos y, debajo, lo de la tecla «i»
            if avisos:   # recortada a lo que cabe en la pantalla, con «…» si sigue
                texto = r.letras.recortar("Avisos: " + "; ".join(avisos), pantalla.get_width() - 16, 9)
                img = r.letras.texto(texto, (30, 30, 30), 9, fondo=(255, 225, 90))
                pantalla.blit(img, (6, y))
                y += img.get_height() + 2
            if info:
                txt = "%.0f fps · simulación %.1f ms · dibujo %.1f ms" % (clock.get_fps(), medias[0], medias[1])
                pantalla.blit(r.letras.texto(txt, (255, 255, 160), 9, fondo=(20, 20, 20)), (6, y))
            pygame.display.flip()

    finally:
        if m.estado is not None:   # lo excavado, los colores y dónde estaba cada hormiga
            m.estado.guardar(m.hormigas.values())


def main(argv=None):
    args = argumentos(argv)
    if args.captura or args.medir:
        sin_pantalla(args)
    else:
        # al parar el servicio (SIGTERM) se sale como con la q, guardando el estado
        signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
        con_pantalla(args)
