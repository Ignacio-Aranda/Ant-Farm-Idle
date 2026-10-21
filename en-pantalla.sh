#!/bin/bash
# Ejecuta cualquier programa en la pantalla de la Pi (tty1) desde SSH, igual que el servicio.
# Para el hormiguero mientras tanto y lo vuelve a lanzar al terminar.
# Ejemplos:  ./en-pantalla.sh python3 prueba-pantalla.py
#            ./en-pantalla.sh python3 hormiguero_pixel.py --demo
DIR="$(cd "$(dirname "$0")" && pwd)"
LOG=/tmp/en-pantalla.log
[ $# -gt 0 ] || { echo "Uso: $0 programa [argumentos]"; exit 1; }
sudo systemctl stop hormiguero
echo "En la pantalla: $*   (Ctrl+C aquí para cortarlo)"
sudo systemd-run --wait --collect --quiet --unit=en-pantalla \
    -p User="$(id -un)" -p WorkingDirectory="$DIR" -p PAMName=login \
    -p TTYPath=/dev/tty1 -p TTYReset=yes -p TTYVHangup=yes -p StandardInput=tty \
    -p StandardOutput=truncate:$LOG -p StandardError=append:$LOG \
    -E SDL_VIDEODRIVER=kmsdrm -E PYTHONUNBUFFERED=1 \
    "$@"
cat $LOG
sudo systemctl start hormiguero
