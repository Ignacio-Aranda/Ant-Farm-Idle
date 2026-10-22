# Fiestas y Halloween

En este capítulo vas a aprender a poner tus fiestas en el calendario del hormiguero: qué
días se decora, qué gorro llevan las hormigas y qué mensaje sale en el cielo. Al final
verás cómo hacer que, en Halloween, los que se fueron vuelvan a pasearse por el
hormiguero.

![El hormiguero en Nochebuena](../noche.png)

## Dónde están las fiestas

Las fiestas están en `calendario.toml`. Si ya tienes tu carpeta `local/`, cámbialas en
`local/calendario.toml` (mira el [capítulo 2](02-primeros-pasos.md)).

**No hace falta reiniciar.** Con el hormiguero en marcha, guarda el fichero y a los pocos
segundos se aplican los cambios. Solo hay que reiniciar si acabas de crear
`local/calendario.toml` y antes no existía.

En la carpeta `ejemplos/` hay un calendario más completo, con las fiestas de Andalucía y
de España. Lo verás más abajo.

## Una fiesta

Cada fiesta es un bloque que empieza con `[[fiesta]]`, con **dos corchetes**:

```toml
[[fiesta]]
nombre = "Fiestas del pueblo"
desde = "08-09"
hasta = "12-09"
decoracion = "feria"
gorro = "flor"
mensaje = "¡Felices fiestas!"
```

Del 8 al 12 de septiembre, ambos incluidos, el hormiguero se decora de feria, las
hormigas llevan una flor en la cabeza y en el cielo sale «¡Felices fiestas!».

