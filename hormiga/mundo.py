"""El hormiguero completo: une la tierra, la superficie y las hormigas."""

import datetime
import math

from motor import fuente
from motor.colores import Fondo, color
from motor.sprites import construir, lineas, mascara_lineas, pintor_fijo

from . import fiestas as F
from . import decoracion as DE
from . import muebles as MU
from . import tiempo as T
from .hormigas import Hormiga
from .superficie import Superficie
from .vida import Vida
from .tierra import ANCHO, ARCILLA, ARENA, HUMUS, PROF, ROCA, Plan

DIAS_CORTOS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
DIAS_LARGOS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES_LARGOS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
                "septiembre", "octubre", "noviembre", "diciembre"]
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

CAPAS_UNI = {HUMUS: "▓", ARENA: "░", ARCILLA: "▒", ROCA: "▓"}
CAPAS_ASCII = {HUMUS: "%", ARENA: ".", ARCILLA: ":", ROCA: "#"}
CAPAS_COLOR = {HUMUS: "marron", ARENA: "arena", ARCILLA: 137, ROCA: "gris"}

CIELO_DIA = Fondo(32, -1)
CIELO_NOCHE = Fondo(17, -1)
CIELO_LLUVIA = Fondo(67, -1)
CIELO_CALIMA = Fondo(173, -1)


def _fecha(v):
    if isinstance(v, datetime.date):
        return v
    return datetime.date.fromisoformat(str(v).strip())


