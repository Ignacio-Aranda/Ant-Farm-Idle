# Referencia

En este capítulo tienes, en un solo sitio, todas las opciones de las órdenes y todas las
claves de los ficheros de configuración, con su valor por defecto y un ejemplo.

No hace falta leerlo de principio a fin. Úsalo para consultar algo concreto: las
explicaciones paso a paso están en los otros capítulos.

Lo que hay aquí:

1. Las órdenes: `hormiguero_pixel.py`, `hormiguero_fb.py`, las teclas, las variables de
   entorno y los otros programas.
2. Los ficheros: dónde se buscan, cómo se escriben y cuándo se aplican los cambios.
3. `config.toml`.
4. `salas/*.toml`.
5. `tipos/*.toml`.
6. `idos.toml`.
7. `calendario.toml`.
8. Los colores.
9. La carpeta `local/`.

---

## 1. Las órdenes

### `hormiguero_pixel.py`

Es el hormiguero normal, el del ordenador. Todas las opciones son optativas y se pueden
combinar. Por ejemplo:

```bash
python3 hormiguero_pixel.py --ventana --fecha 2026-12-24 --hora 21:00 --tiempo nieve
```

En la línea de órdenes, los números con decimales llevan **punto**, no coma: `--seg-dia 0.5`.

#### Qué ficheros usa

| Opción | Qué es | Por defecto |
|---|---|---|
| `-c RUTA` o `--config RUTA` | El fichero de configuración. | `local/config.toml` si existe; si no, `config.toml` |
| `--salas RUTA` | La carpeta de las salas. | `local/salas` si existe; si no, `salas` |
| `--tipos RUTA` | La carpeta de los tipos de sala. | `local/tipos` si existe; si no, `tipos` |
| `--idos RUTA` | El fichero de los que se fueron. | `local/idos.toml` si existe; si no, `idos.toml` |
| `--calendario RUTA` | El fichero de las fiestas. | `local/calendario.toml` si existe; si no, `calendario.toml` |

- Los valores por defecto están siempre dentro de la carpeta del hormiguero, aunque lances
  la orden desde otra carpeta.
- Una ruta que escribas tú se busca desde la carpeta en la que está abierta la terminal.
- Si la ruta no existe, el hormiguero no se para. Sale un aviso (por ejemplo,
  `--salas: no encuentro mis-salas`) y sigue sin ese fichero.

Ejemplo: probar el calendario de Andalucía que viene en `ejemplos/`.

```bash
python3 hormiguero_pixel.py --ventana --calendario ejemplos/calendario-andalucia.toml
```

#### El reloj

| Opción | Qué hace | Por defecto |
|---|---|---|
| `--fecha AAAA-MM-DD` | Empieza ese día, a la hora de ahora. | Hoy |
| `--hora HH:MM` | Empieza a esa hora (hoy, o el día de `--fecha`). | La hora de ahora |
| `--dias N` | Empieza N días después de la fundación, a las 12:00. Admite decimales: `--dias 10.25` son 10 días y 6 horas (las 18:00). | — |
| `--acelerar N` | El reloj va N veces más deprisa. Con `--acelerar 60`, pasa un minuto cada segundo. | `1` |

- Desde el momento elegido, el reloj sigue avanzando.
- Si eliges un día anterior a la fundación, se ve el día 0.
- Con `--dias` y `--fecha` a la vez, manda el día de `--fecha`, a la hora que marque `--dias`
  (las 12:00 si es un número entero).
- Con cualquiera de estas cuatro opciones (`--acelerar` distinto de 1), **no se toca**
  `local/estado.json`: tu hormiguero de verdad no cambia.
- El tiempo real de OpenWeather solo se usa cuando el reloj del hormiguero va en hora (con
  menos de 5 minutos de diferencia). Si no, el tiempo sale del modelo estadístico.
- Escribe la fecha con el año delante y guiones (`2026-12-24`) y la hora con dos puntos
  (`21:00`, de `00:00` a `23:59`). Si están mal escritas, el programa no arranca y dice
  qué falla, por ejemplo «opción --fecha: «24-12-2026» no es una fecha: escríbela así,
  2026-12-24».

Ejemplo: cómo estará el hormiguero dentro de 100 días desde la fundación.

```bash
python3 hormiguero_pixel.py --ventana --dias 100
```

#### La demo

| Opción | Qué hace | Por defecto |
|---|---|---|
| `--demo` | Un año entero a toda velocidad. Empieza el día de la fundación a las 9:00 y se para en las fechas importantes. | — |
| `--seg-dia N` | En la demo, segundos que dura cada día. El mínimo es 0.2. | `4` |
| `--pausa N` | En la demo, segundos que se para en cada fecha importante. | `5` |

- Las fechas importantes son el primer día de cada fiesta, los cumpleaños de quien está ese
  día en el hormiguero y el día en que alguien se va. Se miran los 400 días desde el
  principio de la demo.
- Con `--fecha`, la demo empieza ese día en lugar de la fundación.
- En la demo no cuentan `--hora`, `--dias` ni `--acelerar`.
- Sin `--semilla`, cada demo usa una semilla al azar, aunque `config.toml` tenga una.
- La demo nunca toca `local/estado.json`.

Ejemplo: la demo desde el 20 de diciembre, con un día cada 2 segundos.

```bash
python3 hormiguero_pixel.py --ventana --demo --fecha 2026-12-20 --seg-dia 2
```

#### Otras opciones

| Opción | Qué hace | Por defecto |
|---|---|---|
| `--semilla N` | Usa otra semilla (un número entero): otra colocación de salas y túneles. | La de `config.toml` o, si no hay, la del primer arranque |
| `--tiempo TIPO` | Fuerza el tiempo todo el rato: `despejado`, `nublado`, `lluvia`, `tormenta`, `nieve` o `calima`. La temperatura se queda fija en 15 °C (con `nieve`, en -1 °C). | El real o el del modelo |
| `--fps N` | Fotogramas por segundo. | `fps_pixel` de `config.toml` (20 si no está) |
| `--ventana` | En una ventana, en lugar de a pantalla completa. | Pantalla completa |
| `-h` o `--help` | Enseña la lista de opciones, cada una con lo que hace, y sale. | — |

