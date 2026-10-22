# Primeros pasos

En este capítulo vas a arrancar el hormiguero, ver la demo, saber qué es cada cosa de la
pantalla y hacer tu primer cambio: poner el nombre de tu grupo y a tu gente.

Antes, una cosa sobre las órdenes. En esta guía se escriben con `python3`, como en macOS,
Linux y la Raspberry Pi:

- En **Windows**, escribe `py` en lugar de `python3`.
- Si en Linux instalaste pygame en un entorno aparte (opción B del
  [capítulo 1](01-instalacion.md)), escribe `~/venv-hormiguero/bin/python`.

Todas se escriben en una terminal abierta dentro de la carpeta del hormiguero.

## Lanzarlo en una ventana

```bash
python3 hormiguero_pixel.py --ventana
```

Se abre una ventana llamada «Ant Farm Idle». Sin `--ventana`, ocupa toda la pantalla.

El hormiguero va con la hora de verdad. La primera vez que lo arrancas así, ese día pasa a
ser el **día 0** del hormiguero, su fundación (si no le pones otra en `config.toml`), y se
apunta en `local/estado.json`. Desde
entonces crece solo: cada día que está encendido, las hormigas cavan un poco más.

## Las teclas

| Tecla | Qué hace |
|---|---|
| `q` o `Esc` | Salir. También puedes cerrar la ventana. |
| `f` | Pasar de ventana a pantalla completa, y al revés. |
| `i` | Enseñar u ocultar los fotogramas por segundo y lo que tarda en dibujar. |

Las teclas sirven en el ordenador. En la Raspberry Pi el hormiguero no lee el teclado:
se maneja por SSH (mira el [capítulo 1](01-instalacion.md)).

## La demo: un año a toda velocidad

```bash
python3 hormiguero_pixel.py --ventana --demo
```

En la demo pasa **un día cada 4 segundos**: un año entero dura unos 25 minutos, más las
paradas. Verás cambiar las estaciones, el día y la noche, y cómo se excavan las salas
nuevas a lo largo del año.

- Se para 5 segundos en cada fecha importante: el primer día de cada fiesta del
  calendario, los cumpleaños y el día en que alguien se va. Mientras está parada, arriba
  a la izquierda sale lo que se celebra en una etiqueta amarilla con una estrella.
- Cuando no está parada, en ese sitio pone `DEMO · semilla ... · un día cada 4 s`.
- Empieza el día de la fundación de tu hormiguero.
- Cada vez que la lanzas, los túneles y las salas se colocan de otra forma (sale otra
  semilla al azar).
- No guarda nada: tu hormiguero de verdad no cambia.

Para que empiece en otra fecha, añade `--fecha`. Por ejemplo, unos días antes de Navidad:

```bash
python3 hormiguero_pixel.py --ventana --demo --fecha 2026-12-20
```

Para que vaya más deprisa o más despacio, cambia los segundos que dura cada día con
`--seg-dia`. Por ejemplo, un día cada 2 segundos:

```bash
python3 hormiguero_pixel.py --ventana --demo --seg-dia 2
```

### La demo en la Raspberry Pi

En la Pi, el script `en-pantalla.sh` para el hormiguero, pone la demo en la pantalla y,
cuando pulsas `Ctrl+C`, vuelve a lanzar el hormiguero. Por SSH, entra en la carpeta:

```bash
cd ~/Ant-Farm-Idle
```

Y lanza la demo:

```bash
./en-pantalla.sh python3 hormiguero_fb.py --demo
```

## Ver un día concreto

Con `--fecha` (año-mes-día) y `--hora` (horas:minutos) ves el hormiguero en el momento
que quieras. Por ejemplo, Nochebuena a las diez de la noche:

```bash
python3 hormiguero_pixel.py --ventana --fecha 2026-12-24 --hora 22:00
```

![El hormiguero en Nochebuena](../noche.png)

- Escribe la fecha así: `2026-12-24`, con guiones y el año delante, y la hora con dos
  puntos: `22:00`. Si no, el hormiguero no arranca y te dice qué está mal escrito.
- Con solo `--fecha`, sale ese día a la hora de ahora. Con solo `--hora`, hoy a esa hora.
- Desde ahí el reloj avanza normal, un segundo cada segundo.
- Las obras salen como si el hormiguero hubiera estado encendido todos los días desde la
  fundación. Si eliges un día anterior a la fundación, ves el día 0.
- El tiempo (sol, lluvia...) sale de un modelo, no del tiempo real. Puedes forzarlo con
  `--tiempo` y uno de estos: `despejado`, `nublado`, `lluvia`, `tormenta`, `nieve` o
  `calima`.