| Línea | Para qué sirve | Si no la pones |
|---|---|---|
| `nombre` | Para reconocerla. Sale en los avisos y en la demo (`--demo`). | Se llama «Fiesta». |
| `desde` | El primer día. | La fiesta cae el 1 de enero. Ponla siempre. |
| `hasta` | El último día (también se decora ese día). | La fiesta dura solo el día de `desde`. |
| `decoracion` | Cómo se decora el hormiguero. Mira [la lista](#las-decoraciones). | Banderines de colores. |
| `gorro` | El gorro que llevan las hormigas. Mira [la lista](#los-gorros). | Sin gorro. |
| `mensaje` | Lo que sale en el cielo todos los días de la fiesta, de día y de noche. El primer día sale también en el diario. | Sale el `nombre`. |

Escribe un mensaje corto, que quepa en una línea: si es largo, sale con letra más pequeña
y, si ni así cabe, recortado con «…».

El orden de las fiestas en el fichero da igual, salvo en un caso que verás en
[Varias fiestas a la vez](#varias-fiestas-a-la-vez).

## Las fechas

Las fechas van siempre **entre comillas**.

### Fechas fijas: `"DD-MM"`

Primero el día y luego el mes: `"14-02"` es el 14 de febrero. También vale con barra:
`"14/02"`. **Sin año**: la fiesta se repite todos los años.

Una fiesta el `"29-02"` solo sale en los años bisiestos. Si es una fiesta de varios días
que acaba el `"29-02"`, los demás años acaba el 28.

### Fechas que dependen de la Pascua

Algunas fiestas cambian de día cada año porque dependen de la Pascua (el Domingo de
Resurrección). Para esas, escribe:

- `"pascua"`: el Domingo de Resurrección.
- `"pascua+N"`: N días **después**.
- `"pascua-N"`: N días **antes**.

El hormiguero calcula la Pascua de cada año. No tienes que cambiar nada al cambiar de año.
Los espacios y las mayúsculas dan igual: `"Pascua + 1"` también vale.

| Día | Cómo se escribe | En 2027 |
|---|---|---|
| Domingo de Carnaval | `"pascua-49"` | 7 de febrero |
| Martes de Carnaval | `"pascua-47"` | 9 de febrero |
| Miércoles de Ceniza | `"pascua-46"` | 10 de febrero |
| Domingo de Ramos | `"pascua-7"` | 21 de marzo |
| Jueves Santo | `"pascua-3"` | 25 de marzo |
| Viernes Santo | `"pascua-2"` | 26 de marzo |
| Domingo de Resurrección | `"pascua"` | 28 de marzo |
| Lunes de Pascua | `"pascua+1"` | 29 de marzo |
| Pentecostés | `"pascua+49"` | 16 de mayo |
| Corpus Christi | `"pascua+60"` | 27 de mayo |

Por ejemplo, la Semana Santa, del Domingo de Ramos al de Resurrección:

```toml
[[fiesta]]
nombre = "Semana Santa"
desde = "pascua-7"
hasta = "pascua"
decoracion = "semana_santa"
mensaje = "Semana Santa"
```

### Fiestas que cruzan el año

Si `hasta` es una fecha anterior a `desde` dentro del año, la fiesta sigue hasta ese día
del año siguiente. Así se hace la Navidad, del 15 de diciembre al 6 de enero:

```toml
[[fiesta]]
nombre = "Navidad"
desde = "15-12"
hasta = "06-01"
decoracion = "navidad"
mensaje = "¡Feliz Navidad desde el hormiguero!"
```

## Varias fiestas a la vez

Puede haber varias fiestas el mismo día. Entonces:

- **Las decoraciones se suman.** Todas se ven a la vez, salvo la guirnalda del cielo: solo
  cabe una. Por ejemplo, con `navidad` y `banderines` a la vez, se ven las lucecitas de
  Navidad y no los banderines.
- **El mensaje es el de la fiesta más corta**, la más concreta.
- **El gorro es el de la fiesta más corta que lleve gorro.**
- **Si duran lo mismo, gana la que está más abajo** en el fichero.

Con el `calendario.toml` de ejemplo:

- **El 24 de diciembre** están «Navidad» (del 15 de diciembre al 6 de enero) y
  «Nochebuena y Navidad» (del 24 al 25). Sale el mensaje de la más corta, «¡Feliz
  Navidad!», y las hormigas llevan su gorro de Papá Noel.
- **El 31 de diciembre** están «Navidad» y «Nochevieja». Se suman las dos decoraciones
  (las luces de Navidad y los fuegos artificiales de Nochevieja), y sale «¡Feliz Año
  Nuevo!» con el gorro de fiesta.

Así puedes poner una fiesta larga con su decoración y, encima, días sueltos con su propio
mensaje y su gorro.

**Los cumpleaños mandan sobre el mensaje.** El día que alguien cumple años, en el cielo
sale «FELIZ CUMPLE» con su nombre en lugar del mensaje de la fiesta. Quien cumple lleva
su gorro de cumpleaños; las demás, el de la fiesta.

## Las decoraciones

En `decoracion` se pone una de estas palabras. Lo que se pone «junto a la entrada» va al
lado del montículo de la entrada principal del hormiguero.

| Decoración | Qué se ve |
|---|---|
| `navidad` | Una guirnalda de lucecitas de colores en el cielo, un árbol de Navidad con su estrella junto a la entrada, lucecitas en el techo de cada sala y un arbolito en las salas de trabajo, reuniones, despacho y comedor. |
| `nochevieja` | De noche, fuegos artificiales; a medianoche, muchos más (si no llueve). En el comedor, las uvas en la mesa. |
| `reyes` | El árbol de Navidad y tres regalos junto a la entrada. |
| `halloween` | Cuatro calabazas en la superficie, que de noche se encienden. Una telaraña en una esquina de cada sala y una calabaza en las de trabajo, reuniones, despacho y comedor. De noche, muchos murciélagos. |
| `difuntos` | Flores rojas y amarillas delante de las lápidas del cementerio (solo si ya hay alguna lápida). |
| `andalucia` | La bandera de Andalucía ondeando en la entrada, una guirnalda de banderines verdes y blancos en el cielo y una banderita en las salas de trabajo, reuniones, despacho y comedor. |
| `espana` | La bandera de España ondeando en la entrada y una banderita en las salas de trabajo, reuniones, despacho y comedor. Se escribe sin eñe. |
| `semana_santa` | De 18:00 a 23:59, una procesión cruza la superficie: un trono iluminado y una fila de nazarenos. |
| `feria` | La portada de la feria, con su letrero «FERIA» y bombillas, junto a la entrada. Una guirnalda de farolillos de colores en el cielo y farolillos en todas las salas. De noche, de 22:30 a 23:59, fuegos artificiales (si no llueve). |
| `carnaval` | Confeti de colores que cae del cielo, y confeti en las salas. |
| `san_juan` | De noche, una hoguera junto a la entrada y algunos fuegos artificiales (si no llueve). |
| `cruces` | Una cruz de mayo, de flores, junto a la entrada. |
| `corazones` | Corazones rojos que suben desde el suelo. |
| `libro` | Una pila de tres libros junto a la entrada. |
| `pi` | El número π (`π = 3,14159265...`) escrito en el cielo, debajo del mensaje. |
| `banderines` | Una guirnalda de banderines de colores en el cielo. Es la que se pone si no dices ninguna. |

Las «salas de trabajo, reuniones, despacho y comedor» son las de un tipo con
`funcion = "trabajo"`, `"reuniones"`, `"despacho"` o `"comedor"` (en `tipos/`). Con los
tipos que vienen hechos, son las de tipo `trabajo`, `reuniones`, `despacho` y `comedor`.

## Los gorros

En `gorro` se pone una de estas palabras:

| Gorro | Cómo es |
|---|---|
| `fiesta` | Un cucurucho rosa con pompón blanco, el mismo del cumpleaños. |
| `papa_noel` | El gorro rojo de Papá Noel, con su borde y su pompón blancos. |
| `corona` | Una corona dorada. |
| `capirote` | Un capirote morado, alto y en punta. |
| `bruja` | Un sombrero de bruja, oscuro y de ala ancha. |
| `flor` | Una flor roja en la cabeza. |
| `antifaz` | Un antifaz azul en la cara. |

Las hormigas que duermen se quitan el gorro.

## El calendario de Andalucía

El fichero `ejemplos/calendario-andalucia.toml` trae 31 fiestas de Andalucía y de España.
Está pensado para Málaga, pero tiene ferias y fiestas de las ocho provincias.

| Fiesta | Fechas | Decoración | Gorro |
|---|---|---|---|
| Navidad | `28-11` a `06-01` | `navidad` | — |
| Nochebuena y Navidad | `24-12` a `25-12` | `navidad` | `papa_noel` |
| Nochevieja | `31-12` a `01-01` | `nochevieja` | `fiesta` |
| Día de la Toma de Granada | `02-01` | `banderines` | — |
| Reyes Magos | `05-01` a `06-01` | `reyes` | `corona` |
| Carnaval de Cádiz | `pascua-52` a `pascua-42` (en 2027, del 4 al 14 de febrero) | `carnaval` | `antifaz` |
| San Valentín | `14-02` | `corazones` | — |
| Día de Andalucía | `27-02` a `28-02` | `andalucia` | — |
| Día Internacional de la Mujer | `08-03` | `banderines` | — |
| Día de Pi | `14-03` | `pi` | — |
| Semana Santa | `pascua-7` a `pascua` (en 2027, del 21 al 28 de marzo) | `semana_santa` | — |
| Procesión | `pascua-3` a `pascua-2` (en 2027, 25 y 26 de marzo) | `semana_santa` | `capirote` |
| Feria de Abril | `pascua+16` a `pascua+21` (en 2027, del 13 al 18 de abril) | `feria` | `flor` |
| Día del Libro | `23-04` | `libro` | — |
| Cruces de Mayo | `01-05` a `03-05` | `cruces` | — |
| Patios de Córdoba | `04-05` a `17-05` | `cruces` | — |
| Día de Internet | `17-05` | `banderines` | — |
| Feria de Córdoba | `23-05` a `30-05` | `feria` | `flor` |
| El Rocío | `pascua+47` a `pascua+50` (en 2027, del 14 al 17 de mayo) | `banderines` | `flor` |
| Corpus de Granada | `pascua+55` a `pascua+62` (en 2027, del 22 al 29 de mayo) | `feria` | `flor` |
| Noche de San Juan | `23-06` a `24-06` | `san_juan` | — |
| Colombinas | `29-07` a `04-08` | `feria` | — |
| Feria de Málaga | `15-08` a `22-08` | `feria` | `flor` |
| Feria de Almería | `22-08` a `29-08` | `feria` | — |
| Virgen de la Victoria | `08-09` | `banderines` | — |
| Fiesta Nacional de España | `12-10` | `espana` | — |
| Feria de San Lucas | `10-10` a `19-10` | `feria` | — |
| Halloween | `25-10` a `31-10` | `halloween` | — |
| Noche de Halloween | `31-10` | `halloween` | `bruja` |
| Todos los Santos | `01-11` a `02-11` | `difuntos` | — |
| Día de la Constitución | `06-12` | `espana` | — |

Algunas cosas que se ven en este calendario:

- **Días con dos fiestas.** El 17 de mayo coinciden los Patios de Córdoba y el Día de
  Internet: hay cruz de mayo y banderines a la vez, y sale el mensaje del Día de
  Internet (la más corta). Algunos años, como 2027, ese día cae también El Rocío, y las
  hormigas llevan su flor. El 22 de agosto coinciden las ferias de Málaga y de Almería,
  que duran lo mismo: sale el mensaje de Almería (está más abajo en el fichero) y el gorro
  de flor de Málaga (la de Almería no lleva gorro).
- **La línea `lugar`.** Muchas fiestas llevan, por ejemplo, `lugar = "Córdoba"`. Es solo
  una nota para ti: el hormiguero no la usa.
- **Revísalo cada enero.** Las fiestas que dependen de la Pascua se calculan solas. Las
  ferias con fecha fija (Córdoba, Málaga, Almería, Colombinas, San Lucas...) cambian un
  poco cada año: las del fichero son las de 2026.

### Usarlo

**Para probarlo sin tocar nada**, mira la demo con ese calendario: verás pasar sus fiestas
a lo largo del año.

```bash
python3 hormiguero_pixel.py --ventana --demo --calendario ejemplos/calendario-andalucia.toml
```

**Para usarlo siempre**, cópialo encima de tu calendario. En macOS, Linux o la Pi, dentro
de la carpeta del hormiguero, crea la carpeta `local` (si ya existe, no pasa nada):

```bash
mkdir -p local
```

Y copia el calendario:

```bash
cp ejemplos/calendario-andalucia.toml local/calendario.toml
```

Si ya tenías un `local/calendario.toml`, lo sustituye: guarda antes las fiestas tuyas que
quieras conservar. En Windows, hazlo con el Explorador de archivos: copia el fichero en la
carpeta `local`, borra el `calendario.toml` que hubiera allí y ponle a la copia el nombre
`calendario.toml` (si el Explorador no enseña el `.toml` del final, escribe solo
`calendario`).

Si `local/calendario.toml` no existía, reinicia el hormiguero. En la Pi:

```bash
sudo systemctl restart hormiguero
```

**Para quedarte solo con algunas fiestas**, abre `ejemplos/calendario-andalucia.toml`,
copia los bloques `[[fiesta]]` que te gusten y pégalos en tu `calendario.toml`.

## Halloween: los que se fueron vuelven

Del 26 al 31 de octubre, los que se fueron (los de `idos.toml`, mira el
[capítulo 3](03-salas-y-gente.md)) pueden salir del cementerio y pasearse por el
hormiguero como **hormigas esqueleto**.

Se activa en `config.toml` (o `local/config.toml`), en la sección `[halloween]`:

```toml
[halloween]
esqueletos = true
```

En el `config.toml` de ejemplo ya viene así. Escribe `true` o `false` (con comillas también
vale). Con `esqueletos = false`, o si no está la sección `[halloween]`, no salen; si pones
otra cosa, tampoco, y sale un aviso. Es un cambio de
`config.toml`: reinicia el hormiguero para que se aplique.

Así son esos días:

- Sale un esqueleto por cada persona de `idos.toml` que ya se había ido ese día. Lleva su
  nombre con una calavera: «CARLOS ☠» (en Windows o macOS, sin la letra DejaVu, la calavera
  sale como un cuadradito: mira el [capítulo 1](01-instalacion.md)).
- Cada esqueleto tiene como casa una de las salas de `salas/`, elegida al azar (siempre la
  misma para cada nombre). De día hace vida normal, como las demás, salvo que se pasea: ni
  va a las reuniones ni le llama el jefe.
- **De noche no duerme**: ronda por las salas y por la superficie.
- Lleva el gorro de la fiesta del día, como todas. Con el calendario de ejemplo, el 31 de
  octubre lleva el sombrero de bruja.
- El 26 de octubre el diario dice: «¡Los que se fueron salen del cementerio! Pasearán por
  aquí hasta Halloween.»
- El 1 de noviembre ya no están. Sus lápidas siguen en el cementerio todo el tiempo.

Los esqueletos no dependen de `calendario.toml`. La fiesta «Halloween» del calendario de
ejemplo (del 25 al 31 de octubre) pone las calabazas y las telarañas; los esqueletos los
pone `[halloween]`. Puedes tener una cosa sin la otra.

## Probar las fiestas sin esperar

Arranca el hormiguero en un día y una hora concretos (la fecha, en formato `AAAA-MM-DD`):

```bash
python3 hormiguero_pixel.py --ventana --fecha 2026-12-24 --hora 21:00
```

Los esqueletos, de noche:

```bash
python3 hormiguero_pixel.py --ventana --fecha 2026-10-28 --hora 23:00
```

O mira un año entero a toda velocidad. La demo se para unos segundos en el primer día de
cada fiesta y enseña su nombre:

```bash
python3 hormiguero_pixel.py --ventana --demo
```

En Windows, cambia `python3` por `py`. Con `--fecha` o `--demo` no se guarda nada: tu
hormiguero de verdad no cambia.

## Si algo sale mal

Si algo del calendario está mal escrito, el hormiguero no se para: lo cuenta en la franja
amarilla de avisos. Si hay muchos, puede que los del calendario no quepan en la franja: el
[capítulo 2](02-primeros-pasos.md) explica cómo verlos todos.

| Aviso | Qué pasa | Qué hacer |
|---|---|---|
| `calendario: «Navidad»: fecha mal escrita (2026-12-24), usa DD-MM o pascua+N` | Esa fiesta no sale; las demás, sí. | Escribe la fecha como `"24-12"` (sin año) o `"pascua+N"`. |
| `calendario: «Feria»: no existe la decoración «cohetes»` | La fiesta sale (con su mensaje y su gorro), pero sin decorar. | Usa una palabra de [la lista](#las-decoraciones). |
| `calendario: «Feria»: no existe el gorro «chistera»` | La fiesta sale, pero sin gorro (si ese día hay otra fiesta con gorro, llevan el de esa). | Usa una palabra de [la lista](#los-gorros). |
| `calendario: escribe [[fiesta]], con dos corchetes (con [fiesta] sólo cabe una)` | Has escrito `[fiesta]` con un solo corchete. Esa fiesta sale, pero si pones otra con `[fiesta]`, el fichero da error (mira la fila siguiente). | Pon `[[fiesta]]` en todas. |
| `calendario: no se puede leer, en la línea 3: ...` | El fichero tiene un error de escritura (por ejemplo, una fecha sin comillas: `desde = 14-02`). **No sale ninguna fiesta** hasta que lo arregles. | Mira esa línea: el aviso dice también qué parece que falla. |

Cuando lo arreglas y guardas, el aviso se va solo a los pocos segundos.

---

Anterior: [5. El paisaje de arriba](05-paisaje.md) · Siguiente: [7. El tiempo y tu ciudad](07-tiempo-y-ciudad.md)
