# El paisaje de arriba

En este capítulo vas a aprender a elegir lo que se ve encima del hormiguero: los árboles,
las casas y las farolas de la superficie, lo que hay al fondo, los montes, las gaviotas y
el sitio del cementerio.

![El hormiguero de día](../dia.png)

## Dónde se cambia

El paisaje está en la sección `[paisaje]` de `config.toml`. Si ya tienes tu copia
`local/config.toml`, cámbialo ahí (mira el [capítulo 2](02-primeros-pasos.md)).

Los cambios de `config.toml` se ven **al reiniciar** el hormiguero:

- **En el ordenador:** ciérralo con `q` y vuelve a arrancarlo.
- **En la Pi:** relanza el servicio.

```bash
sudo systemctl restart hormiguero
```

## Cómo se dice dónde va cada cosa

Cada pieza lleva una `x`: su posición en tanto por ciento del ancho de la pantalla.

- `x = 0` es el borde izquierdo.
- `x = 50` es el centro.
- `x = 100` es el borde derecho.

La `x` marca el centro de la pieza. Puede llevar decimales (`x = 12.5`). Si pones menos de
0 se queda en 0, y si pones más de 100 se queda en 100. En los bordes, parte de la pieza
se queda fuera de la pantalla. Si no pones `x`, o la escribes mal (`X = 30`, en
mayúscula), la pieza va en el centro y no sale ningún aviso.

## Las piezas

Hay dos clases de piezas: las de la **superficie** (`[[paisaje.suelo]]`) y las del
**fondo** (`[[paisaje.fondo]]`), que se ponen sobre la ladera de los montes, detrás de
todo lo demás.

![Todas las piezas del paisaje, de día y de noche](../galeria-paisaje.png)

### En la superficie: `[[paisaje.suelo]]`

| Pieza | Qué es | Cómo cambia |
|---|---|---|
| `chumbera` | Una chumbera. | De julio a septiembre tiene higos chumbos. |
| `almendro` | Un almendro. | Sin hojas desde primeros de diciembre hasta el 19 de enero. En flor, rosa y blanco, del 20 de enero a primeros de marzo. Verde en primavera y verano, con mariquitas de marzo a junio. En octubre y noviembre se pone naranja y se va quedando sin hojas. |
| `palmera` | Una palmera. | De agosto a finales de octubre tiene dátiles. |
| `olivo` | Un olivo. | De octubre a enero tiene aceitunas. |
| `pino` | Un pino. | Siempre igual. |
| `farola` | Una farola. | De noche se enciende y alumbra alrededor. |
| `banco` | Un banco de parque. | Siempre igual. |
| `casa` | Una casa con tejado y chimenea. | Cada casa sale con sus colores de pared y de tejado. De noche se encienden algunas ventanas. |

Las fechas son las del hemisferio norte. Si tu ciudad tiene la latitud negativa
(hemisferio sur), las flores, las hojas y los frutos van medio año desplazados.

### Al fondo: `[[paisaje.fondo]]`

| Pieza | Qué es | De noche |
|---|---|---|
| `catedral` | La catedral de Málaga, «la Manquita»: una torre terminada y la otra sin terminar. | Se iluminan sus ventanas. |
| `ciudad` | Un grupo de edificios altos. | Se encienden ventanas sueltas. |
| `faro` | Un faro de rayas rojas y blancas. | Se enciende y su haz de luz barre el cielo. |
| `molino` | Un molino de viento. Sus aspas giran siempre, despacio. | Se ilumina su ventana. |
| `torre` | Una torre alta con el tejado en punta. | Se ilumina. |
| `castillo` | Un castillo con dos torres y almenas. | Se ilumina su puerta. |

### Cómo se colocan

- **Puedes repetir piezas.** Pon tres casas o cinco pinos si quieres. Cada casa elige sus
  colores por su cuenta, y cada almendro y cada olivo tienen su copa un poco distinta.
