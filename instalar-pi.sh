#!/bin/bash
# Deja la Raspberry (Raspberry Pi OS Lite, sin escritorio) mostrando el hormiguero pixel:
#  - instala pygame y la fuente DejaVu (sin ella los textos se ven mal)
#  - crea el servicio "hormiguero", que pinta en la pantalla de la Pi (tty1),
#    arranca al encender y se relanza solo si se cierra
#  - la pantalla no se apaga nunca
# Uso (en la Pi):  bash ~/hormiguero/instalar-pi.sh
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

echo "== Quitando el arranque anterior (inicio de sesión automático), si estaba"
sed -i '/# hormiguero-autoarranque/,/^fi$/d' ~/.bash_profile 2>/dev/null || true
rm -f "$DIR/arrancar-pi.sh"
sudo raspi-config nonint do_boot_behaviour B1   # consola pidiendo usuario (sin autologin)

echo "== Servicio hormiguero"
sudo tee /etc/systemd/system/hormiguero.service >/dev/null <<EOF
[Unit]
Description=Ant Farm Idle en la pantalla
After=systemd-user-sessions.service plymouth-quit-wait.service
Conflicts=getty@tty1.service

[Service]
User=$USUARIO
WorkingDirectory=$DIR
Environment=PYTHONUNBUFFERED=1 HORMIGUERO_FB_INFO=1
# Pinta en el framebuffer (/dev/fb0): con kmsdrm/EGL la pantalla de la Pi 3 se queda en negro
ExecStart=/usr/bin/python3 $DIR/hormiguero_fb.py
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
