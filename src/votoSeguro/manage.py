"""CLI administrativo local. No exponemos estos controles como rutas web."""
import argparse
import json
from pathlib import Path
from .config import DATA, DB_PATH
from .crypto import generate_keys
from .storage import create_database, close_election, audit_chain
from .services import demo_voters, tally_election, verify_published_record


def main():
    parser = argparse.ArgumentParser(description="Administración LOCAL de la elección ficticia")
    parser.add_argument("action", choices=["init", "close", "tally", "verify"])
    args = parser.parse_args()
    try:
        if args.action == "init":
            if DB_PATH.exists():
                raise ValueError("Ya existe la base de datos. No se sobrescriben elecciones")
            generate_keys()
            create_database()
            creds = demo_voters(5)
            credentials_file = DATA / "demo_credentials.txt"
            credentials_file.write_text("USUARIOS FICTICIOS. NO PUBLICAR.\n" +
                                        "\n".join(f"{u} : {p}" for u, p in creds) + "\n",
                                        encoding="utf-8")
            credentials_file.chmod(0o600)
            print(f"Elección creada. Credenciales locales: {credentials_file}")
        elif args.action == "close":
            if not audit_chain():
                raise ValueError("La cadena está alterada")
            close_election()
            print("Elección cerrada: ya no se reciben votos")
        elif args.action == "tally":
            record = tally_election()
            print(json.dumps(record["manifest"], indent=2, ensure_ascii=False))
            print("Resultados y auditoría publicados en data/")
        elif args.action == "verify":
            record = json.loads((DATA / "results.json").read_text(encoding="utf-8"))
            audit = json.loads((DATA / "audit.json").read_text(encoding="utf-8"))
            valid = verify_published_record(record, audit)
            print("Firma y cadena válidas" if valid else "ERROR: registro público no válido")
            if not valid:
                raise SystemExit(1)
    except (ValueError, FileExistsError, FileNotFoundError) as exc:
        parser.exit(1, f"Error: {exc}\n")

if __name__ == "__main__":
    main()
