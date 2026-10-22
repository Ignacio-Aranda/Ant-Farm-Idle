#!/bin/bash
# Ejecuta cualquier programa en la pantalla de la Pi (tty1) desde SSH, igual que el servicio
# (también con las variables de local/entorno, como la clave de OpenWeather).
# Para el hormiguero mientras tanto y lo vuelve a lanzar al terminar (también con Ctrl+C).
# Ejemplos:  ./en-pantalla.sh python3 hormiguero_fb.py --demo
#            ./en-pantalla.sh python3 hormiguero_fb.py --fecha 2026-12-24 --hora 21:00
DIR="$(cd "$(dirname "$0")" && pwd)"
LOG=/tmp/en-pantalla.log
[ $# -gt 0 ] || { echo "Uso: $0 programa [argumentos]"; exit 1; }

# Al salir, sea como sea (acaba el programa, Ctrl+C o se corta el SSH): quitar el programa
# de la pantalla (systemd-run no lo para al cortarlo), enseñar lo que ha escrito y volver a
# lanzar el hormiguero
fin() {
    trap '' INT TERM HUP
    sudo systemctl stop en-pantalla 2>/dev/null
    sudo systemctl reset-failed en-pantalla 2>/dev/null
    cat "$LOG" 2>/dev/null
    sudo systemctl start hormiguero
}
trap fin EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP

sudo systemctl stop hormiguero
# si quedó otro en la pantalla de antes, fuera (si no, systemd-run no puede lanzar este)
sudo systemctl stop en-pantalla 2>/dev/null
sudo systemctl reset-failed en-pantalla 2>/dev/null
echo "En la pantalla: $*   (Ctrl+C aquí para cortarlo)"
sudo systemd-run --wait --collect --quiet --unit=en-pantalla \
    -p User="$(id -un)" -p WorkingDirectory="$DIR" -p PAMName=login \
    -p TTYPath=/dev/tty1 -p TTYReset=yes -p TTYVHangup=yes -p StandardInput=tty \
    -p StandardOutput=truncate:"$LOG" -p StandardError=append:"$LOG" \
    -p EnvironmentFile=-"$DIR/local/entorno" \
    -E PYTHONUNBUFFERED=1 \
    "$@"
