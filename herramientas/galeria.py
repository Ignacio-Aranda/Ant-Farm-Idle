#!/usr/bin/env python3
"""Genera las galerías de docs/ con todo lo que se puede poner en el hormiguero:

    docs/galeria-muebles.png   cada mueble de las salas (tipos/*.toml)
    docs/galeria-tipos.png     cada tipo de sala, tal cual viene
    docs/galeria-paisaje.png   cada pieza del paisaje, de día y de noche

Uso:  python3 herramientas/galeria.py   (no abre ninguna ventana)
"""

import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import pygame  # noqa: E402

from pixel import app as APP  # noqa: E402
from pixel import muebles as MU  # noqa: E402
from pixel import paisaje as PA  # noqa: E402
from pixel.base import Letras, multiplicar, superficie  # noqa: E402
from pixel.render import MADERA, MADERA_OSC, PAREDES, Render  # noqa: E402

FONDO = (24, 22, 28)
TEXTO = (240, 236, 220)
GRIS = (160, 156, 150)


def mundo_de_ejemplo():
    """Un hormiguero de ejemplo ya crecido (para que la vitrina tenga hallazgos), siempre el
    mismo: con los ficheros del repositorio (no los de local/), la fundación y la semilla de
    por defecto y sin escribir nada en local/."""
    def r(nombre):
        return os.path.join(RAIZ, nombre)
    args = APP.argumentos(["--fecha", "2027-03-01", "--hora", "12:00", "-c", r("config.toml"),
                           "--salas", r("salas"), "--tipos", r("tipos"), "--idos", r("idos.toml"),
                           "--calendario", r("calendario.toml")])
    args.sin_estado = True
    A, cfg, salas, idos, fiestas, avisos = APP.preparar(args)
    cfg["general"].update(A.POR_DEFECTO["general"])
    pygame.init()
    pantalla = pygame.display.set_mode((640, 512))
    from hormiga.mundo import Mundo
    reloj = A.crear_reloj(args, cfg, fiestas, salas, idos)
    m = Mundo(cfg, salas, idos, fiestas, APP.PantallaNula(), reloj, avisos)
    m.paso(0.05)
    return m, Render(m, pantalla), cfg


def sala_vacia(ancho, alto, paredes="madera", suelo="madera"):
    """Una sala de muestra: pared, papel pintado y suelo, como en el hormiguero."""
    s = pygame.Surface((ancho, alto))
    pared = PAREDES.get(paredes, PAREDES["madera"])
    s.fill(pared)
    for x in range(2, ancho - 2, 6):
        pygame.draw.line(s, [int(v * 0.88) for v in pared], (x, 6), (x, alto - 6))
    r = pygame.Rect(0, 0, ancho, alto - 3)
    if suelo == "baldosa":
        for x in range(0, ancho, 6):
            pygame.draw.rect(s, (200, 210, 215), (x, r.bottom, 5, 3))
    elif suelo == "tierra":
        pygame.draw.rect(s, (110, 78, 50), (0, r.bottom, ancho, 3))
    else:
        pygame.draw.rect(s, MADERA, (0, r.bottom, ancho, 3))
        for x in range(4, ancho - 4, 9):
            pygame.draw.line(s, MADERA_OSC, (x, r.bottom), (x, r.bottom + 2))
    return s, r


def rotulo(letras, texto, sub=None):
    t = letras.texto(texto, TEXTO, 9, sombra=False)
    if not sub:
        return t
    t2 = letras.texto(sub, GRIS, 7, sombra=False)
    out = pygame.Surface((max(t.get_width(), t2.get_width()), t.get_height() + t2.get_height()))
    out.fill(FONDO)
    out.blit(t, (0, 0))
    out.blit(t2, (0, t.get_height()))
    return out


