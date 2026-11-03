"""
Lógica de autenticación, escrutinio y publicación de resultados.
"""

import json
import secrets
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError, VerificationError
from .config import DATA, CANDIDATES, ELECTION_ID, GENESIS_HASH
from .crypto import decrypt_ballot, sign_manifest, verify_manifest
from .storage import (connection, create_database, get_voter, all_ballots,
                      audit_chain, get_status, timestamp)

HASHER = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)


def demo_voters(number=5):
    """
    Genera usuarios totalmente ficticios
    lit puro demo
    """
    # killed
    if not 1 <= number <= 20:
        raise ValueError("Numero de usuarios de prueba invalido")
    
    create_database()
    results = []
    
    with connection() as db:
        if db.execute("SELECT COUNT(*) FROM voters").fetchone()[0]:
            raise ValueError("El padron de demostracion ya fue generado")
        
        for number_id in range(1, number + 1):
            user = f"demo{number_id:02}"
            password = secrets.token_urlsafe(14)
            db.execute("INSERT INTO voters(username,password_hash) VALUES(?,?)",
                       (user, HASHER.hash(password)))
            
            results.append((user, password))

    return results


def authenticate(username, password):
    if not isinstance(username, str) or not isinstance(password, str):
        return False
    user = get_voter(username)
    if not user:
        return False
    try:
        return bool(HASHER.verify(user["password_hash"], password))
    except (VerifyMismatchError, InvalidHashError, VerificationError):
        return False


def public_audit():
    """Sólo huellas cifradas y eslabones de la cadena, sin selección ni identidad."""
    return [{"position": r["id"], "receipt": r["receipt"],
             "prev_hash": r["prev_hash"], "chain_hash": r["chain_hash"]}
            for r in all_ballots()]


def tally_election():
    if get_status() != "closed":
        raise ValueError("Primero debe cerrarse la elección")
    if not audit_chain():
        raise ValueError("Cadena de integridad alterada; escrutinio detenido")
    ballots = all_ballots()
    counts = {candidate: 0 for candidate in CANDIDATES}
    invalid = 0
    for row in ballots:
        try:
            choice = decrypt_ballot(row)
            if choice not in CANDIDATES:
                raise ValueError("Candidato no registrado")
            counts[choice] += 1
        except (ValueError, KeyError, TypeError, json.JSONDecodeError,
                __import__("cryptography").exceptions.InvalidTag):
            invalid += 1
    manifest = {
        "election_id": ELECTION_ID,
        "status": "closed",
        "timestamp_utc": timestamp(),
        "counts": counts,
        "ballots_received": len(ballots),
        "valid_ballots": sum(counts.values()),
        "invalid_ballots": invalid,
        "final_chain_hash": ballots[-1]["chain_hash"] if ballots else GENESIS_HASH,
    }
    signature = sign_manifest(manifest)
    record = {"manifest": manifest, "signature_base64": signature}
    (DATA / "results.json").write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    (DATA / "audit.json").write_text(json.dumps(public_audit(), indent=2), encoding="utf-8")
    return record


def verify_published_record(record, audit_list):
    """Verifica firma + cadena publicada, pero NO demuestra escrutinio correcto."""
    verify_manifest(record["manifest"], record["signature_base64"])
    previous = GENESIS_HASH
    for pos, row in enumerate(audit_list, 1):
        from .crypto import sha256
        expected = sha256(f"{previous}:{pos}:{row['receipt']}".encode())
        if (row.get("position") != pos or row.get("prev_hash") != previous or
                row.get("chain_hash") != expected):
            return False
        previous = expected
    m = record["manifest"]
    return (m["final_chain_hash"] == previous and m["ballots_received"] == len(audit_list)
            and m["valid_ballots"] + m["invalid_ballots"] == len(audit_list))