- Igual que la demo, no guarda nada.

Por ejemplo, para ver cómo queda nevando:

```bash
python3 hormiguero_pixel.py --ventana --fecha 2027-01-15 --hora 12:00 --tiempo nieve
```

Todas las opciones, con su explicación, están en el [capítulo 10](10-referencia.md). Esta
orden enseña la lista, casi sin explicaciones:

```bash
python3 hormiguero_pixel.py --help
```

## Qué se ve en la pantalla

![El hormiguero de día](../dia.png)

**Arriba a la izquierda**, la fecha y, debajo, el día del hormiguero (los días que han
pasado desde la fundación), la estación y la temperatura. Si llueve o nieva, también lo
pone.

**Arriba a la derecha**, la hora, en grande.

**El cielo.** De día cruza el sol, que sale y se pone a su hora según la ciudad de
`config.toml`. De noche se ven la luna, con su fase, y las estrellas. Hay nubes, lluvia,
nieve y, a veces, un arcoíris. En el centro sale el mensaje de la fiesta del día (como
«Feliz Halloween»). El día de un cumpleaños, en su lugar, sale **FELIZ CUMPLE** con los
nombres.

**La superficie.** La hierba, los árboles, las farolas y las casas que elijas en
`config.toml`, y al fondo los montes y algún edificio (en el ejemplo, una catedral). El
montículo de tierra marca la entrada del hormiguero, y crece con lo que excavan. En el
cementerio (en el ejemplo, a la derecha) hay una lápida por cada persona de `idos.toml`
que ya se ha ido; si no hay ninguna, no hay cementerio. También pasan conejos, pájaros,
mariposas y otros bichos, y los días de cumpleaños hay tarta y regalos.

**Las plantas.** Bajo tierra hay cuatro plantas, como en un edificio: la 1 es la más
cercana a la superficie y la 4 la más honda. Se va de una a otra por rampas. La tierra
cambia de color con la profundidad, y las manchas grises son roca.

**Las salas.** Cada sala tiene un cartel con su nombre, en su color, y los muebles de su
tipo: escritorios, la mesa del comedor, la fuente de agua... Las de la carpeta `salas/`
están desde el día 0. Durante el año, las hormigas excavan otras: en el ejemplo, despensa,
museo, vivero de hongos, almacén y biblioteca (se eligen en `config.toml`).

**Las hormigas.** Cada persona es una hormiga, con su nombre encima en su color. Trabajan
en su sala, bajan al comedor a desayunar y a comer, van a por agua, salen a buscar comida
y van a las reuniones. De noche casi todas duermen en su sala (les salen unas «z»).

**El diario, abajo del todo.** Una franja oscura con lo que ha pasado: «Hoy · ...»,
«Ayer · ...» o «Hace 3 días · ...». Cada 8 segundos cambia a otra de las últimas
noticias. Lo que acaba de pasar sale en amarillo, empezando por «¡Ahora!».

**La franja amarilla de avisos.** Si algo de tus ficheros está mal escrito (una fecha, un
color que no existe, una reunión que no convoca a nadie...), sale una franja amarilla
debajo de la fecha que empieza por «Avisos:». El hormiguero no se para: usa un valor por
defecto y te lo cuenta ahí (si no entiende un fichero entero, por ejemplo porque faltan
unas comillas, lo deja fuera). Cuando lo arreglas y guardas el fichero, el aviso se va solo
a los pocos segundos. Si lo que has cambiado solo se aplica al reiniciar (`config.toml`, los
tipos o la sala en sí: su nombre, color, planta, sitio, ancho y tipo), sale además un aviso
que te lo recuerda, por ejemplo «config.toml ha cambiado: reinicia el hormiguero para
aplicarlo».

Los avisos nombran el fichero sin `local/` delante (`salas/reuniones.toml`, por ejemplo):
si tus datos están en `local/` (lo verás en la sección siguiente), el que tienes que
arreglar es el de `local/`.

En la franja solo cabe una línea: si hay más avisos, acaba en «…». Para leerlos todos haz
una captura sin pantalla: los avisos salen en la terminal, uno por línea, empezando por
`aviso:`. En Linux, macOS o la Pi:

```bash
python3 hormiguero_pixel.py --captura /tmp/prueba.png
```

En Windows, pon `prueba.png` en lugar de `/tmp/prueba.png`.

## Dónde poner TUS datos: la carpeta `local/`

Los ficheros que vienen con el hormiguero (`config.toml`, `salas/`, `idos.toml`,
`calendario.toml` y `tipos/`) son **de ejemplo**, con gente inventada. Tus datos van en
la carpeta `local/`:

