#!/usr/bin/env python3
"""Ant Farm Idle, versión gráfica (pixel art).  python3 hormiguero_pixel.py
Teclas: q/Esc salir · f pantalla completa · i rendimiento."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pixel.app import main  # noqa: E402

if __name__ == "__main__":
    main()