- **Si dos piezas se pisan, la que va más abajo en el fichero se pinta delante.**
- **Las piezas del fondo quedan detrás** de las de la superficie, también las aspas del
  molino y el haz del faro.
- **Las entradas del hormiguero** tienen un montículo de tierra que se pinta encima de las
  piezas. Si una pieza queda tapada, muévela un poco.
- **Como guía de tamaños:** un almendro o una palmera ocupan más o menos de `x - 5` a
  `x + 5`; un olivo o una casa, de `x - 4` a `x + 4`; la chumbera, el pino, la farola y el
  banco, menos. Al fondo, la más ancha es la ciudad: de `x - 8` a `x + 8`.

## Cómo se escribe

Así viene en el `config.toml` de ejemplo:

```toml
[paisaje]
montes = true              # montes al fondo
costa = true               # gaviotas
cementerio = 74            # dónde empieza el cementerio de los que se fueron (en %)

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
```

Fíjate en esto:

1. Cada pieza empieza con `[[paisaje.suelo]]` o `[[paisaje.fondo]]`, con **dos
   corchetes**.
2. Debajo van `pieza` (el nombre, entre comillas) y `x` (un número, sin comillas).
3. Las líneas `montes`, `costa` y `cementerio` van justo debajo de `[paisaje]`, **antes**
   de la primera pieza. Si las pones después, cuentan como parte de la pieza de encima, no
   sirven de nada y sale un aviso.
4. Si escribes al menos un `[[paisaje.suelo]]`, salen **solo** los tuyos. Si no escribes
   ninguno, salen los de ejemplo de arriba. Con `[[paisaje.fondo]]` pasa lo mismo.

### Ejemplo: un pueblo de interior

Copia este bloque en lugar de todo lo que hay en tu `[paisaje]` (desde `[paisaje]` hasta
la última pieza; deja `[halloween]` y el resto como están):

```toml
[paisaje]
montes = true
costa = false
cementerio = 80

[[paisaje.suelo]]
pieza = "olivo"
x = 8

[[paisaje.suelo]]
pieza = "casa"
x = 35

[[paisaje.suelo]]
pieza = "farola"
x = 44

[[paisaje.suelo]]
pieza = "banco"
x = 50

[[paisaje.suelo]]
pieza = "almendro"
x = 64

[[paisaje.fondo]]
pieza = "castillo"
x = 30

[[paisaje.fondo]]
pieza = "molino"
x = 72
```

### Ejemplo: un pueblo de costa

Sin montes, con gaviotas, un faro y una ciudad al fondo:

```toml
[paisaje]
montes = false
costa = true
cementerio = 60

[[paisaje.suelo]]
pieza = "palmera"
x = 5

[[paisaje.suelo]]
pieza = "chumbera"
x = 30

[[paisaje.suelo]]
pieza = "farola"
x = 40

[[paisaje.suelo]]
pieza = "palmera"
x = 92

[[paisaje.fondo]]
pieza = "ciudad"
x = 45

[[paisaje.fondo]]
pieza = "faro"
x = 85
```

### Ejemplo: sin nada

Para dejar la superficie y el fondo vacíos, cambia todo tu `[paisaje]` por dos listas
vacías (si quieres, con `montes`, `costa` y `cementerio` debajo de `[paisaje]`):

```toml
[paisaje]
suelo = []
fondo = []
```

Para vaciar solo uno de los dos, pon solo su línea. Pero no la mezcles con piezas de ese
grupo: con `suelo = []` y algún `[[paisaje.suelo]]` a la vez, el hormiguero no puede leer
`config.toml` entero y sale el aviso «config: no se puede leer, en la línea ...: la sección
[paisaje.suelo] ya estaba escrita de otra forma más arriba».

## Montes y costa

**`montes`**

- `montes = true` (lo normal): montes azulados al fondo. Cuando nieva, sus cumbres se
  ponen blancas.
- `montes = false`: sin montes lejanos. Se quedan las colinas verdes de delante, y las
  piezas del fondo se ponen más bajas, en el horizonte.

