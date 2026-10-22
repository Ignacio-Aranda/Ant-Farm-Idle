# Tipos de sala

Cada fichero de esta carpeta es un tipo de sala. Una sala de `salas/` dice de qué
tipo es con `tipo = "nombre_del_fichero"` (sin el `.toml`). Si no lo dice, es `trabajo`.

```toml
funcion = "trabajo"   # qué hacen las hormigas aquí (ver abajo)
paredes = "madera"    # madera | azulejo | piedra | "#RRGGBB"
suelo = "madera"      # madera | baldosa | tierra

[[mueble]]
pieza = "escritorio"  # una pieza del catálogo (ver abajo)
sitio = "izquierda"   # un hueco fijo, o un número del 0 (borde izquierdo) al 100 (borde derecho)
aparece = 0           # opcional: día del hormiguero en que aparece (sale en el diario)
```

Si algo está mal escrito (una función, unas paredes o un suelo que no existen), sale un
aviso en la franja amarilla de la pantalla y se usa el valor por defecto (`otra`, `madera`).

## Funciones

| funcion | Qué pasa |
|---|---|
| `trabajo` | Sala de trabajo, con adornos de más en algunas fiestas. No cambia lo que hacen las hormigas: como en cualquier sala, su gente pasa aquí la mayor parte del tiempo. |
| `reuniones` | Sala de reuniones, con los mismos adornos que `trabajo` (las reuniones se ponen con `[[reunion]]` en el fichero de la sala). |
| `despacho` | Despacho, con los mismos adornos que `trabajo` (las llamadas al despacho las hace `jefe = true` en el fichero de la sala, sea del tipo que sea). |
| `comedor` | Van a desayunar y a comer (ver `[horario]` en `config.toml`) y se refugian aquí. |
| `agua` | Van a beber de vez en cuando. |
| `despensa` | Aquí guardan la comida que traen de fuera (si no hay despensa, la llevan al comedor o, si tampoco hay, a la primera sala). |
| `museo` | Igual que `otra`. Los hallazgos no los enseña la función, sino la pieza `vitrina`, en la sala que esté (el tipo `museo` trae dos). |
| `otra` | Sólo decorativa: la visitan de vez en cuando. |

## Huecos

En el suelo: `izquierda`, `centro_izquierda`, `centro`, `centro_derecha`, `derecha`.
En la pared: `pared_izquierda`, `pared`, `pared_derecha`.
Cada pieza ya sabe si va en el suelo o en la pared; si no pones `sitio`, usa el suyo.
Si el hueco no existe, sale un aviso y la pieza va a su sitio de siempre; con un número
de fuera del 0 al 100, también sale un aviso y se queda en el borde. Si una pieza no
existe, o no cabe en la sala (en las más estrechas), no se pinta y sale un aviso.

## Piezas

![Todos los muebles](../docs/galeria-muebles.png)
![Los tipos que vienen hechos](../docs/galeria-tipos.png)

Las imágenes se generan con `python3 herramientas/galeria.py`.

| Pieza | Dónde | |
|---|---|---|
| `escritorio` | suelo | Mesa con ordenador y silla (la pantalla parpadea). |
| `escritorio_grande` | suelo | Escritorio de despacho. |
| `sillon` | suelo | |
| `sofa` | suelo | |
| `planta` | suelo | Crece con los días. |
| `mesa_reuniones` | suelo | Ocupa casi toda la sala. |
| `mesa_comedor` | suelo | Mesa larga con platos. |
| `nevera` | suelo | |
| `encimera` | suelo | Microondas y cafetera (que echa vapor). |
| `fuente` | suelo | Fuente de agua (con burbujas). |
| `estanteria` | suelo | Con libros. |
| `vitrina` | suelo | Enseña los hallazgos de la colonia. |
| `sacos` | suelo | |
| `cajas` | suelo | |
| `setas` | suelo | Una fila de setas. |
| `cuadro` | pared | |
| `pantalla` | pared | Pantalla con gráficas. |
| `pizarra` | pared | |
| `reloj` | pared | Marca la hora del hormiguero (la de verdad o, si la simulas con `--fecha`, `--hora`, `--dias`, `--acelerar` o la demo, la simulada). |

Los tipos se leen al arrancar: si cambias uno, reinicia el hormiguero.
