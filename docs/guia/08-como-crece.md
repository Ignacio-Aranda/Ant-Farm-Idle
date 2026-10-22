# Cómo crece el hormiguero

En este capítulo vas a aprender cómo se excava el hormiguero a lo largo del año, cómo
elegir las salas nuevas, qué encuentran las hormigas al cavar y qué se guarda para que un
reinicio o un apagón no le hagan perder nada.

Antes de empezar:

- Lo que se configura aquí está en `config.toml`. Edita tu copia, la de
  `local/config.toml` (mira el [capítulo 2](02-primeros-pasos.md)).
- Los cambios de `config.toml` se ven **al reiniciar** el hormiguero. En el ordenador,
  ciérralo con `q` y vuelve a lanzarlo. En la Pi:

```bash
sudo systemctl restart hormiguero
```

- Las órdenes se escriben con `python3`. En Windows, escribe `py` en su lugar.
- En tu `config.toml` ya están las secciones `[nido]` y `[horario]`. Cambia sus líneas;
  no pegues otra sección con el mismo nombre debajo, porque una sección repetida hace
  que no se pueda leer el fichero entero.

## El día 0

El día de la fundación (el día 0) el hormiguero ya tiene:

- **Las plantas.** Bajo tierra hay cuatro plantas, como en un edificio: la 1 es la más
  cercana a la superficie y la 4, la más honda.
- **Las salas** de la carpeta `salas/`, cada una en su planta. Dónde se pone cada una lo
  cuenta el [capítulo 3](03-salas-y-gente.md).
- **Los túneles.** En cada planta, una galería une sus salas.
- **Las rampas.** Una rampa baja desde la entrada, en la superficie, hasta la planta 1, y
  otra de cada planta a la siguiente, hasta la más honda que tenga salas.

Los túneles y las rampas se trazan solos: no hay que configurar nada. El hormiguero
prueba varias colocaciones hasta encontrar una en la que se llega andando a todas las
salas y ninguna rampa atraviesa una sala. Si no lo consigue, lo cuenta en la franja
amarilla, por ejemplo «Ventas no cabe en la planta 2 (no deja sitio a las rampas)»: esa
sala se queda fuera para que se pueda llegar a las demás.

Todo sale de la **semilla** y de la **fecha de fundación**: con las mismas salas, el
hormiguero queda siempre igual. Si cambias las salas o la `entrada`, al reiniciar se
vuelve a trazar todo y puede quedar distinto.

## La entrada

La entrada es el agujero por el que las hormigas salen a la superficie. Encima se va
haciendo un montículo con la tierra que sacan al cavar, que crece con las obras. La tarta
de los cumpleaños también se pone cerca de la entrada.

Dónde va se elige en la sección `[nido]`, con `entrada`:

```toml
[nido]
entrada = 20
cavar = "encendido"
obras = ["despensa", "museo", "hongos", "almacen", "biblioteca"]
```

- `entrada` es una columna. El hormiguero mide 160 columnas de ancho: la 3 es casi el
  borde izquierdo, la 80 el centro y la 156 casi el borde derecho. Si no la pones, es la
  20.
- Es la columna **preferida**, no siempre la exacta. La rampa que baja desde la entrada
  no puede atravesar ninguna sala de la planta 1, y además la entrada se arrima a las
  salas de esa planta para que la galería no sea más larga. Si pides una columna lejos de
  esas salas, o hay salas en medio, puede acabar bastante lejos. Mira en pantalla dónde
  ha quedado.
- En el paisaje (el [capítulo 5](05-paisaje.md)) las posiciones van en % del ancho. Para
  pasar una columna a %, divídela entre 1,6: la columna 20 está en el 12,5 %. Te sirve
  para que la entrada no quede debajo de un árbol.

## Las obras del año

Después del primer día, las hormigas empiezan a cavar. A lo largo del año:

1. Excavan **salas nuevas**, una detrás de otra, con la galería que lleva hasta cada una.
2. Si no les cabe una sala en ninguna planta, cavan antes una **rampa a una planta más
   honda** (como mucho, hasta la 4).
3. Después de las primeras obras, si encuentran sitio, abren una **segunda salida** a la
   superficie.
4. Al final, alargan las galerías **hacia los bordes**, como si exploraran.