**`costa`**

- `costa = true` (lo normal): de día y sin lluvia, de vez en cuando cruzan gaviotas.
- `costa = false`: sin gaviotas. Los demás pájaros siguen saliendo.

Escribe `true` o `false` (con comillas también vale, y `"sí"` o `"no"`). Si pones otra
cosa, sale un aviso y se queda como si no lo hubieras puesto: con montes y con gaviotas.

## El cementerio

El cementerio sale **solo si hay alguien en `idos.toml` que ya se ha ido** (cómo se
apunta a quien se va está en el [capítulo 3](03-salas-y-gente.md)). Cada uno tiene su
lápida con su nombre, dentro de una valla y con un cartel de «R.I.P.» encima.

`cementerio = 74` dice dónde empieza (su borde izquierdo), en tanto por ciento del ancho,
como la `x` de las piezas. Lo normal es que salga ahí, pero:

- **Nunca se pone encima de una entrada del hormiguero.** Si en ese sitio hay una, se va
  al hueco libre más cercano. Por eso a veces sale un poco más a la izquierda o a la
  derecha de lo que pusiste.
- **Si puede, no tapa las piezas de la superficie** (los árboles, las casas, los bancos,
  las farolas...). Si donde lo pones tapa alguna, se va al hueco más cercano donde quepa sin
  tapar nada, aunque para eso tenga que escribir los nombres más pequeños o ponerlos en dos
  filas. Si no hay ningún hueco así, se queda lo más cerca posible de donde lo pones (nunca
  encima de una entrada), aunque tape alguna pieza.
- **No se sale por la derecha.** Si desde ahí no cabe entero, se corre a la izquierda lo
  que haga falta (con `cementerio = 100` empieza bastante antes del borde).
- **Si no caben todas las lápidas**, primero se escriben los nombres con letra más
  pequeña y luego se ponen en dos filas. Si aun así no caben, se quedan fuera los
  primeros de `idos.toml` y sale un aviso con sus nombres.

Cuando no le queda más remedio que tapar una pieza, el cementerio se pinta encima de ella:
mueve la pieza o el cementerio, o deja más sitio libre en la superficie.

Cuando nieva, también se cubren de nieve las lápidas. Además, el cementerio tiene sus
días especiales: flores en Todos los Santos, si tu calendario trae esa fiesta (el de
ejemplo no la trae; el de Andalucía de `ejemplos/`, sí), y esqueletos en Halloween (lo
verás todo en el [capítulo 6](06-fiestas-y-halloween.md)).

## Qué depende de cada pieza

Algunas cosas de la superficie solo salen si tienes cierta pieza. Cuando hay varias del
mismo tipo, cuenta **la primera que aparece en el fichero** (no la que está más a la
izquierda).

| Qué | De qué pieza depende | Cuándo |
|---|---|---|
| Pétalos que caen del almendro | El primer `almendro`. | Del 20 de enero a primeros de marzo. |
| Hojas que caen en otoño | El primer `almendro`. | Octubre y noviembre. |
| Almendras en el suelo, para que las hormigas las recojan | El primer `almendro`: caen a su lado. Sin almendro, no hay almendras. | Agosto y septiembre. |
| Higos chumbos en el suelo, para que las hormigas los recojan | La primera `chumbera`: caen a su lado. Sin chumbera, no hay higos. | De julio a septiembre. |
| El búho | El primer `olivo`. Si no hay olivo, el primer `pino`; si tampoco, el primer `almendro`; y si tampoco, la primera `palmera`. Sin ninguno de estos árboles, no hay búho. | De noche y sin lluvia. No todas las noches: más o menos seis de cada diez. |
| La luz de las farolas | Todas las `farola`. | De noche. |

Las almendras y los higos salen de día y sin lluvia, y no siempre: son parte de la comida
que las hormigas encuentran arriba, junto con migas, semillas, azucarillos, alguna
galleta y, muy de vez en cuando, medio bocadillo. Las flores de los árboles (y los frutos
que se ven en ellos) salen en todos los árboles de ese tipo, no solo en el primero.

