import copy
import json
import sqlite3
import pytest
from cryptography.exceptions import InvalidTag
from votoSeguro.config import ELECTION_ID, GENESIS_HASH


def test_login_correct_and_wrong(election):
    username, password = election["creds"][0]
    assert election["services"].authenticate(username, password)
    assert not election["services"].authenticate(username, "no-es-la-contrasena")
    assert not election["services"].authenticate("nadie", password)


def test_password_is_not_stored_as_plaintext(election):
    user, pwd = election["creds"][0]
    entry = election["storage"].get_voter(user)
    assert pwd not in entry["password_hash"]
    assert entry["password_hash"].startswith("$argon2id$")


def test_encryption_decryption_roundtrip(election):
    c = election["crypto"]
    assert c.decrypt_ballot(c.encrypt_ballot_for_test("B")) == "B"


def test_ciphertext_modified_fails(election):
    c = election["crypto"]

    sealed = c.encrypt_ballot_for_test("A")

    blob = bytearray(c.unb64(sealed["ciphertext"]))
    blob[-1] ^= 1
    sealed["ciphertext"] = c.b64(blob)

    with pytest.raises(InvalidTag):
        c.decrypt_ballot(sealed)


def test_nonce_modified_fails(election):
    c = election["crypto"]
    sealed = c.encrypt_ballot_for_test("A")
    b = bytearray(c.unb64(sealed["nonce"]))
    b[0] ^= 1
    sealed["nonce"] = c.b64(b)

    with pytest.raises(InvalidTag):
        c.decrypt_ballot(sealed)


def test_invalid_envelope_rejected(election):
    c = election["crypto"]

    for value in [{}, {"wrapped_key":"x", "nonce":"no", "ciphertext":"bad"}, [1,2,3]]:
        with pytest.raises(ValueError):
            c.validate_ballot_envelope(value)


def test_vote_only_once(election):
    c, db = election["crypto"], election["storage"]
    user = election["creds"][0][0]
    receipt = db.record_vote(user, c.encrypt_ballot_for_test("A"))
    assert len(receipt) == 64 and db.count_ballots() == 1

    with pytest.raises(ValueError, match="voto ya emitido"):
        db.record_vote(user, c.encrypt_ballot_for_test("B"))

    assert db.count_ballots() == 1


def test_unregistered_user_rejected(election):
    with pytest.raises(ValueError):
        election["storage"].record_vote("usuario_falso", election["crypto"].encrypt_ballot_for_test("A"))


def test_chain_for_two_votes(election):

    db = election["storage"]

    for i, choice in enumerate(["A", "C"]):
        db.record_vote(election["creds"][i][0], election["crypto"].encrypt_ballot_for_test(choice))

    assert db.audit_chain()
    assert db.count_ballots() == 2


def test_chain_detects_database_tampering(election):
    db = election["storage"]
    db.record_vote(election["creds"][0][0], election["crypto"].encrypt_ballot_for_test("C"))

    with db.connection() as conn:
        conn.execute("UPDATE ballots SET ciphertext='AAAA' WHERE id=1")

    assert not db.audit_chain()


def test_close_prevents_votes(election):
    db = election["storage"]
    db.close_election()
    assert db.get_status() == "closed"
    with pytest.raises(ValueError, match="cerrada"):
        db.record_vote(election["creds"][0][0], election["crypto"].encrypt_ballot_for_test("A"))


def test_tally_and_signed_manifest(election):
    c, db, s = election["crypto"], election["storage"], election["services"]
    for i, choice in enumerate(["A", "B", "A"]):
        db.record_vote(election["creds"][i][0], c.encrypt_ballot_for_test(choice))
    db.close_election()
    result = s.tally_election()
    assert result["manifest"]["counts"] == {"A":2,"B":1,"C":0}
    assert result["manifest"]["ballots_received"] == 3
    assert s.verify_published_record(result, s.public_audit())


def test_signature_tamper_detected(election):
    c, db, s = election["crypto"], election["storage"], election["services"]
    db.record_vote(election["creds"][0][0], c.encrypt_ballot_for_test("A"))
    db.close_election()
    result = s.tally_election()
    fake = copy.deepcopy(result)
    fake["manifest"]["counts"]["A"] = 50
    with pytest.raises(Exception):
        s.verify_published_record(fake, s.public_audit())


def test_published_chain_tamper_detected(election):
    c, db, s = election["crypto"], election["storage"], election["services"]
    db.record_vote(election["creds"][0][0], c.encrypt_ballot_for_test("A"))
    db.close_election()
    result = s.tally_election()
    audit = s.public_audit()
    audit[0]["chain_hash"] = "f"*64
    assert not s.verify_published_record(result, audit)


def test_no_identity_saved_in_ballot(election):
    c, db = election["crypto"], election["storage"]
    username = election["creds"][0][0]
    db.record_vote(username, c.encrypt_ballot_for_test("C"))
    ballot = db.all_ballots()[0]
    assert "username" not in ballot and "candidate_id" not in ballot
    assert username not in json.dumps(ballot)


def test_tally_before_close_rejected(election):
    with pytest.raises(ValueError, match="cerrarse"):
        election["services"].tally_election()


def test_invalid_choice_is_invalid_ballot(election):
    c, db, s = election["crypto"], election["storage"], election["services"]
    db.record_vote(election["creds"][0][0], c.encrypt_ballot_for_test("D"))
    db.close_election()
    result = s.tally_election()
    assert result["manifest"]["invalid_ballots"] == 1
    assert result["manifest"]["valid_ballots"] == 0


def test_javascript_webcrypto_interoperability(election):
    import shutil
    import subprocess
    from pathlib import Path
    if not shutil.which("node"):
        pytest.skip("Node.js no está instalado")
    script = Path(__file__).resolve().parents[1] / "scripts" / "test_browser_crypto.mjs"
    pem = election["dir"] / "encryption_public.pem"
    text = subprocess.check_output(["node", str(script), str(pem), "C"], text=True)
    envelope = json.loads(text)
    assert election["crypto"].decrypt_ballot(envelope) == "C"


def test_two_parallel_attempts_allow_exactly_one_vote(election):
    
    import threading
    from concurrent.futures import ThreadPoolExecutor

    c, db = election["crypto"], election["storage"]
    username = election["creds"][0][0]
    env_a, env_b = c.encrypt_ballot_for_test("A"), c.encrypt_ballot_for_test("B")

    def submit(envelope):
        try:
            return bool(db.record_vote(username, envelope))
        except ValueError:
            return False
        
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(submit, [env_a, env_b]))

    assert sorted(results) == [False, True]
    assert db.count_ballots() == 1


def test_corrupted_ballot_is_counted_invalid_on_tally(election):

    c, db, s = election["crypto"], election["storage"], election["services"]

    bad = c.encrypt_ballot_for_test("A")

    raw = bytearray(c.unb64(bad["ciphertext"]))
    raw[-1] ^= 1

    bad["ciphertext"] = c.b64(raw)

    db.record_vote(election["creds"][0][0], bad)
    db.close_election()

    result = s.tally_election()

    assert result["manifest"]["invalid_ballots"] == 1
