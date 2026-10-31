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
    Claves privadas unicamente para escrutinioo LOCAL
    y firma de resultados
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
        encryption.private_bytes(serialization.Encoding.PEM, serialization.ParameterFormat.PKCS3,
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
