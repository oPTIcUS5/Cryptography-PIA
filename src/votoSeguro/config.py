"""
Constantes ficticas no reales
"""

from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[2]
DATA = Path(os.environ.get("VOTOSEGURO_DATA", str(ROOT / "data"))).resolve()

# Data base (en sqlite)
DB_PATH = DATA / "election.sqlite3"

ELECTION_ID = "MUNICIPAL-DEMO-2026"
ELECTION_NAME = "Eleccion municipal de demostracion"

# diccionario - candidatod
CANDIDATES = { 
    "A": "Candidatura A",
    "B": "Candidatura B",
    "C": "Candidatura C"
}

GENESIS_HASH = "0" * 64
MAX_B64_FIELD = 8192