Mientras tanto verás crecer el hueco poco a poco. Las hormigas van y vienen del sitio
donde se cava y sacan la tierra a la superficie, junto a la entrada.

### Qué salas se excavan: `obras`

La línea `obras` de `[nido]` dice qué salas se excavan y en qué orden. Si no la pones,
son estas cinco:

| En `obras` | Nombre en el cartel | Ancho (columnas) |
|---|---|---|
| `"despensa"` | Despensa | 24 |
| `"museo"` | Museo de hallazgos | 28 |
| `"hongos"` | Vivero de hongos | 22 |
| `"almacen"` | Almacén | 16 |
| `"biblioteca"` | Biblioteca | 20 |

- Cada obra usa el **tipo de sala con su mismo nombre**: la despensa, el de
  `tipos/despensa.toml`; el museo, el de `tipos/museo.toml`... Los tipos (sus muebles,
  sus paredes y para qué sirven) los cuenta el [capítulo 4](04-tipos-y-muebles.md).
- La despensa es importante: ahí guardan la comida que traen de fuera. Mientras no
  exista, la llevan al comedor (o, si no hay comedor, a otra sala).
- Puedes quitar salas, cambiar el orden o repetir una (salen dos salas con el mismo
  nombre).
- Con `obras = []` no se excava ninguna sala nueva. Siguen cavando galerías y, si hay
  sitio, la segunda salida.

**Una sala nueva que no está en la tabla.** Por ejemplo, un cine:

```toml
[nido]
entrada = 20
cavar = "encendido"
obras = ["despensa", "museo", "Cine"]
```

- En el cartel sale tal cual lo escribes: «Cine». Mide 22 columnas.
- Necesita un tipo llamado igual pero en minúsculas: `cine.toml`, en la carpeta de tipos.
  Por ejemplo, con un sofá y una pantalla:

```toml
funcion = "otra"
paredes = "piedra"
suelo = "baldosa"

[[mueble]]
pieza = "sofa"
sitio = "centro"

[[mueble]]
pieza = "pantalla"
```

- El tipo va en la carpeta `tipos/` del hormiguero. Si usas `local/tipos/`, va ahí,
  junto con todos los demás (mira el [capítulo 4](04-tipos-y-muebles.md)).
- Usa nombres de una palabra y sin tildes. Así es fácil acertar con el nombre del
  fichero del tipo.
- Si no hay tipo, la sala se excava igual, pero vacía, y sale el aviso «config: [nido] la
  obra «cine» no tiene tipo en tipos/ (será una sala vacía)».

### Dónde se ponen

- Junto a la galería de la planta más honda que tenga sitio, una vez a un lado y otra al
  otro.
- Si no caben en ninguna planta, cavan una rampa a una planta nueva, más honda. El diario
  dice «Terminan la rampa a la planta 3.».
- Si no pueden bajar más (ya están las cuatro plantas o no hay sitio para la rampa), las
  hacen más estrechas, de 4 en 4 columnas, hasta un mínimo de 14. Nunca tan estrechas que
  no quepa el mueble más ancho de su tipo.
- Si aun así no caben, se quedan sin hacer. Cuando acaban las obras, el diario lo cuenta:
  «Ya no cabe nada más en el hormiguero: se quedan sin hacer Biblioteca.».

Para que quepan todas, deja sitio libre en las plantas al colocar tus salas.

### Cuánto tardan

- El trabajo de todo el año se reparte en **unos 11 meses**. Si hay menos obras, cada
  una dura más. No se puede cambiar.
- Entre obra y obra descansan unos días (de 2 a 6).
- **El ritmo va con las estaciones:** en primavera cavan más deprisa, y en invierno van a
  la mitad de ritmo que en verano. En el hemisferio sur, al revés (mira el
  [capítulo 7](07-tiempo-y-ciudad.md)).
- **La roca cuesta más.** Las manchas grises de la tierra son roca: atravesarla cuesta el
  triple que la arena. El diario lo celebra: «¡Han atravesado una roca!».

Con las cinco salas de siempre, la primera (la despensa) suele estar lista entre mes y
medio y tres meses y medio después de la fundación, y la última (la biblioteca), hacia el
décimo mes. Depende de la semilla y de la estación en la que empiece.

