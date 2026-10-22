"""Pruebas de los scripts de la Pi (instalar-pi.sh y en-pantalla.sh) y de la limpieza del repositorio.

No se ejecuta sudo ni se toca el sistema: la unidad de systemd se genera con un sudo falso que
la guarda en un directorio temporal, y en-pantalla.sh se lanza con un PATH en el que sólo hay
un sudo falso que apunta las órdenes que recibe.
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

BASH = shutil.which("bash")
GIT = shutil.which("git")
SCRIPTS = ("instalar-pi.sh", "en-pantalla.sh")
UNIDAD = "/etc/systemd/system/hormiguero.service"


def leer(nombre):
    return (RAIZ / nombre).read_text(encoding="utf-8")


def necesita_bash():
    if BASH is None:
        raise unittest.SkipTest("no hay bash")


def git(*args):
    """Ejecuta git en el repositorio; si no hay git o no es un repositorio, se salta la prueba."""
    if GIT is None:
        raise unittest.SkipTest("no hay git")
    r = subprocess.run([GIT, "-C", str(RAIZ), *args], capture_output=True, timeout=30)
    if r.returncode not in (0, 1) or (r.returncode == 1 and r.stderr.strip()):
        raise unittest.SkipTest("git no funciona aquí: " + r.stderr.decode("utf-8", "replace"))
    return r


def ficheros_versionados():
    r = git("ls-files", "-z")
    return [n for n in r.stdout.decode("utf-8", "surrogateescape").split("\0") if n]


# --- La unidad de systemd que escribe instalar-pi.sh ---------------------------------------

# Sudo falso (función de bash, que tiene preferencia sobre cualquier programa del PATH):
# sólo admite "sudo tee FICHERO" y guarda lo que recibe en $SALIDA en vez de escribir FICHERO
PRELUDIO_UNIDAD = r"""set -e
DIR="$1"
USUARIO="$2"
SALIDA="$3"
DESTINOS="$4"
sudo() {
    if [ "$1" = tee ] && [ $# -eq 2 ]; then
        printf '%s\n' "$2" >> "$DESTINOS"
        cat > "$SALIDA"
    else
        echo "sudo inesperado: $*" >&2
        return 99
    fi
}
"""


def trozo_unidad():
    """Las líneas de instalar-pi.sh que preparan la ruta y escriben la unidad (hasta el fin del heredoc)."""
    lineas = leer("instalar-pi.sh").splitlines()
    inicio = next(i for i, l in enumerate(lineas) if l.startswith("RUTA="))
    tee = next(i for i, l in enumerate(lineas)
               if "tee" in l and "hormiguero.service" in l and "<<" in l)
    if not inicio < tee:
        raise AssertionError("RUTA= debería prepararse antes de escribir la unidad")
    delimitador = re.search(r"<<-?\s*([\"']?)(\w+)\1", lineas[tee]).group(2)
    fin = next(i for i in range(tee + 1, len(lineas)) if lineas[i].strip() == delimitador)
    return "\n".join(lineas[inicio:fin + 1]) + "\n"


def generar_unidad(dir_repo, usuario="prueba"):
    """Genera la unidad como lo haría instalar-pi.sh con DIR=dir_repo. Devuelve (texto, destinos)."""
    necesita_bash()
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp, "generar.sh")
        salida = Path(tmp, "unidad.service")
        destinos = Path(tmp, "destinos.txt")
        script.write_text(PRELUDIO_UNIDAD + trozo_unidad(), encoding="utf-8")
        entorno = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LANG": "C.UTF-8"}
        r = subprocess.run([BASH, str(script), dir_repo, usuario, str(salida), str(destinos)],
                           cwd=tmp, env=entorno, capture_output=True, timeout=30)
        if r.returncode != 0:
            raise AssertionError("el trozo de instalar-pi.sh falla: "
                                 + r.stderr.decode("utf-8", "replace"))
        return (salida.read_text(encoding="utf-8"),
                destinos.read_text(encoding="utf-8").splitlines())


def leer_unidad(texto):
    """{sección: {clave: [valores]}} de un fichero de unidad de systemd."""
    secciones = {}
    actual = None
    for linea in texto.splitlines():
        l = linea.strip()
        if not l or l.startswith(("#", ";")):
            continue
        if l.startswith("[") and l.endswith("]"):
            actual = secciones.setdefault(l[1:-1], {})
            continue
        if actual is None or "=" not in l:
            raise AssertionError("línea rara en la unidad: " + linea)
        clave, valor = l.split("=", 1)
        actual.setdefault(clave.strip(), []).append(valor.strip())
    return secciones


def quitar_especificadores(texto):
    """Lo que hace systemd con los "%": "%%" es un "%"; cualquier otro "%x" lo cambiaría."""
    def cambio(m):
        if m.group(0) == "%%":
            return "%"
        raise ValueError("especificador sin escapar: " + repr(m.group(0)))
    return re.sub(r"%.?", cambio, texto, flags=re.S)


def quitar_dolares(texto):
    """Lo que hace systemd con los "$" de ExecStart: "$$" es un "$"; "$X" sería una variable."""
    def cambio(m):
        if m.group(0) == "$$":
            return "$"
        raise ValueError("variable sin escapar: " + repr(m.group(0)))
    return re.sub(r"\$.?", cambio, texto, flags=re.S)


ESCAPES_C = {"a": "\a", "b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t", "v": "\v",
             "\\": "\\", '"': '"', "'": "'", "s": " "}


def partir_execstart(linea):
    """Parte el valor de ExecStart= en argumentos como systemd: separa por espacios, quita
    comillas, entiende los escapes de C y luego quita especificadores y "$$"."""
    palabras = []
    i, n = 0, len(linea)
    while True:
        while i < n and linea[i] in " \t":
            i += 1
        if i >= n:
            return palabras
        palabra, comilla = [], None
        while i < n:
            c = linea[i]
            if c == "\\":
                if i + 1 >= n or linea[i + 1] not in ESCAPES_C:
                    raise ValueError("escape que systemd no entiende en: " + linea)
                palabra.append(ESCAPES_C[linea[i + 1]])
                i += 2
                continue
            if comilla:
                if c == comilla:
                    comilla = None
                else:
                    palabra.append(c)
            elif c in "\"'":
                comilla = c
            elif c in " \t":
                break
            else:
                palabra.append(c)
            i += 1
        if comilla:
            raise ValueError("comillas sin cerrar en: " + linea)
        palabras.append(quitar_dolares(quitar_especificadores("".join(palabra))))


class PruebaScriptsSintaxis(unittest.TestCase):
    def test_bash_n(self):
        necesita_bash()
        for nombre in SCRIPTS:
            with self.subTest(script=nombre):
                r = subprocess.run([BASH, "-n", str(RAIZ / nombre)], capture_output=True,
                                   timeout=30)
                self.assertEqual(r.returncode, 0, r.stderr.decode("utf-8", "replace"))

    def test_cabecera_bash_y_fin_de_linea_unix(self):
        # usan cosas de bash (${var//a/b}, trap ... EXIT): no valen con sh; y con \r no arrancan
        for nombre in SCRIPTS:
            with self.subTest(script=nombre):
                datos = (RAIZ / nombre).read_bytes()
                self.assertTrue(datos.startswith((b"#!/bin/bash\n", b"#!/usr/bin/env bash\n")))
                self.assertNotIn(b"\r", datos)

    def test_gitattributes_fuerza_fin_de_linea_unix(self):
        # al clonar con git en Windows (core.autocrlf=true) los .sh no deben llegar con \r
        for nombre in SCRIPTS:
            with self.subTest(script=nombre):
                r = git("check-attr", "eol", "--", nombre)
                self.assertTrue(r.stdout.decode("utf-8").strip().endswith(": eol: lf"), r.stdout)

    def test_ejecutables_en_git(self):
        # el README dice ./en-pantalla.sh: tiene que llegar ejecutable al clonar
        r = git("ls-files", "-s", "--", *SCRIPTS)
        modos = {}
        for linea in r.stdout.decode("utf-8").splitlines():
            datos, nombre = linea.split("\t", 1)
            modos[nombre] = datos.split()[0]
        for nombre in SCRIPTS:
            with self.subTest(script=nombre):
                self.assertEqual(modos.get(nombre), "100755")


class PruebaInstalarPi(unittest.TestCase):
    def test_para_si_algo_falla(self):
        self.assertRegex(leer("instalar-pi.sh"), r"(?m)^set -e\b")

    def test_activa_el_servicio_y_la_pantalla_siempre_encendida(self):
        texto = leer("instalar-pi.sh")
        self.assertIn("systemctl daemon-reload", texto)
        self.assertIn("systemctl enable hormiguero", texto)
        self.assertIn("consoleblank=0", texto)

    def test_trozo_sin_sudo_salvo_tee(self):
        # la prueba sólo reproduce el trozo que escribe la unidad: ahí no debe haber más sudo
        ordenes = [l for l in trozo_unidad().splitlines() if re.match(r"\s*sudo\b", l)]
        self.assertEqual(len(ordenes), 1, ordenes)
        self.assertIn("tee " + UNIDAD, ordenes[0])

    def test_unidad_sin_espacios(self):
        texto, destinos = generar_unidad("/home/pi/Ant-Farm-Idle", "pi")
        self.assertEqual(destinos, [UNIDAD])
        servicio = leer_unidad(texto)["Service"]
        self.assertEqual(servicio["ExecStart"],
                         ['/usr/bin/python3 "/home/pi/Ant-Farm-Idle/hormiguero_fb.py"'])
        self.assertEqual(servicio["WorkingDirectory"], ["/home/pi/Ant-Farm-Idle"])
        self.assertEqual(servicio["EnvironmentFile"], ["-/home/pi/Ant-Farm-Idle/local/entorno"])
        self.assertEqual(servicio["User"], ["pi"])

    def test_unidad_con_espacios_y_caracteres_raros(self):
        with tempfile.TemporaryDirectory() as tmp:
            pruebas = [
                os.path.join(tmp, "Mis cosas", "Ant Farm Idle"),
                os.path.join(tmp, 'raro 100% "comillas" $HOME l\'hormiga \\barra & más'),
            ]
            for dir_repo in pruebas:
                with self.subTest(dir=dir_repo):
                    self.comprobar_unidad(dir_repo)

    def como_systemd(self, funcion, valor):
        try:
            return funcion(valor)
        except ValueError as e:
            self.fail("systemd no entendería " + repr(valor) + ": " + str(e))

    def comprobar_unidad(self, dir_repo):
        texto, destinos = generar_unidad(dir_repo, "usuario de prueba")
        self.assertEqual(destinos, [UNIDAD])
        unidad = leer_unidad(texto)
        self.assertEqual(set(unidad), {"Unit", "Service", "Install"})
        servicio = unidad["Service"]
        # ExecStart con la ruta entre comillas (si no, systemd la parte por los espacios)
        self.assertEqual(len(servicio["ExecStart"]), 1)
        exec_start = servicio["ExecStart"][0]
        self.assertRegex(exec_start, r'^/usr/bin/python3 ".*/hormiguero_fb\.py"$')
        self.assertEqual(self.como_systemd(partir_execstart, exec_start),
                         ["/usr/bin/python3", dir_repo + "/hormiguero_fb.py"])
        self.assertEqual(len(servicio["WorkingDirectory"]), 1)
        self.assertEqual(self.como_systemd(quitar_especificadores,
                                           servicio["WorkingDirectory"][0]), dir_repo)
        # EnvironmentFile opcional ("-"): las variables propias, en local/entorno
        self.assertEqual(len(servicio["EnvironmentFile"]), 1)
        fichero = servicio["EnvironmentFile"][0]
        self.assertTrue(fichero.startswith("-"), fichero)
        self.assertEqual(self.como_systemd(quitar_especificadores, fichero[1:]),
                         dir_repo + "/local/entorno")
        self.assertEqual(servicio["Restart"], ["always"])
        self.assertEqual(servicio["TTYPath"], ["/dev/tty1"])
        self.assertEqual(servicio["StandardInput"], ["tty"])
        self.assertEqual(servicio["User"], ["usuario de prueba"])
        conflictos = " ".join(unidad["Unit"].get("Conflicts", [])).split()
        self.assertIn("getty@tty1.service", conflictos)
        self.assertIn("multi-user.target", " ".join(unidad["Install"].get("WantedBy", [])).split())

    def test_el_programa_del_servicio_existe(self):
        self.assertTrue((RAIZ / "hormiguero_fb.py").is_file())
        texto, _ = generar_unidad(str(RAIZ))
        exec_start = leer_unidad(texto)["Service"]["ExecStart"][0]
        self.assertTrue(Path(partir_execstart(exec_start)[1]).is_file())


# --- en-pantalla.sh con un sudo falso ------------------------------------------------------

SUDO_FALSO = """#!/bin/sh
# sudo falso: apunta la orden (argumentos separados por \\037) y no ejecuta nada
for a in "$@"; do printf '%s\\037' "$a"; done >> "$REGISTRO"
printf '\\n' >> "$REGISTRO"
if [ "$1" = systemd-run ]; then
    case "$MODO" in
        falla) exit 3 ;;
        espera) : > "$MARCA"; exec {sleep} 30 ;;
    esac
