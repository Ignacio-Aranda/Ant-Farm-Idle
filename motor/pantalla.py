"""Salida: terminal (curses) y un volcado HTML para capturas/pruebas."""

import html

from .colores import rgb_de_256


class Pantalla:
    """Interfaz común. 'modo' es 256, 16, 8 o 0 (sin color)."""
    modo = 256
    alto = 24
    ancho = 80

    def poner(self, y, x, texto, fg, fondo):
        raise NotImplementedError

    def nuevo_cuadro(self):
        pass

    def mostrar(self):
        pass

    def reiniciar_colores(self):
        pass


class PantallaCurses(Pantalla):
    def __init__(self, scr, forzar_modo=None):
        import curses
        self.curses = curses
        self.scr = scr
        self.modo = 0
        if curses.has_colors():
            curses.start_color()
            try:
                curses.use_default_colors()
                self.por_defecto = -1
            except curses.error:
                self.por_defecto = 0
            n = curses.COLORS
            self.modo = 256 if n >= 256 else 16 if n >= 16 else 8
        if forzar_modo is not None:
            self.modo = min(self.modo, forzar_modo) if self.modo else 0
        # Python/ncurses sólo codifica 255 pares dentro de los atributos.
        self.max_pares = min(getattr(curses, "COLOR_PAIRS", 64), 256) - 1
        self.reiniciar_colores()
        self.actualizar_tamano()

    def actualizar_tamano(self):
        self.alto, self.ancho = self.scr.getmaxyx()

    def reiniciar_colores(self):
        self._attr = {}       # (fg, fondo) -> atributo curses
        self._pares = {}      # (fgc, bgc) -> número de par
        self._uso = {}        # número de par -> último cuadro usado
        self._cuadro = 0

    def nuevo_cuadro(self):
        self._cuadro += 1
        self.scr.erase()

    def _par(self, fgc, bgc):
        p = self._pares.get((fgc, bgc))
        if p is not None:
            return p
        if len(self._pares) < self.max_pares:
            p = len(self._pares) + 1
        else:
            # Reciclar el par que lleva más tiempo sin usarse.
            p = min(self._uso, key=self._uso.get)
            if self._uso[p] >= self._cuadro - 1:
                return 0
            viejo = next(k for k, v in self._pares.items() if v == p)
            del self._pares[viejo]
            self._attr = {k: v for k, v in self._attr.items() if v[1] != p}
        try:
            self.curses.init_pair(p, fgc, bgc)
        except self.curses.error:
            return 0
        self._pares[(fgc, bgc)] = p
        return p

    def atributo(self, fg, fondo):
        clave = (fg, fondo)
        a = self._attr.get(clave)
        if a is None:
            curses = self.curses
            negrita = 0
            if self.modo == 0:
                a = (curses.A_BOLD if fg.vivo else 0, 0)
                self._attr[clave] = a
                return a[0]
            if self.modo == 256:
                fgc, bgc = fg.c256, fondo.c256 if fondo is not None else -1
            else:
                fgc = fg.c8
                if fg.vivo:
                    if self.modo == 16:
                        fgc += 8
                    else:
                        negrita = curses.A_BOLD
                bgc = fondo.c8 if fondo is not None else -1
            if bgc == -1:
                bgc = self.por_defecto
            p = self._par(fgc, bgc)
            a = (curses.color_pair(p) | negrita, p)
            if not p:
                return a[0]  # sin pares libres este cuadro: no cachear
            self._attr[clave] = a
        if a[1]:
            self._uso[a[1]] = self._cuadro
        return a[0]

    def poner(self, y, x, texto, fg, fondo):
        try:
            self.scr.addstr(y, x, texto, self.atributo(fg, fondo))
        except self.curses.error:
            pass  # la esquina inferior derecha siempre "falla" en curses

    def mostrar(self):
        self.scr.noutrefresh()
        self.curses.doupdate()


class PantallaHTML(Pantalla):
    """Pantalla en memoria; sirve para pruebas sin terminal y para capturas."""

    def __init__(self, ancho, alto, modo=256):
        self.ancho, self.alto, self.modo = ancho, alto, modo
        self.nuevo_cuadro()

    def nuevo_cuadro(self):
        self.celdas = [[(" ", None, None)] * self.ancho for _ in range(self.alto)]

    def poner(self, y, x, texto, fg, fondo):
        if not 0 <= y < self.alto:
            return
        fila = self.celdas[y]
        for i, ch in enumerate(texto):
            if 0 <= x + i < self.ancho:
                fila[x + i] = (ch, fg, fondo)

    def texto(self):
        return "\n".join("".join(c[0] for c in fila) for fila in self.celdas)

    def _hex(self, n, por_defecto):
        if n is None or n < 0:
            return por_defecto
        return "#%02x%02x%02x" % rgb_de_256(n)

    def a_html(self, titulo="Acuario"):
        out = ['<!doctype html><meta charset="utf-8"><title>%s</title>' % titulo,
               '<body style="background:#000;margin:0">'
               '<pre style="font:14px/1.15 DejaVu Sans Mono,monospace;margin:8px">']
        for fila in self.celdas:
            previo, trozo = None, []
            for ch, fg, fondo in fila:
                estilo = (self._hex(fg.c256 if fg else None, "#ccc"),
                          self._hex(fondo.c256 if fondo else None, "#000"))
                if estilo != previo and trozo:
                    out.append('<span style="color:%s;background:%s">%s</span>'
                               % (previo + (html.escape("".join(trozo)),)))
                    trozo = []
                previo = estilo
                trozo.append(ch)
            if trozo:
                out.append('<span style="color:%s;background:%s">%s</span>'
                           % (previo + (html.escape("".join(trozo)),)))
            out.append("\n")
        out.append("</pre></body>")
        return "".join(out)
