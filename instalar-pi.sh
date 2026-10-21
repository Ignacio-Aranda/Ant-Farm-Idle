#!/bin/bash
# Deja la Raspberry (Raspberry Pi OS Lite, sin escritorio) mostrando el hormiguero pixel:
#  - instala pygame y la fuente DejaVu (sin ella los textos se ven mal)
#  - crea el servicio "hormiguero", que pinta en la pantalla de la Pi (tty1),
#    arranca al encender y se relanza solo si se cierra
#  - la pantalla no se apaga nunca
# Uso (en la Pi):  bash ~/Ant-Farm-Idle/instalar-pi.sh
# Luego, desde SSH:
#   sudo systemctl restart hormiguero     (re)lanzarlo en la pantalla
#   sudo systemctl stop hormiguero        pararlo
#   journalctl -u hormiguero -f           ver lo que imprime y los errores
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
USUARIO="$(id -un)"

echo "== Instalando pygame y la fuente DejaVu"
sudo apt-get update
sudo apt-get install -y python3-pygame fonts-dejavu-core
chmod +x "$DIR"/*.sh "$DIR"/*.py

echo "== Servicio hormiguero"
# La ruta del repositorio, escrita para la unidad: systemd toma "%" por un especificador
# (va "%%") y ExecStart lo parte por los espacios (va entre comillas, con \ " y $ escapados)
RUTA="${DIR//%/%%}"
PROGRAMA="$RUTA/hormiguero_fb.py"
PROGRAMA="${PROGRAMA//\\/\\\\}"
PROGRAMA="${PROGRAMA//\"/\\\"}"
PROGRAMA="${PROGRAMA//\$/\$\$}"
sudo tee /etc/systemd/system/hormiguero.service >/dev/null <<EOF
[Unit]
Description=Ant Farm Idle en la pantalla
After=systemd-user-sessions.service plymouth-quit-wait.service
Conflicts=getty@tty1.service

[Service]
User=$USUARIO
WorkingDirectory=$RUTA
Environment=PYTHONUNBUFFERED=1 HORMIGUERO_FB_INFO=1
# variables propias (p. ej. OPENWEATHER_API_KEY=...), si existe el fichero
EnvironmentFile=-$RUTA/local/entorno
# Pinta en el framebuffer (/dev/fb0): con kmsdrm/EGL la pantalla de la Pi 3 se queda en negro
ExecStart=/usr/bin/python3 "$PROGRAMA"
Restart=always
RestartSec=5
TTYPath=/dev/tty1
TTYReset=yes
TTYVHangup=yes
StandardInput=tty
StandardOutput=journal
StandardError=journal
PAMName=login

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable hormiguero

echo "== Pantalla siempre encendida"
CMDLINE=/boot/firmware/cmdline.txt
[ -f "$CMDLINE" ] || CMDLINE=/boot/cmdline.txt
if ! grep -q "consoleblank=0" "$CMDLINE"; then
    sudo sed -i '1 s/$/ consoleblank=0/' "$CMDLINE"
fi

echo "== Lanzándolo"
sudo systemctl restart hormiguero
sleep 5
systemctl --no-pager status hormiguero | head -12
echo
echo "Listo. Desde SSH:  sudo systemctl restart|stop hormiguero   ·   journalctl -u hormiguero -f"
