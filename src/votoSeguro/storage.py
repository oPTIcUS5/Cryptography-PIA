"""
Voto en transaccion atomico
"""

import sqlite3
from datetime import datetime, timezone

from .config import DB_PATH, GENESIS_HASH
from .config import sha256, envelope_receipt, canonical

def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connection():

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row

    db.execute("PRAGMA busy_timeout=10000")
    db.execute("PRAGMA foreign_keys=ON")

    return db


def create_database():

    with connection() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS voters (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            has_voted INTEGER NOT NULL DEFAULT 0 CHECK(has_voted IN (0,1))
        );

        CREATE TABLE IF NOT EXISTS ballots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            receipt TEXT NOT NULL UNIQUE,
            wrapped_key TEXT NOT NULL,
            nonce TEXT NOT NULL,
            ciphertext TEXT NOT NULL,
            prev_hash TEXT NOT NULL,
            chain_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS settings (
            name TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        
        INSERT OR IGNORE INTO settings(name,value) VALUES('election_status','open');
    """)
