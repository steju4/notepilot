"""Create a Basic Auth secret interactively; never put passwords in CLI arguments."""

import argparse
import getpass
import json
import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.access import make_password_hash, valid_username  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="NotePilot Basic-Auth-Secret erstellen")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replace", action="store_true", help="Vorhandenes Secret atomar ersetzen")
    args = parser.parse_args()
    destination = args.output.resolve()
    if destination.exists() and not args.replace:
        raise SystemExit("Secret existiert bereits. Zum Passwortwechsel --replace verwenden.")
    username = input("Benutzername: ")
    if not valid_username(username):
        raise SystemExit("Benutzername: 1–128 UTF-8-Bytes, keine Steuerzeichen oder Doppelpunkte.")
    password = getpass.getpass("Passwort (mindestens 12 Zeichen): ")
    confirm = getpass.getpass("Passwort wiederholen: ")
    if password != confirm:
        raise SystemExit("Passwörter stimmen nicht überein.")
    try:
        hashed = make_password_hash(password)
    except ValueError as error:
        raise SystemExit(str(error)) from None
    temporary = destination.parent / (".basic-auth-" + uuid.uuid4().hex + ".tmp")
    try:
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            json.dump({"username": username, "password_hash": hashed}, file)
            file.write("\n")
        if args.replace:
            temporary.replace(destination)
        else:
            os.link(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    print("Secret gespeichert. Bei Passwortwechsel den NotePilot-Container neu erstellen.")


if __name__ == "__main__":
    main()