Cuando se terminan todas las obras, el hormiguero ya no crece más: se queda como está. Las
fiestas, el tiempo, los cumpleaños y la vida de las hormigas siguen igual.

Para ver ahora cómo estará un día concreto, usa `--dias` con el número del día del
hormiguero. Por ejemplo, el día 300 (no guarda nada):

```bash
python3 hormiguero_pixel.py --ventana --dias 300
```

O mira el año entero en la demo, como en el [capítulo 2](02-primeros-pasos.md):

```bash
python3 hormiguero_pixel.py --ventana --demo
```

### La segunda salida

Después de las primeras obras, las hormigas intentan abrir una segunda salida a la
superficie. Sube desde la galería de la planta 1 y sale lo más lejos posible de la
entrada (a 25 columnas como poco).

- Cuando se termina, el diario dice «Abren una segunda salida a la superficie.» y encima
  se ve un montículo pequeño.
- Desde entonces, cada hormiga sale por la que le pilla más cerca. La tierra la siguen
  sacando por la entrada principal.
- **No siempre hay sitio.** La rampa no puede pasar por encima de las salas de la planta 1,
  y tiene que poder subirse desde dentro (no puede empezar justo encima de una rampa que
  baja, donde se quedaría colgada). Con las salas del ejemplo, sale en algo más de la mitad
  de los hormigueros.

## Hallazgos y museo

Al terminar una obra, muchas veces encuentran algo enterrado: una peseta de 1982, una
pieza de Lego, un fósil de amonites, una Raspberry Pi 1... Hay doce cosas distintas, y
cada una sale como mucho una vez. Qué sale y dónde depende de la semilla.

- El diario lo cuenta: «Hallazgo: una moneda romana.».
- El objeto se queda a la vista en la tierra, junto al túnel donde apareció.
- Y además se expone en las **vitrinas**. Cada vitrina enseña seis hallazgos: la primera,
  los seis primeros; la segunda, del séptimo al duodécimo.
- El museo (el tipo `museo`) trae dos vitrinas, así que caben todos. Lo encontrado antes
  de que se excave el museo también sale en él cuando lo inauguran.
- Cualquier sala puede tener vitrinas: añádele un `[[mueble]]` con `pieza = "vitrina"`
  (mira el [capítulo 4](04-tipos-y-muebles.md)). Enseña los mismos hallazgos.
- Si quitas el museo de `obras`, las hormigas siguen encontrando cosas. Se ven en la
  tierra y en las vitrinas que haya.

## Cavar sólo encendido o por fecha: `cavar`

La línea `cavar` de `[nido]` decide qué pasa con las obras cuando el hormiguero está
apagado.

**`cavar = "encendido"`** (lo normal). Las hormigas sólo cavan mientras el hormiguero está
en marcha. Una semana apagado es una semana sin obras.

- Lo que llevan cavado se guarda en `local/estado.json` (mira más abajo).
- Si el reloj da un salto de más de 5 minutos (el ordenador se suspende, alguien cambia la
  hora), ese rato no cuenta.
- El número de días de arriba («Día 40 del hormiguero») sigue contando aunque esté
  apagado. Lo que se para son las obras.
- El diario apunta cada sala el día en que de verdad se terminó.

**`cavar = "fecha"`**. Las obras avanzan con los días desde la fundación, esté encendido
o no. Al arrancar, el hormiguero enseña lo que debería estar hecho ese día.

Es útil para que un hormiguero nuevo salga ya crecido, como si llevara meses: pon una
fundación pasada en `[general]` y `cavar = "fecha"` en `[nido]`.

```toml
[general]
nombre = "la Oficina"
fundacion = "2026-01-01"
fps_pixel = 20
```

```toml
[nido]
entrada = 20
cavar = "fecha"
obras = ["despensa", "museo", "hongos", "almacen", "biblioteca"]
```

Escribe `"encendido"` o `"fecha"` (las mayúsculas dan igual). Con cualquier otra cosa
(por ejemplo, `"encendida"`) sale un aviso y se usa `"encendido"`.

En la demo, y con `--fecha`, `--hora`, `--dias` o `--acelerar`, las obras van siempre por
fecha, como si el hormiguero hubiera estado encendido todos los días, y no se guarda nada.