Con la hora de verdad y `--semilla`, sí se guarda en `local/estado.json`, pero aparte: es
otro hormiguero y no toca el tuyo. Si vuelves a tu semilla, vuelves a tu hormiguero tal
como estaba.

#### Sin pantalla

Estas opciones no abren ninguna ventana. Sirven para hacer capturas, leer todos los avisos
y medir lo que tarda cada fotograma.

| Opción | Qué hace | Por defecto |
|---|---|---|
| `--captura FICHERO.png` | Simula un rato y guarda una imagen de 1280x1024. Escribe en la terminal todos los avisos, uno por línea, empezando por `aviso:`. | — |
| `--medir` | Simula un rato dibujando todos los fotogramas y escribe lo que tarda de media cada uno (simulación y dibujo) y la memoria máxima (en Windows no se puede saber y no sale). También escribe los avisos. | — |
| `--segundos N` | Con `--captura` y `--medir`: cuántos segundos del hormiguero se simulan. Se multiplican por `--acelerar`. | `10` |

- Con `--captura` y `--medir` no se toca `local/estado.json`.
- Los fotogramas por segundo son los de `--fps` o, si no lo pones, 20 (aquí no se usa
  `fps_pixel`).
- Se pueden combinar con las demás opciones (`--fecha`, `--hora`, `--tiempo`...).

Ejemplo: una captura de Nochebuena.

```bash
python3 hormiguero_pixel.py --captura nochebuena.png --fecha 2026-12-24 --hora 21:00
```

Ejemplo: medir durante un minuto del hormiguero.

```bash
python3 hormiguero_pixel.py --medir --segundos 60
```

Escribe algo así (los números cambian de un ordenador a otro):

```
simulación 0.07 ms · dibujo 0.25 ms por fotograma (1200 fotogramas)
memoria máxima: 47.4 MB
```

### `hormiguero_fb.py`

Es el que usa la Raspberry Pi. Pinta directamente en la pantalla (el *framebuffer*,
`/dev/fb0`), sin escritorio ni aceleración gráfica. Lo explica el
[capítulo 9](09-problemas-frecuentes.md).

- Acepta **las mismas opciones** que `hormiguero_pixel.py`.
- `--ventana` no hace nada: siempre ocupa la pantalla entera.
- Las teclas no funcionan.
- Para `--captura` y `--medir`, usa `hormiguero_pixel.py`.
- Al arrancar escribe el tamaño de la pantalla, por ejemplo `framebuffer 1920x1080`.
- La imagen de 640x512 se amplía el número entero de veces que quepa (x2, x3...), centrada
  y con bandas negras si sobra sitio. Si la pantalla es más pequeña que 640x512, se encoge.

En la Pi, no lo lances directamente mientras el servicio está en marcha: usa
`en-pantalla.sh` (más abajo). Por ejemplo:

```bash
./en-pantalla.sh python3 hormiguero_fb.py --demo
```

### Las teclas

Solo con `hormiguero_pixel.py` y una pantalla. Con `hormiguero_fb.py`, el de la Pi, no
funcionan.

| Tecla | Qué hace |
|---|---|
| `q` o `Esc` | Salir (guardando el estado, si va con la hora de verdad). |
| `f` | Pasar de ventana a pantalla completa, y al revés. |
| `i` | Enseñar u ocultar los fotogramas por segundo y lo que tardan la simulación y el dibujo. |

### Variables de entorno

| Variable | Qué hace |
|---|---|
| `OPENWEATHER_API_KEY` | La clave de OpenWeather, para el tiempo real. Tiene prioridad sobre el fichero y sobre `config.toml`. |
| `HORMIGUERO_FB` | Solo `hormiguero_fb.py`: el dispositivo de la pantalla. Por defecto, `/dev/fb0`. |
| `HORMIGUERO_FB_INFO` | Solo `hormiguero_fb.py`: con cualquier valor (por ejemplo, `1`), escribe cada minuto lo que tarda de media en pasar la imagen a la pantalla: `volcado a pantalla: 9.5 ms de media`. El servicio de la Pi la trae puesta. |

El servicio de la Pi no ve las variables de tu sesión. Para darle una, escríbela en el
fichero `local/entorno`, una por línea:

```
OPENWEATHER_API_KEY=tu_clave
```

Lo leen el servicio, al arrancar, y lo que lanzas con `en-pantalla.sh`. Lo que arrancas
tú directamente en una terminal no lo ve: ahí vale `export NOMBRE=valor`.

### Otros programas

| Programa | Qué hace |
|---|---|
| `instalar-pi.sh` | En la Pi: instala pygame y la fuente DejaVu, crea el servicio `hormiguero` y deja la pantalla siempre encendida. No tiene opciones y se puede ejecutar todas las veces que quieras. Ver el [capítulo 1](01-instalacion.md). |
| `en-pantalla.sh PROGRAMA [OPCIONES]` | En la Pi: para el hormiguero, lanza el programa en la pantalla de la Pi y, al terminar (o con `Ctrl+C`, o si se corta el SSH), vuelve a lanzar el hormiguero. Lo que escribe el programa se guarda en `/tmp/en-pantalla.log` y se enseña al final. El programa se ejecuta en la carpeta del hormiguero y, como el servicio, con las variables de `local/entorno`. |
| `herramientas/galeria.py` | Vuelve a hacer las imágenes de `docs/` (`galeria-muebles.png`, `galeria-tipos.png` y `galeria-paisaje.png`). No tiene opciones, no abre ventana y usa los ficheros de ejemplo, no los de `local/`. |

---

## 2. Los ficheros

### Dónde se buscan

