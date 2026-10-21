#!/usr/bin/env python3
"""Ant Farm Idle: ejecuta  python3 hormiguero.py   (q para salir)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hormiga.app import main  # noqa: E402

if __name__ == "__main__":
    main()