## El diario

El diario es la franja oscura de abajo del todo. Cuenta dos clases de cosas:

- **Lo que ha pasado cada día**, con cuándo fue: «Hoy · ...», «Ayer · ...» o «Hace 3
  días · ...».
- **Lo que está pasando ahora**, en amarillo, empezando por «¡Ahora!». Se queda 25
  segundos.

Cada 8 segundos cambia a otra cosa. Van pasando las cuatro últimas del diario y las
cuatro últimas noticias.

Esto es lo que apunta el diario:

| Qué | Ejemplo |
|---|---|
| La fundación (el día 0) | «Se funda el hormiguero de la Oficina: Ana, Luis, Marta...» |
| Una sala nueva | «Inauguran: Despensa.» |
| Una rampa a otra planta | «Terminan la rampa a la planta 3.» |
| La segunda salida | «Abren una segunda salida a la superficie.» |
| Una roca atravesada | «¡Han atravesado una roca!» |
| Un hallazgo | «Hallazgo: una peseta de 1982.» |
| Salas que no caben | «Ya no cabe nada más en el hormiguero: se quedan sin hacer Biblioteca.» |
| Un mueble nuevo | «Novedad en Desarrollo: un sofá.» ([capítulo 4](04-tipos-y-muebles.md)) |
| Una fiesta, el primer día | El mensaje de la fiesta ([capítulo 6](06-fiestas-y-halloween.md)) |
| Un cumpleaños | «¡Cumpleaños de Ana! Hay tarta arriba.» |
| Alguien que llega o se va | «Llega Carmen al hormiguero. ¡Bienvenida/o!» ([capítulo 3](03-salas-y-gente.md)) |
| El tiempo | «Tormenta. Todas dentro.» ([capítulo 7](07-tiempo-y-ciudad.md)) |

Las noticias de «¡Ahora!» son lo que hacen las hormigas en ese momento: una reunión que
empieza, el jefe que llama a alguien al despacho, la comida que guardan, una araña o unas
hormigas rojas que se acercan...

Al reiniciar, el diario se rehace solo, con todo lo que ha pasado desde la fundación. Las
noticias de «¡Ahora!», en cambio, se pierden.

## La memoria del hormiguero: `local/estado.json`

La primera vez que arrancas el hormiguero con la hora de verdad, crea el fichero
`local/estado.json`. En cada arranque lo vuelve a leer. Por eso reiniciar la Pi, relanzar
el servicio o un apagón no cambian nada.

No se crea ni se toca en la demo, con `--fecha`, `--hora`, `--dias` o `--acelerar`, ni al
hacer capturas con `--captura` o `--medir`.

### Qué guarda

- **La fundación y la semilla**, si no las pones en `config.toml`. La fundación es el día
  del primer arranque, y la semilla se elige al azar una sola vez.
- **El color de cada hormiga** que no tiene uno fijo en su sala. Se elige una vez y ya no
  cambia.
- **Lo que llevan cavado** (con `cavar = "encendido"`) y el día en que se terminó cada
  obra, para el diario. También si cavan encendido o por fecha.
- **Dónde estaba cada hormiga.** Al volver a arrancar, sigue en el mismo sitio.

Lo cavado y dónde estaba cada hormiga se guardan aparte para cada hormiguero (cada
fundación con su semilla). Así, una prueba con otra semilla, por ejemplo con
`--semilla 7`, tiene lo suyo y no toca tu hormiguero de verdad.

Si `config.toml` tiene una errata y no se puede leer, el hormiguero sigue con su fundación
y su semilla de siempre, y cavando como la última vez (encendido o por fecha): una errata
no te cambia de hormiguero. Eso sí, hasta que la arregles, lo demás de `config.toml` no
cuenta: se usan los valores de siempre.

### Cuándo se guarda

Cada minuto, y al cerrar el hormiguero (con `q`, con `Esc`, al cerrar la ventana o al
pararlo con `sudo systemctl stop hormiguero`). En un apagón, como mucho se pierde el
último minuto.

No edites `estado.json` a mano. Para hacer una copia de seguridad de tu hormiguero, copia
la carpeta `local/` entera: ahí están también tus ficheros.

En `local/` también puede haber:

