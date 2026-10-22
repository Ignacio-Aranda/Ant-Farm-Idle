# Problemas frecuentes

En este capítulo vas a aprender a resolver los problemas más habituales del hormiguero,
sobre todo en la Raspberry Pi: busca el tuyo en la lista y sigue los pasos.

- [Antes de nada: dos órdenes para mirar](#antes-de-nada-dos-órdenes-para-mirar)
- [La pantalla de la Pi se queda en negro](#la-pantalla-de-la-pi-se-queda-en-negro)
- [El servicio no arranca](#el-servicio-no-arranca)
- [Los textos se ven borrosos](#los-textos-se-ven-borrosos)
- [La hora o el día están mal](#la-hora-o-el-día-están-mal)
- [La franja amarilla de avisos](#la-franja-amarilla-de-avisos)
- [He cambiado un fichero y no pasa nada](#he-cambiado-un-fichero-y-no-pasa-nada)
- [Poner otra cosa en la pantalla: `en-pantalla.sh`](#poner-otra-cosa-en-la-pantalla-en-pantallash)
- [Va lento o a tirones](#va-lento-o-a-tirones)
- [Cambiar de monitor o de resolución](#cambiar-de-monitor-o-de-resolución)
- [La pantalla se apaga sola](#la-pantalla-se-apaga-sola)
- [Empezar de cero](#empezar-de-cero)

Las órdenes de la Pi se escriben por SSH (mira el [capítulo 1](01-instalacion.md)), en una
terminal abierta dentro de la carpeta del hormiguero:

```bash
cd ~/Ant-Farm-Idle
```

---

## Antes de nada: dos órdenes para mirar

Casi todos los problemas de la Pi se entienden con estas dos órdenes.

**1. ¿Está en marcha?**

```bash
systemctl status hormiguero
```

Fíjate en la línea `Active:`:

| Pone | Qué significa |
|---|---|
| `active (running)` | Está en marcha. |
| `activating (auto-restart)` | Se cierra por un error y se vuelve a lanzar solo cada 5 segundos. |
| `inactive (dead)` | Está parado. |
| `could not be found` | El servicio no está instalado: ejecuta `instalar-pi.sh` (ver el [capítulo 1](01-instalacion.md)). |

Si la orden no vuelve sola a la terminal, pulsa `q`.

**2. ¿Qué ha escrito?** Las últimas 50 líneas de sus mensajes:

```bash
journalctl -u hormiguero -n 50 --no-pager
```

Si algo ha fallado, verás un bloque que empieza por `Traceback`. La línea importante es la
última de ese bloque: dice qué ha pasado.

---

## La pantalla de la Pi se queda en negro

### Por qué la Pi usa `hormiguero_fb.py`

En una Raspberry Pi 3 sin escritorio, pygame con aceleración gráfica (`kmsdrm`) deja la
pantalla en negro: el programa funciona, pero no se ve nada.

Por eso el servicio de la Pi no usa `hormiguero_pixel.py`, sino `hormiguero_fb.py`. Este
dibuja cada fotograma en memoria y lo copia directamente a la pantalla (el *framebuffer*,
`/dev/fb0`), sin pasar por la aceleración gráfica. Es el mismo hormiguero, con las mismas
opciones.

En la Pi, entonces:

- Para ver algo en la pantalla, usa siempre `hormiguero_fb.py`, y lánzalo con
  `en-pantalla.sh` (más abajo).
- `hormiguero_pixel.py` en la Pi solo sirve para lo que no usa la pantalla: `--captura` y
  `--medir`.
- Las teclas (`q`, `f`, `i`) no funcionan con `hormiguero_fb.py`.

### Si aun así está en negro

1. Comprueba que la pantalla está encendida y en la entrada a la que está conectada la Pi.
2. Mira si el servicio está en marcha:

```bash
systemctl status hormiguero
```

   Si no pone `active (running)`, ve a [El servicio no arranca](#el-servicio-no-arranca).

3. Mira qué pantalla ha encontrado al arrancar:

```bash
journalctl -u hormiguero -b | grep framebuffer
```

   Tiene que salir una línea como `framebuffer 1920x1080`. Si sale, el hormiguero está
   pintando: el problema está entre la Pi y la pantalla.

4. Conecta y enciende la pantalla, y reinicia la Pi con ella encendida. Algunas pantallas
   (sobre todo con adaptadores a VGA) necesitan estar conectadas cuando la Pi arranca:

```bash
sudo reboot
```

Si la pantalla parpadea entre el hormiguero y otra cosa, seguramente has lanzado otro
programa a mano mientras el servicio estaba en marcha, y los dos pintan a la vez. Cierra
el tuyo con `Ctrl+C` y usa [`en-pantalla.sh`](#poner-otra-cosa-en-la-pantalla-en-pantallash).

---

## El servicio no arranca

1. Mira el estado y los mensajes con las [dos órdenes del principio](#antes-de-nada-dos-órdenes-para-mirar).
2. Busca en los mensajes alguna de estas frases:

| Si pone... | Qué pasa | Qué hacer |
|---|---|---|
| `No such file or directory` con la ruta del hormiguero, o `CHDIR` | Has movido o cambiado de nombre la carpeta del hormiguero. El servicio guarda la ruta que tenía al instalarlo. | Vuelve a ejecutar el instalador desde la carpeta nueva (abajo). |
| `No module named 'pygame'` | Falta pygame. | Vuelve a ejecutar el instalador. |
| `Permission denied` y `/dev/fb0` | Tu usuario no puede pintar en la pantalla. | Añádelo al grupo `video` (abajo) y reinicia. |
| `No such file or directory` y `/dev/fb0` | La Pi no ha preparado la pantalla. | Conecta y enciende la pantalla y reinicia la Pi. |

Para volver a ejecutar el instalador (cambia la ruta si tu carpeta está en otro sitio).
Se puede ejecutar todas las veces que quieras:

```bash
bash ~/Ant-Farm-Idle/instalar-pi.sh
```

Para añadir tu usuario al grupo `video` (cambia `TU_USUARIO` por el tuyo):

```bash
sudo usermod -aG video TU_USUARIO
```

Y reinicia:

```bash
sudo reboot
```

3. Comprueba que arranca solo al encender la Pi:

```bash
systemctl is-enabled hormiguero
```

   Tiene que poner `enabled`. Si pone `disabled`, actívalo y lánzalo:

```bash
sudo systemctl enable --now hormiguero
```

Los fallos de tus ficheros (una fecha mal escrita, una comilla que falta...) **no** paran
el servicio: salen en la [franja amarilla de avisos](#la-franja-amarilla-de-avisos).

---

## Los textos se ven borrosos

Puede haber varias causas. Pruébalas en este orden.

### 1. Falta la fuente DejaVu

El hormiguero escribe con la letra DejaVu. Si no la encuentra, usa la que trae pygame, que
en pantalla se ve peor. Raspberry Pi OS Lite no la trae; la pone el instalador.

Para comprobar si está:

```bash
ls /usr/share/fonts/truetype/dejavu/
```

Tiene que salir `DejaVuSans-Bold.ttf`. Si sale un error o no está, instálala:

```bash
sudo apt install -y fonts-dejavu-core
```

Y relanza el hormiguero:

```bash
sudo systemctl restart hormiguero
```

### 2. Un monitor por VGA, o letras pequeñas

Hay dos ajustes en la sección `[general]` de `local/config.toml`:

- `texto_suavizado = false` (sin comillas): letras con los bordes duros, sin suavizar.
  Suelen leerse mejor en monitores VGA (o conectados con un adaptador de HDMI a VGA).
- `texto_aumento = 1`: todas las letras un punto más grandes (con `2`, dos puntos).

Añade las líneas a la sección `[general]` que ya tienes. No escribas otra `[general]`: si
la repites, el fichero no se puede leer. Por ejemplo:

```toml
[general]
nombre = "la Oficina"
fps_pixel = 20
texto_suavizado = false
texto_aumento = 1
```

Después reinicia el hormiguero:

```bash
sudo systemctl restart hormiguero
```

### 3. La pantalla es pequeña o va a una resolución rara

Si la pantalla tiene menos de 640 píxeles de ancho o menos de 512 de alto (por ejemplo, una
de 800x480), la imagen se encoge y se ve menos nítida. Y si la Pi manda una resolución
distinta de la del monitor, el monitor la reescala y todo se ve borroso. Mira
[Cambiar de monitor o de resolución](#cambiar-de-monitor-o-de-resolución).

En Windows y macOS las letras se ven algo distintas que en la Pi. Es normal.

---

## La hora o el día están mal

El hormiguero usa el reloj del ordenador o de la Pi, en su zona horaria. Si pones
`zona_horaria` en `[ciudad]`, usa la de la ciudad.

### La hora de la pantalla está mal

1. Mira la hora y la zona horaria de la Pi:

```bash
timedatectl
```

2. Fíjate en tres líneas:
   - `Local time`: la hora de la Pi.
   - `Time zone`: tiene que ser la tuya (por ejemplo, `Europe/Madrid`).
   - `System clock synchronized`: tiene que poner `yes`.

3. Si la zona no es la tuya, cámbiala (aquí, la de España peninsular):

```bash
sudo timedatectl set-timezone Europe/Madrid
```

4. Relanza el hormiguero para que coja la hora nueva:

```bash
sudo systemctl restart hormiguero
```

Otra forma de arreglar la zona: pon la zona horaria en `config.toml`, en `[ciudad]`, con
`zona_horaria`. Así el hormiguero va en la hora de la ciudad aunque la Pi esté en otra
zona. Lo explica el [capítulo 7](07-tiempo-y-ciudad.md).

Si `System clock synchronized` pone `no`: la Pi no tiene pila para el reloj. Coge la hora
de internet al arrancar y, hasta que lo consigue, puede ir mal. Comprueba que tiene WiFi o
cable. Cuando se pone en hora, el reloj da un salto; los saltos de más de 5 minutos no
cuentan como tiempo cavando, así que no adelantan las obras.

### El «Día N del hormiguero» no es el que esperabas

El día 0 es la fundación:

- Si `config.toml` tiene `fundacion`, es esa fecha.
- Si no, es el día en que arrancó por primera vez con la hora de verdad. Se apunta en
  `local/estado.json`.

Para cambiarla, pon en la sección `[general]` de `local/config.toml` la fecha que quieras:

```toml
[general]
nombre = "la Oficina"
fundacion = "2026-01-01"
```

Y reinicia el hormiguero. Ojo: con otra fundación, el hormiguero es otro. Con
`cavar = "encendido"` en `[nido]` (lo normal), lo excavado empieza de cero.

### El sol sale o se pone a una hora rara

Revisa `lat` y `lon` en `[ciudad]` (al oeste de Greenwich, la longitud es negativa) y la
zona horaria. Más en el [capítulo 7](07-tiempo-y-ciudad.md).

---

## La franja amarilla de avisos

Si algo de tus ficheros está mal escrito, el hormiguero no se para: usa un valor por
defecto y te lo cuenta en una franja amarilla, arriba a la izquierda, debajo de la fecha.

### Cómo leerla

- Empieza por `Avisos:`.
- Si hay varios, van seguidos, separados por `;`.
- Solo cabe lo que entra en una línea de la pantalla (menos con `texto_aumento`). Si sigue,
  acaba en «…».

Cada aviso dice **dónde** está el fallo, **qué** pasa y, muchas veces, **qué ha hecho** el
hormiguero. Por ejemplo:

> salas/diseno.toml: no existe el color «verdoso» (puse blanco)

Quiere decir: en el fichero `salas/diseno.toml` hay un color, `verdoso`, que no existe; de
momento ha puesto blanco.

El principio del aviso te dice qué fichero mirar:

| Empieza por | Mira en |
|---|---|
| `salas/...` | Ese fichero de sala |
| `tipos/...` | Ese tipo de sala |
| `config:`, `paisaje:` o `horario:` | `config.toml` |
| `tiempo:` | La clave de OpenWeather (mira el [capítulo 7](07-tiempo-y-ciudad.md)) |
| `idos.toml:` | `idos.toml` |
| `calendario:` | `calendario.toml` |
| `-c:`, `--salas:`, `--idos:`... | La opción de la orden: no encuentra ese fichero |
| El nombre de una sala | Su fichero de sala |

Si tienes tus ficheros en `local/`, el aviso no lo dice: entonces `salas/diseno.toml` es
`local/salas/diseno.toml`, y `config.toml`, `local/config.toml`.

### Leerlos todos

Como en la franja no caben todos, haz una captura sin pantalla: escribe los avisos en la
terminal, uno por línea, empezando por `aviso:`. Usa los mismos ficheros que el
hormiguero (los de `local/`, si los tienes) y no cambia tu hormiguero.

En la Pi, en macOS y en Linux:

```bash
python3 hormiguero_pixel.py --captura /tmp/prueba.png
```

En Windows:

```bash
py hormiguero_pixel.py --captura prueba.png
```

### Los avisos más habituales

| Aviso (o parte de él) | Qué hacer |
|---|---|
| `no se puede leer, en la línea 3: ...` | El fichero entero no se puede leer. Mira esa línea: el aviso dice qué parece que falla. Suele faltar una comilla, sobrar una coma en un número (`36,72` en vez de `36.72`), haber un texto sin comillas, unas comillas curvas (`“ ”`) o una sección repetida. |
| `... ha cambiado: reinicia el hormiguero para aplicarlo`, `... es nueva: la sala sale al reiniciar...` | Has cambiado algo que solo se aplica al reiniciar. Reinicia el hormiguero. |
| `debe ser true o false` | Pon `true` o `false`. |
| `no existe el color «...»` | Usa uno de la lista del [capítulo 10](10-referencia.md#8-los-colores). |
| `cumple mal escrito (...), usa DD-MM` | Escríbelo día-mes: `"14-03"`. |
| `la planta va de 1 a 4` | Pon una planta del 1 al 4. |
| `el ancho mínimo es 14` | Pon un `ancho` de 14 o más. |
| `... no cabe en la planta 2` | Haz la sala más estrecha o pásala a otra planta. |
| `la columna 40 choca con otra sala` | Cambia la `x` o quítala (sin `x`, busca hueco sola). |
| `«mesa_comedor» no cabe en la sala (tiene 16 columnas y hacen falta 17)` | Haz la sala más ancha o quita ese mueble. |
| `hay dos «Ana» ...: la segunda sale como «Ana (Diseño)»` | Dos personas se llaman igual. Mejor ponles nombres distintos. |
| `reunión «...»: hoy no convoca a nadie` | Hoy no hay nadie de los citados (una sala vacía, o gente que se fue o aún no ha llegado). Ese día no se hace. |
| `idos.toml: ... se va el ..., pero ya no está en ninguna sala` | Si se va en una fecha futura, déjalo en su sala hasta ese día. |
| `idos.toml: no caben todas las lápidas en el cementerio (no salen ...)` | No hay sitio para tantas: faltan las de los primeros de la lista. Si quieres que salga alguien en concreto, ponlo más abajo en `idos.toml`, o quita a alguien. |
| `fecha mal escrita (...), usa DD-MM o pascua+N` | Una fiesta de `calendario.toml` con la fecha mal escrita. Esa fiesta no se pone. |
| `config: fundacion mal escrita` | Escríbela `"AAAA-MM-DD"`, por ejemplo `"2026-01-01"`. |

### Cuándo se va el aviso

Cuando arreglas el fichero y lo guardas, los avisos se rehacen a los pocos segundos. Pero
los de `[paisaje]` y los de dónde va cada sala solo se van al reiniciar. Y lo que cambies
en `config.toml`, en los tipos o en la sala en sí (nombre, color, planta, `x`, ancho y
tipo) solo se aplica al reiniciar: hasta entonces, sale un aviso que te lo recuerda. Si un
aviso no se va en unos segundos, reinicia el hormiguero:

```bash
sudo systemctl restart hormiguero
```

En el ordenador, si pulsas `i` para ver los fotogramas por segundo, esa línea sale debajo de
la franja amarilla.

---

## He cambiado un fichero y no pasa nada

1. **¿Estás cambiando el fichero bueno?** Si existe la copia de `local/`, el hormiguero no
   mira el del ejemplo. Por ejemplo, si tienes `local/salas/`, cambiar `salas/` no hace
   nada: cambia `local/salas/`.
2. **¿Lo has guardado?** En `nano`, se guarda con `Ctrl+O` e Intro.
3. **¿Hace falta reiniciar?** La gente, las reuniones, los muebles y `jefe` de las salas,
   `idos.toml` y `calendario.toml` se aplican solos a los pocos segundos. Hay que reiniciar
   para `config.toml`, los tipos, el nombre, color, planta, `x`, ancho y tipo de las
   salas, cuando creas o borras un fichero de sala y cuando creas algo nuevo en `local/`.
4. **¿Sale un aviso?** Mira la [franja amarilla](#la-franja-amarilla-de-avisos).

La lista completa de qué se aplica solo y qué no está en el
[capítulo 10](10-referencia.md).

---

## Poner otra cosa en la pantalla: `en-pantalla.sh`

La pantalla de la Pi es del servicio. Si lanzas otro programa por SSH, los dos pintan a la
vez. Para eso está `en-pantalla.sh`:

- Para el hormiguero.
- Lanza lo que le digas en la pantalla de la Pi.
- Cuando el programa termina (o pulsas `Ctrl+C`, o se corta el SSH), vuelve a lanzar el
  hormiguero.

### Cómo se usa

1. Entra en la carpeta del hormiguero:

```bash
cd ~/Ant-Farm-Idle
```

2. Escribe `./en-pantalla.sh` y, detrás, lo que quieres lanzar. Por ejemplo, la demo:

```bash
./en-pantalla.sh python3 hormiguero_fb.py --demo
```

3. Si te pide una contraseña, es la de tu usuario de la Pi.
4. Mientras está en marcha, la terminal se queda esperando. Para terminar, pulsa `Ctrl+C`.
   A los pocos segundos vuelve el hormiguero de siempre.

### Ejemplos

Nochebuena a las nueve de la noche:

```bash
./en-pantalla.sh python3 hormiguero_fb.py --fecha 2026-12-24 --hora 21:00
```

Tu hormiguero, pero nevando:

```bash
./en-pantalla.sh python3 hormiguero_fb.py --tiempo nieve
```

La demo con otra semilla, para ver otra colocación de las salas:

```bash
./en-pantalla.sh python3 hormiguero_fb.py --demo --semilla 7
```

Todas las opciones están en el [capítulo 10](10-referencia.md).

### A tener en cuenta

- Usa siempre `hormiguero_fb.py`. Con `hormiguero_pixel.py`, la pantalla se queda en negro.
- Lo que escribe el programa se guarda en `/tmp/en-pantalla.log` y se enseña al terminar.
  Si algo falla, el error está ahí.
- El programa se lanza dentro de la carpeta del hormiguero, como tu usuario, y con las
  variables de `local/entorno`, como el servicio (por ejemplo, la clave de OpenWeather).
- Si escribes `./en-pantalla.sh` sin nada detrás, solo te explica cómo se usa.
- Solo sirve en la Pi con el servicio instalado.

---

## Va lento o a tirones

### Qué cuesta cada fotograma

Por defecto, el hormiguero pinta 20 fotogramas por segundo (`fps_pixel` en `[general]`).
Así que cada fotograma tiene 50 milisegundos (ms). En ese tiempo hay que:

1. Mover a las hormigas y todo lo demás (**simulación**).
2. Dibujar la imagen (**dibujo**).
3. En la Pi, copiarla a la pantalla (**volcado**).

Si entre las tres cosas tardan más de 50 ms, no da tiempo: salen menos fotogramas por
segundo y el movimiento va a tirones.

| `fps_pixel` | Tiempo para cada fotograma |
|---|---|
| 20 | 50 ms |
| 15 | 67 ms |
| 10 | 100 ms |

### Medirlo en la Pi

1. **El volcado.** El servicio escribe cada minuto lo que tarda de media. Para ver las
   últimas líneas:

```bash
journalctl -u hormiguero | grep volcado | tail -n 5
```

   Sale algo como `volcado a pantalla: 9.5 ms de media`.

2. **La simulación y el dibujo.** Para el servicio, para que no moleste a la medida:

```bash
sudo systemctl stop hormiguero
```

   Mide:

```bash
python3 hormiguero_pixel.py --medir
```

   Escribe algo así (los números cambian de un ordenador a otro):

```
simulación 0.10 ms · dibujo 0.29 ms por fotograma (200 fotogramas)
memoria máxima: 47.4 MB
```

   Para una medida más larga, añade `--segundos 60`. Cuando acabes, vuelve a lanzar el
   servicio:

```bash
sudo systemctl start hormiguero
```

3. **Suma** simulación, dibujo y volcado. Si se acerca al tiempo de cada fotograma (50 ms
   con 20 fotogramas por segundo) o lo pasa, baja los fotogramas.

### Bajar los fotogramas

Para probar antes de cambiar nada, lanza el hormiguero un rato a 15 fotogramas por
segundo:

```bash
./en-pantalla.sh python3 hormiguero_fb.py --fps 15
```

Si va mejor, déjalo puesto en `local/config.toml`, en la sección `[general]` que ya tienes
(si aún va a tirones, prueba con `10`):

```toml
[general]
nombre = "la Oficina"
fps_pixel = 15
```

Y reinicia:

```bash
sudo systemctl restart hormiguero
```

### Otras cosas que influyen

- **La resolución de la pantalla.** En cada fotograma se copia la pantalla entera: con más
  píxeles (por ejemplo, 1920x1080 frente a 1280x1024), el volcado tarda más.
- **En el ordenador**, pulsa `i`: arriba a la izquierda salen los fotogramas por segundo y
  lo que tardan la simulación y el dibujo, por ejemplo
  `20 fps · simulación 0.5 ms · dibujo 3.2 ms`.

---

## Cambiar de monitor o de resolución

### Cómo se ve en cada pantalla

La imagen del hormiguero mide 640x512 píxeles. En la Pi, `hormiguero_fb.py` la amplía el
mayor número **entero** de veces que quepa en la pantalla, para que los píxeles se vean
nítidos, y la centra con bandas negras si sobra sitio.

| Pantalla | Se ve a | Tamaño de la imagen |
|---|---|---|
| 800x600, 1024x768, 1280x720, 1366x768, 1600x900 | x1 | 640x512 |
| 1280x1024 | x2 | 1280x1024 (la llena entera) |
| 1600x1200, 1680x1050, 1920x1080, 1920x1200, 2560x1440 | x2 | 1280x1024 |
| 3840x2160 | x4 | 2560x2048 |
| Menos de 640 de ancho o de 512 de alto (por ejemplo, 800x480) | Se encoge (menos nítida) | 600x480 en una de 800x480 |

Fíjate en que con 1280x720 o 1366x768 sale al tamaño original, pequeña en el centro:
para que salga al doble hace falta al menos 1280x1024.

### Qué resolución usa la Pi

El hormiguero la escribe al arrancar:

```bash
journalctl -u hormiguero -b | grep framebuffer
```

Sale, por ejemplo, `framebuffer 1920x1080`.

### Si cambias de monitor

El hormiguero mira el tamaño de la pantalla solo al arrancar. Conecta el monitor nuevo,
enciéndelo y reinicia la Pi:

```bash
sudo reboot
```

### Forzar una resolución

Normalmente la Pi elige sola la resolución del monitor. Si elige una que no es la buena
(pasa a veces con adaptadores de HDMI a VGA, porque la Pi no puede preguntarle al
monitor), puedes decírsela tú. Este ajuste es de Raspberry Pi OS, no del hormiguero.

1. Abre el fichero de arranque:

```bash
sudo nano /boot/firmware/cmdline.txt
```

   (En sistemas antiguos, el fichero es `/boot/cmdline.txt`.)

2. Todo el fichero es **una sola línea**. Ve al final de esa línea, escribe un espacio y
   añade esto, con la resolución de tu monitor:

```
video=HDMI-A-1:1280x1024M@60
```

   No pulses Intro: tiene que seguir siendo una sola línea.

3. Guarda con `Ctrl+O` e Intro, y sal con `Ctrl+X`.
4. Reinicia:

```bash
sudo reboot
```

5. Comprueba la resolución con la orden de `journalctl` de antes.

Para deshacerlo, borra ese trozo de la línea y reinicia.

### En el ordenador

Con `--ventana` sale en una ventana; sin ella, a pantalla completa. La tecla `f` cambia de
una a otra.

---

## La pantalla se apaga sola

El instalador pone `consoleblank=0` en el fichero de arranque de la Pi, para que no apague
la pantalla nunca. Se aplica después de reiniciar la Pi una vez.

Para comprobar que está:

```bash
grep consoleblank /boot/firmware/cmdline.txt
```

Tiene que salir la línea del fichero, con `consoleblank=0`. (En sistemas antiguos, el
fichero es `/boot/cmdline.txt`.) Si no sale nada, vuelve a ejecutar el
instalador:

```bash
bash ~/Ant-Farm-Idle/instalar-pi.sh
```

Y reinicia:

```bash
sudo reboot
```

Si aun así se apaga, mira el menú del propio monitor: algunos tienen un apagado
automático o un ahorro de energía propio.

---

## Empezar de cero

El hormiguero guarda en `local/estado.json`:

- La fecha de fundación y la semilla, si no están en `config.toml`.
- El color de cada hormiga que no tiene uno fijo.
- Dónde estaba cada hormiga.
- Lo excavado (con `cavar = "encendido"`).

Para empezar un hormiguero nuevo, hay que borrar ese fichero **con el hormiguero parado**.
Se guarda cada minuto y al pararlo: si está en marcha, lo vuelve a escribir.

### En la Pi

1. Para el hormiguero:

```bash
sudo systemctl stop hormiguero
```

2. Borra el estado:

```bash
rm ~/Ant-Farm-Idle/local/estado.json
```

3. Vuelve a lanzarlo:

```bash
sudo systemctl start hormiguero
```

### En el ordenador

1. Cierra el hormiguero con `q`.
2. Borra el fichero `estado.json` de la carpeta `local/` (en Windows, con el Explorador de
   archivos).
3. Vuelve a lanzarlo.

### Qué pasa después

- Si `config.toml` **no** tiene `fundacion` ni `semilla`: hoy pasa a ser el día 0 y sale
  una semilla nueva al azar, así que las salas y los túneles se colocan de otra forma.
- Si `config.toml` **sí** las tiene: la fundación y la colocación son las mismas, pero lo
  excavado, los colores y dónde estaba cada hormiga empiezan de cero. Para cambiar también
  la colocación, cambia o quita `semilla`. Para que hoy sea el día 0, cambia o quita
  `fundacion`.

Tus ficheros (`salas/`, `idos.toml`, `calendario.toml`, `config.toml`...) no se tocan. No
borres la carpeta `local/` entera: ahí están tus datos.

### Probar otra colocación sin perder nada

Lo guardado va aparte para cada fundación y semilla. Si pones otra semilla en
`local/config.toml` (por ejemplo, `semilla = 7` en `[general]`) y reinicias, tienes otro
hormiguero, con lo suyo. Si luego vuelves a la semilla de antes (o quitas la línea, si no
la tenías), vuelve tu hormiguero tal como estaba.

---

Anterior: [8. Cómo crece el hormiguero](08-como-crece.md) · Siguiente: [10. Referencia](10-referencia.md)