class Mundo:
    def __init__(self, cfg, salas_cfg, idos, fiestas, pantalla, reloj, avisos=None):
        self.cfg = cfg
        self.pantalla = pantalla
        self.reloj = reloj
        self.avisos = avisos if avisos is not None else []
        self.semilla = cfg["general"]["semilla"]
        nombre = str(cfg["general"].get("nombre", "")).strip()
        self.de_quien = " de %s" % nombre if nombre else ""
        self.fundacion = _fecha(cfg["general"]["fundacion"])
        self.unicode = True
        self.fiestas = fiestas
        self.t = 0.0
        self.contexto_cada = 1.0
        self.demo_texto = None
        self.pausa_texto = None
        self.colores_tierra = {k: color(v) for k, v in CAPAS_COLOR.items()}
        self.hormigas = {}
        self.cargar_gente(salas_cfg, idos)
        principales = self.salas_cfg
        self.plan = Plan(self.semilla, self.fundacion, principales)
        self.detalles = DE.detalles_suelo(self.plan, self.semilla)
        self.colores_borde = {k: color(v) for k, v in DE.BORDE.items()}
        self._muebles_cache = {}
        self.construir()

    # ----------------------------------------------------------- la gente

    def cargar_gente(self, salas_cfg, idos):
        """Se puede volver a llamar en marcha (al editar los ficheros)."""
        self.salas_cfg = salas_cfg
        self.personas = []
        for s in salas_cfg:
            for p in s.get("miembros", []):
                q = dict(p)
                q["nombre"] = str(q.get("nombre", "?")).strip()
                q["sala"] = s["clave"]
                try:
                    q["alta"] = _fecha(q["alta"]) if q.get("alta") else None
                except ValueError:
                    self.avisos.append("%s: fecha de alta mal escrita" % q["nombre"])
                    q["alta"] = None
                self.personas.append(q)
        self.idos_cfg = []
        for d in idos:
            q = dict(d)
            q["nombre"] = str(q.get("nombre", "?")).strip()
            try:
                q["fecha"] = _fecha(q["fecha"]) if q.get("fecha") else None
            except ValueError:
                self.avisos.append("%s: fecha de baja mal escrita" % q["nombre"])
                q["fecha"] = None
            self.idos_cfg.append(q)
        self.hormigas = {}
        self._diario_dia = None

    # -------------------------------------------------------------- montaje

    def construir(self):
        p = self.pantalla
        self.ancho, self.alto = p.ancho, p.alto
        self.suelo_y = max(10, self.alto - 1 - PROF - 1)
        self.cielo_alto = self.suelo_y
        self.ox = (self.ancho - ANCHO) // 2
        self.oy = self.suelo_y + 1
        self.plan_ancho = ANCHO
        self.superficie = Superficie(self)
        self.vida = Vida(self)
        self.noticias = []
        self._citas_hechas = set()
        self._espera_jefe = 600.0
        self._cache_tierra = None
        self.hormigas = {}
        self.actualizar_contexto(forzar=True)
        self._diario_dia = None
        self.diario = []

    def a_pantalla(self, gx, gy):
        return self.ox + gx, self.oy + gy

    # ------------------------------------------------------------ contexto

    def actualizar_contexto(self, forzar=False):
        self.ahora = self.reloj()
        hoy = self.ahora.date()
        inicio = datetime.datetime.combine(self.fundacion, datetime.time())
        self.dia = max(0.0, (self.ahora - inicio).total_seconds() / 86400)
        self.plan.actualizar(self.dia)
        self.tiempo_hoy = T.tiempo_del_dia(hoy, self.semilla)
        self.sol_hoy = T.sol(hoy)
        mins = self.ahora.hour * 60 + self.ahora.minute
        a, p = self.sol_hoy
        self.de_noche = not (a <= mins < p)
        self.lluvia = self.tiempo_hoy.lluvia(mins)
        self.temperatura = self.tiempo_hoy.temperatura(mins)
        self.estacion = T.estacion(hoy)
        if forzar or int(self.t) % 30 == 0:
            self.llovio = T.llovio_hace(self.ahora, 8, self.semilla)
            self.llovio_semana = any(T.tiempo_del_dia(hoy - datetime.timedelta(d), self.semilla).llueve
                                     for d in range(4))
        if self.tiempo_hoy.calima and not self.de_noche:
            self.fondo_cielo = CIELO_CALIMA
        elif self.lluvia > 0 and not self.de_noche:
            self.fondo_cielo = CIELO_LLUVIA
        else:
            self.fondo_cielo = CIELO_NOCHE if self.de_noche else CIELO_DIA
        if self.pantalla.modo != 256:
            self.fondo_cielo = None

        act = F.activas(self.fiestas, hoy)
        self.decoraciones = {f.decoracion for f in act}
        self.fiesta_mensaje = act[-1].mensaje if act else None
        self.gorro_fiesta = next((f.gorro for f in reversed(act) if f.gorro), None)

        self.salas = self.plan.salas(self.dia)
        self.sala_por_clave = {s.clave: s for s in self.salas}
        self.frente = self.plan.frente(self.dia)
        self.salidas_x_grid = self.plan.salidas(self.dia)
        self.salidas_x = [self.ox + x for x in self.salidas_x_grid]

        # quién está y quién se ha ido
        idos_hoy = [d for d in self.idos_cfg if not d["fecha"] or d["fecha"] <= hoy]
        self.idos = [d["nombre"] for d in idos_hoy]
        nombres_idos = {n.lower() for n in self.idos}
        presentes = [p for p in self.personas
                     if (not p["alta"] or p["alta"] <= hoy) and p["nombre"].lower() not in nombres_idos]
        self.cumples = [p["nombre"] for p in presentes if F.es_cumple(p, hoy)]
        self.x_cumple = self.plan.entrada + 42
        vivos = {p["nombre"] for p in presentes}
        for n in list(self.hormigas):
            if n not in vivos:
                del self.hormigas[n]
        for i, p in enumerate(presentes):
            h = self.hormigas.get(p["nombre"])
            if h is None:
                self.hormigas[p["nombre"]] = Hormiga(p, i, self)
            elif h.sala != p["sala"] or h.persona != p:
                h.persona, h.sala = p, p["sala"]  # la han cambiado de sala
                if p.get("color"):
                    h.color = color(p["color"])

    # ------------------------------------------------------------ noticias

    def noticia(self, texto):
        self.noticias.append((int(self.dia), texto, self.t))
        self.noticias = self.noticias[-30:]

    def vida_entregada(self, h, cosa):
        destino = "la despensa" if "despensa" in self.sala_por_clave else "el comedor"
        if cosa.peso >= 2:
            ayudantes = [o.nombre for o in self.hormigas.values()
                         if o.escoltando and o.escoltando[0] is h]
            quienes = [h.nombre] + ayudantes
            texto = (", ".join(quienes[:-1]) + " y " + quienes[-1]) if len(quienes) > 1 else quienes[0]
            self.noticia("%s han guardado %s en %s." % (texto, cosa.nombre, destino))
        self.guardado = getattr(self, "guardado", 0) + cosa.peso

    def _citas(self):
        """Reuniones de la sala de reuniones y llamadas del jefe al despacho."""
        ahora = self.ahora
        laborable = ahora.weekday() < 5
        dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        for cfg in self.salas_cfg:
            sala = self.sala_por_clave.get(cfg["clave"])
            if not sala:
                continue
            for r in cfg.get("reuniones", []):
                try:
                    h, mi = (int(v) for v in str(r.get("hora", "10:00")).split(":"))
                    dia = str(r.get("dia", "todos")).lower()
                    dur = float(r.get("minutos", 60))
                except ValueError:
                    continue
                if dia == "todos":
                    if not laborable:
                        continue
                elif dia.replace("miercoles", "miércoles") != dias[ahora.weekday()]:
                    continue
                inicio = ahora.replace(hour=h, minute=mi, second=0, microsecond=0)
                fin = inicio + datetime.timedelta(minutes=dur)
                clave = (ahora.date(), cfg["clave"], r.get("nombre", ""), h, mi)
                if not (inicio <= ahora < fin) or clave in self._citas_hechas:
                    continue
                self._citas_hechas.add(clave)
                quien = r.get("quien", "todos")
                hs = list(self.hormigas.values())
                if isinstance(quien, list):
                    nombres = {n.lower() for n in quien}
                    invitadas = [x for x in hs if x.nombre.lower() in nombres]
                elif quien == "todos":
                    invitadas = hs
                else:
                    invitadas = [x for x in hs if x.sala == str(quien).lower()]
                for x in invitadas:
                    x.convocar(self, sala, fin, "reunion")
                self.noticia("%s en la %s." % (r.get("nombre", "Reunión"), sala.nombre))
        # el jefe llama a alguien al despacho de vez en cuando (días laborables, horario de oficina)
        jefe = next((c for c in self.salas_cfg if c.get("jefe")), None)
        if not jefe or not laborable or not 9 <= ahora.hour < 18:
            return
        despacho = self.sala_por_clave.get(jefe["clave"])
        jefes = [x for x in self.hormigas.values() if x.sala == jefe["clave"]]
        otras = [x for x in self.hormigas.values() if x.sala != jefe["clave"] and not x.cita
                 and x.carga_cosa is None and not x.escoltando]
        if despacho and jefes and otras and self._espera_jefe <= 0:
            self._espera_jefe = self.vida.rng.uniform(900, 2400)
            x = self.vida.rng.choice(otras)
            x.convocar(self, despacho, ahora + datetime.timedelta(minutes=self.vida.rng.uniform(5, 20)),
                       "despacho")
            self.noticia("%s llama a %s al despacho." % (jefes[0].nombre, x.nombre))

    def punto_libre(self, sala, rng, yo):
        """Un sitio de la sala lejos de las demás hormigas (para que no se amontonen)."""
        otras = []
        for h in self.hormigas.values():
            if h is yo:
                continue
            fx, fy = h.ruta[-1] if h.ruta else (h.x, h.y)
            if fy == sala.piso:
                otras.append(fx)
        mejor, dist = None, -1
        for _ in range(8):
            px, py = sala.punto(rng)
            d = min((abs(px - o) for o in otras), default=99)
            if d > dist:
                mejor, dist = (px, py), d
            if d >= 11:
                break
        return mejor

    # --------------------------------------------------------------- paso

    def paso(self, dt):
        self.t += dt
        c = self.contexto_cada
        if int(self.t / c) != int((self.t - dt) / c) or self.t - dt <= 0:
            self.actualizar_contexto()
        self._espera_jefe -= dt
        if int(self.t) != int(self.t - dt):
            self._citas()
        for h in self.hormigas.values():
            h.actualizar(self, dt)
        self.vida.actualizar(dt)
        self.superficie.actualizar(dt)

    # ------------------------------------------------------------- dibujo

    def texto(self, y, x, t, c, fondo=None):
        yy = int(y)
        if yy < 0 or yy >= self.alto - 1:
            return
        xx = math.floor(x)
        if xx < 0:
            t = t[-xx:]
            xx = 0
        if xx + len(t) > self.ancho:
            t = t[:self.ancho - xx]
        if not t:
            return
        if yy < self.suelo_y and (fondo is None or fondo is self.fondo_cielo):
            # en el cielo, el fondo de cada casilla es el del cielo o el de la montaña
            fondo = self.fondo_cielo
            monte = self.superficie.fondo_monte
            alturas = self.superficie.cima
            if monte is not None and yy >= self.superficie.cima_min:
                ini = xx
                actual = None
                for i in range(len(t) + 1):
                    if i < len(t):
                        x = xx + i
                        f = monte if 0 <= x < len(alturas) and yy >= alturas[x] else fondo
                    else:
                        f = None
                    if i == 0:
                        actual = f
                        continue
                    if f is not actual or i == len(t):
                        self.pantalla.poner(yy, ini, t[ini - xx:i], c, actual)
                        ini, actual = xx + i, f
                return
        self.pantalla.poner(yy, xx, t, c, fondo)

    def blit(self, cuadro, x, y):
        ix, iy = math.floor(x), math.floor(y)
        for dy, dx, t, c in cuadro.tramos:
            self.texto(iy + dy, ix + dx, t, c)

    def _tierra(self):
        """Filas de tierra troceadas en tramos de un mismo color (se recalcula al excavar).
        Lleva raíces, piedras, gemas y fósiles, y los bordes de los túneles más oscuros."""
        clave = (self.plan.version, self.ancho, self.alto, self.unicode)
        if self._cache_tierra and self._cache_tierra[0] == clave:
            return self._cache_tierra[1]
        capas = CAPAS_UNI if self.unicode else CAPAS_ASCII
        cav = self.plan.cavado
        detalles = self.detalles
        filas = []
        visibles = min(PROF, self.alto - 1 - self.oy)
        cache_color = {}
        for gy in range(visibles):
            tramos = []
            actual, ini, buf = None, 0, []
            for sx in range(self.ancho):
                gx = sx - self.ox
                dentro = 0 <= gx < ANCHO
                gxc = min(ANCHO - 1, max(0, gx))
                if dentro and cav(gx, gy):
                    celda = None
                else:
                    tipo = self.plan.tipo(gxc, gy)
                    ch = capas[tipo]
                    col = self.colores_tierra[tipo]
                    det = detalles.get((gx, gy)) if dentro else None
                    if det and self.unicode:
                        ch, nombre = det
                        col = cache_color.get(nombre)
                        if col is None:
                            col = cache_color[nombre] = color(nombre)
                    elif dentro and (cav(gx - 1, gy) or cav(gx + 1, gy) or cav(gx, gy - 1)
                                     or cav(gx, gy + 1)):
                        col = self.colores_borde[tipo]
                    elif tipo == ARENA and (sx * 7 + gy * 13) % 29 == 0:
                        ch = "·" if self.unicode else ","
                    elif tipo == ROCA and (sx * 5 + gy * 3) % 7 == 0:
                        ch = "▒" if self.unicode else "#"
                    celda = (ch, col)
                c = celda[1] if celda else None
                if c != actual or (celda is None) != (actual is None):
                    if actual is not None:
                        tramos.append((ini, "".join(buf), actual))
                    actual, ini, buf = c, sx, []
                if celda:
                    buf.append(celda[0])
            if actual is not None:
                tramos.append((ini, "".join(buf), actual))
            filas.append(tramos)
        self._cache_tierra = (clave, filas)
        return filas

    def dibujar_tierra(self):
        poner = self.pantalla.poner
        for gy, tramos in enumerate(self._tierra()):
            sy = self.oy + gy
            for x, t, c in tramos:
                poner(sy, x, t, c, None)

    def _muebles(self, s):
        """Muebles de una sala que ya han aparecido hoy, listos para pintar."""
        dia = int(self.dia)
        clave = (s.clave, dia, self.unicode)
        if clave in self._muebles_cache:
            return self._muebles_cache[clave]
        lista = list(MU.de_sala(s))
        cfg = next((c for c in self.salas_cfg if c["clave"] == s.clave), None)
        for mu in (cfg or {}).get("muebles", []):
            try:
                d = mu.get("dia", 0)
                if mu.get("fecha"):
                    d = (_fecha(mu["fecha"]) - self.fundacion).days
                lista.append((mu.get("nombre", "algo nuevo"), mu["arte"], mu.get("mascara"),
                              mu.get("color", "blanco"), int(mu.get("x", 2)),
                              mu.get("sitio", "suelo"), d))
            except (KeyError, ValueError):
                continue
        # si un mueble sustituye a otro en el mismo sitio, gana el más nuevo
        visibles = {}
        for nombre, arte, masc, col, dx, sitio, d in lista:
            if d <= dia:
                visibles[(dx, sitio)] = (arte, masc, col, dx, sitio)
        out = []
        for arte, masc, col, dx, sitio in visibles.values():
            al = lineas(arte) if "\n" in arte else [arte]
            cu = construir(al, mascara_lineas(masc, len(al)), pintor_fijo(col), solido=False)
            x = s.x0 + (dx if dx >= 0 else s.ancho + dx - cu.ancho + 1)
            y = s.piso - cu.alto + 1 if sitio == "suelo" else s.y0 + 2
            out.append((cu, x, y))
        if len(self._muebles_cache) > 50:
            self._muebles_cache.clear()
        self._muebles_cache[clave] = out
        return out

    def dibujar_salas(self):
        cumple_en = {}
        for h in self.hormigas.values():
            if h.nombre in self.cumples:
                cumple_en.setdefault(h.sala, []).append(h.nombre)
        for s in self.salas:
            sx, sy = self.a_pantalla(s.x0, s.y0)
            col = color(s.color) if s.color else color("blanco")
            DE.dibujar_sala(self, s, " y ".join(cumple_en.get(s.clave, [])) or None)
            etiqueta = s.nombre[:s.ancho - 6]
            marco = ("╡ %s ╞" if self.unicode else "[ %s ]") % etiqueta
            self.texto(sy, sx + (s.ancho - len(marco)) // 2, marco, col if s.principal else color("blanco"))
            for cu, x, y in self._muebles(s):
                gx, gy = self.a_pantalla(x, y)
                self.blit(cu, gx, gy)
            if s.clave == "planta2" and int(self.t * 2) % 4 == 0:
                fx, fy = self.a_pantalla(s.x0 + 6, s.piso - 4)
                self.texto(fy, fx, "°", color("C"))  # burbuja en la fuente
            if s.clave == "museo":
                hallados = [o for o in self.plan.objetos if o[5] <= self.dia]
                vitrina = "  ".join(o[3] for o in hallados)[:s.ancho - 4] or "(vacío)"
                self.texto(sy + 3, sx + 2, vitrina, color("Y"))
            if s.clave == "despensa":
                lleno = min(1.0, (self.dia - self.plan._obra_sala["despensa"].fin) / 150)
                self.texto(sy + s.alto - 1, sx + 14, "°" * max(1, int((s.ancho - 16) * lleno)),
                           color("amarillo"))
            if "navidad" in self.decoraciones and s.principal or ("navidad" in self.decoraciones
                                                                  and s.clave == "comedor"):
                for k in range(2, s.ancho - 2, 3):
                    if int(self.t * 2 + k) % 3:
                        self.texto(sy + 1, sx + k, "*", color("RYGB"[k % 4]))
            if "halloween" in self.decoraciones:
                self.texto(sy + 1, sx + 1, "╱╲" if self.unicode else "/\\", color("s"))
        for x, y, nombre, icono, col, dia in self.plan.objetos:
            if dia <= self.dia:
                sx, sy = self.a_pantalla(x, y)
                self.texto(sy, sx, icono, color(col))

    def dibujar_nombres(self, etiquetas):
        """Los nombres van siempre encima de todo. Si dos chocan, uno sube una fila."""
        ocupado = {}
        for x, y, texto, col in sorted(etiquetas, key=lambda e: (e[1], e[0])):
            x0, x1 = x, x + len(texto)
            for fila in (y, y - 1, y - 2, y + 1):
                usados = ocupado.setdefault(fila, [])
                if all(x1 + 1 <= a or x0 >= b + 1 for a, b in usados):
                    break
            else:
                fila = y
            ocupado.setdefault(fila, []).append((x0, x1))
            fondo = self.fondo_cielo if fila < self.suelo_y else None
            self.texto(fila, x0, texto, col, fondo)

    def dibujar_hud(self):
        """Arriba: la fecha a la izquierda y la hora en grande a la derecha."""
        W = self.ancho
        a = self.ahora
        f = self.fondo_cielo
        fecha = "%s, %d de %s de %d" % (DIAS_LARGOS[a.weekday()], a.day, MESES_LARGOS[a.month - 1], a.year)
        icono = ("☂" if self.lluvia else "☁" if self.tiempo_hoy.nubes > 0.6 else
                 "☾" if self.de_noche else "☀") if self.unicode else ""
        self.texto(0, 1, fecha, color("W"), f)
        self.texto(1, 1, "Día %d del hormiguero · %s · %s %.0f °C" % (
            int(self.dia), self.estacion, icono, self.temperatura), color("blanco"), f)
        if self.pausa_texto:
            self.texto(2, 1, " ⏸ %s " % self.pausa_texto, color("negro"), Fondo(229, 3))
        elif self.demo_texto:
            self.texto(2, 1, self.demo_texto, color("s"), f)
        filas = fuente.renderizar(a.strftime("%H:%M"), "bloque" if self.unicode else "#", 1)
        x = W - len(filas[0]) - 2
        for i, fila in enumerate(filas):
            self.texto(i, x, fila, color("W"), f)

    def dibujar_estado(self):
        """Abajo: sólo el diario (con lo que acaba de pasar, si es reciente)."""
        W = self.ancho
        self.actualizar_diario()
        y = self.alto - 1
        if self.noticias and self.t - self.noticias[-1][2] < 25:
            n = self.noticias[-1]
            t = " ¡Ahora! · %s" % n[1]
            self.pantalla.poner(y, 0, t[:W - 1], color("amarillo_brillante"), None)
        elif self.diario:
            recientes = self.diario[-4:] + [(n[0], n[1]) for n in self.noticias[-4:]]
            e = recientes[-1 - int(self.t / 8) % len(recientes)]
            t = " Día %d · %s" % (e[0], e[1])
            self.pantalla.poner(y, 0, t[:W - 1], color("arena"), None)

    def actualizar_diario(self):
        hoy = self.ahora.date()
        if self._diario_dia == (hoy, int(self.dia * 24)):
            return
        self._diario_dia = (hoy, int(self.dia * 24))
        ev = []
        fundadores = [p["nombre"] for p in self.personas if not p["alta"] or p["alta"] <= self.fundacion]
        ev.append((0, 0, "Se funda el hormiguero%s: %s." % (self.de_quien, ", ".join(fundadores))))
        for o in self.plan.obras:
            if o.fin > self.dia or o.ini < 0:
                continue
            d = int(o.fin)
            if o.tipo == "sala":
                ev.append((d, o.fin, "Inauguran: %s." % o.sala.nombre))
            elif o.tipo == "salida":
                ev.append((d, o.fin, "Abren una segunda salida a la superficie."))
            elif o.tipo == "rampa":
                ev.append((d, o.fin, "Terminan %s." % o.nombre))
            if o.roca:
                ev.append((d, o.fin - 0.01, "¡Han atravesado una roca!"))
            if o.objeto:
                ev.append((d, o.fin + 0.01, "Hallazgo: %s." % o.objeto[2]))
        for s in self.plan.salas_todas:
            cfg = next((c for c in self.salas_cfg if c["clave"] == s.clave), None)
            lista = list(MU.de_sala(s))
            for nombre, _a, _m, _c, _x, _s, d in lista:
                if 0 < d <= self.dia:
                    ev.append((d, d + 0.5, "%s: %s." % (s.nombre, nombre)))
            for mu in (cfg or {}).get("muebles", []):
                d = mu.get("dia", 0)
                if mu.get("fecha"):
                    try:
                        d = (_fecha(mu["fecha"]) - self.fundacion).days
                    except ValueError:
                        continue
                if 0 < d <= self.dia:
                    ev.append((d, d + 0.5, "%s: %s." % (s.nombre, mu.get("nombre", "algo nuevo"))))
        dias = int(self.dia)
        # los días ya calculados se guardan (si no cambia la gente ni el calendario)
        firma = (id(self.fiestas), tuple((p["nombre"], str(p.get("cumple")), p["alta"]) for p in self.personas),
                 tuple((d["nombre"], d["fecha"]) for d in self.idos_cfg))
        if getattr(self, "_dias_firma", None) != firma or dias < len(getattr(self, "_dias_ev", [])) - 1:
            self._dias_firma = firma
            self._dias_ev = []
            self._dias_seco = 0
        seco = self._dias_seco
        for k in range(len(self._dias_ev), dias + 1):
            antes = len(ev)
            f = self.fundacion + datetime.timedelta(days=k)
            for fi in self.fiestas:
                if fi.empieza(f):
                    ev.append((k, k, fi.mensaje))
            for p in self.personas:
                if F.es_cumple(p, f):
                    ev.append((k, k + 0.1, "¡Cumpleaños de %s! Hay tarta arriba." % p["nombre"]))
                if p["alta"] == f and k > 0:
                    ev.append((k, k + 0.2, "Llega %s al hormiguero. ¡Bienvenida/o!" % p["nombre"]))
            for d in self.idos_cfg:
                if d["fecha"] == f:
                    ev.append((k, k + 0.2, "%s se va del hormiguero. Gone, but not forgotten." % d["nombre"]))
            tdia = T.tiempo_del_dia(f, self.semilla)
            if tdia.llueve:
                if seco >= 25:
                    ev.append((k, k + 0.3, "¡Por fin llueve después de %d días!" % seco))
                if tdia.tormenta:
                    ev.append((k, k + 0.3, "Tormenta. Todas dentro."))
                seco = 0
            else:
                seco += 1
            if tdia.calima:
                ev.append((k, k + 0.3, "Calima: el cielo se pone naranja."))
            if tdia.terral:
                ev.append((k, k + 0.3, "Terral. Hace un calor que derrite."))
            self._dias_ev.append(ev[antes:])
            del ev[antes:]
        self._dias_seco = seco
        for lista in self._dias_ev:
            ev.extend(lista)
        ev.sort(key=lambda e: e[1])
        self.diario = [(e[0], e[2]) for e in ev]

    def dibujar(self):
        p = self.pantalla
        p.nuevo_cuadro()
        if self.alto < 40 or self.ancho < 80:
            p.poner(0, 0, "Terminal demasiado pequeña (mín. 80x40)"[:self.ancho], color("W"), None)
            return
        self.superficie.dibujar_cielo()
        self.dibujar_tierra()
        self.dibujar_salas()
        self.superficie.dibujar_suelo()
        self.vida.dibujar()
        self.superficie.dibujar_pancarta()
        gorro = self.gorro_fiesta
        etiquetas = []
        for h in self.hormigas.values():
            g = "cumple" if h.nombre in self.cumples else gorro
            e = h.dibujar(self, g)
            if e:
                etiquetas.append(e)
        self.dibujar_nombres(etiquetas)
        self.dibujar_hud()
        self.dibujar_estado()
