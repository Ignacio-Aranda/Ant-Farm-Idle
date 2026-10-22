# Ant Farm Idle

Un hormiguero en pixel art para dejar puesto en una pantalla. Cada persona de tu
equipo, tu familia o tu grupo de amigos es una hormiga con su nombre: tiene su sala,
baja al comedor a desayunar y a comer, va a por agua, cava túneles, sale a buscar
comida, celebra su cumpleaños y vive las estaciones, el tiempo de tu ciudad y las
fiestas del año. El hormiguero crece solo durante todo el año.

*A pixel-art ant farm for an always-on screen: every person in your team, family or
group of friends is an ant with their name, their room and their birthday. It grows
by itself over the year, follows your city's real weather and celebrates holidays.
Everything is in Spanish.*

![El hormiguero de día](docs/dia.png)
![El hormiguero en Nochebuena](docs/noche.png)

## Qué hace

- **Cada hormiga es una persona**, con su nombre, su color y su sala. Trabaja, desayuna y
  come en el comedor, va a por agua, acude a las reuniones y, si hay jefe, a veces la
  llaman al despacho.
- **Crece solo.** Durante el año las hormigas excavan salas nuevas (despensa, museo,
  vivero de hongos, almacén, biblioteca) y encuentran objetos que acaban en las vitrinas.
- **Sale a por comida**: cazan grillos, y si alguien tira medio bocadillo, hacen falta
  varias para moverlo.
- **El cielo de tu ciudad.** El sol sale y se pone a su hora, de noche hay estrellas y
  luciérnagas, y el tiempo puede ser el real: lluvia, tormenta, nieve que cubre las cosas,
  calima...
- **Estaciones y fiestas.** Los árboles florecen y pierden la hoja. Navidad, Carnaval,
  Halloween o las fiestas que tú elijas decoran el hormiguero.
- **Cumpleaños**: cartel de «FELIZ CUMPLE», tarta, regalos, globos y gorro de fiesta.
- **Los que se fueron** tienen su lápida en el cementerio y, si quieres, salen como
  esqueletos en Halloween.
- **Un diario** abajo cuenta lo que va pasando.
- **No se olvida de nada**: aunque se apague, al volver cada hormiga sigue en su sitio, con
  su color y con todo lo que ha excavado.

## Probarlo en tu ordenador

Hace falta Python 3.11 o más nuevo y pygame. Para instalar pygame:

```bash
# Debian, Ubuntu y Raspberry Pi OS
sudo apt install python3-pygame fonts-dejavu-core
# macOS y otros sistemas
python3 -m pip install pygame
# Windows
py -m pip install pygame
```

Descarga el hormiguero (botón verde **Code → Download ZIP**, y descomprímelo) y,
desde su carpeta:

```bash
python3 hormiguero_pixel.py --ventana     # en Windows: py hormiguero_pixel.py --ventana
```

Teclas: `q` o `Esc` para salir, `f` pantalla completa.

| Opción | |
|---|---|
| `--ventana` | En una ventana (si no, a pantalla completa). |
| `--demo` | Un año entero a toda velocidad, parando en las fechas importantes. |
| `--fecha 2026-12-24 --hora 21:00` | Ver un día y una hora concretos. |
| `--tiempo nieve` | Ver otro tiempo: `despejado`, `nublado`, `lluvia`, `tormenta`, `nieve` o `calima`. |

Paso a paso, y qué hacer si algo falla, en el [capítulo 1 de la guía](docs/guia/01-instalacion.md).

## Ponerlo a tu gusto

Todo se cambia con ficheros de texto. Los que vienen son **de ejemplo**, con gente
inventada. Para poner los tuyos, cópialos a la carpeta `local/` y edita las copias: el
hormiguero usa los de `local/` en lugar de los de ejemplo, y así, cuando actualices el
hormiguero, no pierdes nada.

```bash
mkdir -p local
cp -r salas idos.toml calendario.toml config.toml local/
```