- **Tiene prioridad.** Si existe `local/config.toml`, se usa ese en lugar del de ejemplo.
  Igual con `local/salas/`, `local/tipos/`, `local/idos.toml` y `local/calendario.toml`.
  No hay que poner ninguna opción, tampoco en el servicio de la Pi.
- **Cada uno sustituye entero al de ejemplo.** Si haces `local/salas/`, salen solo las
  salas que haya dentro. Lo que no tengas en `local/` se sigue cogiendo del ejemplo.
- **Es solo tuya.** Cuando actualices el hormiguero, tus ficheros no se tocan.
- **Al crear uno nuevo en `local/`, reinicia el hormiguero** para que lo vea.

En `local/` vive también `estado.json`, que el hormiguero escribe solo. No lo toques.

### Crear tu carpeta `local/`

En macOS, Linux o la Pi, dentro de la carpeta del hormiguero. Crea la carpeta (si ya
existe, no pasa nada):

```bash
mkdir -p local
```

Y copia dentro los ficheros de ejemplo:

```bash
cp -r salas config.toml idos.toml calendario.toml local/
```

Hazlo solo esta vez: si la repites más adelante, cambia tus ficheros de `local/` por los
de ejemplo.

En **Windows**, hazlo con el Explorador de archivos: dentro de la carpeta del hormiguero
abre la carpeta `local` (o créala si no está) y copia en ella la carpeta `salas` y los
ficheros `config.toml`, `idos.toml` y `calendario.toml`.

A partir de ahora, edita siempre las copias de `local/`.

### Con qué editar los ficheros

Son ficheros de texto. Vale cualquier editor de texto plano:

- **Windows:** el Bloc de notas (clic derecho en el fichero, **Abrir con**, **Bloc de
  notas**). Al guardar, deja la codificación en **UTF-8**, la que viene puesta. Si se
  guarda con otra («UTF-8 con BOM» o «ANSI»), también se entiende.
- **macOS:** TextEdit sirve, pero desactiva antes **Edición > Sustituciones > Comillas
  inteligentes**. Si no, cambia las comillas `"` por otras curvas y el fichero deja de
  entenderse.
- **Linux:** el editor de texto de tu escritorio.
- **En la Pi, por SSH:** `nano`. Por ejemplo, `nano local/config.toml`. Guardas con
  `Ctrl+O` e Intro, y sales con `Ctrl+X`.

## Tu primer cambio: tu grupo y tus salas

Vamos a convertir el hormiguero de ejemplo en el de un equipo inventado, «Soporte
Técnico», con tres personas y un jefe. Cambia los nombres por los de tu gente.

### Paso 1. El nombre del grupo

Abre `local/config.toml`. Al principio está la sección `[general]`. Cambia la línea
`nombre`:

```toml
[general]
nombre = "Soporte Técnico"
```

Deja el resto del fichero como está. Este nombre sale en el diario el día de la
fundación: «Se funda el hormiguero de Soporte Técnico: ...». Si tu grupo lleva artículo,
ponlo tú: con `nombre = "la familia García"` sale «de la familia García», y con
`nombre = "el Taller"`, «del Taller».

### Paso 2. Tu gente

Abre `local/salas/desarrollo.toml`. Cada fichero de `local/salas/` es una sala, y cada
`[[miembro]]` es una hormiga. Cambia todo su contenido por esto:

```toml
nombre = "Soporte"
color = "cian"
planta = 2
ancho = 40
tipo = "trabajo"

[[miembro]]
nombre = "Pilar"
cumple = "08-02"

[[miembro]]
nombre = "Javi"
cumple = "21-06"
color = "naranja"

[[miembro]]
nombre = "Nuria"
cumple = "03-10"
```

- `nombre` es lo que pone en el cartel de la sala.
- `planta` va de 1 (la más alta) a 4 (la más honda).
- `ancho` es la anchura de la sala; como mínimo, 14.
- `cumple` es día-mes: ese día la hormiga lleva gorro de fiesta y hay tarta arriba.
- `color` es opcional. Sin él, a cada hormiga se le da uno y ya no le cambia.

Algunos colores que puedes usar: `rojo_brillante`, `amarillo_brillante`, `cian`,
`magenta_brillante`, `verde_brillante`, `naranja`, `azul_brillante`, `rosa`, `turquesa`,
`lima` y `dorado`.

El nombre del fichero no tiene que coincidir con el de la sala: puede seguir llamándose
`desarrollo.toml`.

### Paso 3. Quien dirige

