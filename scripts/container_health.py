"""Probe SQLite and protected HTTP without exempting a route or storing plaintext credentials."""

import json
import os
import sqlite3
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.access import CHALLENGE, GATE  # noqa: E402


def main():
    database = Path(os.environ.get("NOTEPILOT_DATA_DIR", "/data")) / "notepilot.sqlite3"
    with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as connection:
        connection.execute("SELECT id FROM pieces LIMIT 1").fetchall()
    # Loopback only; never fetches external resources or bypasses public authentication.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open("http://127.0.0.1:8000/api/v1/health", timeout=3) as response:
            assert GATE is None
            assert json.load(response)["status"] == "ok"
    except urllib.error.HTTPError as error:
        if GATE is None or error.code != 401:
            raise
        assert error.headers.get("WWW-Authenticate") == CHALLENGE
        assert error.headers.get("Cache-Control") == "no-store"


if __name__ == "__main__":
    main()
