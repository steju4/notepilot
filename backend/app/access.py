"""Optional HTTP Basic Auth for a private hosted instance; no application accounts."""

import base64
import binascii
import hashlib
import hmac
import json
import os
import threading
from dataclasses import dataclass, field
from pathlib import Path

CHALLENGE = 'Basic realm="NotePilot", charset="UTF-8"'
# Fixed, bounded scrypt parameters: 32 MiB per verification, three passes.
SCRYPT_N, SCRYPT_R, SCRYPT_P = 32768, 8, 3
MAX_PASSWORD_BYTES = 1024


def valid_username(username):
    return (
        isinstance(username, str)
        and 1 <= len(username.encode("utf-8")) <= 128
        and all(ord(char) >= 32 and ord(char) != 127 and char != ":" for char in username)
    )


def password_digest(password: bytes, salt: bytes):
    return hashlib.scrypt(
        password, salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, dklen=32, maxmem=64 * 1024 * 1024
    )


def make_password_hash(password: str):
    encoded = password.encode("utf-8")
    if not 12 <= len(password) or len(encoded) > MAX_PASSWORD_BYTES:
        raise ValueError("Passwort: mindestens 12 Zeichen, maximal 1024 UTF-8-Bytes.")
    salt = os.urandom(16)
    digest = password_digest(encoded, salt)
    return "$".join(
        (
            "scrypt",
            str(SCRYPT_N),
            str(SCRYPT_R),
            str(SCRYPT_P),
            base64.b64encode(salt).decode("ascii"),
            base64.b64encode(digest).decode("ascii"),
        )
    )


@dataclass
class BasicAuthGate:
    username: bytes
    salt: bytes = field(repr=False)
    digest: bytes = field(repr=False)
    workers: threading.BoundedSemaphore = field(
        default_factory=lambda: threading.BoundedSemaphore(2), repr=False
    )

    @classmethod
    def from_file(cls, path: Path):
        try:
            if path.stat().st_size > 4096:
                raise ValueError
            config = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(config, dict) or set(config) != {"username", "password_hash"}:
                raise ValueError
            if not valid_username(config["username"]) or not isinstance(config["password_hash"], str):
                raise ValueError
            parts = config["password_hash"].split("$")
            if len(parts) != 6 or parts[:4] != ["scrypt", str(SCRYPT_N), str(SCRYPT_R), str(SCRYPT_P)]:
                raise ValueError
            salt, digest = (base64.b64decode(part, validate=True) for part in parts[4:])
            if len(salt) != 16 or len(digest) != 32:
                raise ValueError
            return cls(config["username"].encode("utf-8"), salt, digest)
        except (OSError, ValueError, TypeError, KeyError, UnicodeError):
            # Never include the file contents, username, hash or parser error in logs.
            raise RuntimeError("Basic Auth: Secret-Datei fehlt, ist unlesbar oder ungültig.") from None

    @classmethod
    def from_environment(cls):
        if any(os.environ.get("NOTEPILOT_ACCESS_" + key) for key in ("TEAM_DOMAIN", "AUD", "EMAILS")):
            raise RuntimeError("Alte Access-Konfiguration entfernen und das Basic-Auth-Profil verwenden.")
        required = os.environ.get("NOTEPILOT_REQUIRE_AUTH", "0")
        if required not in ("0", "1"):
            raise RuntimeError("NOTEPILOT_REQUIRE_AUTH muss 0 oder 1 sein.")
        filename = os.environ.get("NOTEPILOT_BASIC_AUTH_FILE", "").strip()
        if not filename:
            if required == "1":
                raise RuntimeError("Basic Auth ist erforderlich: NOTEPILOT_BASIC_AUTH_FILE fehlt.")
            return None
        return cls.from_file(Path(filename))

    def verify(self, authorization: str):
        if len(authorization) > 8192:
            return False
        scheme, separator, payload = authorization.partition(" ")
        if not separator or scheme.lower() != "basic":
            return False
        try:
            decoded = base64.b64decode(payload, validate=True).decode("utf-8")
            username, separator, password = decoded.partition(":")
            encoded = password.encode("utf-8")
            if not separator or not valid_username(username) or not 1 <= len(encoded) <= MAX_PASSWORD_BYTES:
                return False
        except (binascii.Error, UnicodeError, ValueError):
            return False
        with self.workers:
            calculated = password_digest(encoded, self.salt)
        valid_password = hmac.compare_digest(calculated, self.digest)
        valid_user = hmac.compare_digest(username.encode("utf-8"), self.username)
        return valid_password & valid_user


GATE = BasicAuthGate.from_environment()
