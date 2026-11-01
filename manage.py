"""
Comandos del administrador de prueba (acceso por terminal local).
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from votoSeguro.manage import main

if __name__ == "__main__":
    main()