fi
exit 0
"""

SEPARADOR = "\x1f"


class PruebaEnPantalla(unittest.TestCase):
    def setUp(self):
        necesita_bash()
        self.tmp = Path(tempfile.mkdtemp(prefix="en pantalla "))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        binarios = self.tmp / "bin"
        binarios.mkdir()
        # en el PATH sólo está el sudo falso y lo que usa el script: el sudo de verdad no se alcanza
        for orden in ("dirname", "cat", "id"):
            real = shutil.which(orden)
            if real is None:
                self.skipTest("falta " + orden)
            os.symlink(real, binarios / orden)
        dormir = shutil.which("sleep")
        if dormir is None or not os.path.exists("/bin/sh"):
            self.skipTest("falta sleep o /bin/sh")
        sudo = binarios / "sudo"
        sudo.write_text(SUDO_FALSO.replace("{sleep}", shlex.quote(dormir)), encoding="utf-8")
        sudo.chmod(0o755)
        self.sudo = sudo
        self.registro = self.tmp / "registro"
        self.marca = self.tmp / "marca"
        self.entorno = {"PATH": str(binarios), "HOME": str(self.tmp), "LANG": "C.UTF-8",
                        "REGISTRO": str(self.registro), "MARCA": str(self.marca), "MODO": "ok"}
        r = subprocess.run([BASH, "-c", "command -v sudo"], env=self.entorno,
                           capture_output=True, timeout=30)
        self.assertEqual(r.stdout.decode().strip(), str(sudo), "no se usaría el sudo falso")

    def orden(self, *args):
        return [BASH, str(RAIZ / "en-pantalla.sh"), *args]

    def lanzar(self, *args, modo="ok"):
        self.entorno["MODO"] = modo
        return subprocess.run(self.orden(*args), env=self.entorno, capture_output=True,
                              timeout=30)

    def llamadas(self):
        if not self.registro.exists():
            return []
        lineas = self.registro.read_text(encoding="utf-8").splitlines()
        return [l.split(SEPARADOR)[:-1] for l in lineas]

    def comprobar_ciclo(self, programa):
        """Para el hormiguero, lanza el programa en tty1 y al acabar lo quita y relanza el hormiguero."""
        llamadas = self.llamadas()
        self.assertTrue(llamadas, "no ha llamado a sudo")
        self.assertEqual(llamadas[0], ["systemctl", "stop", "hormiguero"])
        self.assertEqual(llamadas[-1], ["systemctl", "start", "hormiguero"])
        self.assertEqual(llamadas.count(["systemctl", "start", "hormiguero"]), 1)
        lanzamientos = [i for i, l in enumerate(llamadas) if l and l[0] == "systemd-run"]
        self.assertEqual(len(lanzamientos), 1, llamadas)
        run = llamadas[lanzamientos[0]]
        self.assertIn("--unit=en-pantalla", run)
        self.assertIn("--wait", run)
        propiedades = {run[i + 1] for i, a in enumerate(run[:-1]) if a == "-p"}
        self.assertIn("TTYPath=/dev/tty1", propiedades)
        self.assertIn("StandardInput=tty", propiedades)
        self.assertIn("WorkingDirectory=" + str(RAIZ), propiedades)
        # como el servicio, con las variables de local/entorno (la clave de OpenWeather...)
        self.assertIn("EnvironmentFile=-" + str(RAIZ / "local" / "entorno"), propiedades)
        self.assertTrue(any(p.startswith("User=") and len(p) > 5 for p in propiedades))
        # el programa llega tal cual, con sus argumentos (también los que llevan espacios)
        self.assertEqual(run[-len(programa):], list(programa))
        # al acabar, quita el programa de la pantalla antes de relanzar el hormiguero
        self.assertIn(["systemctl", "stop", "en-pantalla"], llamadas[lanzamientos[0] + 1:-1])

    def test_tiene_trap_de_salida_que_relanza_el_hormiguero(self):
        texto = leer("en-pantalla.sh")
        m = re.search(r"(?m)^\s*trap\s+(\w+)\s+EXIT\b", texto)
        self.assertIsNotNone(m, "falta trap ... EXIT")
        funcion = re.search(r"(?ms)^%s\s*\(\)\s*\{(.*?)^\}" % re.escape(m.group(1)), texto)
        self.assertIsNotNone(funcion, "falta la función " + m.group(1))
        self.assertIn("systemctl start hormiguero", funcion.group(1))
        for senal in ("INT", "TERM", "HUP"):
            with self.subTest(senal=senal):
                self.assertRegex(texto, r"(?m)^\s*trap\s+.*\b%s\b" % senal)

    def test_sin_argumentos_explica_el_uso_y_no_toca_nada(self):
        r = self.lanzar()
        self.assertEqual(r.returncode, 1)
        self.assertIn("Uso", r.stdout.decode("utf-8", "replace"))
        self.assertEqual(self.llamadas(), [])

    def test_lanza_el_programa_y_relanza_el_hormiguero(self):
        programa = ("python3", "hormiguero_fb.py", "--fecha", "2026-12-24", "--hora", "21:00",
                    "texto con espacios")
        r = self.lanzar(*programa)
        self.assertEqual(r.returncode, 0, r.stderr.decode("utf-8", "replace"))
        self.comprobar_ciclo(programa)

    def test_si_el_programa_falla_tambien_relanza_el_hormiguero(self):
        programa = ("python3", "no-existe.py")
        r = self.lanzar(*programa, modo="falla")
        self.assertNotEqual(r.returncode, 0)
        self.comprobar_ciclo(programa)

    def test_ctrl_c_o_corte_relanza_el_hormiguero(self):
        programa = ("python3", "hormiguero_fb.py", "--demo")
        for senal, codigo in ((signal.SIGINT, 130), (signal.SIGTERM, 143), (signal.SIGHUP, 129)):
            with self.subTest(senal=senal.name):
                if signal.getsignal(senal) == signal.SIG_IGN:
                    self.skipTest(senal.name + " llega ignorada: bash no podría atraparla")
                for f in (self.registro, self.marca):
                    if f.exists():
                        f.unlink()
                self.entorno["MODO"] = "espera"
                # en su propia sesión, para mandar la señal a todo el grupo como hace Ctrl+C
                proc = subprocess.Popen(self.orden(*programa), env=self.entorno,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        start_new_session=True)
                self.addCleanup(self.matar, proc)
                limite = time.monotonic() + 15
                while not self.marca.exists() and proc.poll() is None:
                    if time.monotonic() > limite:
                        self.fail("el programa no llegó a lanzarse")
                    time.sleep(0.02)
                self.assertIsNone(proc.poll(), "en-pantalla.sh acabó antes de tiempo")
                os.killpg(proc.pid, senal)
                try:
                    _, err = proc.communicate(timeout=15)
                except subprocess.TimeoutExpired:
                    self.fail("en-pantalla.sh no termina tras " + senal.name)
                self.assertEqual(proc.returncode, codigo, err.decode("utf-8", "replace"))
                self.comprobar_ciclo(programa)

    @staticmethod
    def matar(proc):
        if proc.poll() is None:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait(timeout=15)
        for flujo in (proc.stdout, proc.stderr):
            if flujo:
                flujo.close()


# --- Repositorio limpio ----------------------------------------------------------------------

class PruebaRepositorio(unittest.TestCase):
    def test_gitignore_ignora_local_y_pycache(self):
        reglas = {l.strip() for l in leer(".gitignore").splitlines()}
        self.assertTrue(reglas & {"local/", "/local/", "local", "/local"}, reglas)
        self.assertTrue(reglas & {"__pycache__/", "__pycache__", "**/__pycache__/"}, reglas)

    def test_git_ignora_local_y_pycache(self):
        rutas = ["local/entorno", "local/config.toml", "local/salas/comedor.toml",
                 "__pycache__/x.cpython-311.pyc", "hormiga/__pycache__/app.cpython-313.pyc",
                 "tests/__pycache__/test_scripts.cpython-311.pyc"]
        for ruta in rutas:
            with self.subTest(ruta=ruta):
                r = git("check-ignore", "-q", "--no-index", ruta)
                self.assertEqual(r.returncode, 0, ruta + " no está ignorado")

    def test_nada_versionado_en_local_ni_pycache(self):
        malos = [n for n in ficheros_versionados()
                 if n.startswith("local/") or "__pycache__/" in n or n.endswith(".pyc")]
        self.assertEqual(malos, [])


if __name__ == "__main__":
    unittest.main()
