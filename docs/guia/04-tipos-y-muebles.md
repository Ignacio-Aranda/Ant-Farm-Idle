# Tipos de sala y muebles

En este capítulo vas a aprender qué es un tipo de sala, qué hacen las hormigas en cada
una, qué muebles puedes poner y dónde, y cómo crear tus propios tipos.

## Qué es un tipo

Cada sala tiene un **tipo**, que dice tres cosas:

- **Su función:** para qué sirve la sala y qué van a hacer allí las hormigas.
- **Sus paredes y su suelo.**
- **Sus muebles.**

Los tipos están en la carpeta `tipos/` (o en `local/tipos/`, si la has creado; mira
[Crear un tipo nuevo](#crear-un-tipo-nuevo)). Cada fichero es un tipo, y su nombre es el del
fichero sin `.toml`: `tipos/comedor.toml` es el tipo `comedor`.

Una sala dice de qué tipo es con la línea `tipo` de su fichero (lo cuenta el
[capítulo 3](03-salas-y-gente.md)). Si no la pone, es de tipo `trabajo`:

```toml
nombre = "Cocina"
planta = 1
ancho = 34
tipo = "comedor"
```

Los tipos se leen al arrancar. Si cambias uno, reinicia el hormiguero.

## Los tipos que vienen hechos

![Los diez tipos de sala que vienen hechos, cada uno con sus paredes, su suelo y sus muebles](../galeria-tipos.png)

| Tipo | Función | Paredes | Suelo | Muebles |
|---|---|---|---|---|
| `trabajo` | `trabajo` | madera | madera | Dos escritorios, un cuadro y una planta. |
| `reuniones` | `reuniones` | madera | madera | La mesa de reuniones y una pantalla con gráficas. |
| `despacho` | `despacho` | madera | madera | Escritorio grande, sillón y, desde el día 60, una planta. |
| `comedor` | `comedor` | madera | madera | Nevera, mesa con platos y encimera con microondas y cafetera. |
| `fuente` | `agua` | azulejo | baldosa | La fuente de agua y una planta. |
| `despensa` | `despensa` | madera | tierra | Sacos y, desde el día 60, más sacos. |
| `museo` | `museo` | madera | madera | Dos vitrinas con los hallazgos. |
| `hongos` | `otra` | piedra | tierra | Una fila de setas. |
| `almacen` | `otra` | madera | tierra | Cajas y una estantería. |
| `biblioteca` | `otra` | madera | madera | Dos estanterías y un reloj. |

Los cinco últimos son los de las salas que las hormigas excavan durante el año (la lista
`obras` de la sección `[nido]` de `config.toml`), pero también los puedes usar en tus
salas.

## Qué hacen las hormigas

Cada hormiga tiene **su sala**: la del fichero donde está su `[[miembro]]`. Da igual de qué
tipo sea. Si pones a alguien en el comedor, el comedor es su casa.

### De día

Cuando una hormiga termina lo que estaba haciendo, elige adónde ir. Es al azar, pero unas
cosas tocan más que otras:

- **Su sala.** Es lo más normal, y es donde se queda más rato.
- **El comedor.** Fuera de las comidas, de vez en cuando. A la hora del desayuno bajan
  bastantes, y a la hora de comer, muchas más. Las horas son las de `desayuno` y
  `comida` en la sección `[horario]` de `config.toml`.
- **La fuente.** Va de vez en cuando a beber, casi el doble que a una sala cualquiera, y
  se queda poco rato.
- **Otras salas.** De visita. Las de tus ficheros, más que las que se excavan durante el
  año.
- **La obra.** Mientras se excava algo, ayudan a cavar y sacan la tierra afuera.
- **Fuera, a buscar comida.** Salen menos si hace frío (menos de 11 °C, o en invierno) o
  mucho calor (más de 30 °C), y nada si llueve. Si alguien encuentra comida o un bicho que
  cazar, van a por él, y entre varias cargan con lo grande. Lo que traen lo guardan en la
  despensa.
- **Los cumpleaños.** Quien cumple años sube a menudo a la tarta, y las demás van a
  felicitarle.

Las reuniones y las llamadas del jefe van aparte: a su hora, lo dejan todo y van (lo
cuenta el [capítulo 3](03-salas-y-gente.md)).

### De noche

Desde que se pone el sol hasta que sale, casi todas duermen en su sala: se quedan quietas
un buen rato y les salen unas zetas. Alguna se queda despierta en el comedor.

### Si hay peligro

Si fuera hay peligro (un pájaro, o una araña que se acerca), las que están fuera corren a
refugiarse al comedor. Abajo sale, por ejemplo, «¡Ahora! · ¡Un pájaro! Todas para
dentro.»

## Las funciones

La función se pone en el tipo con `funcion = "..."`. Es lo que cambia lo que hacen las
hormigas en las salas de ese tipo:

| `funcion` | Qué cambia |
|---|---|
| `comedor` | Es adonde van a desayunar y a comer. Es también el refugio: si hay peligro fuera, corren aquí, y aquí se quedan las que no duermen. Si no hay despensa, la comida se guarda aquí. |
| `agua` | Van a beber de vez en cuando: la visitan más que una sala cualquiera y se quedan poco. |
| `despensa` | Aquí guardan la comida que traen de fuera. |
| `trabajo` | Nada en lo que hacen las hormigas. En algunas fiestas lleva adornos (abajo). |
| `reuniones` | Igual que `trabajo`. Las reuniones no dependen de la función: se ponen en el fichero de la sala. |
| `despacho` | Igual que `trabajo`. Las llamadas al despacho las hace `jefe = true` en el fichero de la sala, sea del tipo que sea. |
| `museo` | Igual que `otra`. Los hallazgos no los enseña la función, sino la pieza `vitrina`, en la sala que esté (el tipo `museo` trae dos). |
| `otra` | Nada especial: la visitan de vez en cuando, como a cualquier sala. |

Algunas cosas más:

- **Sin comedor**, el refugio es la primera de tus salas por orden alfabético del nombre
  de su fichero (las que llevan `x` van antes). **Sin despensa**, la comida se guarda en
  el comedor (o, si tampoco hay, en esa primera sala). La despensa del ejemplo es una de
  las salas que se excavan durante el año: hasta que la terminan, la comida va al comedor.
- **Adornos de fiesta:** las salas con función `trabajo`, `reuniones`, `despacho` o
  `comedor` llevan un arbolito en Navidad, una calabaza en Halloween y una banderita en
  las fiestas con la bandera de Andalucía o de España (las decoraciones `andalucia` y
  `espana`). En Nochevieja, en el comedor hay uvas. Lo cuenta el
  [capítulo 6](06-fiestas-y-halloween.md).
- Si un tipo no dice su función, es `otra`. Si pones una que no existe, sale un aviso y
  también es `otra`.

## Paredes y suelo

```toml
paredes = "azulejo"
suelo = "baldosa"
```

| `paredes` | Cómo son |
|---|---|
| `madera` | Marrón oscuro. Es la que se pone si no dices nada. |
| `azulejo` | Azul grisáceo, como en la fuente. |
| `piedra` | Gris, como en el vivero de hongos. |
| `"#RRGGBB"` | Del color que quieras, con su código. Por ejemplo, `"#6a5a7a"` es un malva. |

| `suelo` | Cómo es |
|---|---|
| `madera` | Tablas de madera. Es el que se pone si no dices nada. |
| `baldosa` | Baldosas claras, como en la fuente. |
| `tierra` | De tierra, como en la despensa. |

Si escribes otra cosa, sale un aviso y se pone `madera`.

## Los muebles: `[[mueble]]`

Cada `[[mueble]]` es una pieza:

```toml
[[mueble]]
pieza = "planta"
sitio = "derecha"
aparece = 60
nombre = "un ficus"
```

| Clave | Qué es | ¿Hace falta? |
|---|---|---|
| `pieza` | Qué mueble es. Están todos en [Todas las piezas](#todas-las-piezas). | Sí |
| `sitio` | Dónde va: un hueco, o un número del 0 al 100. Mira [Los huecos](#los-huecos). | No. Sin él, va a su hueco de siempre. |
| `aparece` | El día del hormiguero en que aparece (un número). | No. Sin él, está desde el principio. |
| `nombre` | Cómo se llama en el diario cuando aparece. | No. Sin él, el de la pieza («una planta», «un sofá»...). |

**Dónde se ponen.** Los muebles de un tipo salen en todas las salas de ese tipo. Una sala
puede añadir los suyos con `[[mueble]]` en su propio fichero: se suman a los del tipo.
Los de la sala se aplican solos al guardar; los del tipo, al reiniciar.

**Muebles que aparecen más tarde.** El día 0 del hormiguero es su fundación, y el de hoy
sale arriba a la izquierda de la pantalla («Día 72 del hormiguero»). Con `aparece = 80`,
la pieza sale el día 80, y ese día el diario lo cuenta con el nombre de la sala y el de la
pieza: una pizarra en la sala «Ventas» sale como «Novedad en Ventas: una pizarra.» Con
`nombre = "un ficus"`, la planta del ejemplo de arriba, en la sala «Despacho», sale como
«Novedad en Despacho: un ficus.» En las salas que se excavan durante el año, nada sale
antes de que la sala esté terminada.

## Los huecos

Los huecos son sitios fijos de la sala, para colocar las piezas sin pensar en medidas.
El número es dónde cae el centro de la pieza, en tanto por ciento del ancho de la sala
(0 es la pared izquierda; 100, la derecha):

| En el suelo | | En la pared | |
|---|---|---|---|
| `izquierda` | 17 % | `pared_izquierda` | 20 % |
| `centro_izquierda` | 38 % | `pared` (o `pared_centro`) | 50 % |
| `centro` | 50 % | `pared_derecha` | 80 % |
| `centro_derecha` | 65 % | | |
| `derecha` | 88 % | | |

- **Cada pieza ya sabe si va en el suelo o en la pared.** El hueco solo dice en qué punto
  de la sala va, de izquierda a derecha. Un sofá en el hueco `pared` se queda en el suelo,
  en el centro.
- **Con un número**, pones la pieza justo donde quieras: `sitio = 35` la centra al 35 %
  del ancho.
- **Las piezas nunca se salen de la sala:** si no caben en su sitio, se arriman hacia
  dentro.
- **Las piezas no se apartan unas de otras.** Si dos caen en el mismo sitio, o la sala es
  estrecha, se pintan una encima de otra. Muévelas con otro hueco o con un número.
- Si el hueco no existe, sale un aviso y la pieza va a su hueco de siempre. Si el número
  es menor que 0 o mayor que 100, sale un aviso y se queda en el borde.

## Todas las piezas

![Todas las piezas, cada una en una sala de muestra, con su nombre, si va en el suelo o en la pared y su hueco por defecto](../galeria-muebles.png)

Los nombres de las piezas van **sin tildes**: `sofa`, `sillon`, `estanteria`.

| Pieza | Dónde | Hueco por defecto | Columnas | Cómo es |
|---|---|---|---|---|
| `escritorio` | suelo | `izquierda` | 11 | Mesa con ordenador y silla. La pantalla parpadea. |
| `escritorio_grande` | suelo | `izquierda` | 13 | Escritorio de despacho, más largo. |
| `sillon` | suelo | `centro_derecha` | 5 | Un sillón oscuro. |
| `sofa` | suelo | `centro` | 12 | Un sofá rojo. |
| `planta` | suelo | `derecha` | 10 | Una planta en su maceta. Crece: es más grande a los 90 días de aparecer, y otra vez a los 240. |
| `mesa_reuniones` | suelo | `centro` | 2 | Mesa larga. Ocupa casi toda la sala, esté en el hueco que esté. |
| `mesa_comedor` | suelo | `centro` | 17 | Mesa larga con platos. |
| `nevera` | suelo | `izquierda` | 6 | Una nevera. |
| `encimera` | suelo | `derecha` | 12 | Con microondas y cafetera. La cafetera echa vapor. |
| `fuente` | suelo | `izquierda` | 5 | Fuente de agua con garrafa. Le suben burbujas. |
| `estanteria` | suelo | `izquierda` | 8 | Con libros de colores. |
| `vitrina` | suelo | `izquierda` | 8 | Enseña los hallazgos de la colonia (abajo). |
| `sacos` | suelo | `izquierda` | 9 | Dos sacos. |
| `cajas` | suelo | `izquierda` | 9 | Tres cajas apiladas. |
| `setas` | suelo | `centro` | 21 | Una fila de cinco setas. |
| `cuadro` | pared | `pared` | 6 | Un paisaje con marco. |
| `pantalla` | pared | `pared` | 13 | Una pantalla con gráficas. |
| `pizarra` | pared | `pared` | 11 | Una pizarra blanca con apuntes. |
| `reloj` | pared | `pared_derecha` | 6 | Marca la hora del hormiguero: la de verdad o, si la simulas (`--fecha`, `--hora`, `--dias`, `--acelerar` o la demo), la simulada. |

**Columnas** es lo que tiene que medir la sala, como poco (su `ancho`), para que la pieza
se pinte. Mira [Si un mueble no cabe](#si-un-mueble-no-cabe).

**La vitrina.** Al excavar, las hormigas encuentran cosas: una peseta de 1982, una pieza de
Lego, una Raspberry Pi 1... Hay 12 hallazgos posibles. Cada vitrina enseña hasta 6, según
se van encontrando: en una sala con dos vitrinas, la primera tiene los 6 primeros y la
segunda, los siguientes.

En las imágenes, cada sala de muestra mide 44 columnas, y en la de las piezas cada una
está en el centro. En tu sala, cada hueco cae siempre en el mismo tanto por ciento de su
ancho.

## Si un mueble no cabe

- **En tus salas** (las que tienen su fichero en `salas/` o `local/salas/`), la sala no
  se ensancha sola. Si mide menos columnas de las que necesita una pieza, esa pieza no se
  pinta y sale un aviso:

  > Comedor: «mesa_comedor» no cabe en la sala (tiene 14 columnas y hacen falta 17)

  Para arreglarlo, ensancha la sala (`ancho`) o usa un tipo sin esa pieza, y reinicia.
  Si la pieza es de la propia sala, quítala de su fichero y el aviso se va al guardar.
- **En las salas que se excavan durante el año**, las hormigas nunca las hacen más
  estrechas de lo que necesitan los muebles de su tipo. Si no caben ni así, se quedan sin
  hacer, y el diario lo cuenta.
- **Que quepa no quiere decir que no se pise con otra.** Cada pieza se mira por separado:
  en una sala estrecha, dos piezas pueden quedar una encima de otra. Con muchos muebles,
  haz la sala más ancha.

## Crear un tipo nuevo

Vamos a crear un tipo `dormitorio`: paredes malva, un sofá cama, una estantería, un
cuadro, un reloj y una planta que llega al mes.

1. **Copia los tipos a `local/`**, si aún no lo has hecho. `local/tipos/` sustituye
   entera a `tipos/`, así que tiene que tener todos los tipos que uses, también los de
   las salas que se excavan durante el año. Dentro de la carpeta del hormiguero, crea
   `local/` (si ya existe, no pasa nada):

   ```bash
   mkdir -p local
   ```

   Y copia dentro la carpeta `tipos`:

   ```bash
   cp -r tipos local/
   ```

   En Windows, hazlo con el Explorador de archivos: copia la carpeta `tipos` dentro de la
   carpeta `local`.

   Hazlo solo esta vez: si lo repites más adelante, los tipos que hayas cambiado vuelven
   a ser los de ejemplo.

2. **Crea el fichero** `local/tipos/dormitorio.toml` con esto:

   ```toml
   # Dormitorio: un sofá cama, una estantería, un cuadro y un reloj.
   # Al mes le ponen una planta.
   funcion = "otra"
   paredes = "#6a5a7a"
   suelo = "madera"

   [[mueble]]
   pieza = "sofa"
   sitio = "centro"

   [[mueble]]
   pieza = "estanteria"
   sitio = "derecha"

   [[mueble]]
   pieza = "cuadro"
   sitio = "pared_izquierda"

   [[mueble]]
   pieza = "reloj"
   sitio = "pared_derecha"

   [[mueble]]
   pieza = "planta"
   sitio = "izquierda"
   aparece = 30
   nombre = "un ficus"
   ```

3. **Úsalo en una sala.** Por ejemplo, `local/salas/dormitorio.toml`. Si aún no tienes
   `local/salas/`, créala antes copiando las de ejemplo como cuenta el
   [capítulo 2](02-primeros-pasos.md#crear-tu-carpeta-local): si no, solo saldría esta sala.

   ```toml
   nombre = "Dormitorio"
   color = "rosa"
   planta = 3
   ancho = 32
   tipo = "dormitorio"

   [[miembro]]
   nombre = "Rosa"
   cumple = "06-06"
   ```

4. **Reinicia el hormiguero.** En el ordenador, ciérralo con `q` y vuelve a lanzarlo:

   ```bash
   python3 hormiguero_pixel.py --ventana
   ```

   En la Raspberry Pi (si has hecho los pasos en tu ordenador, copia antes a la Pi
   `local/tipos` y la sala nueva, como cuenta el [capítulo 2](02-primeros-pasos.md)):

   ```bash
   sudo systemctl restart hormiguero
   ```

5. **Mira si hay avisos** en la franja amarilla de arriba. También puedes verlos en la
   terminal (cada uno en una línea que empieza por `aviso:`):

   ```bash
   python3 hormiguero_pixel.py --captura /tmp/prueba.png
   ```

   En Windows, pon `prueba.png` en lugar de `/tmp/prueba.png`.

Unos consejos:

- El nombre del fichero, mejor en minúsculas, sin espacios ni tildes. En la sala, escribe
  el tipo igual: `tipo = "dormitorio"`.
- Para que quepan todos los muebles sin pisarse, haz la sala ancha: este dormitorio queda
  bien con 32 columnas.
- Si quieres que en Navidad lleve su arbolito, pon `funcion = "trabajo"`: las hormigas
  harán lo mismo, solo cambian los adornos.

### Un tipo para las salas que se excavan

Las salas que las hormigas excavan durante el año usan el tipo que se llama como ellas,
en minúsculas. Si pones `"Gimnasio"` en la lista `obras` de la sección `[nido]` de
`config.toml` y existe el tipo `gimnasio` (el fichero `gimnasio.toml`), excavarán una sala
«Gimnasio» con sus muebles. En el cartel sale tal como lo escribes en la lista (menos las
cinco de siempre, que llevan su nombre: «Museo de hallazgos», «Vivero de hongos»...).
Las mayúsculas, las tildes y los espacios dan igual: `"Almacén"` usa el tipo `almacen`, y
`"Sala de juegos"`, el fichero `sala_de_juegos.toml` (o `sala de juegos.toml`). Si no hay
ningún tipo con ese nombre, sale el aviso «config: [nido] la obra «Gimnasio» no tiene tipo
en tipos/ (será una sala vacía)». Lo cuenta entero el [capítulo 8](08-como-crece.md).

## Si algo sale mal

| Aviso | Qué pasa | Qué hacer |
|---|---|---|
| `salas/dormitorio.toml: no existe el tipo «dormitorio» (en tipos/)` | La sala sale sin los muebles del tipo, con paredes y suelo de madera, y funciona como `trabajo`. | Revisa el nombre del fichero del tipo. Si lo acabas de crear, reinicia. Si usas `local/tipos/`, el tipo tiene que estar ahí. |
| `tipos/dormitorio.toml: función desconocida «dormir»` | Funciona como `otra`. | Usa una función de la tabla de [Las funciones](#las-funciones). |
| `tipos/dormitorio.toml: paredes «verde» no existe (...)` | Paredes de madera. | Usa `madera`, `azulejo`, `piedra` o un código como `"#6a5a7a"`. |
| `tipos/dormitorio.toml: suelo «moqueta» no existe (...)` | Suelo de madera. | Usa `madera`, `baldosa` o `tierra`. |
| `tipos/dormitorio.toml: no existe la pieza «sofá»` | Esa pieza no sale. | Escribe el nombre como en la tabla, sin tildes. |
| `tipos/dormitorio.toml: no existe el hueco «arriba» (sofa va a su sitio de siempre)` | La pieza va a su hueco por defecto. | Usa un hueco de la tabla o un número del 0 al 100. |
| `tipos/dormitorio.toml: el sitio de reloj va de 0 a 100 (puse 100)` | La pieza se queda en el borde. | Pon un número del 0 al 100. |
| `Dormitorio: «setas» no cabe en la sala (tiene 14 columnas y hacen falta 21)` | Esa pieza no sale. | Ensancha la sala o quita la pieza (mira [Si un mueble no cabe](#si-un-mueble-no-cabe)). |
| `tipos/dormitorio.toml: aparece de planta debe ser un número de días (treinta; puse 0)` | La pieza está desde el principio. | Pon un número: `aparece = 30`. |
| `tipos/dormitorio.toml: «suelo» está dentro de un [[mueble]] (cuadro) y el tipo no lo ve; ...` | Esa clave no cuenta: la escribiste debajo de un mueble. | Súbela arriba, antes del primer `[[mueble]]`. |

Los avisos no ponen `local/` delante: si usas `local/`, `tipos/dormitorio.toml` es tu
`local/tipos/dormitorio.toml`. Si el aviso empieza por `salas/` en vez de por `tipos/`, la
pieza está en el fichero de la sala. Si un fichero de tipo tiene un error de escritura
(por ejemplo, unas comillas sin cerrar), el aviso dice en qué línea está y qué parece que
falla, y ese tipo no existe hasta que lo arregles y reinicies.

---

Anterior: [3. Salas y gente](03-salas-y-gente.md) · Siguiente: [5. El paisaje de arriba](05-paisaje.md)
