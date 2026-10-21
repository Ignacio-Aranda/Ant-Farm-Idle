# Ant Farm Idle

Un hormiguero en pixel art para dejar puesto en una pantalla. Cada persona de tu
equipo, tu familia o tu grupo de amigos es una hormiga con su nombre: tiene su sala,
baja al comedor a desayunar y a comer, va a por agua, cava túneles, sale a buscar
comida, celebra su cumpleaños y vive las estaciones, el tiempo de tu ciudad y las
fiestas del año. El hormiguero crece solo durante todo el año.

*A pixel-art ant farm for an always-on screen: every person in your team, family or
group of friends is an ant with their name, their room and their birthday. It grows
by itself over the year, follows your city's real weather and celebrates holidays.
Configuration and code are in Spanish.*

![El hormiguero de día](docs/dia.png)
![El hormiguero en Nochebuena](docs/noche.png)

## Probarlo

Hace falta Python 3.11 o más nuevo y pygame.

```bash
pip install pygame
python3 hormiguero_pixel.py --ventana
```

| Opción | |
|---|---|
| `--ventana` | En una ventana (si no, a pantalla completa). |
| `--demo` | Un año entero a toda velocidad, parando en las fechas importantes. |
| `--fecha 2026-12-24 --hora 21:00` | Ver un día y una hora concretos. |
| `--tiempo nieve` | Forzar el tiempo: `despejado`, `nublado`, `lluvia`, `tormenta`, `nieve` o `calima`. |
| `--captura imagen.png` | Sin pantalla: simula un rato y guarda una imagen. |
| `--medir` | Sin pantalla: mide lo que tarda cada fotograma. |

Teclas: `q` o `Esc` para salir, `f` pantalla completa, `i` fotogramas por segundo.

## Ponerlo a tu gusto

