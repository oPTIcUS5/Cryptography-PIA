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


def get_status(db=None):
    if db is None:
        with connection() as conn:
            return get_status(conn)
    return db.execute("SELECT value FROM settings WHERE name='election_status'").fetchone()[0]


def get_voter(username):
    with connection() as db:
        return db.execute("SELECT * FROM voters WHERE username=?", (username,)).fetchone()


def count_ballots():
    with connection() as db:
        return db.execute("SELECT count(*) FROM ballots").fetchone()[0]


def record_vote(username, envelope):
    """Condición de carrera resuelta con BEGIN IMMEDIATE + actualización condicional."""
    receipt = envelope_receipt(envelope)
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        if get_status(db) != "open":
            raise ValueError("La elección está cerrada")
        cur = db.execute("UPDATE voters SET has_voted=1 WHERE username=? AND has_voted=0", (username,))
        if cur.rowcount != 1:
            raise ValueError("Cuenta no autorizada o voto ya emitido")
        last = db.execute("SELECT chain_hash FROM ballots ORDER BY id DESC LIMIT 1").fetchone()
        prev = last[0] if last else GENESIS_HASH
        pos = db.execute("SELECT COALESCE(MAX(id),0)+1 FROM ballots").fetchone()[0]
        chain = sha256(f"{prev}:{pos}:{receipt}".encode())
        db.execute("""INSERT INTO ballots(receipt,wrapped_key,nonce,ciphertext,prev_hash,chain_hash,created_at)
           VALUES(?,?,?,?,?,?,?)""", (receipt, envelope["wrapped_key"], envelope["nonce"],
                envelope["ciphertext"], prev, chain, timestamp()))
    return receipt


def get_ballot(receipt):
    with connection() as db:
        row = db.execute("SELECT receipt,chain_hash,created_at FROM ballots WHERE receipt=?", (receipt,)).fetchone()
        return dict(row) if row else None


def all_ballots():
    with connection() as db:
        return [dict(r) for r in db.execute("SELECT * FROM ballots ORDER BY id")]


def audit_chain(rows=None):
    rows = all_ballots() if rows is None else rows
    previous = GENESIS_HASH
    for index, item in enumerate(rows, 1):
        envelope = {k: item[k] for k in ("wrapped_key", "nonce", "ciphertext")}
        if item["id"] != index or envelope_receipt(envelope) != item["receipt"]:
            return False
        actual = sha256(f"{previous}:{index}:{item['receipt']}".encode())
        if item["prev_hash"] != previous or item["chain_hash"] != actual:
            return False
        previous = actual
    return True


def close_election():
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        if get_status(db) != "open":
            raise ValueError("La elección ya está cerrada")
        db.execute("UPDATE settings SET value='closed' WHERE name='election_status'")

