import pytest
from votoSeguro import crypto, services, storage
from votoSeguro.config import CANDIDATES

@pytest.fixture
def election(tmp_path, monkeypatch):

    monkeypatch.setattr(crypto, "DATA", tmp_path)

    monkeypatch.setattr(services, "DATA", tmp_path)

    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test.sqlite3")

    crypto.generate_keys()
    storage.create_database()

    creds = services.demo_voters(3)
    
    return {"creds": creds, "dir": tmp_path, "crypto": crypto, "storage": storage,
            "services": services}
