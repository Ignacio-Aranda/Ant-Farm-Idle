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
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class PantallaNula:
    """La simulación necesita saber el tamaño "en celdas": 160x64 (640x512 píxeles)."""
    modo = 256

    def __init__(self, ancho=160, alto=64):
        self.ancho, self.alto = ancho, alto

    def poner(self, *a):
        pass

    def nuevo_cuadro(self):
        pass

    def reiniciar_colores(self):
        pass


def argumentos(argv=None):
    p = argparse.ArgumentParser(prog="hormiguero_pixel", description="Ant Farm Idle (pixel art).")
    p.add_argument("-c", "--config", default=os.path.join(RAIZ, "config.toml"))
    p.add_argument("--salas", default=os.path.join(RAIZ, "salas"))
    p.add_argument("--idos", default=os.path.join(RAIZ, "idos.toml"))
    p.add_argument("--calendario", default=os.path.join(RAIZ, "calendario.toml"))
    p.add_argument("--fecha")
    p.add_argument("--hora")
    p.add_argument("--dias", type=float)
    p.add_argument("--acelerar", type=float, default=1.0)
    p.add_argument("--demo", action="store_true")
    p.add_argument("--seg-dia", type=float, default=4.0)
    p.add_argument("--pausa", type=float, default=5.0)
    p.add_argument("--semilla", type=int)
    p.add_argument("--fps", type=float, default=None, help="fotogramas por segundo (por defecto 20)")
    p.add_argument("--ventana", action="store_true", help="en ventana en vez de pantalla completa")
    p.add_argument("--captura", metavar="PNG", help="sin pantalla: simula y guarda una imagen")
    p.add_argument("--segundos", type=float, default=10)
    p.add_argument("--medir", action="store_true", help="sin pantalla: mide cuánto tarda cada fotograma")
    return p.parse_args(argv)


def preparar(args):
    sys.path.insert(0, RAIZ)
    from hormiga import app as A
    avisos = []
    cfg, salas, idos, fiestas = A.cargar(args, avisos)
    if args.semilla is not None:
        cfg["general"]["semilla"] = args.semilla
    elif args.demo:
        cfg["general"]["semilla"] = random.randrange(1, 100000)
    from .base import ajustar_textos
    ajustar_textos(cfg)
    return A, cfg, salas, idos, fiestas, avisos


def sin_pantalla(args):
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    import pygame
    A, cfg, salas, idos, fiestas, avisos = preparar(args)
    pygame.init()
    pantalla = pygame.display.set_mode((640, 512))
    from hormiga.mundo import Mundo
    from .render import Render
    reloj = A.crear_reloj(args, cfg, fiestas, salas, idos)
    simulado = [reloj()]
    fps = args.fps or 20.0
    m = Mundo(cfg, salas, idos, fiestas, PantallaNula(), lambda: simulado[0], avisos)
    m.unicode = True
    r = Render(m, pantalla)
    pasos = int(args.segundos * fps)
    t_sim = t_dib = 0.0
    import resource
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
        print("memoria máxima: %.1f MB" % (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024))
    if args.captura:
        grande = pygame.transform.scale(pantalla, (1280, 1024))
        pygame.image.save(grande, args.captura)
        print("captura guardada en", args.captura)
    for a in avisos:
        print("aviso:", a)


def firma(args):
    from hormiga import app as A
    return A.firma(args)


def con_pantalla(args):
    import pygame
    A, cfg, salas, idos, fiestas, avisos = preparar(args)
    pygame.init()
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
    m = Mundo(cfg, salas, idos, fiestas, PantallaNula(), reloj, avisos)
    m.unicode = True
    if args.demo:
        m.contexto_cada = 0.25
        m.demo_texto = "DEMO · semilla %s · un día cada %g s" % (cfg["general"]["semilla"], args.seg_dia)
    r = Render(m, pantalla)
    fps = args.fps or float(cfg["general"].get("fps_pixel", 20))
    clock = pygame.time.Clock()
    huella = firma(args)
    revisado = time.monotonic()
    info = False
    medias = [0.0, 0.0]
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
                avisos.clear()
                _cfg, salas, idos, fiestas = A.cargar(args, avisos)
                m.fiestas = fiestas
                m.cargar_gente(salas, idos)
                m.actualizar_contexto(forzar=True)
                r.clave_sup = None
        if args.demo:
            m.pausa_texto = reloj.texto if reloj.en_pausa() else None
        t0 = time.perf_counter()
        m.paso(dt)
        t1 = time.perf_counter()
        r.dibujar()
        t2 = time.perf_counter()
        medias[0] = medias[0] * 0.95 + (t1 - t0) * 50
        medias[1] = medias[1] * 0.95 + (t2 - t1) * 50
        if info:
            txt = "%.0f fps · simulación %.1f ms · dibujo %.1f ms" % (clock.get_fps(), medias[0], medias[1])
            pantalla.blit(r.letras.texto(txt, (255, 255, 160), 9, fondo=(20, 20, 20)), (6, 44))
        if avisos:
            pantalla.blit(r.letras.texto("Avisos: " + "; ".join(avisos)[:120], (30, 30, 30), 9,
                                         fondo=(255, 225, 90)), (6, 44))
        pygame.display.flip()


def main(argv=None):
    args = argumentos(argv)
    if args.captura or args.medir:
        sin_pantalla(args)
    else:
        con_pantalla(args)
