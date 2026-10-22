# Instalación

En este capítulo vas a instalar el hormiguero en tu ordenador para probarlo y en una
Raspberry Pi para dejarlo siempre puesto en una pantalla.

Puedes hacer solo una de las dos partes. Lo normal es probarlo primero en el ordenador
y, cuando te guste, pasarlo a la Pi.

## Qué necesitas

**En un ordenador** (Windows, macOS o Linux):

- Python 3.11 o más nuevo (en Windows y macOS, la 3.13: mira el paso 1).
- pygame, una librería de Python para dibujar en pantalla.
- El hormiguero (este repositorio).

**En una Raspberry Pi:**

- Una Raspberry Pi 3 o más nueva.
- Una tarjeta microSD (con 8 GB sobra) y su fuente de alimentación.
- Una pantalla con HDMI.
- Un ordenador con el programa Raspberry Pi Imager, para preparar la tarjeta.
- WiFi o cable de red. Después la Pi se maneja desde el ordenador, por SSH.
  No hace falta teclado ni ratón en la Pi.

---

## Parte 1. En un ordenador

### Paso 1. Instala Python

**Windows y macOS.** No instales la última versión de Python: pygame tarda en llegar a
cada versión nueva y, por ahora, funciona hasta la 3.13. Entra en
[python.org/downloads/windows](https://www.python.org/downloads/windows/) (en macOS,
[python.org/downloads/macos](https://www.python.org/downloads/macos/)), busca en la lista
la primera **Python 3.13** y pulsa **Download Windows installer (64-bit)** (en macOS,
**Download macOS installer**). Instálalo. En Windows, marca la casilla
**Add python.exe to PATH** en la primera pantalla del instalador.

**Linux.** Casi siempre viene instalado.

Para ver qué versión tienes, en macOS y Linux:

```bash
python3 --version
```

Y en Windows:

```bash
py --version
```

Tiene que ser la 3.11 o más nueva y, en Windows y macOS, como mucho la 3.13.

### Paso 2. Instala pygame

**Windows:**

```bash
py -m pip install pygame
```

**macOS** (con el Python de python.org):

```bash
python3 -m pip install pygame
```

**Linux.** En Debian, Ubuntu y Raspberry Pi OS, `pip install` suele negarse con un
error que dice `externally-managed-environment`. Tienes dos caminos.

*Opción A: con los paquetes del sistema* (lo más fácil). Instala pygame y la fuente
DejaVu, la misma letra que usa la Pi:

```bash
sudo apt install python3-pygame fonts-dejavu-core
```

*Opción B: con pip, en un entorno aparte.* Sirve en cualquier distribución, pero solo si
tu Python es la 3.11, la 3.12 o la 3.13. Primero, en
Debian y Ubuntu, instala lo necesario para crear entornos:

```bash
sudo apt install python3-venv
```

Crea el entorno en tu carpeta personal:

```bash
python3 -m venv ~/venv-hormiguero
```

E instala pygame dentro:

```bash
~/venv-hormiguero/bin/pip install pygame
```

Si eliges esta opción, en todas las órdenes de esta guía cambia `python3` por
`~/venv-hormiguero/bin/python`.

### Paso 3. Descarga el hormiguero

Hay dos formas. Elige una.

**Con git**, si ya lo tienes instalado (así luego es más fácil actualizarlo):

```bash
git clone https://github.com/Ignacio-Aranda/Ant-Farm-Idle.git
```

Se crea una carpeta llamada `Ant-Farm-Idle`.

**Con un zip** (sin instalar nada más):

1. Entra en <https://github.com/Ignacio-Aranda/Ant-Farm-Idle>.
2. Pulsa el botón verde **Code** y luego **Download ZIP**.
3. Descomprime el zip. Sale una carpeta llamada `Ant-Farm-Idle-main`. (En Windows a
   veces queda una dentro de otra con el mismo nombre: la buena es la de dentro, la que
   tiene `hormiguero_pixel.py`.)

### Paso 4. Abre una terminal dentro de la carpeta

Todas las órdenes se escriben en una terminal abierta **dentro** de la carpeta del
hormiguero (la que tiene `hormiguero_pixel.py`).

- **Windows:** abre la carpeta en el Explorador de archivos. Haz clic en la barra de
  direcciones (donde pone la ruta), escribe `powershell` y pulsa Intro.
- **macOS:** abre la app Terminal, escribe `cd` y un espacio, arrastra la carpeta a la
  ventana de la Terminal y pulsa Intro.
- **Linux:** clic derecho dentro de la carpeta y **Abrir en una terminal** (el nombre
  cambia según el escritorio). O entra con `cd` (si bajaste el zip, la carpeta se llama
  `Ant-Farm-Idle-main`):

```bash
cd Ant-Farm-Idle
```

### Paso 5. Pruébalo

En Windows:

```bash
py hormiguero_pixel.py --ventana
```

En macOS y Linux:

```bash
python3 hormiguero_pixel.py --ventana
```

Se abre una ventana con el hormiguero. Para cerrarla, pulsa `q` o `Esc`. El ratón no
se ve encima del hormiguero: es a propósito.

Sin `--ventana`, el hormiguero ocupa toda la pantalla. Sales igual, con `q` o `Esc`.

> La primera vez que lo arrancas con la hora de verdad (como ahora, sin opciones de prueba
> como `--demo`) se crea la carpeta `local/`, con un fichero `estado.json`. Ahí se apunta,
> entre otras cosas, que ese día es el día 0 del hormiguero. No la borres: en el
> [capítulo 2](02-primeros-pasos.md) verás para qué más sirve esa carpeta.

En Windows y macOS (y en algunos Linux) las letras se ven algo distintas que en la Pi.
El hormiguero usa la letra DejaVu si la encuentra (también en Windows y macOS, si la
instalas) y, si no, la que trae pygame. Es normal. Con la de pygame, la calavera de los
esqueletos de Halloween sale como un cuadradito.

### Si algo falla en el ordenador

- **Windows dice que no conoce `py`.** Prueba con `python` en su lugar. Si tampoco,
  vuelve a instalar Python y marca **Add python.exe to PATH**.
- **`pip` se pone a compilar y acaba con un error largo.** Suele pasar cuando tu Python es
  tan nuevo que pygame aún no tiene paquete para él (por ahora, de la 3.14 en adelante).
  Instala la 3.13, como en el paso 1, y repite el paso 2. En Linux, usa la opción A.
- **En Windows, `py --version` dice 3.14 o más aunque instalaste la 3.13.** Tienes varias
  versiones y `py` usa la más nueva. Escribe `py -3.13` en lugar de `py` en todas las
  órdenes.
- **`No module named pygame`.** pygame está instalado para otro Python. Usa la misma
  orden (`py`, `python3` o la del entorno) para instalar pygame y para arrancar el
  hormiguero.

---

## Parte 2. En una Raspberry Pi

El hormiguero está pensado para una Raspberry Pi 3 con **Raspberry Pi OS Lite**, la
versión sin escritorio: así va lo más fluido posible. El instalador lo deja como un
servicio: arranca solo al encender la Pi y se vuelve a lanzar si se cierra.

### Paso 1. Graba la tarjeta con Raspberry Pi Imager

1. Instala [Raspberry Pi Imager](https://www.raspberrypi.com/software/) en tu ordenador
   y ábrelo.
2. Como dispositivo, elige tu modelo (por ejemplo, **Raspberry Pi 3**).
3. Como sistema operativo, entra en **Raspberry Pi OS (other)** y elige
   **Raspberry Pi OS Lite (64-bit)**.
4. Como almacenamiento, elige la tarjeta microSD.
5. Rellena la personalización. Según la versión del Imager, salen como pasos del
   asistente o al pulsar **Editar ajustes** antes de grabar:
   - **Nombre del equipo:** por ejemplo `hormiguero`.
   - **Usuario y contraseña:** invéntalos y apúntalos. Los necesitarás para entrar.
   - **WiFi:** el nombre de tu red, su contraseña y el país (ES).
   - **Zona horaria** (por ejemplo, `Europe/Madrid`) y **teclado** (`es`).
   - **SSH:** actívalo, con contraseña.
6. Graba. El Imager avisa de que borrará la tarjeta: acepta.

### Paso 2. Enciende la Pi y entra por SSH

1. Mete la tarjeta en la Pi, conecta la pantalla y enciéndela.
2. Espera unos minutos. El primer arranque tarda más de lo normal.
3. En tu ordenador, abre una terminal (en Windows, PowerShell) y entra en la Pi.
   Cambia `TU_USUARIO` por el usuario que pusiste en el Imager (y `hormiguero`, si le
   diste otro nombre al equipo):

```bash
ssh TU_USUARIO@hormiguero.local
```

La primera vez te pregunta si confías en el equipo: escribe `yes` y pulsa Intro. Luego
escribe la contraseña (no se ve mientras la escribes; es normal).

Si no encuentra `hormiguero.local`, busca la dirección IP de la Pi en tu router (son cuatro
números separados por puntos) y úsala en su lugar: por ejemplo, `ssh TU_USUARIO@10.0.0.50`.

Desde aquí, todo lo que escribes en esa terminal pasa en la Pi.

### Paso 3. Comprueba la zona horaria

El hormiguero usa la hora de la Pi. A veces el Imager no llega a aplicar la zona horaria,
así que conviene mirarla:

```bash
timedatectl
```

En la línea `Time zone` tiene que salir tu zona. Si no, cámbiala (aquí, la de España
peninsular):

```bash
sudo timedatectl set-timezone Europe/Madrid
```

### Paso 4. Copia el hormiguero a la Pi

Elige una de estas dos formas.

**Opción A: con git, en la Pi** (la recomendada). Al entrar por SSH ya estás en tu
carpeta personal. Instala git (no hace nada si ya lo tienes):

```bash
sudo apt update
```

```bash
sudo apt install -y git
```

Y descarga el hormiguero:

```bash
git clone https://github.com/Ignacio-Aranda/Ant-Farm-Idle.git
```

Queda en `~/Ant-Farm-Idle`.

**Opción B: con scp, desde tu ordenador.** Si descargaste el zip, cambia antes el nombre
de la carpeta `Ant-Farm-Idle-main` (la que tiene `hormiguero_pixel.py`) a `Ant-Farm-Idle`.
Si ya lo probaste en el ordenador, saca de ella la carpeta `local/` (muévela a otro sitio):
es la del ordenador, y la Pi tiene que empezar con la suya. Tus datos se pasan aparte, como
verás en el [capítulo 2](02-primeros-pasos.md). Después, en una terminal **de tu
ordenador** (no en la de la Pi), dentro de la carpeta que contiene `Ant-Farm-Idle`:

```bash
scp -r Ant-Farm-Idle TU_USUARIO@hormiguero.local:
```

Los dos puntos del final son importantes: copian la carpeta a tu carpeta personal de la Pi.

> Desde Windows vale tanto la carpeta que sale del zip como una copia hecha con git: los
> scripts (`.sh`) llegan siempre con los finales de línea de Linux, los que necesita la Pi.

### Paso 5. Ejecuta el instalador

En la Pi:

```bash
bash ~/Ant-Farm-Idle/instalar-pi.sh
```

Si te pide una contraseña, es la de tu usuario de la Pi. Tarda unos minutos. Esto es
lo que hace:

- Instala pygame y la fuente DejaVu (sin ella los textos se ven mal).
- Crea el servicio `hormiguero`: arranca al encender la Pi y se vuelve a lanzar solo,
  a los 5 segundos, si se cierra.
- Hace que la pantalla no se apague nunca.
- Lanza el hormiguero.

Al terminar enseña el estado del servicio y escribe `Listo.` En la pantalla de la Pi ya
tiene que verse el hormiguero.

Reinicia la Pi una vez, para que se aplique lo de no apagar la pantalla y para comprobar
que el hormiguero arranca solo:

```bash
sudo reboot
```

La conexión SSH se corta. Espera un minuto y vuelve a entrar con `ssh`, como en el paso 2.

Ten en cuenta que el hormiguero ocupa la pantalla de la Pi en lugar de la consola y no
hace caso a un teclado conectado a la Pi (`q` y `Esc` solo sirven en el ordenador): todo
se hace por SSH.

La imagen del hormiguero mide 640x512 píxeles. Se amplía un número entero de veces, lo
máximo que quepa, para que los píxeles se vean nítidos, y se centra con bandas negras si
sobra sitio. En una pantalla de 1280x1024 o de 1920x1080 sale al doble; en una de
1366x768 o de 1024x768, a su tamaño, sin ampliar. En una más pequeña que 640x512, se
reduce para que quepa.

### Paso 6. Comprueba que funciona

Para ver el estado del servicio:

```bash
systemctl status hormiguero
```

Tiene que poner `active (running)`. Si no vuelve solo a la terminal, pulsa `q`.

Para ver los mensajes del hormiguero según van saliendo:

```bash
journalctl -u hormiguero -f
```

Al arrancar sale una línea como `framebuffer 1920x1080` (el tamaño de tu pantalla) y,
cada minuto, otra como `volcado a pantalla: 9.5 ms de media`. Si algo va mal, ahí salen
los errores. Pulsa `Ctrl+C` para salir.

Otras órdenes útiles. Para relanzarlo (por ejemplo, después de cambiar `config.toml`):

```bash
sudo systemctl restart hormiguero
```

Para pararlo:

```bash
sudo systemctl stop hormiguero
```

Y para volver a arrancarlo:

```bash
sudo systemctl start hormiguero
```

---

## Actualizar

### En la Pi, si lo copiaste con git

Entra en la carpeta del hormiguero:

```bash
cd ~/Ant-Farm-Idle
```

Descarga lo nuevo:

```bash
git pull
```

Y relanza el servicio:

```bash
sudo systemctl restart hormiguero
```

Si en la lista de ficheros que enseña `git pull` aparece `instalar-pi.sh`, vuelve a
ejecutar el instalador. Se puede ejecutar todas las veces que quieras:

```bash
bash ~/Ant-Farm-Idle/instalar-pi.sh
```

**Si `git pull` se queja** de que tienes cambios (`Your local changes to the following
files would be overwritten`), es que has editado los ficheros de ejemplo del repositorio.
Pasa tus cambios a la carpeta `local/` (mira el [capítulo 2](02-primeros-pasos.md)).
Después aparta los cambios de los ficheros de ejemplo, sin perderlos:

```bash
git stash
```

Y vuelve a hacer `git pull`. Si algún día necesitas recuperar lo apartado, `git stash pop`
lo devuelve.

### En la Pi, si lo copiaste con scp

Descarga el zip nuevo en tu ordenador, cambia el nombre de la carpeta a `Ant-Farm-Idle`
y cópiala igual que la primera vez (paso 4, opción B). Lo que tienes en `local/` en la
Pi no se toca, siempre que no copies también una carpeta `local/` desde el ordenador.
Después, en la Pi, relanza el servicio:

```bash
sudo systemctl restart hormiguero
```

### En el ordenador

Con git, dentro de la carpeta del hormiguero:

```bash
git pull
```

Con el zip: descarga el nuevo y mueve tu carpeta `local/` de la versión vieja a la nueva.

---

## Desinstalar el servicio

Si quieres que la Pi deje de mostrar el hormiguero, en la Pi:

1. Para el servicio y quita el arranque automático:

```bash
sudo systemctl disable --now hormiguero
```

2. Borra el servicio:

```bash
sudo rm /etc/systemd/system/hormiguero.service
```

3. Avisa al sistema de que ya no está:

```bash
sudo systemctl daemon-reload
```

4. Devuelve la consola a la pantalla (o reinicia la Pi):

```bash
sudo systemctl start getty@tty1
```

Si además quieres quitar el ajuste que puso el instalador para que la pantalla no se
apague, bórralo y reinicia:

```bash
sudo sed -i 's/ consoleblank=0//' /boot/firmware/cmdline.txt
```

```bash
sudo reboot
```

(En sistemas antiguos, el fichero es `/boot/cmdline.txt`.)

La carpeta `~/Ant-Farm-Idle` se queda donde estaba. Si también quieres borrarla, guarda
antes tu carpeta `local/`: ahí están tus datos.

---

Anterior: [Índice de la guía](README.md) · Siguiente: [2. Primeros pasos](02-primeros-pasos.md)
