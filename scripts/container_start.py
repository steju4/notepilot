"""Seed the persistent model cache, then replace this process with the API."""

import hashlib
import json
import os
import shutil
import sys
from pathlib import Path


def seed_models(seed: Path, data: Path):
    source = seed / "models"
    if not (source / "manifest.json").is_file():
        if os.environ.get("NOTEPILOT_REQUIRE_MODELS") == "1":
            raise RuntimeError("Dieses Image benötigt vorinstallierte Modelle. Bitte neu bauen.")
        return
    manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    destination = data / "models"
    destination.mkdir(parents=True, exist_ok=True)
    for item in manifest["artifacts"]:
        name = item["name"]
        if Path(name).name != name or not name.endswith(".onnx"):
            raise RuntimeError("Ungültiger Modellpfad im Image.")
        original, target = source / name, destination / name
        with original.open("rb") as file:
            if hashlib.file_digest(file, "sha256").hexdigest() != item["sha256"]:
                raise RuntimeError("Modellintegrität im Image verletzt.")
        valid = False
        if target.is_file():
            with target.open("rb") as file:
                valid = hashlib.file_digest(file, "sha256").hexdigest() == item["sha256"]
        if not valid:
            temporary = destination / (name + ".tmp")
            shutil.copyfile(original, temporary)
            temporary.replace(target)
    temporary = destination / "manifest.json.tmp"
    temporary.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    temporary.replace(destination / "manifest.json")


def main():
    data = Path(os.environ.get("NOTEPILOT_DATA_DIR", "/data"))
    data.mkdir(parents=True, exist_ok=True)
    seed_models(Path("/opt/notepilot-seed"), data)
    os.execv(
        sys.executable,
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.api:app",
            "--app-dir",
            "/app/backend",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
            "--no-proxy-headers",
        ],
    )


if __name__ == "__main__":
    main()
