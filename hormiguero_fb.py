#!/usr/bin/env python3
"""Ant Farm Idle, pintando directamente en el framebuffer (/dev/fb0), sin escritorio
ni aceleración gráfica (KMS/EGL). Para la Pi cuando pygame con kmsdrm deja la pantalla en negro.
    python3 hormiguero_fb.py [las mismas opciones que hormiguero_pixel.py]
Variables: HORMIGUERO_FB=/dev/fb0 (dispositivo) · HORMIGUERO_FB_INFO=1 (imprime el coste cada minuto)."""

import atexit
import fcntl
import mmap
import os
import struct
import sys
import time

os.environ["SDL_VIDEODRIVER"] = "dummy"   # pygame dibuja en memoria; aquí lo copiamos a la pantalla
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402

FBIOGET_VSCREENINFO = 0x4600
KDSETMODE, KD_TEXT, KD_GRAPHICS = 0x4B3A, 0, 1


def geometria(fd, nombre):
    """(ancho, alto, bits, (rojo, verde, azul) como (desplazamiento, longitud), bytes por línea)."""
    v = struct.unpack("20I", fcntl.ioctl(fd, FBIOGET_VSCREENINFO, bytes(80)))
    ancho, alto, bits = v[0], v[1], v[6]
    canales = ((v[8], v[9]), (v[11], v[12]), (v[14], v[15]))
    try:
        with open("/sys/class/graphics/%s/stride" % nombre) as f:
            linea = int(f.read())
    except OSError:
        linea = ancho * bits // 8
    return ancho, alto, bits, canales, linea


class Framebuffer:
    def __init__(self, ruta):
        self.fd = os.open(ruta, os.O_RDWR)
        self.ancho, self.alto, bits, canales, self.linea = geometria(self.fd, os.path.basename(ruta))
        mascaras = [((1 << lon) - 1) << desp for desp, lon in canales] + [0]
        self.lienzo = pygame.Surface((self.ancho, self.alto), 0, bits, mascaras)
        self.mapa = mmap.mmap(self.fd, self.linea * self.alto)
        self.costes = []

    def destino(self, w, h):
        """Zona centrada donde cabe la imagen de w x h, ampliada lo máximo sin deformarla."""
        k = min(self.ancho / w, self.alto / h)
        if k >= 1:
            k = int(k)   # ampliar por un número entero: los píxeles quedan nítidos
        dw, dh = int(w * k), int(h * k)
        return self.lienzo.subsurface(((self.ancho - dw) // 2, (self.alto - dh) // 2, dw, dh))

    def volcar(self, imagen):
        t0 = time.perf_counter()
        if not hasattr(self, "zona"):
            self.lienzo.fill((0, 0, 0))
            self.zona = self.destino(*imagen.get_size())
            self.copia = pygame.Surface(imagen.get_size(), 0, self.lienzo)   # mismo formato que la pantalla
        self.copia.blit(imagen, (0, 0))
        pygame.transform.scale(self.copia, self.zona.get_size(), self.zona)
        datos = self.lienzo.get_buffer().raw
        paso = self.lienzo.get_pitch()
        if paso == self.linea:
            self.mapa[:len(datos)] = datos
        else:
            n = min(paso, self.linea)
            for y in range(self.alto):
                self.mapa[y * self.linea:y * self.linea + n] = datos[y * paso:y * paso + n]
        self.costes.append(time.perf_counter() - t0)


def modo_grafico_consola():
    """Que la consola no pinte el cursor ni texto encima (solo si somos dueños de la terminal)."""
    try:
        fcntl.ioctl(0, KDSETMODE, KD_GRAPHICS)
        atexit.register(lambda: fcntl.ioctl(0, KDSETMODE, KD_TEXT))
    except OSError:
        pass


def main():
    fb = Framebuffer(os.environ.get("HORMIGUERO_FB", "/dev/fb0"))
    print("framebuffer %dx%d" % (fb.ancho, fb.alto), flush=True)
    modo_grafico_consola()
    info = os.environ.get("HORMIGUERO_FB_INFO")
    original = pygame.display.set_mode
    ultimo = [time.monotonic()]

    def set_mode(tam=(0, 0), flags=0, *a, **k):
        return original(tam)

    def flip():
        fb.volcar(pygame.display.get_surface())
        if info and time.monotonic() - ultimo[0] > 60:
            ultimo[0] = time.monotonic()
            print("volcado a pantalla: %.1f ms de media" % (1000 * sum(fb.costes) / len(fb.costes)), flush=True)
            fb.costes.clear()

    pygame.display.set_mode = set_mode
    pygame.display.flip = flip
    pygame.display.update = lambda *a: flip()
    from pixel.app import main as hormiguero
    hormiguero()


if __name__ == "__main__":
    main()
