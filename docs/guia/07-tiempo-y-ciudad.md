# El tiempo y tu ciudad

En este capítulo vas a aprender a poner tu ciudad, para que el sol salga y se ponga a su
hora, y a conectar el hormiguero con el tiempo de verdad, para que llueva, nieve o haya
tormenta cuando de verdad pasa.

Antes de empezar:

- Casi todo esto va en `config.toml`. Edita tu copia, la de `local/config.toml` (crearla
  lo cuenta el [capítulo 2](02-primeros-pasos.md)).
- Los cambios de `config.toml` se ven **al reiniciar** el hormiguero. En el ordenador,
  ciérralo con `q` y vuelve a lanzarlo. En la Pi:

```bash
sudo systemctl restart hormiguero
```

- Las órdenes se escriben con `python3`. En Windows, escribe `py` en su lugar.

## Tu ciudad: `[ciudad]`

En tu `config.toml` ya hay una sección `[ciudad]`. Así viene en el ejemplo:

```toml
[ciudad]
nombre = "Málaga"
lat = 36.72
lon = -4.42
# zona_horaria = "Europe/Madrid"
```

| Línea | Qué es |
|---|---|
| `nombre` | Solo para ti: no sale en la pantalla. |
| `lat` | La latitud. Positiva al norte del ecuador y negativa al sur. |
| `lon` | La longitud. Positiva al este del meridiano de Greenwich y negativa al oeste. En España casi siempre es negativa; es positiva en Cataluña, en Baleares y en algunas zonas del este de Aragón y de la Comunidad Valenciana. |
| `zona_horaria` | Opcional. Mira [más abajo](#la-zona-horaria). |

Si no pones `lat` o `lon`, se usan las de Málaga. La latitud va de -90 a 90 y la longitud,
de -180 a 180: si te sales, sale un aviso.

> **Cambia las líneas, no copies la sección entera debajo.** Si en el fichero hay dos
> `[ciudad]`, no se puede leer y el hormiguero usa los valores por defecto en todo. Lo
> avisa en la franja amarilla con un mensaje como «config: no se puede leer, en la línea
> 40: la sección [ciudad] está repetida (escríbela una sola vez)».

### Cómo saber la latitud y la longitud

1. Abre [Google Maps](https://maps.google.com) en el ordenador y busca tu ciudad.
2. Haz clic derecho en el sitio exacto (tu casa, tu oficina o el centro).
3. Lo primero del menú son dos números, por ejemplo `36.72132, -4.42162`. Haz clic en
   ellos y se copian.
4. El primero es `lat` y el segundo, `lon`.

Con dos decimales sobra. Escríbelos **con punto**, nunca con coma: con `lat = 36,72` el
fichero entero deja de entenderse.

Algunas ciudades, ya con su zona horaria:

| Ciudad | `lat` | `lon` | `zona_horaria` |
|---|---|---|---|
| Málaga | `36.72` | `-4.42` | `"Europe/Madrid"` |
| Madrid | `40.42` | `-3.70` | `"Europe/Madrid"` |
| Barcelona | `41.39` | `2.17` | `"Europe/Madrid"` |
| Las Palmas de Gran Canaria | `28.12` | `-15.43` | `"Atlantic/Canary"` |
| Ciudad de México | `19.43` | `-99.13` | `"America/Mexico_City"` |
| Bogotá | `4.71` | `-74.07` | `"America/Bogota"` |
| Buenos Aires | `-34.60` | `-58.38` | `"America/Argentina/Buenos_Aires"` |
| Santiago de Chile | `-33.45` | `-70.67` | `"America/Santiago"` |

Por ejemplo, para Madrid la sección queda así:

```toml
[ciudad]
nombre = "Madrid"
lat = 40.42
lon = -3.70
```

### La zona horaria

El hormiguero usa la hora del ordenador o de la Pi. Si ya está en la hora de tu ciudad
(en la Pi lo miraste al instalarla, en el
[capítulo 1](01-instalacion.md#paso-3-comprueba-la-zona-horaria)), no hace falta nada más.

Pon `zona_horaria` si el ordenador está en otra zona. Por ejemplo, si la Pi está en hora
UTC, o si el ordenador va en la hora de la Península y la ciudad es de Canarias:

```toml
[ciudad]
nombre = "Las Palmas de Gran Canaria"
lat = 28.12
lon = -15.43
zona_horaria = "Atlantic/Canary"
```

Con ella, todo va en la hora de la ciudad: el reloj de la pantalla, el cambio de día (y
con él los cumpleaños y las fiestas), los horarios de `[horario]`, las reuniones y el sol.

- El nombre va en inglés, con barra y guiones bajos: `"Europe/Madrid"`,
  `"America/Mexico_City"`. Están todos en la
  [lista de zonas horarias](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)
  de la Wikipedia (columna *TZ identifier*).
- Si el nombre no existe (por ejemplo, `"Europa/Madrid"`), sale el aviso «config:
  [ciudad] zona_horaria «Europa/Madrid» no existe (p. ej. "Europe/Madrid"; uso la del
  ordenador)» y se usa la hora del ordenador.
- **En Windows**, Python no trae la lista de zonas horarias. Si sale el aviso «config:
  [ciudad] zona_horaria: este ordenador no tiene la lista de zonas horarias...»,
  instálala con esta orden y reinicia el hormiguero:

```bash
py -m pip install tzdata
```

## El sol y las estaciones

Con la latitud, la longitud y la fecha, el hormiguero calcula a qué hora sale y se pone
el sol en tu ciudad. Entre la puesta y la salida es de noche: salen la luna y las
estrellas, se encienden las ventanas y las farolas, y casi todas las hormigas se van a
dormir a su sala. Sirve para cualquier sitio del mundo, también donde hay sol de
medianoche o noche polar.

La estación sale arriba a la izquierda, junto al día del hormiguero. Cambia en estas
fechas (aproximadas):

| Estación | Empieza |
|---|---|
| Primavera | 20 de marzo |
| Verano | 21 de junio |
| Otoño | 23 de septiembre |
| Invierno | 21 de diciembre |

Con las estaciones cambian las flores del suelo, las hojas que caen, los bichos que pasan
y el ritmo de las obras: en invierno cavan más despacio (lo verás en el
[capítulo 8](08-como-crece.md)).

### Si vives en el hemisferio sur

Con la latitud en negativo, las estaciones van al revés: en julio es invierno y en enero,
verano. Las flores, las hojas, los bichos y el ritmo de las obras se desplazan medio año.

Las fiestas no se mueven: Navidad sigue siendo el 25 de diciembre (en verano).

> **Ojo:** sin OpenWeather, la temperatura y la lluvia salen de un año normal de Málaga,
> mes a mes, y eso **no** se da la vuelta. En Buenos Aires, en julio pondría algo como
> «invierno · 28 °C». Si vives en el hemisferio sur, usa OpenWeather.

## De dónde sale el tiempo

Hay dos fuentes:

- **OpenWeather**, una web que da el tiempo de verdad de cualquier sitio. Es gratis, pero
  hace falta una clave. Los pasos están en la siguiente sección.
- **Un modelo de respaldo**, sin internet: un año normal de Málaga, con los días de
  lluvia y las temperaturas de cada mes (datos de AEMET). El mismo día siempre tiene el
  mismo tiempo. En este modelo **nunca nieva**.

El modelo de respaldo se usa cuando no hay clave, cuando no hay internet, en la demo y
cuando eliges otra fecha u otra hora con `--fecha` o `--hora`.

Lo elige la sección `[tiempo]`:

```toml
[tiempo]
fuente = "openweather"
cada_minutos = 10
```

| Línea | Qué es |
|---|---|
| `fuente` | `"openweather"` (lo normal): el tiempo real, si hay clave. `"estadistico"`: siempre el modelo de respaldo, sin conectarse a nada. Con otra cosa (una errata), sale un aviso y se usa `"openweather"`. |
| `cada_minutos` | Cada cuántos minutos se pide el tiempo. Como mínimo, 5. |

Con `fuente = "openweather"` y sin clave, el hormiguero funciona igual, con el modelo de
respaldo.

## OpenWeather paso a paso

### Paso 1. Crea una cuenta gratuita

La web de OpenWeather está en inglés.

1. Entra en <https://home.openweathermap.org/users/sign_up>.
2. Escribe un nombre de usuario, tu correo y una contraseña (dos veces).
3. Marca las dos casillas obligatorias: **I am 16 years old and over** y **I agree with
   Privacy Policy...** Las de noticias (*System news*, *Product news*, *Corporate news*)
   son opcionales.
4. Marca la casilla de que no eres un robot y pulsa el botón para crear la cuenta.
5. Si sale una ventana que pregunta para qué vas a usarla, rellénala y guárdala.
6. Te llega un correo de OpenWeather. Ábrelo y pulsa el botón para confirmar tu correo.

No hace falta contratar nada ni dar una tarjeta. El hormiguero usa el tiempo actual
(*Current Weather*), que entra en el plan gratuito. Lo pide cada 10 minutos, unas 4.300
veces al mes: muy por debajo del límite gratuito.

### Paso 2. Copia tu clave

1. Entra en tu cuenta y abre la pestaña **API keys**
   (<https://home.openweathermap.org/api_keys>).
2. Ya hay una clave creada, llamada **Default**. Es una ristra de 32 letras y números,
   como `0123456789abcdef0123456789abcdef`. Cópiala entera. (También te llega en el
   correo de bienvenida.)

Si quieres, ahí mismo puedes crear otra solo para el hormiguero: escribe un nombre (por
ejemplo, `hormiguero`) y pulsa **Generate**.

> La clave es como una contraseña: no la pongas en sitios públicos.

### Paso 3. Comprueba que la clave funciona

Una clave nueva puede tardar **hasta 2 horas** en funcionar. Para saber si ya va, pega
esta dirección en el navegador, cambiando `TU_CLAVE` por tu clave:

```text
https://api.openweathermap.org/data/2.5/weather?lat=36.72&lon=-4.42&units=metric&lang=es&appid=TU_CLAVE
```

- **Si funciona**, sale un texto con el tiempo de Málaga: la temperatura (`"temp"`), una
  descripción (`"description":"cielo claro"`)...
- **Si sale** `{"cod":401, "message": "Invalid API key...`, la clave aún no está activa o
  está mal copiada. Espera un rato y vuelve a probar.

### Paso 4. Guarda la clave en el hormiguero

Lo mejor es un fichero de texto con la clave dentro: `local/openweather_clave.txt`. La
carpeta `local/` no se sube a git, así que tu clave no se publica. Sirve en el ordenador
y en la Pi.

**En macOS, Linux o la Pi**, dentro de la carpeta del hormiguero (en la Pi, entra en ella
con `cd ~/Ant-Farm-Idle`). Crea la carpeta `local` (si ya existe, no pasa nada):

```bash
mkdir -p local
```

Y guarda la clave, cambiando `TU_CLAVE` por la tuya:

```bash
echo TU_CLAVE > local/openweather_clave.txt
```

**En Windows**, con el Bloc de notas:

1. Abre el Bloc de notas y pega la clave, sola.
2. **Archivo > Guardar como**.
3. Entra en la carpeta `local` del hormiguero.
4. Como nombre, escribe `openweather_clave.txt` y guarda.

En el fichero va solo la clave. Los espacios o las líneas en blanco de alrededor no
importan, ni que el Bloc de notas lo guarde «con BOM». Si el fichero está vacío, se usa la
de `config.toml` (si la hay).

### Paso 5. Reinicia y comprueba

La clave se lee al arrancar: reinicia el hormiguero.

En cuanto recibe el primer dato bueno, el hormiguero crea el fichero
`local/openweather.json`, y lo vuelve a escribir cada vez que recibe el tiempo (cada 10
minutos). Para verlo en macOS, Linux o la Pi, dentro de la carpeta del hormiguero:

```bash
ls -l local/openweather.json
```

En Windows, mira si está en la carpeta `local` con el Explorador de archivos.

Si aparece, con la hora de hace unos minutos, ya va. La temperatura de arriba a la
izquierda tiene que ser la que hace ahora en tu ciudad.

Si al cabo de unos minutos no aparece, vuelve al paso 3. Mientras, el hormiguero sigue con
el modelo de respaldo y lo vuelve a intentar cada 2 minutos. Si OpenWeather rechaza la
clave tres veces seguidas, sale en la franja amarilla el aviso «tiempo: OpenWeather no
acepta la clave...». Si lo que falla es internet, no avisa.

### Otras formas de dar la clave

Hay tres sitios para la clave. Si la pones en varios, el hormiguero usa el primero de
esta lista:

1. La variable `OPENWEATHER_API_KEY`.
2. El fichero `local/openweather_clave.txt`, el del paso 4.
3. La línea `clave` de la sección `[tiempo]` de `config.toml`.

**La variable, para probar en el ordenador.** En macOS o Linux, escribe esto en una
terminal (con tu clave) y lanza el hormiguero desde esa misma terminal. Solo vale para
esa terminal y hasta que la cierres:

```bash
export OPENWEATHER_API_KEY=TU_CLAVE
```

**La línea `clave` en `config.toml`.** Funciona así:

```toml
[tiempo]
fuente = "openweather"
cada_minutos = 10
clave = "TU_CLAVE"
```

Pero **no la pongas en el `config.toml` del repositorio**: si lo subes a GitHub o lo
compartes, cualquiera puede ver tu clave y usarla. Si la quieres ahí, que sea en
`local/config.toml`.

**En la Pi, el servicio no ve las variables** que pones con `export`: allí usa el fichero
del paso 4. Otra opción en la Pi es el fichero `local/entorno`, que leen el servicio, al
arrancar, y `en-pantalla.sh`. Asegúrate de que existe la carpeta `local`:

```bash
mkdir -p ~/Ant-Farm-Idle/local
```

Y abre el fichero con `nano`:

```bash
nano ~/Ant-Farm-Idle/local/entorno
```

Escribe esta línea (con tu clave, sin espacios ni comillas), guarda con `Ctrl+O` e Intro,
y sal con `Ctrl+X`:

```text
OPENWEATHER_API_KEY=TU_CLAVE
```

Y relanza el servicio:

```bash
sudo systemctl restart hormiguero
```

Si instalaste el hormiguero hace tiempo, antes de que existiera `local/entorno`, vuelve a
ejecutar el instalador para que el servicio lo lea:

```bash
bash ~/Ant-Farm-Idle/instalar-pi.sh
```

## Si se va internet

El hormiguero nunca se para a esperar a internet:

- Si falla una petición, lo vuelve a intentar a los 2 minutos.
- Mientras tanto, se fía del último dato bueno **durante 3 horas**. Como ese dato se
  guarda en `local/openweather.json`, también vale después de reiniciar.
- Pasadas 3 horas sin datos, usa el modelo de respaldo (el de Málaga) hasta que vuelve
  la conexión.

Si arranca sin internet y sin un dato de las últimas 3 horas, empieza con el modelo de
respaldo y cambia al tiempo real en cuanto llega el primer dato.

## Qué se ve con cada tiempo

**Despejado.** Cielo azul y sol. De noche, luna y estrellas, y alguna estrella fugaz.

**Nublado.** Pasan más nubes y, si está muy cubierto, el cielo se pone gris y no se ven
las estrellas.

**Lluvia.** Caen gotas y arriba a la izquierda pone «· lluvia». Mientras llueve, las
hormigas no salen a buscar comida: solo salen a cazar alguna lombriz. Además:

- Desde que empieza a llover hasta unas 8 horas después de que pare, hay charcos, y salen
  lombrices (que las hormigas cazan) y algún caracol.
- Si sale el sol, algunos días aparece un arcoíris.
- En otoño, si ha llovido en los últimos días, salen setas.
- Si llevaba 25 días o más sin llover, el diario lo celebra: «¡Por fin llueve después de
  30 días!».

**Tormenta.** Llueve en diagonal, por el viento, y de vez en cuando un relámpago ilumina
el cielo. El diario dice «Tormenta. Todas dentro.».

**Nieve.** Caen copos y arriba pone «· nieve». La nieve se queda encima de los árboles,
los tejados, las lápidas, el suelo y las cumbres de los montes. Con OpenWeather, sigue ahí
hasta un día después de que deje de nevar, si hace menos de 5 grados. El diario dice
«¡Nieva! Todo se queda blanco.». Recuerda: sin OpenWeather nunca nieva, salvo si lo
fuerzas con `--tiempo nieve` (más abajo).

**Calima.** El polvo en el aire pone el cielo y el sol de color naranja. El diario dice
«Calima: el cielo se pone naranja.». Con OpenWeather sale cuando hay polvo o arena en el
aire; con el modelo de respaldo, algunos días sueltos de febrero, marzo y verano.

**Terral.** Solo con el modelo de respaldo: algunos días de verano sopla el terral, el
viento caliente de Málaga. Hace 5 grados más y el diario dice «Terral. Hace un calor que
derrite.».

**Frío y calor.** Con menos de 11 grados, en invierno o con más de 30, las hormigas salen
menos. Las lagartijas solo salen con más de 20.

## Probar cada tiempo: `--tiempo`

Para ver cómo queda cada tiempo sin esperar a que pase, fuérzalo con `--tiempo` y uno de
estos: `despejado`, `nublado`, `lluvia`, `tormenta`, `nieve` o `calima`.

```bash
python3 hormiguero_pixel.py --ventana --tiempo tormenta
```

- Todo el rato hace ese tiempo y no se pide nada a OpenWeather.
- La temperatura es siempre de 15 grados (con nieve, -1).
- Se puede juntar con `--fecha` y `--hora`. Por ejemplo, nevando de noche:

```bash
python3 hormiguero_pixel.py --ventana --fecha 2027-01-15 --hora 21:00 --tiempo nieve
```

- Y con la demo, para ver el año entero con ese tiempo:

```bash
python3 hormiguero_pixel.py --ventana --demo --tiempo lluvia
```

Con `--fecha`, `--hora` o `--demo` no se guarda nada. Con solo `--tiempo`, en cambio, es
tu hormiguero de verdad con la hora de ahora: cuenta como encendido y guarda lo que hace,
como siempre.

**En la Pi**, entra en la carpeta del hormiguero:

```bash
cd ~/Ant-Farm-Idle
```

Y ponlo en la pantalla con `en-pantalla.sh` (al pulsar `Ctrl+C`, vuelve el hormiguero
normal):

```bash
./en-pantalla.sh python3 hormiguero_fb.py --fecha 2027-01-15 --hora 12:00 --tiempo nieve
```

## Si algo no sale

- **El sol sale o se pone a una hora rara.** Revisa los signos de `lat` y `lon` (en
  España, la longitud va en negativo, salvo en Cataluña, Baleares y alguna zona más). Y
  revisa la zona horaria del ordenador o la `zona_horaria`.
- **La hora de la pantalla está mal.** La Pi no está en tu zona horaria: arréglalo como
  en el [capítulo 1](01-instalacion.md#paso-3-comprueba-la-zona-horaria) o pon
  `zona_horaria`.
- **Nunca hace el tiempo de verdad.** Comprueba la clave en el navegador (paso 3), que
  el fichero se llama exactamente `openweather_clave.txt` y está dentro de `local/`, que
  en `[tiempo]` pone `fuente = "openweather"` (o nada) y que has reiniciado el hormiguero.
  Con otra fecha u otra hora (`--fecha`, `--hora`, `--demo`) o con `--tiempo`, no se usa
  OpenWeather.
- **Pone «invierno» con 28 grados.** Estás en el hemisferio sur sin OpenWeather. Pon la
  clave.
- **Ha salido un aviso en la franja amarilla.** Lee lo que dice: te cuenta qué está mal.
  Si es «config: no se puede leer...», el fichero entero no se puede leer. El mensaje dice
  en qué línea está el fallo y qué parece que falla. Suele ser una coma en un número o una
  sección repetida.

---

Anterior: [6. Fiestas y Halloween](06-fiestas-y-halloween.md) · Siguiente: [8. Cómo crece el hormiguero](08-como-crece.md)
