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

## Funciones

| funcion | Qué pasa |
|---|---|
| `trabajo` | Sala de trabajo: las hormigas de la sala pasan aquí la mayor parte del tiempo. |
| `reuniones` | Sala de reuniones (las reuniones se ponen en el fichero de la sala). |
| `despacho` | Despacho. Si la sala tiene `jefe = true`, llama a gente de vez en cuando. |
| `comedor` | Van a desayunar y a comer (ver `[horario]` en `config.toml`) y se refugian aquí. |
| `agua` | Van a beber de vez en cuando. |
| `despensa` | Aquí guardan la comida que traen de fuera (si no hay, la llevan al comedor). |
| `museo` | Expone los objetos que encuentran al excavar. |
| `otra` | Sólo decorativa: la visitan de vez en cuando. |

## Huecos

En el suelo: `izquierda`, `centro_izquierda`, `centro`, `centro_derecha`, `derecha`.
En la pared: `pared_izquierda`, `pared`, `pared_derecha`.
Cada pieza ya sabe si va en el suelo o en la pared; si no pones `sitio`, usa el suyo.

## Piezas

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
| `reloj` | pared | Marca la hora de verdad. |

Los tipos se leen al arrancar: si cambias uno, reinicia el hormiguero.