## Probarlo sin esperar

No hace falta esperar a febrero para ver el almendro en flor. En el ordenador, arranca el
hormiguero en otra fecha, a la hora de ahora (la fecha, siempre en formato `AAAA-MM-DD`):

```bash
python3 hormiguero_pixel.py --ventana --fecha 2027-02-10
```

De noche, para ver las farolas y las ventanas (y el búho, si esa noche sale y no llueve):

```bash
python3 hormiguero_pixel.py --ventana --fecha 2027-02-10 --hora 23:00
```

Con nieve (`--tiempo` fuerza el tiempo: `despejado`, `nublado`, `lluvia`, `tormenta`,
`nieve` o `calima`):

```bash
python3 hormiguero_pixel.py --ventana --fecha 2027-01-10 --tiempo nieve
```

En Windows, cambia `python3` por `py`. Con `--fecha` no se guarda nada: tu hormiguero de
verdad no cambia.

En la Pi, o si quieres leer todos los avisos, haz una captura: se guarda una imagen y los
avisos salen en la terminal.

```bash
python3 hormiguero_pixel.py --fecha 2027-02-10 --hora 23:00 --captura prueba.png
```

## Si algo sale mal

Si algo del paisaje está mal escrito, el hormiguero no se para: lo cuenta en la franja
amarilla de avisos.

| Aviso | Qué pasa | Qué hacer |
|---|---|---|
| `paisaje: no existe la pieza «baobab»` | Ese nombre no está en la lista de piezas de la superficie. | Escríbelo como en la tabla (las mayúsculas dan igual). |
| `paisaje: no existe la pieza de fondo «pino»` | Has puesto una pieza de la superficie en `[[paisaje.fondo]]`, o el nombre está mal. | Las piezas del fondo son `catedral`, `ciudad`, `faro`, `molino`, `torre` y `castillo`. |
| `paisaje: pieza mal escrita (...)` | A la pieza le falta `pieza = "..."`, o su `x` no es un número (por ejemplo, `x = "mucho"`). | Revisa la pieza que sale entre paréntesis. |
| `paisaje: escribe [[paisaje.suelo]], con dos corchetes (...)` | Has abierto la pieza con un solo corchete: `[paisaje.suelo]`. Sale, pero solo cabe una. | Cada pieza empieza con dos corchetes. |
| `paisaje: suelo mal escrito (true), usa [[paisaje.suelo]] (puse el de siempre)` | Has escrito `suelo = ...` con algo que no es una lista de piezas. Salen las de ejemplo. | Escribe cada pieza con su `[[paisaje.suelo]]` (o `suelo = []` para no poner ninguna). |
| `paisaje: no conozco «monte» (no lo tengo en cuenta)` | Una clave que no existe en `[paisaje]` (aquí, `monte` en vez de `montes`). Dentro de una pieza, dice también qué pieza es: `paisaje: olivo: no conozco «X» ...` | Corrige el nombre: dentro de `[paisaje]` valen `montes`, `costa`, `cementerio`, `suelo` y `fondo`; dentro de una pieza, `pieza` y `x`. |
| `paisaje: «costa» está dentro de una pieza (olivo) y [paisaje] no lo ve; ...` | Has escrito `costa`, `montes` o `cementerio` debajo de una pieza. | Súbelo arriba, justo debajo de `[paisaje]`. |
| `paisaje: montes debe ser true o false (puse true)` | `montes` o `costa` con algo que no es sí o no. | Pon `true` o `false`. |
| `config: [paisaje] cementerio debe ser un número (puse 74)` | `cementerio` no es un número. | Pon un número del 0 al 100. |

Las piezas que están mal no salen. Las demás, sí.

---

Anterior: [4. Tipos de sala y muebles](04-tipos-y-muebles.md) · Siguiente: [6. Fiestas y Halloween](06-fiestas-y-halloween.md)
