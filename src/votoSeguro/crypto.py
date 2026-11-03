"""
Criptografia con librrias
"""

import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .config import DATA, ELECTION_ID

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def b64(data):
    """
    De un texto plano a base64
    """
    return base64.b64encode(data).decode("ascii")

def unb64(text, limit=8192):
    """
    de base 64 a str comun
    """

    if not isinstance(text, str) or len(text) > limit:
        raise ValueError("Campo base64 invalido")
    try:
        return base64.b64decode(text, validate=True)
    except Exception as e:
        raise ValueError("Campo Baase64 invalido") from e

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def secure_write(path: Path, content: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("xb") as f:
        f.write(content)

    path.chmod(0o600)

def generate_keys():
    """
    Claves privadas solo para escrutinioo LOCAL
    y lafirma de resultados
    """

    DATA.mkdir(parents=True, exist_ok=True)
    keys = [DATA / n for n in (
        "encryption_private.pem", "encryption_public.pem",
        "signing_private.pem", "signing_public.pem"
    )]

    if any(p.exists() for p in keys):
        raise FileExistsError("Ya exiten claves: no se deben generar para la misma eleccion")
    
    encryption = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    signing = ed25519.Ed25519PrivateKey.generate()
    serialization_best = serialization.BestAvailableEncryption

    values = [
        encryption.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                 serialization.NoEncryption()),
        encryption.public_key().public_bytes(serialization.Encoding.PEM,
                                             serialization.PublicFormat.SubjectPublicKeyInfo),
        signing.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()),
        signing.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo),
    ]

    for p, content in zip(keys, values):
        secure_write(p, content)

def public_encryption_spki_base64():

    public = serialization.load_pem_public_key((DATA / "encryption_public.pem").read_bytes())

    return b64(public.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo))


def validate_ballot_envelope(envelope):

    if not isinstance(envelope, dict) or set(envelope) != {"wrapped_key", "nonce", "ciphertext"}:
        raise ValueError("sobre del voto incompleto")

    wrapped = unb64(envelope["wrapped_key"])
    nonce = unb64(envelope["nonce"])
    ciphertext = unb64(envelope["ciphertext"])

    if len(wrapped) != 384 or len(nonce) != 12 or not 17 <= len(ciphertext) <= 4096:
        raise ValueError("Tamanios criptgoraficos incorrectos")
    
    return {key: envelope[key] for key in ("wrapped_key", "nonce", "ciphertext")}


def encrypt_ballot_for_test(candidate_id):

    key = AESGCM.generate_key(bit_length=256)

    nonce = __import__("secrets").token_bytes(12)
    plaintext = canonical({"election_id": ELECTION_ID, "candidate_id": candidate_id})
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, ELECTION_ID.encode())

    public = serialization.load_pem_public_key((DATA / "encryption_public.pem").read_bytes())
    wrapped = public.encrypt(key, padding.OAEP(mgf=padding.MGF1(hashes.SHA256()),
                                               algorithm=hashes.SHA256(), label=None))
    
    return {"wrapped_key": b64(wrapped), "nonce": b64(nonce), "ciphertext": b64(ciphertext)}


def envelope_receipt(envelope):
    return sha256(canonical({"election_id": ELECTION_ID, **envelope}))

def decrypt_ballot(envelope):
    private = serialization.load_pem_private_key((DATA / "encryption_private.pem").read_bytes(), password=None)
    aes_key = private.decrypt(unb64(envelope["wrapped_key"]),
                              padding.OAEP(mgf=padding.MGF1(hashes.SHA256()),
                                           algorithm=hashes.SHA256(), label=None))
    
    plaintext = AESGCM(aes_key).decrypt(unb64(envelope["nonce"]),
                                        unb64(envelope["ciphertext"]), ELECTION_ID.encode())
    
    message = json.loads(plaintext)

    if not isinstance(message, dict) or set(message) != {"election_id", "candidate_id"}:
        raise ValueError("Formato interno incorrecto")
    
    if message["election_id"] != ELECTION_ID:
        raise ValueError("Elección incorrecta")
    
    return message["candidate_id"]


def sign_manifest(manifest):

    signer = serialization.load_pem_private_key((DATA / "signing_private.pem").read_bytes(), password=None)

    return b64(signer.sign(canonical(manifest)))


def verify_manifest(manifest, signature):

    public = serialization.load_pem_public_key((DATA / "signing_public.pem").read_bytes())
    public.verify(unb64(signature), canonical(manifest))
    
    return True
