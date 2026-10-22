# Desarrollo

**Pruebas.** Están en `tests/` y no necesitan pantalla ni tocan tu `local/` (todo se hace
en carpetas temporales). Desde la carpeta del repositorio:

```bash
SDL_VIDEODRIVER=dummy python3 -m unittest discover -s tests -v
```

Tardan alrededor de un minuto. GitHub las pasa solas en cada cambio, con Python 3.11 y
3.13 (`.github/workflows/tests.yml`).

**Galerías.** Las imágenes de muebles, tipos de sala y paisaje de `docs/` se regeneran con
`python3 herramientas/galeria.py` (por ejemplo, después de añadir una pieza nueva). Usa
siempre los ficheros de ejemplo del repositorio (no los de `local/`) y no escribe en `local/`.

**Capturas del README.** `docs/dia.png` y `docs/noche.png` se hacen con los ficheros de
ejemplo y una copia de `config.toml` con la fundación y la semilla puestas (`--captura` no
escribe en `local/`):

```bash
sed -e 's/^# fundacion = /fundacion = /' -e 's/^# semilla = /semilla = /' config.toml > /tmp/capturas.toml
python3 hormiguero_pixel.py -c /tmp/capturas.toml --salas salas --tipos tipos --idos idos.toml \
    --calendario calendario.toml --segundos 30 --fecha 2026-10-27 --hora 11:00 --captura docs/dia.png
python3 hormiguero_pixel.py -c /tmp/capturas.toml --salas salas --tipos tipos --idos idos.toml \
    --calendario calendario.toml --segundos 30 --fecha 2026-12-24 --hora 22:00 --captura docs/noche.png
```

Las nubes, los pájaros y lo que hacen las hormigas cambian un poco de una vez a otra: si
algo queda feo (una nube encima de la fecha, un nombre encima de otro), repítelo.