Para cada fichero, el hormiguero mira primero en la carpeta `local/`:

| Si existe... | ...se usa en lugar de |
|---|---|
| `local/config.toml` | `config.toml` |
| `local/salas/` | `salas/` |
| `local/tipos/` | `tipos/` |
| `local/idos.toml` | `idos.toml` |
| `local/calendario.toml` | `calendario.toml` |

Cada uno sustituye **entero** al de ejemplo. Si haces `local/tipos/`, tiene que tener todos
los tipos que uses. Las opciones `-c`, `--salas`, `--tipos`, `--idos` y `--calendario`
mandan sobre todo esto.

En las carpetas `salas/` y `tipos/` solo se leen los ficheros que acaban en `.toml` y no
empiezan por un punto. Se leen por orden alfabético del nombre del fichero.

### Cómo se escriben (TOML)

Los ficheros son de texto, en formato [TOML](https://toml.io/es/). Lo que necesitas saber:

| Qué | Cómo se escribe | Ejemplo |
|---|---|---|
| Texto | Entre comillas rectas `"` | `nombre = "Ana"` |
| Número | Sin comillas, con punto decimal | `lat = 36.72` |
| Sí o no | `true` o `false` (con comillas también vale, y `"sí"` o `"no"`; otra cosa da un aviso) | `jefe = true` |
| Lista | Entre corchetes, separada por comas | `quien = ["Elena", "Ana"]` |
| Fecha | Entre comillas, con el año delante | `alta = "2026-03-01"` |
| Comentario | Desde `#` hasta el final de la línea | `planta = 2   # la de en medio` |
| Sección | Entre corchetes, en su propia línea | `[general]` |
| Elemento repetible | Entre corchetes dobles; cada vez que lo escribes, es uno nuevo | `[[miembro]]` |

Una regla que conviene recordar: todo lo que va debajo de `[algo]` o de `[[algo]]`
pertenece a ese bloque, hasta el siguiente. Por eso, en una sala, las claves de la sala
(`nombre`, `planta`, `jefe`...) van **arriba**, antes del primer `[[miembro]]`. Si escribes
`jefe = true` debajo de un `[[miembro]]`, se entiende como algo de ese miembro (y sale un
aviso).

### Cuándo se aplican los cambios

Con el hormiguero en marcha, cada 3 segundos mira si has guardado algún fichero.

| Cambio | Cuándo se ve |
|---|---|
| La gente (`[[miembro]]`), las reuniones, `jefe` y los `[[mueble]]` de una sala | A los pocos segundos de guardar |
| `idos.toml` | A los pocos segundos de guardar |
| `calendario.toml` | A los pocos segundos de guardar |
| `nombre`, `color`, `planta`, `x`, `ancho` y `tipo` de una sala | Al reiniciar |
| Crear o borrar un fichero de sala | La sala, al reiniciar (su gente llega o se va antes, a los pocos segundos) |
| `tipos/` | Al reiniciar |
| `config.toml` | Al reiniciar |
| Crear un fichero nuevo en `local/` | Al reiniciar |

Si cambias algo de lo que se ve al reiniciar (salvo crear un fichero en `local/`), la
franja amarilla te lo recuerda hasta que reinicies.

Para reiniciar: en el ordenador, cierra con `q` y vuelve a lanzarlo. En la Pi:

```bash
sudo systemctl restart hormiguero
```

### Si algo está mal escrito

El hormiguero no se para. Usa el valor por defecto y lo cuenta en la franja amarilla de
avisos, arriba a la izquierda. Si un fichero entero no se puede leer (por ejemplo, porque
falta una comilla), sale un aviso con el nombre del fichero, la línea del error y qué parece
que falla. Los ficheros se leen en UTF-8, pero también se entienden guardados «con BOM» o
en «ANSI». Cómo leer los avisos: en el [capítulo 9](09-problemas-frecuentes.md).

---

## 3. `config.toml`

Tiene siete secciones. Todas son optativas: lo que no pongas toma el valor por defecto.

Las explicaciones con calma están en el [capítulo 7](07-tiempo-y-ciudad.md) (`[ciudad]` y
`[tiempo]`), el [capítulo 5](05-paisaje.md) (`[paisaje]`), el
[capítulo 6](06-fiestas-y-halloween.md) (`[halloween]`) y el
[capítulo 8](08-como-crece.md) (`[nido]`).

### `[general]`

| Clave | Tipo | Por defecto | Qué hace |
|---|---|---|---|
| `nombre` | Texto | Ninguno | El nombre del grupo. Sale en el diario: «Se funda el hormiguero de *nombre*: ...» (si empieza por «el», «del ...»). Sin nombre: «Se funda el hormiguero: ...». |
| `fundacion` | Fecha `"AAAA-MM-DD"` (de 1900 a 2999) | El día del primer arranque con la hora de verdad (se guarda en `local/estado.json`) | El día 0 del hormiguero. Si está mal escrita, se usa la del primer arranque o, si aún no la hay, `2026-01-01`. |
| `semilla` | Número entero | Una al azar, elegida en el primer arranque y guardada | El número del que sale todo lo que se elige al azar: dónde van las salas y los túneles, las rocas, el tiempo del modelo estadístico... Con otra semilla, el hormiguero es otro. Si está mal escrita (una lista, una fecha...), sale un aviso y se usa la del primer arranque o, si no la hay, `2026`. |
| `fps_pixel` | Número de 1 a 60 | `20` | Fotogramas por segundo en pantalla. Menos fotogramas, menos trabajo para el ordenador. |
| `texto_aumento` | Número entero de -3 a 8 | `0` | Puntos que se suman a todos los tamaños de letra. `1` o `2` hacen los textos más grandes. |
| `texto_suavizado` | `true` o `false` | `true` | Con `false`, las letras tienen los bordes duros (más legibles en algunos monitores VGA). |

```toml
[general]
nombre = "la Oficina"
fundacion = "2026-01-01"
semilla = 2026
fps_pixel = 20
texto_aumento = 0
texto_suavizado = true
```

### `[ciudad]`

| Clave | Tipo | Por defecto | Qué hace |
|---|---|---|---|
| `nombre` | Texto | Ninguno | Solo para ti: el hormiguero no lo usa. |
| `lat` | Número | `36.72` (Málaga) | Latitud de la ciudad: para el sol y el tiempo real. Si es negativa (hemisferio sur), las estaciones, las flores y los bichos van al revés. |
| `lon` | Número | `-4.42` (Málaga) | Longitud de la ciudad. Al oeste de Greenwich es negativa. |
| `zona_horaria` | Texto | La del ordenador | La zona horaria de la ciudad, por ejemplo `"Europe/Madrid"`. Con ella, el reloj, los horarios y el sol van en la hora de la ciudad aunque el ordenador esté en otra zona. Si no existe, sale un aviso y se usa la del ordenador. |

```toml
[ciudad]
nombre = "Málaga"
lat = 36.72
lon = -4.42
zona_horaria = "Europe/Madrid"
```

### `[tiempo]`

| Clave | Tipo | Por defecto | Qué hace |
|---|---|---|---|
| `fuente` | Texto | `"openweather"` | `"openweather"`: tiempo real, si hay clave. `"estadistico"`: siempre el modelo estadístico, sin internet. Con otra cosa, sale un aviso y se usa `"openweather"`. |
| `cada_minutos` | Número | `10` | Cada cuántos minutos se pide el tiempo a OpenWeather. El mínimo es 5. |
| `clave` | Texto | Ninguna | La clave de OpenWeather. Mejor no la pongas aquí si vas a subir el fichero a algún sitio. |

La clave se busca en este orden:

1. La variable de entorno `OPENWEATHER_API_KEY`.
2. El fichero `local/openweather_clave.txt` (solo la clave, sin nada más; si está vacío,
   cuenta como si no estuviera).
3. `clave` en `[tiempo]`.

Sin clave, o si falla internet, el tiempo sale del modelo estadístico (el clima de Málaga).
Si falla una petición, vuelve a probar a los 2 minutos. Si OpenWeather rechaza la clave
tres veces seguidas, sale un aviso que empieza por `tiempo:`. Los últimos datos buenos valen 3
horas. Se guardan en `local/openweather.json`.

```toml
[tiempo]
fuente = "openweather"
cada_minutos = 10
```

### `[horario]`

Cada franja se escribe `"HH:MM-HH:MM"`, de `00:00` a `23:59` y con la primera hora antes
que la segunda. Si está mal escrita, sale un aviso y se usa la de por defecto.

| Clave | Por defecto | Qué hace |
|---|---|---|
| `desayuno` | `"10:30-11:00"` | A esta hora muchas hormigas van al comedor. |
| `comida` | `"13:30-15:30"` | A esta hora van casi todas al comedor. |
| `jornada` | `"09:00-18:00"` | Quien es jefe solo llama al despacho dentro de esta franja, de lunes a viernes. |

```toml
[horario]
desayuno = "10:30-11:00"
comida = "13:30-15:30"
jornada = "09:00-18:00"
```

### `[nido]`

| Clave | Tipo | Por defecto | Qué hace |
|---|---|---|---|
| `entrada` | Número entero | `20` | Columna preferida para la entrada (de 3 a 156; el hormiguero mide 160 columnas). Es solo una preferencia: su rampa no puede atravesar las salas de la planta 1 y se arrima a ellas, así que puede acabar bastante lejos. |
| `cavar` | Texto | `"encendido"` | `"encendido"`: las obras solo avanzan mientras el hormiguero está en marcha con la hora de verdad. `"fecha"`: avanzan con los días desde la fundación, esté encendido o no. Con otra cosa, sale un aviso y se usa `"encendido"`. |
| `obras` | Lista de nombres | `["despensa", "museo", "hongos", "almacen", "biblioteca"]` | Las salas que se excavan durante el año, en orden. |

Sobre `cavar`:

- Con `"encendido"`, lo que llevan cavado se guarda en `local/estado.json`. Una semana
  apagado es una semana sin obras.
- Si el reloj salta más de 5 minutos de golpe (por ejemplo, al ponerse en hora), ese salto
  no cuenta como tiempo cavando.
- En la demo y con `--fecha`, `--hora`, `--dias` o `--acelerar`, las obras van siempre por
  la fecha.
- Si `config.toml` no se puede leer, se sigue cavando como la última vez.

Sobre `obras`:

- Cada obra usa el tipo de sala de su nombre, sin mirar mayúsculas, tildes ni espacios:
  `"Museo"` usa `tipos/museo.toml`, y `"Sala de juegos"`, `tipos/sala_de_juegos.toml`. Si
  no existe ese tipo, sale un aviso y será una sala vacía.
- Las cinco de por defecto tienen su propio nombre y anchura:

| Obra | Nombre en el cartel | Ancho (columnas) |
|---|---|---|
| `despensa` | Despensa | 24 |
| `museo` | Museo de hallazgos | 28 |
| `hongos` | Vivero de hongos | 22 |
| `almacen` | Almacén | 16 |
| `biblioteca` | Biblioteca | 20 |

- Cualquier otra se llama como la escribas y mide 22 columnas.
- Nunca se hacen más estrechas de lo que necesitan los muebles de su tipo.
- Si no caben, abren una planta más honda o las hacen más estrechas, de 4 en 4 columnas
  (hasta 14 como mucho).
  Si aun así no caben, se quedan sin hacer y lo cuenta el diario.
- Con `obras = []` no se excava ninguna sala nueva.

```toml
[nido]
entrada = 20
cavar = "encendido"
obras = ["despensa", "museo", "hongos", "almacen", "biblioteca"]
```

### `[paisaje]`

| Clave | Tipo | Por defecto | Qué hace |
|---|---|---|---|
| `montes` | `true` o `false` | `true` | Los montes azulados del fondo. Con `false` solo quedan las colinas verdes de delante. |
| `costa` | `true` o `false` | `true` | Gaviotas que cruzan el cielo los días claros. |
| `cementerio` | Número de 0 a 100 | `74` | Dónde empieza el cementerio, en % del ancho. Va lo más cerca posible de ahí: nunca encima de una salida y, si hay algún hueco donde quepa, sin tapar las piezas de `[[paisaje.suelo]]` (si hace falta, con los nombres más pequeños o en dos filas). |

Lo que se pone en la superficie va en bloques `[[paisaje.suelo]]`, y lo del fondo, sobre
los montes, en bloques `[[paisaje.fondo]]`. Cada bloque tiene:

| Clave | Tipo | Por defecto | Qué hace |
|---|---|---|---|
| `pieza` | Texto | Obligatoria | Qué pieza es (ver la lista). |
| `x` | Número de 0 a 100 | `50` | Dónde va, en % del ancho (0 = izquierda, 100 = derecha). |

| Dónde | Piezas |
|---|---|
| `[[paisaje.suelo]]` | `chumbera`, `almendro`, `palmera`, `olivo`, `pino`, `farola`, `banco`, `casa` |
| `[[paisaje.fondo]]` | `catedral`, `ciudad`, `faro`, `molino`, `torre`, `castillo` |

- Si no pones ningún `[[paisaje.suelo]]`, salen los de por defecto: chumbera (2), palmera
  (30), farola (42), olivo (49) y almendro (89).
- Si no pones ningún `[[paisaje.fondo]]`, sale la catedral (58).
- En cuanto escribes uno, sustituye a todos los de por defecto de ese grupo.
- Para no poner nada, escribe `suelo = []` o `fondo = []` dentro de `[paisaje]`.

![Todas las piezas del paisaje, de día y de noche](../galeria-paisaje.png)

```toml
[paisaje]
montes = true
costa = true
cementerio = 74

[[paisaje.suelo]]
pieza = "pino"
x = 22

[[paisaje.suelo]]
pieza = "farola"
x = 42

[[paisaje.fondo]]
pieza = "faro"
x = 45
```

### `[halloween]`

| Clave | Tipo | Por defecto | Qué hace |
|---|---|---|---|
| `esqueletos` | `true` o `false` | `false` | Del 26 al 31 de octubre, los de `idos.toml` salen del cementerio y se pasean por el hormiguero como hormigas esqueleto. |

```toml
[halloween]
esqueletos = true
```

### Un `config.toml` completo

Puedes copiarlo entero y cambiar lo que quieras:

```toml
[general]
nombre = "la Oficina"
# fundacion = "2026-01-01"
# semilla = 2026
fps_pixel = 20
texto_aumento = 0
texto_suavizado = true

[ciudad]
nombre = "Málaga"
lat = 36.72
lon = -4.42
zona_horaria = "Europe/Madrid"

[tiempo]
fuente = "openweather"
cada_minutos = 10

[horario]
desayuno = "10:30-11:00"
comida = "13:30-15:30"
jornada = "09:00-18:00"

[nido]
entrada = 20
cavar = "encendido"
obras = ["despensa", "museo", "hongos", "almacen", "biblioteca"]

[paisaje]
montes = true
costa = true
cementerio = 74

[[paisaje.suelo]]
pieza = "chumbera"
x = 2

[[paisaje.suelo]]
pieza = "palmera"
x = 30

[[paisaje.suelo]]
pieza = "farola"
x = 42

[[paisaje.suelo]]
pieza = "olivo"
x = 49

[[paisaje.suelo]]
pieza = "almendro"
x = 89

[[paisaje.fondo]]
pieza = "catedral"
x = 58

[halloween]
esqueletos = true
```

---

## 4. `salas/*.toml`

Cada fichero `.toml` de la carpeta `salas/` es una sala del nido: existe desde el día 0.
Paso a paso, en el [capítulo 3](03-salas-y-gente.md).

### Las claves de la sala

| Clave | Tipo | Por defecto | Qué hace |
|---|---|---|---|
| `nombre` | Texto | El nombre del fichero sin `.toml` | Lo que pone en el cartel de la sala. |
| `color` | Color | `"blanco"` | El color del cartel. Ver [los colores](#8-los-colores). |
| `planta` | Número entero de 1 a 4 | `2` | 1 es la más alta, junto a la superficie; 4, la más honda. Si te sales, se pone la 1 o la 4, con aviso. (También vale escribirlo `nivel`.) |
| `x` | Número entero | Ninguna: un hueco al azar de su planta | Columna del borde izquierdo de la sala. Si choca con otra sala, sale un aviso y va a un hueco al azar. |
| `ancho` | Número entero, como mínimo 14 | `32` | Anchura de la sala, en columnas. El hormiguero mide 160. |
| `tipo` | Texto | `"trabajo"` | El tipo de sala: el nombre de un fichero de `tipos/`, sin `.toml`. Decide los muebles, las paredes, el suelo y qué hacen allí las hormigas. |
| `jefe` | `true` o `false` | `false` | Quien está en esta sala llama de vez en cuando (cada 15 a 40 minutos) a alguien de otra sala a esta, en el horario de `jornada`, de lunes a viernes. Lo cuenta el diario. Si varias salas lo tienen, solo cuenta la primera por orden alfabético del fichero. |

Si una sala no cabe en su planta, sale un aviso como `Diseño no cabe en la planta 2`:
hazla más estrecha o cámbiala de planta.

### `[[miembro]]`: la gente

Cada `[[miembro]]` es una hormiga de la sala.

| Clave | Tipo | Por defecto | Qué hace |
|---|---|---|---|
| `nombre` | Texto | Obligatorio | El nombre que sale encima de la hormiga. Sin nombre, el miembro no sale (con aviso). |
| `cumple` | `"DD-MM"` | Ninguno | Su cumpleaños: ese día lleva gorro de fiesta, hay tarta arriba y sale «FELIZ CUMPLE». También valen `"DD/MM"`, `"DD-MM-AAAA"` y `"AAAA-MM-DD"`. Los del 29 de febrero lo celebran el 28 en los años no bisiestos. |
| `color` | Color | Uno de la paleta, elegido una vez y guardado | El color de la hormiga y de su nombre. |
| `alta` | Fecha `"AAAA-MM-DD"` | Ninguna: está desde el principio | El día en que llega. Antes de ese día no sale, y ese día lo cuenta el diario: «Llega *nombre* al hormiguero. ¡Bienvenida/o!». |

- Cada hormiga va por su nombre. Si dos personas se llaman igual, la segunda sale con el de
  su sala: «Ana (Diseño)».
- Si no tiene `color`, con la hora de verdad se le da el menos usado de la paleta y ya no
  cambia (se apunta en `local/estado.json`). En la demo y en las pruebas, se reparten en orden.

### `[[reunion]]`: reuniones fijas

Se pueden poner en cualquier sala. A esa hora, las hormigas citadas vienen a **esta** sala.

| Clave | Tipo | Por defecto | Qué hace |
|---|---|---|---|
| `nombre` | Texto | `"Reunión"` | Sale en el diario: «*nombre* en la sala *Sala*». |
| `dia` | Texto | `"todos"` | `lunes`, `martes`, `miércoles`, `jueves`, `viernes`, `sábado`, `domingo` (con o sin tilde), o `todos` (de lunes a viernes). |
| `hora` | `"HH:MM"` | `"10:00"` | A qué hora empieza, de `"00:00"` a `"23:59"`. |
| `minutos` | Número | `60` | Cuánto dura. |
| `quien` | Texto o lista | `"todos"` | A quién convoca: `"todos"`; una sala, por el nombre de su fichero sin `.toml` (`"diseno"`) o por el de su cartel (`"Diseño"`); una persona (`"Elena"`); o una lista de personas (`["Elena", "Ana"]`). |

Si la reunión está mal escrita o no convoca a nadie, sale un aviso y no se hace.

### `[[mueble]]`: muebles de más

Una sala tiene los muebles de su tipo y, además, los que pongas aquí. Las claves son las
mismas que en los tipos: mira [`[[mueble]]` en los tipos](#mueble-los-muebles).

### Una sala completa

```toml
nombre = "Desarrollo"
color = "cian"
planta = 2
x = 40
ancho = 40
tipo = "trabajo"
jefe = false

[[miembro]]
nombre = "Ana"
cumple = "14-03"

[[miembro]]
nombre = "Luis"
cumple = "02-07"
color = "naranja"

[[miembro]]
nombre = "Sara"
cumple = "30-01"
alta = "2026-03-01"

[[reunion]]
nombre = "Café del viernes"
dia = "viernes"
hora = "12:00"
minutos = 30
quien = "todos"

[[mueble]]
pieza = "sofa"
sitio = "centro_derecha"
```

---

## 5. `tipos/*.toml`

Cada fichero de la carpeta `tipos/` es un tipo de sala. Su nombre, sin `.toml` y en
minúsculas, es lo que se escribe en `tipo` de una sala o en `obras` de `[nido]`. Paso a
paso, en el [capítulo 4](04-tipos-y-muebles.md).

![Los tipos que vienen hechos](../galeria-tipos.png)

### Las claves del tipo

| Clave | Tipo | Por defecto | Qué hace |
|---|---|---|---|
| `funcion` | Texto | `"otra"` | Qué hacen allí las hormigas (ver la tabla siguiente). |
| `paredes` | Texto | `"madera"` | `"madera"`, `"azulejo"`, `"piedra"` o un color `"#RRGGBB"`. |
| `suelo` | Texto | `"madera"` | `"madera"`, `"baldosa"` o `"tierra"`. |

Si alguno no existe, sale un aviso y se usa el de por defecto.

### Las funciones

| `funcion` | Qué pasa |
|---|---|
| `trabajo` | Sala de trabajo. Lleva adornos de más en Navidad, Halloween y los días de Andalucía y de España (`andalucia` y `espana`). |
| `reuniones` | Sala de reuniones, con los mismos adornos de más que `trabajo`. (Las reuniones se ponen con `[[reunion]]` en el fichero de la sala.) |
| `despacho` | Despacho, con los mismos adornos de más que `trabajo`. (Para que alguien llame a los demás al despacho, pon `jefe = true` en la sala.) |
| `comedor` | Van a desayunar y a comer (según `[horario]`) y se refugian aquí cuando hay peligro fuera. Si una hormiga no tiene sala, este es su sitio. Lleva los mismos adornos de más que `trabajo`. |
| `agua` | Van a beber de vez en cuando (más a menudo que a otras salas). |
| `despensa` | Aquí guardan la comida que traen de fuera. Si no hay despensa, la llevan al comedor y, si tampoco hay, a la primera sala. |
| `museo` | Igual que `otra`. Los hallazgos no los enseña la función, sino la pieza `vitrina`, en la sala que esté (el tipo `museo` trae dos). |
| `otra` | Solo decorativa: la visitan de vez en cuando. |

Si hay varias salas con función `comedor` o `despensa`, para refugiarse y para guardar la
comida se usa la primera.

### `[[mueble]]`: los muebles

Cada `[[mueble]]` es una pieza. Valen igual en un tipo y en una sala.

| Clave | Tipo | Por defecto | Qué hace |
|---|---|---|---|
| `pieza` | Texto | Obligatoria | Qué mueble es (ver la lista de piezas). Si no existe, sale un aviso y no se pinta. |
| `sitio` | Hueco o número de 0 a 100 | El hueco de siempre de la pieza | Dónde va. Un número es la posición del centro de la pieza en % del ancho de la sala (0 = borde izquierdo, 100 = derecho). |
| `aparece` | Número entero | `0` | Día del hormiguero en que aparece. Si es mayor que 0, ese día lo cuenta el diario. Si no es un número, sale un aviso y está desde el principio. |
| `nombre` | Texto | El de la pieza («una planta») | Cómo se llama en el diario el día en que aparece: «Novedad en *Sala*: *nombre*.». |

- Si el hueco no existe, sale un aviso y la pieza va a su hueco de siempre.
- Con un número de fuera del 0 al 100, sale un aviso y se queda en el borde.
- Si la sala es demasiado estrecha para la pieza, no se pinta y sale un aviso como
  `«mesa_comedor» no cabe en la sala (tiene 16 columnas y hacen falta 17)`.
- En las salas que se excavan durante el año, un mueble no sale en el diario antes de que
  se termine la sala.

### Los huecos

| Hueco | Dónde | Posición aproximada (%) |
|---|---|---|
| `izquierda` | Suelo | 17 |
| `centro_izquierda` | Suelo | 38 |
| `centro` | Suelo | 50 |
| `centro_derecha` | Suelo | 65 |
| `derecha` | Suelo | 88 |
| `pared_izquierda` | Pared | 20 |
| `pared` (o `pared_centro`) | Pared | 50 |
| `pared_derecha` | Pared | 80 |

Cada pieza ya sabe si va en el suelo o en la pared. El hueco solo dice en qué punto del
ancho de la sala va, así que cualquier hueco vale para cualquier pieza.

### Las piezas

| Pieza | Dónde | Hueco de siempre | Columnas que necesita | Notas |
|---|---|---|---|---|
| `escritorio` | Suelo | `izquierda` | 11 | Mesa con ordenador y silla (la pantalla parpadea). |
| `escritorio_grande` | Suelo | `izquierda` | 13 | Escritorio de despacho. |
| `sillon` | Suelo | `centro_derecha` | 5 | |
| `sofa` | Suelo | `centro` | 12 | |
| `planta` | Suelo | `derecha` | 10 | Crece con los días desde que aparece. |
| `mesa_reuniones` | Suelo | `centro` | 2 | Ocupa casi toda la sala. |
| `mesa_comedor` | Suelo | `centro` | 17 | Mesa larga con platos. |
| `nevera` | Suelo | `izquierda` | 6 | |
| `encimera` | Suelo | `derecha` | 12 | Microondas y cafetera (que echa vapor). |
| `fuente` | Suelo | `izquierda` | 5 | Fuente de agua (con burbujas). |
| `estanteria` | Suelo | `izquierda` | 8 | Con libros. |
| `vitrina` | Suelo | `izquierda` | 8 | Enseña los hallazgos de la colonia. |
| `sacos` | Suelo | `izquierda` | 9 | |
| `cajas` | Suelo | `izquierda` | 9 | |
| `setas` | Suelo | `centro` | 21 | Una fila de setas. |
| `cuadro` | Pared | `pared` | 6 | |
| `pantalla` | Pared | `pared` | 13 | Pantalla con gráficas. |
| `pizarra` | Pared | `pared` | 11 | |
| `reloj` | Pared | `pared_derecha` | 6 | Marca la hora del hormiguero: la de verdad o, si la simulas (`--fecha`, `--hora`, `--dias`, `--acelerar` o la demo), la simulada. |

![Todos los muebles](../galeria-muebles.png)

### Un tipo completo

```toml
funcion = "otra"
paredes = "#5a7a9a"
suelo = "baldosa"

[[mueble]]
pieza = "sofa"
sitio = "izquierda"

[[mueble]]
pieza = "estanteria"
sitio = 70

[[mueble]]
pieza = "pizarra"
sitio = "pared"

[[mueble]]
pieza = "planta"
sitio = "derecha"
aparece = 30
nombre = "macetero"
```

Guardado como `tipos/sala_estar.toml`, una sala lo usa con `tipo = "sala_estar"`.

---

## 6. `idos.toml`

Cada `[[ido]]` es alguien que se fue. Tiene su lápida en el cementerio de arriba, con su
nombre tal como lo escribas. Paso a paso, en el [capítulo 3](03-salas-y-gente.md).

| Clave | Tipo | Por defecto | Qué hace |
|---|---|---|---|
| `nombre` | Texto | Obligatorio | Lo que pone en la lápida. Sin nombre, no se tiene en cuenta (y sale un aviso). |
| `fecha` | Fecha `"AAAA-MM-DD"` | Ninguna: ya se fue | El día en que se va. Hasta ese día sigue su hormiga; ese día sale su lápida y lo cuenta el diario. |
| `epitafio` | Texto | `"Se fue, pero no lo olvidamos"` | Su despedida en el diario el día en que se va: «*nombre* se va del hormiguero. *Epitafio*.». Sin `fecha` no sale. |

- Con una `fecha` futura, deja a la persona en su sala hasta ese día. Si ya no está en
  ninguna, sale un aviso.
- Sin `fecha`, si la persona sigue en una sala, sale un aviso y su hormiga no aparece.
- Si una fecha está mal escrita, sale un aviso y se toma como «ya se fue».
- Si no caben todas las lápidas, se quitan las de los primeros de la lista, con un aviso.

```toml
[[ido]]
nombre = "CARLOS"

[[ido]]
nombre = "IRENE"
fecha = "2026-09-30"
epitafio = "se fue a otra colonia"
```

---

## 7. `calendario.toml`

Cada `[[fiesta]]` decora el hormiguero entre `desde` y `hasta`, los dos días incluidos.
Paso a paso, en el [capítulo 6](06-fiestas-y-halloween.md).

| Clave | Tipo | Por defecto | Qué hace |
|---|---|---|---|
| `nombre` | Texto | `"Fiesta"` | Para los avisos y para la pausa de la demo. |
| `desde` | Fecha de fiesta | `"01-01"` | El primer día. |
| `hasta` | Fecha de fiesta | La misma que `desde` | El último día. |
| `decoracion` | Texto | `"banderines"` | Cómo se decora (ver la lista). |
| `gorro` | Texto | Ninguno | El sombrero que llevan las hormigas esos días (ver la lista). |
| `mensaje` | Texto | El `nombre` | Sale en el cielo mientras dura la fiesta y en el diario el primer día. |
| `lugar` | Texto | Ninguno | Solo como nota: el hormiguero no lo usa. |

### Cómo se escriben las fechas

| Forma | Qué es | Ejemplo |
|---|---|---|
| `"DD-MM"` (o `"DD/MM"`) | Día fijo cada año | `"14-02"` |
| `"pascua"` | El Domingo de Resurrección | `"pascua"` |
| `"pascua+N"` | N días después | `"pascua+16"` |
| `"pascua-N"` | N días antes | `"pascua-47"` |

- Un rango puede cruzar el año: `desde = "15-12"` y `hasta = "06-01"`.
- Si una fecha está mal escrita, sale un aviso y esa fiesta no se tiene en cuenta.
- Escribe `[[fiesta]]` con dos corchetes. Con uno solo cabe una fiesta, y sale un aviso.

### Las decoraciones

`navidad`, `nochevieja`, `reyes`, `halloween`, `difuntos`, `andalucia`, `espana`,
`semana_santa`, `feria`, `carnaval`, `san_juan`, `cruces`, `corazones`, `libro`, `pi` y
`banderines` (la genérica).

Si escribes una que no existe, sale un aviso. La fiesta se mantiene (su mensaje y su
gorro), pero sin esa decoración.

### Los gorros

`fiesta`, `papa_noel`, `corona`, `capirote`, `bruja`, `flor` y `antifaz`.

Si escribes uno que no existe, sale un aviso y no se pinta.

### Si coinciden varias fiestas

- Se ponen las decoraciones de todas.
- El mensaje es el de la más corta (la más concreta). El día de un cumpleaños, en el cielo
  sale «FELIZ CUMPLE» en su lugar.
- El gorro es el de la más corta que tenga gorro.

```toml
[[fiesta]]
nombre = "Navidad"
desde = "15-12"
hasta = "06-01"
decoracion = "navidad"
mensaje = "¡Feliz Navidad desde el hormiguero!"

[[fiesta]]
nombre = "Nochebuena y Navidad"
desde = "24-12"
hasta = "25-12"
decoracion = "navidad"
gorro = "papa_noel"
mensaje = "¡Feliz Navidad!"

[[fiesta]]
nombre = "Carnaval"
desde = "pascua-49"
hasta = "pascua-47"
decoracion = "carnaval"
gorro = "antifaz"
mensaje = "¡Carnaval!"
```

En `ejemplos/calendario-andalucia.toml` hay un calendario más completo, con las fiestas de
Andalucía y de España.

---

## 8. Los colores

Donde se pide un color (`color` de una sala o de un miembro), vale cualquiera de estos:

- **Un nombre:** `negro`, `rojo`, `verde`, `amarillo`, `azul`, `magenta`, `cian`, `blanco`,
  `gris`, `gris_oscuro`, `naranja`, `rosa`, `morado`, `marron`, `dorado`, `arena`,
  `turquesa`, `lima`, `coral`, `salmon` y `plata`.
- **Un nombre con `_brillante`:** `negro_brillante`, `rojo_brillante`, `verde_brillante`,
  `amarillo_brillante`, `azul_brillante`, `magenta_brillante`, `cian_brillante`,
  `blanco_brillante`, `naranja_brillante`, `morado_brillante`, `marron_brillante`,
  `arena_brillante` y `plata_brillante`.
- **Un color exacto:** `"#RRGGBB"` o `"#RGB"`, por ejemplo `"#ff8800"`.
- **Un número** de 0 a 255 (la paleta de 256 colores de los terminales).

Las mayúsculas no importan, y `marrón` y `salmón` también valen con tilde. También se
entienden los nombres en inglés (`red`, `blue`, `gold`...).

Las paredes de un tipo de sala solo admiten `madera`, `azulejo`, `piedra` o un color exacto
(`"#RRGGBB"` o `"#RGB"`).

La paleta de la que salen los colores de las hormigas que no tienen uno: `rojo_brillante`,
`amarillo_brillante`, `cian`, `magenta_brillante`, `verde_brillante`, `naranja`,
`azul_brillante`, `rosa`, `blanco_brillante`, `turquesa`, `lima`, `coral`, `dorado`,
`morado` y `salmon`.

---

## 9. La carpeta `local/`

No se sube a git. Ahí van tus datos y lo que el hormiguero guarda solo.

| Fichero | Quién lo escribe | Qué es |
|---|---|---|
| `config.toml`, `salas/`, `tipos/`, `idos.toml`, `calendario.toml` | Tú | Tus ficheros, que se usan en lugar de los de ejemplo. |
| `openweather_clave.txt` | Tú | La clave de OpenWeather. |
| `entorno` | Tú | Variables para el servicio de la Pi y para `en-pantalla.sh`, una por línea (`NOMBRE=valor`). |
| `estado.json` | El hormiguero | La fundación y la semilla del primer arranque, el color de cada hormiga, dónde estaba cada una y lo excavado. Se guarda cada minuto y al pararlo. No lo edites. |
| `openweather.json` | El hormiguero | Los últimos datos de OpenWeather y el historial de los dos últimos años (si llovió, si nevó...), para el diario. |

`estado.json` solo se escribe con la hora de verdad: nunca en la demo, con `--fecha`,
`--hora`, `--dias` o `--acelerar`, ni con `--captura` o `--medir`. Para empezar de cero,
mira el [capítulo 9](09-problemas-frecuentes.md).

---

Anterior: [9. Problemas frecuentes](09-problemas-frecuentes.md) · Siguiente: [Índice de la guía](README.md)