| Fichero | Qué hay |
|---|---|
| `salas/*.toml` | Una sala por fichero: su nombre, color, planta, tipo y la gente que trabaja en ella. |
| `idos.toml` | Los que se fueron: cada uno tiene su lápida en el cementerio. |
| `calendario.toml` | Las fiestas y cómo se decora el hormiguero. En `ejemplos/` hay uno con las fiestas de Andalucía y de España. |
| `config.toml` | El nombre del grupo, la ciudad, el tiempo real, los horarios, las salas que se excavan durante el año, el paisaje y Halloween. |

Una sala con su gente:

```toml
nombre = "Desarrollo"
color = "cian"
planta = 2          # de 1 (la más alta) a 4 (la más honda)
ancho = 40
tipo = "trabajo"    # trabajo, reuniones, despacho, comedor, fuente...

[[miembro]]
nombre = "Ana"
cumple = "14-03"    # día-mes: ese día lleva gorro de fiesta y hay tarta arriba
```

Los túneles y las rampas se hacen solos. Si añades o quitas a alguien, o cambias las
fiestas, se ve a los pocos segundos de guardar. Otros cambios necesitan reiniciar el
hormiguero; una franja amarilla arriba te lo recuerda, y también te avisa si algo está
mal escrito.

### Lo que puedes poner

Cada tipo de sala trae sus muebles, y puedes añadir más:

![Todos los muebles](docs/galeria-muebles.png)
![Los tipos de sala que vienen hechos](docs/galeria-tipos.png)

Y arriba, el paisaje que quieras: árboles, chumberas, farolas, bancos y casas; al fondo,
catedral, ciudad, faro, molino, torre o castillo.

![Todas las piezas del paisaje, de día y de noche](docs/galeria-paisaje.png)

### El tiempo de verdad

Pon tu ciudad en `config.toml` y el sol saldrá a su hora. Para que además llueva o nieve
cuando de verdad pasa en tu ciudad, crea una clave gratuita en
[OpenWeather](https://openweathermap.org/api) y guárdala en `local/openweather_clave.txt`:

```bash
mkdir -p local && echo tu_clave > local/openweather_clave.txt
```

Sin clave, o si se va internet, el tiempo se inventa, según la época del año. Todos los
detalles, en el [capítulo 7 de la guía](docs/guia/07-tiempo-y-ciudad.md).

## Dejarlo puesto en una Raspberry Pi

Pensado para una Raspberry Pi 3 o más nueva con **Raspberry Pi OS Lite** (sin
escritorio, para que vaya lo más fluido posible) conectada a una pantalla.

1. Graba Raspberry Pi OS Lite con Raspberry Pi Imager (con WiFi, SSH y tu zona horaria).
2. Copia la carpeta del hormiguero a la Pi.
3. En la Pi: `bash ~/Ant-Farm-Idle/instalar-pi.sh`

Desde ese momento arranca solo al encender la Pi y la pantalla no se apaga. Para
manejarlo por SSH:

```bash
sudo systemctl restart hormiguero     # reiniciarlo
sudo systemctl stop hormiguero        # pararlo
./en-pantalla.sh python3 hormiguero_fb.py --demo   # ver la demo en la pantalla (Ctrl+C: vuelve el hormiguero)
```

Paso a paso, en el [capítulo 1 de la guía](docs/guia/01-instalacion.md).

## Guía de usuario

Todo explicado paso a paso y sin dar nada por sabido, en [la guía](docs/guia/README.md):

1. [Instalación](docs/guia/01-instalacion.md)
2. [Primeros pasos](docs/guia/02-primeros-pasos.md)
3. [Salas y gente](docs/guia/03-salas-y-gente.md)
4. [Tipos de sala y muebles](docs/guia/04-tipos-y-muebles.md)
5. [El paisaje de arriba](docs/guia/05-paisaje.md)
6. [Fiestas y Halloween](docs/guia/06-fiestas-y-halloween.md)
7. [El tiempo y tu ciudad](docs/guia/07-tiempo-y-ciudad.md)
8. [Cómo crece el hormiguero](docs/guia/08-como-crece.md)
9. [Problemas frecuentes](docs/guia/09-problemas-frecuentes.md)
10. [Referencia](docs/guia/10-referencia.md)

## Licencia

MIT. Ver [LICENSE](LICENSE).