En `local/salas/despacho.toml` está la jefa del ejemplo, Elena. Con `jefe = true`, de vez
en cuando llama a alguien al despacho (en horario de trabajo, entre semana) y lo cuenta el
diario. Cambia todo el fichero por esto:

```toml
nombre = "Despacho"
color = "dorado"
planta = 1
ancho = 22
tipo = "despacho"
jefe = true

[[miembro]]
nombre = "Tomás"
cumple = "17-09"
```

Si en tu grupo no manda nadie, borra el fichero `local/salas/despacho.toml`.

### Paso 4. Quita la sala que sobra

La sala de Diseño del ejemplo no nos hace falta. Borra el fichero
`local/salas/diseno.toml` (en Windows, desde el Explorador de archivos). En macOS, Linux
o la Pi:

```bash
rm local/salas/diseno.toml
```

Pero ojo: en `local/salas/reuniones.toml` había una reunión fija solo para Diseño. Si no
la quitas, saldrá en la franja amarilla un aviso como este:

> Avisos: salas/reuniones.toml: reunión «Revisión de diseño»: «diseno» no es ninguna sala
> ni nadie del hormiguero

Así que cambia todo `local/salas/reuniones.toml` por esto, que deja solo la reunión de
todos los lunes:

```toml
nombre = "Reuniones"
color = "azul_brillante"
planta = 1
ancho = 30
tipo = "reuniones"

[[reunion]]
nombre = "Reunión de equipo"
dia = "lunes"
hora = "10:00"
minutos = 60
quien = "todos"
```

Deja el comedor (`comedor.toml`) y la fuente (`fuente.toml`): es donde las hormigas van a
comer y a beber.

### Paso 5. Los que se fueron

`local/idos.toml` trae dos personas inventadas, CARLOS e IRENE, con su lápida en el
cementerio. Cambia todo el fichero por esto:

```toml
# Los que se fueron. De momento, nadie.
```

### Paso 6. Reinicia y mira

En el ordenador, cierra el hormiguero con `q` y vuelve a lanzarlo:

```bash
python3 hormiguero_pixel.py --ventana
```

En la Pi, relanza el servicio:

```bash
sudo systemctl restart hormiguero
```

Ahora verás la sala «Soporte» con Pilar, Javi y Nuria, a Tomás en el despacho y ya no
habrá cementerio, porque no se ha ido nadie. Puede que alguna sala o algún túnel cambie
de sitio, porque ahora hay otras salas. Si es el primer día del hormiguero, en el diario
de abajo saldrá:

> Hoy · Se funda el hormiguero de Soporte Técnico: Pilar, Javi, Nuria, Tomás.

Si sale la franja amarilla, lee lo que dice: te cuenta qué fichero revisar y qué le pasa.

### Cambios sin reiniciar

Con el hormiguero en marcha, añade a alguien al final de `local/salas/desarrollo.toml` y
guarda:

```toml
[[miembro]]
nombre = "Carmen"
cumple = "12-12"
```

A los pocos segundos aparece su hormiga, sin reiniciar nada. Lo mismo pasa con la gente,
las reuniones, los muebles y `jefe` de las salas, con `idos.toml` y con `calendario.toml`.

Hay que reiniciar para ver los cambios de `config.toml`, de los tipos y de la sala en sí
(su nombre, color, planta, sitio, ancho y tipo), y cuando creas o borras un fichero de
sala. Hasta que reinicias, la franja amarilla te lo recuerda.

### Si tu hormiguero está en la Pi

Puedes hacer todo esto directamente en la Pi, por SSH: entra en `~/Ant-Farm-Idle`, crea
`local/` con las mismas órdenes y edita los ficheros con `nano`.

O prepara `local/` en tu ordenador y cópialo a la Pi. Desde una terminal de tu ordenador,
dentro de la carpeta del hormiguero, asegúrate de que la carpeta `local` existe en la Pi:

```bash
ssh TU_USUARIO@hormiguero.local mkdir -p Ant-Farm-Idle/local
```

Copia tus ficheros (no copies `estado.json`, que es el del ordenador):

```bash
scp -r local/salas local/config.toml local/idos.toml local/calendario.toml TU_USUARIO@hormiguero.local:Ant-Farm-Idle/local/
```

Si en la Pi ya tenías un `local/salas/`, lo que copias se suma a lo que había: borra allí
los ficheros de sala que ya no quieras.

Y relanza el servicio desde la Pi:

```bash
sudo systemctl restart hormiguero
```

---

Anterior: [1. Instalación](01-instalacion.md) · Siguiente: [3. Salas y gente](03-salas-y-gente.md)