- `openweather.json`: el último tiempo de OpenWeather y lo que hizo cada día de los dos
  últimos años, para el diario (lo escribe el hormiguero).
- `openweather_clave.txt` y `entorno`: tu clave de OpenWeather, si la pusiste ahí
  ([capítulo 7](07-tiempo-y-ciudad.md)).

### Que no dependa del fichero

Si la fundación y la semilla salieron del primer arranque, están al principio de
`local/estado.json`, así:

```text
{
 "inicio": {
  "fundacion": "2026-10-22",
  "semilla": 22111
 },
```

Puedes copiarlas a `[general]` de tu `config.toml`. Con los mismos números sigue siendo
el mismo hormiguero, y aunque algún día se pierda `estado.json`, las salas y los túneles
volverán a salir igual:

```toml
[general]
nombre = "la Oficina"
fundacion = "2026-10-22"
semilla = 22111
fps_pixel = 20
```

### Empezar de cero

Para que el hormiguero vuelva a empezar, hay que borrar `local/estado.json` **con el
hormiguero parado**. Si lo borras con él en marcha, lo vuelve a escribir al minuto o al
cerrarlo.

**En la Pi:**

1. Para el servicio:

```bash
sudo systemctl stop hormiguero
```

2. Borra el fichero:

```bash
rm ~/Ant-Farm-Idle/local/estado.json
```

3. Vuelve a arrancarlo:

```bash
sudo systemctl start hormiguero
```

**En el ordenador:**

1. Cierra el hormiguero con `q`.
2. Borra el fichero `estado.json` de la carpeta `local` (en Windows, con el Explorador de
   archivos). En macOS o Linux, dentro de la carpeta del hormiguero:

```bash
rm local/estado.json
```

3. Vuelve a lanzarlo.

Qué pasa después:

- **Si en `config.toml` no hay `fundacion` ni `semilla`:** es un hormiguero nuevo. Hoy es
  el día 0, sale otra semilla (las salas y los túneles quedan distintos) y el diario
  empieza con «Se funda el hormiguero...».
- **Si están en `config.toml`:** las salas y los túneles quedan igual y el día del
  hormiguero sigue contando desde la misma fundación. Con `cavar = "encendido"`, las obras
  empiezan otra vez desde cero.
- En los dos casos, las hormigas sin color fijo pueden cambiar de color.

**Otra forma, sin perder nada:** pon otra `semilla` en `[general]` de `config.toml` y
reinicia. Sale otro hormiguero, con la misma fundación (el día del hormiguero sigue
contando), y el de antes sigue guardado en `estado.json`: vuelve si pones la semilla de
antes (o quitas la línea, si no la tenías).

## El horario: `[horario]`

```toml
[horario]
desayuno = "10:30-11:00"
comida = "13:30-15:30"
jornada = "09:00-18:00"
```

| Línea | Qué pasa a esas horas |
|---|---|
| `desayuno` | Muchas hormigas bajan al comedor. |
| `comida` | Casi todas bajan al comedor. |
| `jornada` | Quien está en una sala con `jefe = true` sólo llama a gente al despacho en este horario, y sólo de lunes a viernes ([capítulo 3](03-salas-y-gente.md)). |

- Se escribe así: `"HH:MM-HH:MM"`, con la hora de inicio y la de fin en formato de 24
  horas, y entre comillas.
- Si está mal escrito, sale un aviso como «horario: comida mal escrito (13:30 a 15:30)» y
  se usa el horario de siempre.
- El desayuno y la comida valen todos los días, también los fines de semana.
- Para comer hace falta un comedor: una sala de tipo `comedor` (o de otro tipo con
  `funcion = "comedor"`). Si no hay, no tienen dónde ir.
- La hora de dormir no se pone aquí: duermen de noche, entre la puesta y la salida del sol
  de tu ciudad ([capítulo 7](07-tiempo-y-ciudad.md)). Las reuniones llevan su propia hora
  ([capítulo 3](03-salas-y-gente.md)).
- Si pusiste `zona_horaria`, las horas son las de la ciudad.

---

Anterior: [7. El tiempo y tu ciudad](07-tiempo-y-ciudad.md) · Siguiente: [9. Problemas frecuentes](09-problemas-frecuentes.md)