Todo se configura con ficheros de texto ([TOML](https://toml.io/es/)). Los cambios de
gente, idas y fiestas se aplican solos a los pocos segundos de guardar; lo demás
(salas, tipos, paisaje...) al reiniciar.

| Fichero | Qué hay |
|---|---|
| `salas/*.toml` | Una sala por fichero: su nombre, color, planta, tipo y la gente que trabaja en ella. |
| `tipos/*.toml` | Los tipos de sala: qué hacen allí las hormigas y qué muebles hay. Ver [tipos/LEEME.md](tipos/LEEME.md). |
| `idos.toml` | Los que se fueron: cada uno tiene su lápida en el cementerio. |
| `calendario.toml` | Las fiestas y cómo se decora el hormiguero. En `ejemplos/` hay uno con las fiestas de Andalucía y de España. |
| `config.toml` | Nombre del grupo, fecha de fundación, ciudad, tiempo real, horarios, salas que se excavan durante el año y paisaje. |

### Salas y gente

```toml
nombre = "Desarrollo"
color = "cian"
planta = 2          # de 1 (la más alta) a 4 (la más honda)
x = 40              # opcional: columna fija; sin x va en un hueco al azar de su planta
ancho = 40
tipo = "trabajo"    # trabajo, reuniones, despacho, comedor, fuente... (tipos/)

[[miembro]]
nombre = "Ana"
cumple = "14-03"    # día-mes: ese día lleva gorro de fiesta y hay tarta arriba
```

Los túneles y las rampas entre plantas se trazan solos, y las hormigas encuentran el
camino por ellos. Si una sala tiene `jefe = true`, quien esté en ella llama de vez en
cuando a alguien al despacho; las reuniones fijas se ponen con `[[reunion]]` (mira
`salas/reuniones.toml`).

### Muebles

Cada tipo de sala lleva sus muebles en huecos fijos (`izquierda`, `centro`, `derecha`,
`pared`...), y una sala puede añadir más con sus propios `[[mueble]]`:

```toml
[[mueble]]
pieza = "sofa"
sitio = "centro_derecha"
```

Hay escritorios, mesas, nevera, cafetera, fuente de agua, estanterías, vitrina con los
hallazgos de la colonia, pizarra, un reloj que marca la hora de verdad, sofá, plantas
que crecen con los días... La lista completa está en [tipos/LEEME.md](tipos/LEEME.md).

![Todos los muebles](docs/galeria-muebles.png)
![Los tipos de sala que vienen hechos](docs/galeria-tipos.png)

Las salas que excavan durante el año (despensa, museo, vivero de hongos, almacén y
biblioteca, se pueden cambiar en `[nido]`) se ponen en los huecos libres. Si ya no
caben, abren una planta más honda con una rampa nueva o las hacen más estrechas; si
el hormiguero está lleno del todo, se quedan sin hacer y lo cuenta el diario.

### Paisaje

En `config.toml` se elige lo que hay arriba y dónde (en % del ancho de la pantalla):
árboles, chumberas, farolas, bancos y casas en la superficie; catedral, ciudad, faro,
molino, torre o castillo al fondo. De noche se encienden las ventanas y las farolas,
el faro barre el cielo y el molino gira.

![Todas las piezas del paisaje, de día y de noche](docs/galeria-paisaje.png)

```toml
[[paisaje.suelo]]
pieza = "pino"
x = 22

[[paisaje.fondo]]
pieza = "faro"
x = 45
```

### Tiempo real

Con `[ciudad]` (latitud y longitud) el sol sale y se pone a su hora. Para que además
llueva, nieve o haya tormenta cuando de verdad pasa en tu ciudad, crea una clave
gratuita en [OpenWeather](https://openweathermap.org/api) y pásasela de una de estas
formas (mejor no la pongas en `config.toml` si vas a subirlo a algún sitio):

```bash
export OPENWEATHER_API_KEY=tu_clave
```

o guárdala en `local/openweather_clave.txt` (la carpeta `local/` no se sube a git).
Sin clave, o si se va internet, el tiempo sale de un modelo estadístico.

Cuando nieva, la nieve se queda encima de los árboles, los tejados, las lápidas y el
suelo, y en las cumbres de los montes, hasta un día después.

### Halloween

Con `esqueletos = true` en `[halloween]`, del 26 al 31 de octubre los que se fueron
(`idos.toml`) salen del cementerio y se pasean por el hormiguero como hormigas
esqueleto, también de noche.

## En una Raspberry Pi

Pensado para una Raspberry Pi 3 o más nueva con **Raspberry Pi OS Lite** (sin
escritorio, para que vaya lo más fluido posible) conectada a una pantalla.

1. Graba Raspberry Pi OS Lite con Raspberry Pi Imager (con WiFi, SSH y tu zona horaria).
2. Copia el repositorio a la Pi (por ejemplo, con `git clone` o `scp -r`).
3. En la Pi: `bash ~/Ant-Farm-Idle/instalar-pi.sh`

El instalador pone pygame y la fuente DejaVu, crea el servicio `hormiguero` (arranca al
encender y se relanza solo si se cierra) y evita que la pantalla se apague. Desde SSH:

```bash
sudo systemctl restart hormiguero     # relanzarlo
sudo systemctl stop hormiguero        # pararlo
journalctl -u hormiguero -f           # ver mensajes y errores
./en-pantalla.sh python3 hormiguero_fb.py --demo   # lanzar otra cosa en la pantalla un rato
```

En la Pi el servicio usa `hormiguero_fb.py`, que pinta directamente en el framebuffer
(`/dev/fb0`): en una Pi 3 sin escritorio, pygame con aceleración gráfica deja la
pantalla en negro.

## Tus datos

Los ficheros de `salas/`, `idos.toml` y `calendario.toml` de este repositorio son de
ejemplo, con gente inventada. Si quieres tener los tuyos fuera del repositorio (para
no subir nombres ni cumpleaños), guárdalos donde quieras y arranca con `--salas`,
`--tipos`, `--idos`, `--calendario` y `-c` apuntando a ellos.

## Galerías

Las imágenes de muebles, tipos de sala y paisaje de `docs/` se regeneran con
`python3 herramientas/galeria.py` (por ejemplo, después de añadir una pieza nueva).

## Licencia

MIT. Ver [LICENSE](LICENSE).
