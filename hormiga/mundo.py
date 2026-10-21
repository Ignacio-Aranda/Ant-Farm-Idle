"""El hormiguero completo: une la tierra, la superficie y las hormigas."""

import datetime

from motor.colores import color

from . import fiestas as F
from . import muebles as MU
from . import tiempo as T
from .hormigas import Hormiga
from .superficie import Superficie
from .vida import Vida
from .tierra import ANCHO, PROF, Plan

DIAS_CORTOS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
DIAS_LARGOS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES_LARGOS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
                "septiembre", "octubre", "noviembre", "diciembre"]
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


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
        self.hormigas = {}
        self.cargar_gente(salas_cfg, idos)
        principales = self.salas_cfg
        self.plan = Plan(self.semilla, self.fundacion, principales)
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
        self.hormigas = {}
        self.actualizar_contexto(forzar=True)
        self._diario_dia = None
        self.diario = []

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
