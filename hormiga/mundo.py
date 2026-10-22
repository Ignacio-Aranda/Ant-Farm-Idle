"""El hormiguero completo: une la tierra, la superficie y las hormigas."""

import datetime
import random

from motor.colores import color

from . import clima_real as CR
from . import fiestas as F
from . import tiempo as T
from .estado import Estado
from .hormigas import COLORES, Hormiga
from .superficie import Superficie
from .vida import Vida
from .tierra import ANCHO, OBRAS, PROF, Plan, clave_de

# cómo se llama cada pieza en el diario («Novedad en Despacho: una planta.»)
PIEZAS_DIARIO = {"escritorio": "un escritorio", "escritorio_grande": "un escritorio grande",
                 "sillon": "un sillón", "sofa": "un sofá", "planta": "una planta",
                 "mesa_reuniones": "una mesa de reuniones", "mesa_comedor": "una mesa de comedor",
                 "nevera": "una nevera", "encimera": "una encimera con cafetera", "fuente": "una fuente de agua",
                 "estanteria": "una estantería", "vitrina": "una vitrina", "sacos": "unos sacos",
                 "cajas": "unas cajas", "setas": "unas setas", "cuadro": "un cuadro", "pantalla": "una pantalla",
                 "pizarra": "una pizarra", "reloj": "un reloj"}


def _fecha(v):
    """Una fecha "AAAA-MM-DD" (o de TOML, también con hora) como date; si no, ValueError."""
    if isinstance(v, datetime.datetime):   # 2026-03-01T09:00:00 sin comillas: vale el día
        return v.date()
    if isinstance(v, datetime.date):
        return v
    return datetime.date.fromisoformat(str(v).strip())