def rejilla(celdas, columnas, ancho, alto, titulo, letras, margen=10):
    filas = (len(celdas) + columnas - 1) // columnas
    cab = 26
    img = pygame.Surface((columnas * (ancho + margen) + margen, cab + filas * (alto + margen) + margen))
    img.fill(FONDO)
    img.blit(letras.texto(titulo, (255, 230, 120), 12), (margen, 6))
    for i, c in enumerate(celdas):
        x = margen + (i % columnas) * (ancho + margen)
        y = cab + margen + (i // columnas) * (alto + margen)
        img.blit(c, (x, y))
    return pygame.transform.scale(img, (img.get_width() * 2, img.get_height() * 2))


def galeria_muebles(m, r, letras):
    celdas = []
    for nombre, (ancho, donde, defecto, pintar, animar) in MU.PIEZAS.items():
        celda = pygame.Surface((176, 92))
        celda.fill(FONDO)
        sala, rect = sala_vacia(176, 64)
        sitio = "centro" if donde == "suelo" else "pared"
        x, y = MU.colocar(nombre, sitio, rect)
        ctx = MU.Contexto(r, 400, 0, 0)
        pintar(sala, x, y, rect, ctx)
        if animar:
            animar(sala, x, y, rect, ctx, 0.0)
        celda.blit(sala, (0, 0))
        celda.blit(rotulo(letras, nombre, "%s · hueco por defecto: %s" % (donde, defecto)), (2, 66))
        celdas.append(celda)
    return rejilla(celdas, 4, 176, 92, "Muebles de las salas (tipos/*.toml, [[mueble]] pieza = ...)", letras)


def galeria_tipos(m, r, letras, tipos):
    celdas = []
    for nombre, tipo in tipos.items():
        celda = pygame.Surface((176, 92))
        celda.fill(FONDO)
        sala, rect = sala_vacia(176, 64, tipo.get("paredes", "madera"), tipo.get("suelo", "madera"))
        cuenta = {}
        for mu in tipo["muebles"]:
            pieza = str(mu.get("pieza", "")).lower()
            if pieza not in MU.PIEZAS:
                continue
            k = cuenta[pieza] = cuenta.get(pieza, -1) + 1
            x, y = MU.colocar(pieza, mu.get("sitio"), rect)
            ctx = MU.Contexto(r, 400, int(mu.get("aparece", 0)), k)
            MU.PIEZAS[pieza][3](sala, x, y, rect, ctx)
            if MU.PIEZAS[pieza][4]:
                MU.PIEZAS[pieza][4](sala, x, y, rect, ctx, 0.0)
        celda.blit(sala, (0, 0))
        celda.blit(rotulo(letras, 'tipo = "%s"' % nombre, "funcion = %s" % tipo["funcion"]), (2, 66))
        celdas.append(celda)
    return rejilla(celdas, 4, 176, 92, "Tipos de sala que vienen hechos (tipos/*.toml)", letras)


def cielo(w, h, noche):
    s = pygame.Surface((w, h))
    arriba, abajo = ((18, 22, 50), (40, 46, 84)) if noche else ((90, 150, 220), (170, 205, 235))
    for y in range(h):
        f = y / max(1, h - 1)
        s.fill([int(a + (b - a) * f) for a, b in zip(arriba, abajo)], (0, y, w, 1))
    return s


def escena_suelo(nombre, noche, semilla):
    w, h, G = 110, 80, 72
    s = cielo(w, h, noche)
    capa = superficie(w, h)
    PA.SUELO[nombre][0](capa, w // 2, G, PA.Contexto(120, semilla, noche, 0))
    pygame.draw.rect(capa, (80, 150, 60), (0, G - 2, w, 3))
    pygame.draw.rect(capa, (92, 62, 38), (0, G + 1, w, h - G))
    if noche:
        capa = multiplicar(capa, (110, 120, 170))
        luces = PA.SUELO[nombre][1]
        if luces:
            luces(capa, w // 2, G, PA.Contexto(120, semilla, True, 0))
    s.blit(capa, (0, 0))
    return s


def escena_fondo(nombre, noche, semilla):
    w, h, base = 150, 80, 70
    s = cielo(w, h, noche)
    monte = (34, 40, 66) if noche else (116, 150, 176)
    pygame.draw.polygon(s, monte, [(0, h), (0, base - 4), (w // 2, base - 12), (w, base - 4), (w, h)])
    cuerpo = (40, 44, 62) if noche else (150, 128, 100)
    pintar, animar = PA.FONDO[nombre]
    ctx = PA.Contexto(0, semilla, noche, 0)
    pintar(s, w // 2, base - 8, ctx, cuerpo, (250, 210, 110))
    if animar:
        animar(s, w // 2, base - 8, ctx, 1.2)
    return s


def galeria_paisaje(letras, semilla):
    celdas = []
    for nombre in PA.SUELO:
        celda = pygame.Surface((228, 104))
        celda.fill(FONDO)
        celda.blit(escena_suelo(nombre, False, semilla), (0, 0))
        celda.blit(escena_suelo(nombre, True, semilla), (116, 0))
        celda.blit(rotulo(letras, nombre, "[[paisaje.suelo]] · de día y de noche"), (2, 82))
        celdas.append(celda)
    for nombre in PA.FONDO:
        celda = pygame.Surface((228, 104))
        celda.fill(FONDO)
        celda.blit(pygame.transform.smoothscale(escena_fondo(nombre, False, semilla), (110, 80)), (0, 0))
        celda.blit(pygame.transform.smoothscale(escena_fondo(nombre, True, semilla), (110, 80)), (116, 0))
        celda.blit(rotulo(letras, nombre, "[[paisaje.fondo]] · de día y de noche"), (2, 82))
        celdas.append(celda)
    return rejilla(celdas, 4, 228, 104, "Paisaje (config.toml, [paisaje])", letras)


def main():
    m, r, cfg = mundo_de_ejemplo()
    letras = Letras()
    docs = os.path.join(RAIZ, "docs")
    os.makedirs(docs, exist_ok=True)
    for nombre, img in (("galeria-muebles.png", galeria_muebles(m, r, letras)),
                        ("galeria-tipos.png", galeria_tipos(m, r, letras, cfg["tipos"])),
                        ("galeria-paisaje.png", galeria_paisaje(letras, m.semilla))):
        ruta = os.path.join(docs, nombre)
        pygame.image.save(img, ruta)
        print("guardada", ruta, img.get_size())


if __name__ == "__main__":
    main()
