"""One-time, repeatable CPU engine setup; no API keys or remote inference."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    argparse.ArgumentParser(description="Lokales HOMR-Modell einrichten").parse_args()
    if sys.version_info[:2] not in ((3, 11), (3, 12)):
        raise SystemExit("Bitte Python 3.11 oder 3.12 verwenden.")
    target = ROOT / ".omr-venv"
    python = target / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.exists():
        print("Die lokale CPU-Erkennungsengine wird installiert.", flush=True)
        venv.EnvBuilder(with_pip=True).create(target)
    if subprocess.run(
        [str(python), "-m", "pip", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    ).returncode:
        subprocess.run([str(python), "-m", "ensurepip", "--upgrade"], check=True)
    subprocess.run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--require-hashes",
            "-r",
            str(ROOT / "scripts/homr-requirements.txt"),
        ],
        check=True,
    )
    print(
        "Das KI-Modell wird für die lokale Notenerkennung eingerichtet. Der Download ist nur erstmalig erforderlich.",
        flush=True,
    )
    data = Path(os.environ.get("NOTEPILOT_DATA_DIR", ROOT / "data"))
    models = data / "models"
    previous = models / "manifest.json"
    if previous.exists():
        saved = json.loads(previous.read_text(encoding="utf-8"))
        for item in saved["artifacts"]:
            name = item["name"]
            if Path(name).name != name or not name.endswith(".onnx"):
                raise SystemExit("Unsicheres Modellmanifest. Bitte den lokalen models-Ordner prüfen.")
            path = models / name
            if path.is_file():
                with path.open("rb") as file:
                    digest = hashlib.file_digest(file, "sha256").hexdigest()
                if digest != item["sha256"]:
                    print(f"Veränderte Modelldatei wird ersetzt: {name}", flush=True)
                    path.unlink()
    subprocess.run([str(python), str(ROOT / "scripts/homr_runner.py"), "--init"], check=True, cwd=ROOT)
    data = Path(os.environ.get("NOTEPILOT_DATA_DIR", ROOT / "data"))
    models = data / "models"
    subprocess.run(
        [
            str(python),
            "-c",
            "import onnxruntime as ort, pathlib, os; root=pathlib.Path(os.environ.get('NOTEPILOT_DATA_DIR', 'data'))/'models'; options=ort.SessionOptions(); options.intra_op_num_threads=4; options.inter_op_num_threads=1; [ort.InferenceSession(str(p),sess_options=options,providers=['CPUExecutionProvider']) for p in root.glob('*.onnx')]",
        ],
        check=True,
        cwd=ROOT,
    )
    # Record provenance and local integrity for offline verification. These are not claimed to be publisher signatures.
    manifest = {
        "engine": "homr",
        "version": "0.7.0",
        "source": "https://github.com/liebharc/homr/releases/tag/onnx_checkpoints",
        "mode": "CPU",
        "artifacts": [],
    }
    for path in sorted(models.glob("*.onnx")):
        manifest["artifacts"].append(
            {
                "name": path.name,
                "bytes": path.stat().st_size,
                "sha256": hashlib.file_digest(path.open("rb"), "sha256").hexdigest(),
            }
        )
    (models / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    subprocess.run([str(python), str(ROOT / "scripts/homr_runner.py"), "--status"], check=True, cwd=ROOT)
    print("Lokale CPU-Erkennung ist eingerichtet.", flush=True)


if __name__ == "__main__":
    main()