class Mundo:
    def __init__(self, cfg, salas_cfg, idos, fiestas, pantalla, reloj, avisos=None):
        self.cfg = cfg
        self.pantalla = pantalla
        self.reloj = reloj
        # avisos de los ficheros (se rehacen en cada recarga) y del trazado y el dibujo (se quedan)
        self.avisos_carga = avisos if avisos is not None else []
        self.avisos = []
        self.avisos_gente = []   # los de idos.toml y las reuniones, que dependen del día (se rehacen solos)
        # los del dibujo que se rehacen al repintar: los muebles que no caben y el cementerio
        self.avisos_dibujo = {}
        self._avisado = set()
        self.raiz = cfg.get("raiz", ".")
        self.clima = False   # se crea al primer uso (y sólo si el reloj va en hora)
        self.semilla = cfg["general"]["semilla"]
        nombre = str(cfg["general"].get("nombre", "")).strip()
        if nombre[:3].lower() == "el ":   # «de el Taller» -> «del Taller»
            nombre = nombre[3:].strip()
            self.de_quien = " del %s" % nombre if nombre else ""
        else:
            self.de_quien = " de %s" % nombre if nombre else ""
        self.fundacion = _fecha(cfg["general"]["fundacion"])
        # lo que sobrevive a los reinicios (local/estado.json); sólo con el reloj de verdad,
        # nunca en la demo, con otra fecha ni al hacer capturas
        self.estado = Estado(self.raiz, self.fundacion.isoformat(), self.semilla) \
            if getattr(reloj, "real", False) else None
        if self.estado is not None:   # cavar: si config.toml no se puede leer, como la última vez
            nido = cfg.setdefault("nido", {})
            if not cfg.get("config_ilegible"):
                self.estado.cavar = "fecha" if str(nido.get("cavar", "encendido")).lower() == "fecha" else "encendido"
            elif self.estado.cavar:
                nido["cavar"] = self.estado.cavar
        self.fiestas = fiestas
        self.t = 0.0
        self.contexto_cada = 1.0
        self.demo_texto = None
        self.pausa_texto = None
        self.hormigas = {}
        self.cargar_gente(salas_cfg, idos)
        nido = cfg.get("nido", {})
        self.tipos = cfg.get("tipos", {})
        nombres_obras = nido.get("obras")
        obras = [dict(o) for o in OBRAS]
        if nombres_obras is not None:   # sin mirar mayúsculas, tildes ni espacios ("Almacén" es almacen)
            por_clave = {clave_de(o["clave"]): o for o in OBRAS}
            obras = [dict(por_clave.get(clave_de(n)) or {"clave": clave_de(n), "nombre": str(n).strip(), "ancho": 22})
                     for n in nombres_obras]
        tipo_de = {clave_de(t): t for t in self.tipos}   # el tipo de cada obra, el de su nombre
        for o in obras:
            o["tipo"] = tipo_de.get(clave_de(o.get("tipo", o["clave"])), o.get("tipo", o["clave"]))
            tipo = self.tipos.get(o["tipo"], {})
            o["funcion"] = tipo.get("funcion", "otra")
            o["minimo"] = tipo.get("ancho_minimo", 0)   # lo que necesitan sus muebles (lo pone pixel/app.py)
        sur = float(cfg.get("ciudad", {}).get("lat", T.MALAGA[0])) < 0
        self.plan = Plan(self.semilla, self.fundacion, self.salas_cfg, obras=obras,
                         entrada=int(nido.get("entrada", 20)), sur=sur)
        self.avisos.extend(self.plan.avisos)
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
                    self.avisos_carga.append("%s: %s: fecha de alta mal escrita (%s), usa AAAA-MM-DD"
                                             % (s.get("fichero", "salas"), q["nombre"], q["alta"]))
                    q["alta"] = None
                self.personas.append(q)
        self.idos_cfg = []
        for d in idos:
            q = dict(d)
            q["nombre"] = str(q.get("nombre", "?")).strip()
            try:
                q["fecha"] = _fecha(q["fecha"]) if q.get("fecha") else None
            except ValueError:
                self.avisos_carga.append("idos.toml: %s: fecha mal escrita (%s), usa AAAA-MM-DD"
                                         % (q["nombre"], q["fecha"]))
                q["fecha"] = None
            self.idos_cfg.append(q)
        # las hormigas no se vuelven a crear: actualizar_contexto quita a quien ya no está,
        # añade a quien llega y cambia de sala (o de color) a las demás sin moverlas
        self._diario_dia = None

    def todos_los_avisos(self):
        """Los avisos de los ficheros, los de idos.toml, los del trazado y el dibujo y el del
        tiempo real (si OpenWeather no acepta la clave), sin repetir."""
        dibujo = [a for avisos in self.avisos_dibujo.values() for a in avisos]
        tiempo = [a for a in [self.clima and self.clima.aviso()] if a]
        return list(dict.fromkeys(self.avisos_carga + self.avisos + self.avisos_gente + dibujo + tiempo))

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

    def _tiempo_real(self):
        """El tiempo de OpenWeather, sólo si el reloj va en hora (no en demo ni en otra fecha)."""
        zona = self.cfg.get("ciudad", {}).get("zona_horaria")
        if abs((self.ahora - T.ahora(zona)).total_seconds()) > 300:
            return None
        if self.clima is False:
            self.clima = CR.desde_config(self.cfg, self.raiz)
        return self.clima.actual() if self.clima else None

    def cava_encendido(self):
        """¿Las obras avanzan sólo mientras está en marcha? (no en demo ni con otra fecha)"""
        modo = str(self.cfg.get("nido", {}).get("cavar", "encendido")).lower()
        return modo == "encendido" and self.estado is not None

    def _dia_obras(self):
        """Hasta dónde llegan las obras, en días de trabajo: el tiempo que lleva el hormiguero
        en marcha (guardado en local/estado.json), o los días desde la fundación."""
        if not self.cava_encendido():
            return self.dia
        e = self.estado
        e.avanzar(self.ahora)
        for i, o in enumerate(self.plan.obras):   # apunta qué día se termina cada obra (para el diario)
            if o.ini >= 0 and o.fin <= e.dias and e.acabar("%d %s" % (i, o.nombre), self.dia):
                # al arrancar aún no hay hormigas: se guarda sin tocar dónde estaba cada una
                e.guardar(self.hormigas.values() if self.hormigas else None)
        return e.dias

    def actualizar_contexto(self, forzar=False):
        self.ahora = self.reloj()
        hoy = self.ahora.date()
        inicio = datetime.datetime.combine(self.fundacion, datetime.time())
        self.dia = max(0.0, (self.ahora - inicio).total_seconds() / 86400)
        self.dia_obras = self._dia_obras()
        self.plan.actualizar(self.dia_obras)
        ciudad = self.cfg.get("ciudad", {})
        lat, lon = float(ciudad.get("lat", T.MALAGA[0])), float(ciudad.get("lon", T.MALAGA[1]))
        forzado = self.cfg.get("tiempo_forzado")
        real = None if forzado else self._tiempo_real()
        self.tiempo_hoy = (T.TiempoForzado(forzado) if forzado else real) or T.tiempo_del_dia(hoy, self.semilla)
        self.sol_hoy = (real and real.sol) or T.sol(hoy, lat, lon, ciudad.get("zona_horaria"))
        mins = self.ahora.hour * 60 + self.ahora.minute
        a, p = self.sol_hoy
        self.de_noche = not (a <= mins < p)
        self.lluvia = self.tiempo_hoy.lluvia(mins)
        self.nieve = self.tiempo_hoy.nieve and self.lluvia > 0
        # nieve en el suelo: mientras nieva y hasta un día después (si no hace calor)
        self.nevado = self.nieve or bool(real and self.clima.nevo_hace(24) and self.tiempo_hoy.temp < 5)
        self.temperatura = self.tiempo_hoy.temperatura(mins)
        self.estacion = T.estacion(hoy, sur=lat < 0)
        # la naturaleza (flores, hojas y frutos, bichos) va con las estaciones: en el hemisferio
        # sur, con el calendario desplazado medio año
        natural = hoy + datetime.timedelta(days=182) if lat < 0 else hoy
        self.dia_natural, self.mes_natural = natural.timetuple().tm_yday, natural.month
        if forzar or int(self.t) % 30 == 0:
            if forzado:   # --tiempo: charcos, caracoles y arcoíris van con el tiempo elegido
                self.llovio = self.llovio_semana = self.tiempo_hoy.llueve
            elif real:
                self.llovio = self.clima.llovio_hace(8)
                self.llovio_semana = self.clima.llovio_hace(96)
            else:
                self.llovio = T.llovio_hace(self.ahora, 8, self.semilla)
                self.llovio_semana = any(T.tiempo_del_dia(hoy - datetime.timedelta(d), self.semilla).llueve
                                         for d in range(4))
        act = F.activas(self.fiestas, hoy)
        self.decoraciones = {f.decoracion for f in act}
        self.fiesta_mensaje = act[-1].mensaje if act else None
        self.gorro_fiesta = next((f.gorro for f in reversed(act) if f.gorro), None)

        self.salas = self.plan.salas(self.dia_obras)
        self.sala_por_clave = {s.clave: s for s in self.salas}
        self.sala_por_funcion = {}
        for s in self.salas:
            self.sala_por_funcion.setdefault(s.funcion, s)
        self.frente = self.plan.frente(self.dia_obras)
        self.salidas_x_grid = self.plan.salidas(self.dia_obras)
        self.salidas_x = [self.ox + x for x in self.salidas_x_grid]

        # quién está y quién se ha ido
        idos_hoy = [d for d in self.idos_cfg if not d["fecha"] or d["fecha"] <= hoy]
        self.idos = [d["nombre"] for d in idos_hoy]
        nombres_idos = {n.lower() for n in self.idos}
        presentes = [p for p in self.personas
                     if (not p["alta"] or p["alta"] <= hoy) and p["nombre"].lower() not in nombres_idos]
        # quien se va más adelante sigue en su sala hasta ese día: si ya no está en ninguna, se avisa
        en_salas = {p["nombre"].lower() for p in self.personas}
        self.avisos_gente = ["idos.toml: %s se va el %s, pero ya no está en ninguna sala; "
                             "déjalo en la suya hasta ese día" % (d["nombre"], d["fecha"].isoformat())
                             for d in self.idos_cfg
                             if d["fecha"] and d["fecha"] > hoy and d["nombre"].lower() not in en_salas]
        self.avisos_gente += self._sin_convocados(presentes)
        self.cumples = [p["nombre"] for p in presentes if F.es_cumple(p, hoy)]
        self.x_cumple = self._sitio_tarta()
        vivos = {p["nombre"] for p in presentes}
        # Halloween: los que se fueron vuelven como hormigas esqueleto (del 26 al 31 de octubre)
        for p in self.esqueletos(hoy, idos_hoy):
            vivos.add(p["nombre"])
            presentes.append(p)
        for n in list(self.hormigas):
            if n not in vivos:   # antes suelta lo que llevaba y lo que estaba haciendo
                self.hormigas.pop(n).liberar(self)
        # el color de quien no tiene uno fijo: el que ya tenía o, si es nueva, el menos usado,
        # contando los fijos y los ya guardados de todas las que están
        usados = [p["color"] for p in presentes if p.get("color")]
        if self.estado is not None:
            usados += [self.estado.colores[p["nombre"]] for p in presentes
                       if not p.get("color") and not p.get("esqueleto") and p["nombre"] in self.estado.colores]
        for i, p in enumerate(presentes):
            if not p.get("color") and self.estado is not None and not p.get("esqueleto"):
                nueva = p["nombre"] not in self.estado.colores
                p = dict(p, color=self.estado.color(p["nombre"], usados, COLORES))
                if nueva:
                    usados.append(p["color"])
            h = self.hormigas.get(p["nombre"])
            if h is None:
                h = self.hormigas[p["nombre"]] = Hormiga(p, i, self)
                donde = self.estado.posiciones.get(p["nombre"]) if self.estado else None
                if donde and self.plan.suelo_en(*donde):   # sigue donde estaba antes de reiniciar
                    h.x, h.y = donde
            elif h.sala != p["sala"] or h.persona != p:
                h.persona, h.sala = p, p["sala"]  # la han cambiado de sala
                if p.get("color"):
                    h.color = color(p["color"])

    def _sitio_tarta(self):
        """Dónde va la tarta: junto a la entrada, en el lado donde quepa (con los regalos ocupa ~20
        columnas) y, si no, lo más cerca posible; nunca encima del cementerio (su sitio lo apunta
        el dibujo en zona_cementerio) ni de los montículos de las salidas."""
        e = self.plan.entrada
        zonas = [(sx - 9, sx + 9) for sx in self.salidas_x_grid]
        if getattr(self, "zona_cementerio", None):
            zonas.append(self.zona_cementerio)

        def libre(x):
            return 3 <= x and x + 20 <= ANCHO - 3 and all(x + 20 < a or x > b for a, b in zonas)
        candidatos = [e + 30, e - 50] + sorted(range(3, ANCHO - 22), key=lambda x: abs(x - e - 30))
        return next((x for x in candidatos if libre(x)), e + 30 if e + 50 <= ANCHO - 3 else max(3, e - 50))

    def _sin_convocados(self, presentes):
        """Avisos de las reuniones que hoy no convocan a nadie que esté (una sala sin gente,
        o gente que ya se fue o que aún no ha llegado): no se hacen."""
        nombres = {p["nombre"].lower() for p in presentes}
        salas = {p["sala"] for p in presentes}
        nombre_sala = {c["clave"]: c["nombre"] for c in self.salas_cfg}
        out = []
        for cfg in self.salas_cfg:
            for r in cfg.get("reuniones", []):
                quien = r.get("quien", "todos")
                if isinstance(quien, list):
                    if any(n.lower() in nombres for n in quien):
                        continue
                    motivo = "no está %s" % " ni ".join(quien)
                elif quien == "todos" or quien in salas:
                    continue
                else:
                    motivo = "en la sala %s no hay nadie" % nombre_sala.get(quien, quien)
                out.append("%s: reunión «%s»: hoy no convoca a nadie (%s)"
                           % (cfg.get("fichero", "salas"), r.get("nombre", "Reunión"), motivo))
        return out

    # ------------------------------------------------------------ noticias

    def noticia(self, texto):
        self.noticias.append((int(self.dia), texto, self.t))
        self.noticias = self.noticias[-30:]

    def vida_entregada(self, h, cosa):
        destino = self.almacen_comida()
        destino = ("la sala %s" % destino.nombre) if destino else "el nido"
        if cosa.peso >= 2:
            ayudantes = [o.nombre for o in self.hormigas.values()
                         if o.escoltando and o.escoltando[0] is h]
            quienes = [h.nombre] + ayudantes
            texto = (", ".join(quienes[:-1]) + " y " + quienes[-1]) if len(quienes) > 1 else quienes[0]
            verbo = "han" if len(quienes) > 1 else "ha"
            self.noticia("%s %s guardado %s en %s." % (texto, verbo, cosa.nombre, destino))
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
                try:   # ya vienen comprobadas al cargar; aun así, una mal escrita no tumba el hormiguero
                    h, mi = (int(v) for v in str(r.get("hora", "10:00")).split(":"))
                    dia = str(r.get("dia", "todos")).lower()
                    inicio = ahora.replace(hour=h, minute=mi, second=0, microsecond=0)
                    fin = inicio + datetime.timedelta(minutes=float(r.get("minutos", 60)))
                except (TypeError, ValueError, OverflowError):
                    continue
                if dia == "todos":
                    if not laborable:
                        continue
                elif dia.replace("miercoles", "miércoles") != dias[ahora.weekday()]:
                    continue
                clave = (ahora.date(), cfg["clave"], r.get("nombre", ""), h, mi)
                if not (inicio <= ahora < fin) or clave in self._citas_hechas:
                    continue
                self._citas_hechas.add(clave)
                quien = r.get("quien", "todos")
                hs = [x for x in self.hormigas.values() if not x.esqueleto]   # los esqueletos, de paseo
                if isinstance(quien, list):
                    nombres = {n.lower() for n in quien}
                    invitadas = [x for x in hs if x.nombre.lower() in nombres]
                elif quien == "todos":
                    invitadas = hs
                else:
                    invitadas = [x for x in hs if x.sala == str(quien).lower()]
                if not invitadas:   # no hay nadie a quien convocar (sale un aviso): no se hace
                    continue
                for x in invitadas:
                    x.convocar(self, sala, fin, "reunion")
                self.noticia("%s en la sala %s." % (r.get("nombre", "Reunión"), sala.nombre))
        # el jefe llama a alguien al despacho de vez en cuando (días laborables, horario de oficina)
        jefe = next((c for c in self.salas_cfg if c.get("jefe")), None)
        ini, fin = self._franja("jornada", "09:00-18:00")
        hora = ahora.hour + ahora.minute / 60
        if not jefe or not laborable or not ini <= hora < fin:
            return
        despacho = self.sala_por_clave.get(jefe["clave"])
        vivas = [x for x in self.hormigas.values() if not x.esqueleto]   # los esqueletos ni llaman ni van
        jefes = [x for x in vivas if x.sala == jefe["clave"]]
        otras = [x for x in vivas if x.sala != jefe["clave"] and not x.cita
                 and x.carga_cosa is None and not x.escoltando]
        if despacho and jefes and otras and self._espera_jefe <= 0:
            self._espera_jefe = self.vida.rng.uniform(900, 2400)
            x = self.vida.rng.choice(otras)
            x.convocar(self, despacho, ahora + datetime.timedelta(minutes=self.vida.rng.uniform(5, 20)),
                       "despacho")
            self.noticia("%s llama a %s al despacho." % (jefes[0].nombre, x.nombre))

    def _franja(self, clave, defecto):
        """Una franja horaria de [horario] en config.toml, "HH:MM-HH:MM", en horas decimales."""
        texto = str(self.cfg.get("horario", {}).get(clave, defecto))
        for t in (texto, defecto):   # ya viene comprobada al cargar; aun así, una mala no tumba nada
            try:
                ini, fin = (v.strip() for v in t.split("-"))
                ini, fin = (int(h) + int(m) / 60 for h, m in (ini.split(":"), fin.split(":")))
                if 0 <= ini < fin <= 24:
                    return ini, fin
            except ValueError:
                pass
            if t == texto and ("horario", clave) not in self._avisado:
                self._avisado.add(("horario", clave))
                self.avisos.append("horario: %s mal escrito (%s)" % (clave, texto))
        return (0, 0)

    def ganas_de_comer(self, hora):
        """Cuánto les apetece ir al comedor a esta hora (según el horario)."""
        a, b = self._franja("comida", "13:30-15:30")
        if a <= hora <= b:
            return 12.0
        a, b = self._franja("desayuno", "10:30-11:00")
        return 5.0 if a <= hora <= b else 1.0

    def sala_funcion(self, funcion):
        """La primera sala con esa función que ya existe (o None)."""
        return self.sala_por_funcion.get(funcion)

    def refugio(self):
        """Donde se juntan: el comedor, o si no hay, la primera sala que haya."""
        return self.sala_funcion("comedor") or (self.salas[0] if self.salas else None)

    def almacen_comida(self):
        return self.sala_funcion("despensa") or self.refugio()

    def muebles_de(self, sala):
        """Muebles de una sala: los de su tipo más los que añade su fichero."""
        lista = list(self.tipos.get(sala.tipo, {}).get("muebles", []))
        cfg = next((c for c in self.salas_cfg if c["clave"] == sala.clave), None)
        if cfg:
            lista += cfg.get("muebles", [])
        return lista

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
            if self.estado is not None and self.estado.toca_guardar():
                self.estado.guardar(self.hormigas.values())
        for h in self.hormigas.values():
            h.actualizar(self, dt)
        self.vida.actualizar(dt)
        self.superficie.actualizar(dt)

    # ------------------------------------------------------------- diario

    def _eventos_dia(self, k, seco):
        """Lo que pasó el día k del hormiguero: fiestas, cumpleaños, llegadas, idas y el tiempo.
        seco: días seguidos sin llover hasta ayer. Devuelve (eventos, seco)."""
        ev = []
        f = self.fundacion + datetime.timedelta(days=k)
        for fi in self.fiestas:
            if fi.empieza(f):
                ev.append((k, k, fi.mensaje))
        # los que ese día ya se han ido (sin fecha: desde siempre)
        idos = {d["nombre"].lower() for d in self.idos_cfg if not d["fecha"] or d["fecha"] <= f}
        for p in self.personas:
            # la tarta, sólo si ese día está en el hormiguero (ya ha llegado y no se ha ido)
            if F.es_cumple(p, f) and (not p["alta"] or p["alta"] <= f) and p["nombre"].lower() not in idos:
                ev.append((k, k + 0.1, "¡Cumpleaños de %s! Hay tarta arriba." % p["nombre"]))
            if p["alta"] == f and k > 0:
                ev.append((k, k + 0.2, "Llega %s al hormiguero. ¡Bienvenida/o!" % p["nombre"]))
        for d in self.idos_cfg:
            if d["fecha"] == f:
                # la despedida: su epitafio de idos.toml, si lo tiene
                adios = str(d.get("epitafio") or "").strip() or "Gone, but not forgotten"
                j = next((j for j, c in enumerate(adios) if c.isalpha()), 0)   # tras «¡», «¿»...
                adios = adios[:j] + adios[j:j + 1].upper() + adios[j + 1:]
                adios += "" if adios[-1] in ".!?…»\"" else "."
                ev.append((k, k + 0.2, "%s se va del hormiguero. %s" % (d["nombre"], adios)))
        if (f.month, f.day) == (10, 26) and idos and self.cfg.get("halloween", {}).get("esqueletos") is True:
            ev.append((k, k + 0.2, "¡Los que se fueron salen del cementerio! Pasearán por aquí hasta Halloween."))
        tdia = self._tiempo_de(f)
        if tdia is None:
            return ev, seco
        if tdia.llueve:
            if seco >= 25:
                ev.append((k, k + 0.3, "¡Por fin llueve después de %d días!" % seco))
            if tdia.tormenta:
                ev.append((k, k + 0.3, "Tormenta. Todas dentro."))
            seco = 0
        else:
            seco += 1
        if tdia.nieve:
            ev.append((k, k + 0.3, "¡Nieva! Todo se queda blanco."))
        if tdia.calima:
            ev.append((k, k + 0.3, "Calima: el cielo se pone naranja."))
        if tdia.terral:
            ev.append((k, k + 0.3, "Terral. Hace un calor que derrite."))
        return ev, seco

    def esqueletos(self, hoy, idos_hoy):
        """Con [halloween] esqueletos = true, del 26 al 31 de octubre los que se fueron vuelven."""
        if self.cfg.get("halloween", {}).get("esqueletos", False) is not True:   # sólo con true
            return []
        if not (hoy.month == 10 and 26 <= hoy.day <= 31):
            return []
        casas = [s.clave for s in self.plan.salas_todas if s.principal] or [None]
        out = []
        for d in idos_hoy:
            nombre = d["nombre"]
            rng = random.Random("esqueleto-%s" % nombre)
            out.append({"nombre": nombre + " ☠", "sala": rng.choice(casas), "esqueleto": True, "alta": None})
        return out

    def _tiempo_de(self, fecha):
        """Cómo fue el tiempo de un día: el elegido con --tiempo (hoy), lo apuntado de OpenWeather
        si se usa o, si no, el de respaldo."""
        if self.cfg.get("tiempo_forzado") and fecha == self.ahora.date():
            return self.tiempo_hoy
        if self.clima:
            d = self.clima.dia(fecha)
            if d is None:
                return None
            class Dia:
                terral = False
            dia = Dia()
            for k in ("llueve", "tormenta", "nieve", "calima"):
                setattr(dia, k, bool(d.get(k)))
            return dia
        return T.tiempo_del_dia(fecha, self.semilla)

    def actualizar_diario(self):
        hoy = self.ahora.date()
        if self._diario_dia == (hoy, int(self.dia * 24)):
            return
        self._diario_dia = (hoy, int(self.dia * 24))
        ev = []
        # los fundadores: quien está el primer día (ya ha llegado y no se ha ido)
        idos = {d["nombre"].lower() for d in self.idos_cfg if not d["fecha"] or d["fecha"] <= self.fundacion}
        fundadores = [p["nombre"] for p in self.personas
                      if (not p["alta"] or p["alta"] <= self.fundacion) and p["nombre"].lower() not in idos]
        quienes = (": " + ", ".join(fundadores)) if fundadores else ""
        ev.append((0, 0, "Se funda el hormiguero%s%s." % (self.de_quien, quienes)))
        ultima = None
        inaugurada = {}   # el día en que se termina cada sala de las obras
        for i, o in enumerate(self.plan.obras):
            if o.fin > self.dia_obras or o.ini < 0:
                continue
            d = int(o.fin)
            if self.cava_encendido():   # cavando sólo encendido: el día en que de verdad se terminó
                d = self.estado.acabadas.get("%d %s" % (i, o.nombre))
                if d is None:
                    continue
            ultima = d
            orden = d + 0.5 + o.fin / 10000   # dentro del día, en el orden en que se terminaron
            if o.tipo == "sala":
                inaugurada[o.sala.clave] = d
                ev.append((d, orden, "Inauguran: %s." % o.sala.nombre))
            elif o.tipo == "salida":
                ev.append((d, orden, "Abren una segunda salida a la superficie."))
            elif o.tipo == "rampa":
                ev.append((d, orden, "Terminan %s." % o.nombre))
            if o.roca:
                ev.append((d, orden - 0.001, "¡Han atravesado una roca!"))
            if o.objeto:
                ev.append((d, orden + 0.001, "Hallazgo: %s." % o.objeto[2]))
        if self.plan.sin_sitio and ultima is not None and self.plan.obras[-1].fin <= self.dia_obras:
            ev.append((ultima, ultima + 0.9, "Ya no cabe nada más en el hormiguero: se quedan sin hacer %s."
                       % ", ".join(self.plan.sin_sitio)))
        for s in self.plan.salas_todas:
            # los muebles nuevos de una sala de las obras, no antes de que se inaugure
            desde = 0 if s.principal else inaugurada.get(s.clave)
            if desde is None:
                continue
            for mu in self.muebles_de(s):
                try:   # el mismo día en que aparece en el dibujo (pixel/render.py)
                    d = int(mu.get("aparece", 0))
                except (TypeError, ValueError, OverflowError):
                    continue
                d = max(d, desde) if d > 0 else 0
                if 0 < d <= self.dia:
                    pieza = str(mu.get("pieza", "")).strip().lower()
                    que = str(mu.get("nombre") or PIEZAS_DIARIO.get(pieza, pieza or "algo")).strip()
                    ev.append((d, d + 0.6, "Novedad en %s: %s." % (s.nombre, que)))
        dias = int(self.dia)
        # los días ya calculados se guardan (si no cambia la gente ni el calendario)
        firma = (id(self.fiestas), tuple((p["nombre"], str(p.get("cumple")), p["alta"]) for p in self.personas),
                 tuple((d["nombre"], d["fecha"], str(d.get("epitafio"))) for d in self.idos_cfg))
        if getattr(self, "_dias_firma", None) != firma or dias < len(getattr(self, "_dias_ev", [])):
            self._dias_firma = firma
            self._dias_ev = []
            self._dias_seco = 0
        # los días pasados se calculan una vez; el de hoy, cada vez (el tiempo real puede cambiar)
        while len(self._dias_ev) < dias:
            lista, self._dias_seco = self._eventos_dia(len(self._dias_ev), self._dias_seco)
            self._dias_ev.append(lista)
        for lista in self._dias_ev:
            ev.extend(lista)
        ev.extend(self._eventos_dia(dias, self._dias_seco)[0])
        ev.sort(key=lambda e: e[1])
        self.diario = [(e[0], e[2]) for e in ev]
