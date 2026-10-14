"""Internal probe: verify SQLite and the HTTP server without exempting a public route."""

import json
import os
import sqlite3
import urllib.error
import urllib.request
from pathlib import Path


def main():
    database = Path(os.environ.get("NOTEPILOT_DATA_DIR", "/data")) / "notepilot.sqlite3"
    with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as connection:
        connection.execute("SELECT id FROM pieces LIMIT 1").fetchall()
    # This loopback probe never fetches external resources.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    protected = bool(os.environ.get("NOTEPILOT_ACCESS_TEAM_DOMAIN"))
    try:
        with opener.open("http://127.0.0.1:8000/api/v1/health", timeout=3) as response:
            assert not protected
            assert json.load(response)["status"] == "ok"
    except urllib.error.HTTPError as error:
        if not protected or error.code != 403:
            raise


if __name__ == "__main__":
    main()
