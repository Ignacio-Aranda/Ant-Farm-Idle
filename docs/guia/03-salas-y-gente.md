# Salas y gente

En este capítulo vas a aprender a describir las salas del hormiguero y a la gente que
vive en ellas: quién está en cada sala, sus cumpleaños, las reuniones, quién llega y
quién se va.

## Antes de empezar

- **Cada sala es un fichero de texto** que termina en `.toml`. Tus salas van en la carpeta
  `local/salas/`. Si todavía no la has creado, se usan las de ejemplo de `salas/`. Cómo
  crear `local/` lo cuenta el [capítulo 2](02-primeros-pasos.md#crear-tu-carpeta-local).
- **El nombre del fichero lo eliges tú.** Mejor en minúsculas, sin espacios ni tildes:
  `ventas.toml`, `cocina.toml`. Sirve para nombrar la sala en las reuniones
  (`quien = "ventas"`). Los ficheros que empiezan por un punto no se leen.
- **Los que se fueron** están en otro fichero: `local/idos.toml` (o `idos.toml`).
- **Si algo está mal escrito**, el hormiguero no se para: usa un valor por defecto (o deja
  fuera lo que no entiende) y lo cuenta en una franja amarilla arriba de la pantalla.

Las órdenes de esta guía se escriben con `python3`. En Windows, escribe `py` en su lugar
(mira el [capítulo 2](02-primeros-pasos.md)).

## Una sala completa

Así es una sala con todo lo que se le puede poner. Cópiala en `local/salas/ventas.toml` y
cambia lo que quieras:

```toml
# Sala de Ventas
nombre = "Ventas"        # lo que pone en el cartel
color = "naranja"        # el color de las letras del cartel
planta = 2               # de 1 (la de arriba) a 4 (la más honda)
x = 60                   # opcional: la columna donde empieza la sala
ancho = 36               # la anchura, en columnas (como mínimo 14)
tipo = "trabajo"         # los muebles y para qué sirve (capítulo 4)
jefe = false             # con true, quien está aquí llama a gente a esta sala

[[miembro]]
nombre = "Jorge"
cumple = "02-07"

[[miembro]]
nombre = "Paula"
cumple = "23-11"
color = "rosa"

[[miembro]]
nombre = "Iván"
cumple = "09-05"
alta = "2026-11-02"

[[reunion]]
nombre = "Previsión de ventas"
dia = "miércoles"
hora = "12:00"
minutos = 45
quien = "ventas"

[[mueble]]
pieza = "pizarra"
sitio = "pared_derecha"
```

Lo que va después de `#` es un comentario: el hormiguero no lo lee (salvo si va entre
comillas, como en `color = "#ff8800"`).

> **Ojo con el orden.** Las claves de la sala (`nombre`, `color`, `planta`, `x`, `ancho`,
> `tipo` y `jefe`) van **arriba del todo**, antes del primer `[[...]]`. Todo lo que
> escribes debajo de un `[[miembro]]` es de esa persona. Si pones `jefe = true` al final
> del fichero, no es de la sala sino del último bloque (en este ejemplo, del mueble). Sale
> el aviso «salas/ventas.toml: «jefe» está dentro de un [[mueble]] (pizarra) y la sala no lo
> ve; ponlo arriba, antes del primer [[...]]».

## La sala

| Clave | Qué es | Si no la pones |
|---|---|---|
| `nombre` | Lo que pone en el cartel de la sala. Si es muy largo, sale con letra más pequeña o recortado. | El nombre del fichero, sin `.toml`. |
| `color` | El color de las letras del cartel. Mira [Colores](#colores). | `blanco` |
| `planta` | En qué planta está: 1 es la de arriba, junto a la superficie; 4, la más honda. | `2` |
| `x` | La columna donde empieza la sala por la izquierda. | Un hueco al azar de su planta. |
| `ancho` | La anchura de la sala, en columnas. Como mínimo, 14. | `32` |
| `tipo` | El tipo de sala: sus muebles, sus paredes, su suelo y para qué sirve. Los tipos están en el [capítulo 4](04-tipos-y-muebles.md). Da igual cómo escribas las mayúsculas y las tildes: `"Almacén"` es el tipo `almacen`. | `trabajo` |
| `jefe` | `true` o `false`. Mira [El jefe](#el-jefe). | `false` |

### Dónde se pone cada sala

- El hormiguero mide **160 columnas** de ancho, de un lado a otro de la pantalla. En cada
  planta se dejan libres 3 columnas en cada borde y, entre sala y sala, al menos 4.
- Sumando todas las salas de una planta, caben unas **110 columnas** con holgura. A veces
  cabe algo más: depende de por dónde pasen las rampas.
- Con `x`, la sala empieza en esa columna. Vale de 3 hasta 157 menos el ancho de la sala
  (con `ancho = 36`, hasta 121); si te pasas, se queda pegada al borde. Si choca con otra
  sala, sale el aviso «Ventas: la columna 60 choca con otra sala» y se pone en un hueco
  libre.
- Sin `x`, la sala va en un hueco al azar de su planta. Primero se colocan las salas con
  `x` y después las demás, por orden alfabético del nombre de fichero.
- Los túneles y las rampas entre plantas se hacen solos, y las hormigas encuentran el
  camino.
- El azar sale siempre igual: depende de la `semilla` del hormiguero (la de `config.toml`
  o, si no la pones, una que se elige la primera vez y se guarda). Con las mismas salas,
  el hormiguero queda siempre igual. Si añades o quitas una sala, o le cambias la
  `planta`, el `ancho` o la `x`, al reiniciar se vuelven a colocar todas y puede quedar
  distinto.
- Deja algo de sitio libre. Durante el año, las hormigas excavan salas nuevas (la
  despensa, el museo...) en los huecos que queden.

**Si una sala no cabe** en su planta, sale el aviso «Ventas no cabe en la planta 2» y la
sala no aparece. Su gente vive mientras tanto en el comedor. Para arreglarlo, hazla más
estrecha, estrecha otras salas de esa planta o cámbiala de planta, y reinicia.

## La gente: `[[miembro]]`

Cada bloque `[[miembro]]` es una persona, y cada persona es una hormiga.

| Clave | Qué es | ¿Hace falta? |
|---|---|---|
| `nombre` | Lo que sale encima de la hormiga. | Sí. Un `[[miembro]]` sin nombre no sale (y hay aviso). |
| `cumple` | Su cumpleaños: día y mes, `"14-03"`. Mira [Cumpleaños](#cumpleaños). | No |
| `color` | El color de la hormiga y de su nombre. Mira [Colores](#colores). | No |
| `alta` | El día en que llega, `"AAAA-MM-DD"`. Mira [Altas](#altas-quien-llega-más-tarde). | No |

```toml
[[miembro]]
nombre = "Paula"
cumple = "23-11"
color = "rosa"
alta = "2026-11-02"
```

Si sólo quieres poner los nombres, sin nada más, también vale una lista:

```toml
nombre = "Soporte"
planta = 2
miembro = ["Nuria", "Óscar", "Bea"]
```

No mezcles las dos formas en el mismo fichero: según el orden, o la sala entera no sale,
o los nombres de la lista se pierden sin ningún aviso.

### Qué hace cada hormiga

Su sala es su casa: allí pasa más rato que en ningún otro sitio y allí duerme por la
noche. Además baja al comedor (sobre todo a la hora de comer), va a por agua, visita otras
salas, ayuda a cavar, sale a buscar comida y va a las reuniones. Lo cuenta con detalle el
[capítulo 4](04-tipos-y-muebles.md#qué-hacen-las-hormigas).

### Mover a alguien de sala

1. Corta su bloque `[[miembro]]` (desde su `[[miembro]]` hasta justo antes del siguiente
   `[[...]]`, o hasta el final si es el último).
2. Pégalo al final del fichero de la otra sala.
3. Guarda los dos ficheros.

A los pocos segundos ya es de la otra sala. No se teletransporta: la próxima vez que
vuelva a casa, irá a la nueva. No le cambies el nombre, que es lo que hace que siga siendo
la misma hormiga (con su color de siempre).

## Colores

El `color` de una sala es el de las letras de su cartel. El de un `[[miembro]]` es el de
su hormiga y su nombre. Estos son los nombres que entiende:

| Color | Versión más viva |
|---|---|
| `rojo` | `rojo_brillante` |
| `naranja` | `naranja_brillante` |
| `amarillo` | `amarillo_brillante` |
| `verde` | `verde_brillante` |
| `cian` | `cian_brillante` |
| `azul` | `azul_brillante` |
| `morado` | `morado_brillante` |
| `magenta` | `magenta_brillante` |
| `marron` o `marrón` | `marron_brillante` |
| `arena` | `arena_brillante` |
| `plata` | `plata_brillante` |
| `blanco` | `blanco_brillante` |
| `negro` | `negro_brillante` |

Y estos, sin versión `_brillante`: `rosa`, `dorado`, `turquesa`, `lima`, `coral`,
`salmon` (o `salmón`), `gris` y `gris_oscuro`.

- Da igual escribirlo en mayúsculas o con espacio: `"Rojo brillante"` también vale.
- También se entienden en inglés: `red`, `bright_red`, `gold`...
- Para cualquier otro color, pon su código: `color = "#ff8800"`.
- Si el nombre no existe, sale un aviso. En una sala, por ejemplo: «salas/ventas.toml: no
  existe el color «violeta» (puse blanco)». En una persona, se le da un color solo.

**Si una persona no tiene `color`**, el hormiguero le da uno de esta lista, el que menos se
esté usando, y lo recuerda (en `local/estado.json`): aunque reinicies o entre gente nueva,
no le cambia. La lista: `rojo_brillante`, `amarillo_brillante`, `cian`,
`magenta_brillante`, `verde_brillante`, `naranja`, `azul_brillante`, `rosa`,
`blanco_brillante`, `turquesa`, `lima`, `coral`, `dorado`, `morado` y `salmon`. En la demo
y en las capturas no se guarda nada, así que ahí puede salir otro.

## Cumpleaños

Se escribe con el día y el mes, separados por un guion: `cumple = "14-03"` es el 14 de
marzo. También vale `"14/03"` o con el año, `"14-03-1990"` (el año no se usa).

Ese día:

- Su hormiga lleva **gorro de fiesta**.
- Arriba, cerca de la entrada del hormiguero, hay **una tarta con regalos**. La hormiga del
  cumpleaños sube a menudo a verla, y las demás van a felicitarla.
- En lo alto de la pantalla pone **FELIZ CUMPLE** con su nombre, y en su sala,
  «¡Feliz cumple, Paula!» con globos.
- El diario de abajo dice «¡Cumpleaños de Paula! Hay tarta arriba.»
- La demo se para unos segundos en ese día.

Quien nació el 29 de febrero lo celebra el 28 los años que no son bisiestos. Sólo se
celebra si ese día la persona está en el hormiguero: si aún no ha llegado o ya se fue, no.

Si está mal escrito, sale el aviso «salas/ventas.toml: Paula: cumple mal escrito (23 de
noviembre), usa DD-MM» y esa persona se queda sin cumpleaños.

## Altas: quien llega más tarde

Con `alta = "AAAA-MM-DD"` (año, mes y día, con guiones y dos cifras), esa persona llega
ese día. Puedes apuntar hoy a quien empieza el mes que viene y olvidarte:

```toml
[[miembro]]
nombre = "Iván"
cumple = "09-05"
alta = "2026-11-02"
```

- **Antes de esa fecha** su hormiga no existe: no se celebra su cumpleaños ni va a las
  reuniones.
- **Ese día** aparece en su sala y el diario dice «Llega Iván al hormiguero.
  ¡Bienvenida/o!».
- Si la fecha es la de la fundación del hormiguero o anterior, está desde el principio y
  sale entre los fundadores («Se funda el hormiguero de...»).

Si la fecha está mal escrita (por ejemplo `"2026-11-2"`), sale el aviso
«salas/desarrollo.toml: Iván: fecha de alta mal escrita (2026-11-2), usa AAAA-MM-DD» y está
desde el principio. Si le pones también la hora (`alta = 2026-11-02T09:00:00`), vale el día.

## Reuniones fijas: `[[reunion]]`

Una reunión se pone en el fichero de **la sala donde se hace**. Puede ser cualquier sala:
la de reuniones, el comedor o la de un equipo.

```toml
[[reunion]]
nombre = "Reunión de los lunes"
dia = "lunes"
hora = "09:30"
minutos = 60
quien = "todos"
```

| Clave | Qué es | Si no la pones |
|---|---|---|
| `nombre` | Lo que sale en el diario. | `"Reunión"` |
| `dia` | `lunes`, `martes`, `miércoles`, `jueves`, `viernes`, `sábado`, `domingo` o `todos` (de lunes a viernes). | `todos` |
| `hora` | A qué hora empieza: `"HH:MM"`, de `"00:00"` a `"23:59"`. | `"10:00"` |
| `minutos` | Cuánto dura. | `60` |
| `quien` | A quién convoca (ahora lo vemos). | `todos` |

- En `dia` dan igual las mayúsculas y las tildes: `"miercoles"` y `"Sábado"` valen.
- `"todos"` es de lunes a viernes. Para el fin de semana, pon otra `[[reunion]]` con
  `dia = "sábado"` u otra con `dia = "domingo"`.

**`quien`** puede ser:

- `"todos"`: todas las hormigas.
- **Una sala**: la gente de esa sala. Por el nombre de su fichero sin `.toml`
  (`"soporte"`) o por el que pone en su cartel (`"Soporte"`).
- **Una persona**: `"Carmen"`.
- **Una lista de personas**: `["Carmen", "Jorge", "Paula"]`.

En `quien` dan igual las mayúsculas y las tildes.

**Qué pasa:** a esa hora, las hormigas convocadas van a la sala y se quedan hasta que
acaba. Abajo sale «¡Ahora! · Reunión de los lunes en la sala Reuniones.» Cada reunión se
hace una vez al día. Si enciendes el hormiguero a mitad de una reunión, se hace igual
hasta su hora de fin.

**Si algo está mal**, sale un aviso:

- Con la hora o el día mal escritos, la reunión no se hace: «salas/reuniones.toml:
  reunión «Reunión de los lunes»: hora mal escrita (25:00), usa HH:MM, de 00:00 a 23:59».
- Con alguien que no existe en `quien`: «salas/reuniones.toml: reunión «Previsión de
  ventas»: «Jorje» no es nadie del hormiguero». A esa persona no se la cuenta; si no queda
  nadie, la reunión no se hace.
- Si un día no hay nadie a quien convocar (la sala está vacía, o la gente aún no ha
  llegado o ya se fue): «hoy no convoca a nadie», y ese día no se hace.

## El jefe

Con `jefe = true` en una sala, quien está en ella llama de vez en cuando a alguien de otra
sala. Esa persona va a la sala del jefe y se queda un rato (entre 5 y 20 minutos). El
diario dice «Carmen llama a Jorge al despacho.»

- Llama más o menos cada 15 a 40 minutos.
- Sólo de lunes a viernes y en horario de trabajo: el de `jornada` en la sección
  `[horario]` de `config.toml` (si no lo cambias, de 9:00 a 18:00).
- Vale en una sala de cualquier tipo, aunque lo normal es el despacho. La sala tiene que
  tener gente.
- Si pones `jefe = true` en varias salas, sólo cuenta la primera por orden alfabético del
  nombre de fichero.

```toml
nombre = "Dirección"
color = "dorado"
planta = 1
ancho = 22
tipo = "despacho"
jefe = true

[[miembro]]
nombre = "Carmen"
cumple = "11-10"
color = "dorado"
```

## Muebles de la sala: `[[mueble]]`

Cada tipo de sala trae sus muebles. Una sala puede añadir más con sus propios
`[[mueble]]`:

```toml
[[mueble]]
pieza = "sofa"
sitio = "centro_derecha"
```

Se suman a los del tipo, no los sustituyen. Las piezas y los sitios están en el
[capítulo 4](04-tipos-y-muebles.md).

## Los que se van: `idos.toml`

Quien se va del grupo tiene su lápida en el cementerio de arriba. Se apunta en
`local/idos.toml` (o `idos.toml`), un bloque `[[ido]]` por persona:

```toml
[[ido]]
nombre = "MANOLO"

[[ido]]
nombre = "Bea"
fecha = "2026-12-18"
epitafio = "¡suerte en Valencia!"
```

| Clave | Qué es | ¿Hace falta? |
|---|---|---|
| `nombre` | Lo que pone en su lápida. Escríbelo como en su sala: las mayúsculas dan igual, pero las tildes no (`Raul` y `Raúl` son dos personas). | Sí |
| `fecha` | El día en que se va, `"AAAA-MM-DD"`. Sin fecha, es que ya se fue. | No |
| `epitafio` | Su despedida en el diario el día en que se va. **Sólo sale si pones `fecha`.** | No |

Si nadie se ha ido, deja el fichero con un comentario, por ejemplo
`# De momento, nadie.`. No lo borres: sin él, al reiniciar se usaría el `idos.toml` de
ejemplo, con sus lápidas.

### Alguien ya se fue

1. Añádelo a `idos.toml`, sin fecha.
2. Borra su `[[miembro]]` de su sala.
3. Guarda los dos ficheros.

A los pocos segundos su hormiga desaparece y sale su lápida. Si se te olvida el paso 2,
sale el aviso ««Luis» está en salas/desarrollo.toml y en idos.toml sin fecha (ya se fue),
así que no sale...» y su hormiga tampoco está.

### Alguien se va un día concreto

1. Añádelo a `idos.toml` con su `fecha` y, si quieres, su `epitafio`.
2. **Déjalo en su sala** hasta ese día: su hormiga sigue como siempre.
3. Ese día su hormiga ya no está, aparece su lápida y el diario dice «Bea se va del
   hormiguero. ¡Suerte en Valencia!».
4. Después, cuando quieras, borra su `[[miembro]]` de la sala.

Del epitafio, el hormiguero pone en mayúscula la primera letra y le añade un punto si no lo
tiene. Sin epitafio, la despedida es «Gone, but not forgotten.»

Si lo borras de su sala antes de tiempo, sale el aviso «idos.toml: Bea se va el
2026-12-18, pero ya no está en ninguna sala; déjalo en la suya hasta ese día».

> **Cuidado con la fecha.** Si está mal escrita (por ejemplo `"2026/12/18"`), sale el
> aviso «idos.toml: Bea: fecha mal escrita (2026/12/18), usa AAAA-MM-DD» y cuenta como si
> no tuviera fecha: se va ya.

### El cementerio

- Está en la superficie: una lápida con su nombre por cada uno que se fue, y «R.I.P.»
  encima.
- Dónde: lo decide `cementerio` en la sección `[paisaje]` de `config.toml`, en % del
  ancho de la pantalla (si no lo cambias, `74`). Se coloca lo más cerca posible de ahí,
  nunca encima de una salida. Lo cuenta el [capítulo 5](05-paisaje.md).
- Si son muchos, las lápidas salen con letra más pequeña, y después en dos filas. Si ni
  así caben, no salen las de los primeros de la lista, con el aviso «idos.toml: no caben
  todas las lápidas en el cementerio (no salen ...)». Los nombres cortos caben mejor.
- Con `esqueletos = true` en la sección `[halloween]` de `config.toml`, del 26 al 31 de
  octubre los que se fueron salen del cementerio y pasean por el hormiguero como hormigas
  esqueleto. Lo cuenta el [capítulo 6](06-fiestas-y-halloween.md).

## Nombres repetidos

Cada hormiga va por su nombre. Si dos personas se llaman igual (las mayúsculas no
cuentan), la segunda sale con el nombre de su sala detrás, y hay aviso:

> hay dos «Ana» (en salas/desarrollo.toml y en salas/diseno.toml): la segunda sale como
> «Ana (Diseño)»

«La segunda» es la que va después: los ficheros se leen por orden alfabético y, dentro de
cada uno, de arriba abajo. Para nombrarla en `idos.toml` o en una reunión, escribe
`"Ana (Diseño)"`. Pasa lo mismo si las dos están en la misma sala: la segunda «Ana» de
Desarrollo sale como «Ana (Desarrollo)». Una tercera «Ana» en esa sala ya no sale (aviso
«salas/desarrollo.toml: hay más de dos «Ana»; las que sobran no salen (cambia un nombre)»).

Mejor ponles nombres distintos desde el principio: `"Ana G."` y `"Ana M."`. Si se lo
cambias más tarde, para el hormiguero es otra hormiga: si no tiene un color fijo, se le
vuelve a elegir.

## Qué se aplica solo y qué hay que reiniciar

Con el hormiguero en marcha, cada 3 segundos mira si has guardado algún fichero. Si lo que
has cambiado solo se aplica al reiniciar, la franja amarilla te lo recuerda (por ejemplo,
«salas/ventas.toml es nueva: la sala sale al reiniciar el hormiguero»).

| Cambio | ¿Hay que reiniciar? |
|---|---|
| Añadir, quitar o mover gente, y su `cumple`, `color` o `alta` | No |
| Las reuniones (`[[reunion]]`) | No |
| `jefe` | No |
| Los muebles de la sala (`[[mueble]]`) | No |
| `idos.toml` | No |
| `calendario.toml` | No |
| `nombre`, `color`, `planta`, `x`, `ancho` o `tipo` de una sala | Sí |
| Crear un fichero de sala | Sí. Hasta entonces, su gente ya está, pero vive en el comedor. |
| Borrar un fichero de sala | Sí. Sus hormigas desaparecen enseguida; la sala, vacía, sigue hasta reiniciar. |
| Los tipos de sala (`tipos/`) | Sí |
| `config.toml` | Sí |
| Crear por primera vez `local/salas/` o `local/idos.toml` | Sí |

Para reiniciar en el ordenador, cierra el hormiguero con `q` y vuelve a lanzarlo:

```bash
python3 hormiguero_pixel.py --ventana
```

En la Raspberry Pi:

```bash
sudo systemctl restart hormiguero
```

## Si algo no sale

Lo primero, lee la franja amarilla de arriba de la pantalla: dice qué falla y, casi
siempre, en qué fichero. También puedes ver los avisos en la terminal, sin mirar la
pantalla. Esta orden simula un rato, guarda una imagen y escribe cada aviso en una línea
que empieza por `aviso:`:

```bash
python3 hormiguero_pixel.py --captura /tmp/prueba.png
```

En Windows, pon `prueba.png` en lugar de `/tmp/prueba.png`.

Si el fichero tiene un error de escritura (por ejemplo, unas comillas sin cerrar), **la
sala entera no sale**, con un aviso que dice la línea del fallo. Si en la primera línea
pones `nombre = "Ventas` (sin la comilla del final), sale
«salas/ventas.toml: no se puede leer, en la línea 1: falta cerrar unas comillas».

## Ejemplos completos

Tres hormigueros enteros, listos para copiar. Para usar uno:

1. Deja en `local/salas/` sólo los ficheros del ejemplo (borra los demás).
2. Crea cada fichero con el nombre que pone encima y pega su contenido.
3. Cambia `local/idos.toml` por el del ejemplo.
4. Si quieres, cambia también `nombre` en la sección `[general]` de `local/config.toml`:
   es lo que sale en el diario («Se funda el hormiguero de...»).
5. Reinicia el hormiguero.

Durante el año, las hormigas excavarán además las salas de `obras` de `config.toml` (la
despensa, el museo, el vivero de hongos, el almacén y la biblioteca).

### Una oficina

Seis salas: dirección (con jefa), reuniones y comedor arriba; dos equipos en la planta 2,
y la fuente debajo.

`local/salas/comedor.toml`:

```toml
nombre = "Comedor"
color = "blanco"
planta = 1
x = 40
ancho = 34
tipo = "comedor"

[[reunion]]
nombre = "Café de los viernes"
dia = "viernes"
hora = "10:30"
minutos = 30
quien = "todos"
```

`local/salas/direccion.toml`:

```toml
nombre = "Dirección"
color = "dorado"
planta = 1
ancho = 22
tipo = "despacho"
jefe = true

[[miembro]]
nombre = "Carmen"
cumple = "11-10"
color = "dorado"
```

`local/salas/reuniones.toml`:

```toml
nombre = "Reuniones"
color = "azul_brillante"
planta = 1
ancho = 30
tipo = "reuniones"

[[reunion]]
nombre = "Reunión de los lunes"
dia = "lunes"
hora = "09:30"
minutos = 60
quien = "todos"

[[reunion]]
nombre = "Previsión de ventas"
dia = "miércoles"
hora = "12:00"
minutos = 45
quien = ["Carmen", "Jorge", "Paula"]

[[reunion]]
nombre = "Revisión de incidencias"
dia = "jueves"
hora = "16:00"
minutos = 30
quien = "soporte"
```

`local/salas/ventas.toml`:

```toml
nombre = "Ventas"
color = "naranja"
planta = 2
ancho = 36
tipo = "trabajo"

[[miembro]]
nombre = "Jorge"
cumple = "02-07"

[[miembro]]
nombre = "Paula"
cumple = "23-11"
color = "rosa"

[[miembro]]
nombre = "Iván"
cumple = "09-05"

[[mueble]]
pieza = "pizarra"
sitio = "pared_derecha"
```

`local/salas/soporte.toml`:

```toml
nombre = "Soporte"
color = "verde_brillante"
planta = 2
ancho = 32
tipo = "trabajo"

[[miembro]]
nombre = "Nuria"
cumple = "14-03"

[[miembro]]
nombre = "Óscar"
cumple = "30-01"
alta = "2026-11-02"

[[miembro]]
nombre = "Bea"
cumple = "18-08"
```

`local/salas/fuente.toml`:

```toml
nombre = "Fuente"
color = "blanco"
planta = 3
ancho = 24
tipo = "fuente"
```

`local/idos.toml` (Manolo ya se jubiló; Bea se va en diciembre, y hasta entonces sigue
en Soporte):

```toml
[[ido]]
nombre = "MANOLO"

[[ido]]
nombre = "Bea"
fecha = "2026-12-18"
epitafio = "¡suerte en Valencia!"
```

### Una familia

La cocina es el comedor de la casa. En el salón, los muebles de la biblioteca más un sofá
y una pantalla que hace de tele. Los peques hacen los deberes en el estudio, y el perro
también es una hormiga.

`local/salas/cocina.toml`:

```toml
nombre = "Cocina"
color = "blanco"
planta = 1
ancho = 34
tipo = "comedor"

[[miembro]]
nombre = "Abuela Pilar"
cumple = "08-12"
color = "plata"

# De lunes a viernes
[[reunion]]
nombre = "Cena"
dia = "todos"
hora = "21:00"
minutos = 45
quien = "todos"

[[reunion]]
nombre = "Comida del domingo"
dia = "domingo"
hora = "14:00"
minutos = 90
quien = "todos"
```

`local/salas/salon.toml`:

```toml
nombre = "Salón"
color = "naranja"
planta = 1
ancho = 36
tipo = "biblioteca"

[[miembro]]
nombre = "Andrés"
cumple = "21-06"
color = "azul_brillante"

[[miembro]]
nombre = "Toby"
cumple = "01-04"
color = "marron"

[[miembro]]
nombre = "Leo"
alta = "2026-12-03"

[[mueble]]
pieza = "sofa"
sitio = "centro_izquierda"

[[mueble]]
pieza = "pantalla"
sitio = "pared"
```

`local/salas/estudio.toml`:

```toml
nombre = "Estudio"
color = "cian"
planta = 2
ancho = 34
tipo = "trabajo"

[[miembro]]
nombre = "Lucas"
cumple = "15-09"

[[miembro]]
nombre = "Vera"
cumple = "29-02"
color = "lima"

[[reunion]]
nombre = "Deberes"
dia = "todos"
hora = "17:30"
minutos = 60
quien = "estudio"
```

`local/salas/despacho.toml` (sin `jefe`: aquí se teletrabaja, no se manda):

```toml
nombre = "Despacho"
color = "morado_brillante"
planta = 2
ancho = 24
tipo = "despacho"

[[miembro]]
nombre = "Laura"
cumple = "03-05"
color = "rojo_brillante"
```

`local/salas/bano.toml` (el tipo `fuente` tiene azulejos y agua):

```toml
nombre = "Baño"
color = "turquesa"
planta = 3
ancho = 22
tipo = "fuente"
```

`local/idos.toml` (el cementerio también vale para quien se va a estudiar fuera):

```toml
[[ido]]
nombre = "Marcos"
fecha = "2026-09-01"
epitafio = "se fue a estudiar a Madrid"
```

### Un piso compartido

Cada uno tiene su cuarto, con el tipo que mejor le va. En el salón, la mesa larga y la
pantalla del tipo `reuniones` hacen de mesa y de tele.

`local/salas/cocina.toml`:

```toml
nombre = "Cocina"
color = "blanco"
planta = 1
ancho = 34
tipo = "comedor"

[[reunion]]
nombre = "Cena de piso"
dia = "jueves"
hora = "21:30"
minutos = 90
quien = "todos"
```

`local/salas/salon.toml`:

```toml
nombre = "Salón"
color = "naranja"
planta = 1
ancho = 30
tipo = "reuniones"

[[reunion]]
nombre = "Limpieza general"
dia = "sábado"
hora = "11:00"
minutos = 60
quien = "todos"
```

`local/salas/marta.toml`:

```toml
nombre = "Cuarto de Marta"
color = "rojo_brillante"
planta = 2
ancho = 30
tipo = "trabajo"

[[miembro]]
nombre = "Marta"
cumple = "12-01"
color = "rojo_brillante"
```

`local/salas/javi.toml`:

```toml
nombre = "Cuarto de Javi"
color = "verde_brillante"
planta = 2
ancho = 26
tipo = "biblioteca"

[[miembro]]
nombre = "Javi"
cumple = "27-07"
color = "verde_brillante"

[[mueble]]
pieza = "sillon"
sitio = "centro_izquierda"
```

`local/salas/nerea.toml` (Nerea llega en noviembre):

```toml
nombre = "Cuarto de Nerea"
color = "amarillo_brillante"
planta = 3
ancho = 28
tipo = "despacho"

[[miembro]]
nombre = "Nerea"
cumple = "04-10"
color = "amarillo_brillante"
alta = "2026-11-01"
```

`local/salas/bano.toml`:

```toml
nombre = "Baño"
color = "turquesa"
planta = 3
ancho = 22
tipo = "fuente"
```

`local/idos.toml`:

```toml
[[ido]]
nombre = "Dani"
```

---

Anterior: [2. Primeros pasos](02-primeros-pasos.md) · Siguiente: [4. Tipos de sala y muebles](04-tipos-y-muebles.md)
