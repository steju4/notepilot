import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description="NotePilot lokal starten")
parser.add_argument("--lan", action="store_true", help="Zugriff aus einem vertrauenswürdigen WLAN erlauben")
parser.add_argument("--port", type=int, default=8000)
args = parser.parse_args()
python = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
if not python.exists() or not (ROOT / "frontend/dist/index.html").exists():
    raise SystemExit("Bitte zuerst python scripts/install.py ausführen.")
host = "0.0.0.0" if args.lan else "127.0.0.1"
print(f"NotePilot: http://127.0.0.1:{args.port}", flush=True)
if args.lan:
    print(
        "LAN-Modus aktiviert: am Smartphone die private IP dieses Computers verwenden. Keine öffentliche Portfreigabe einrichten.",
        flush=True,
    )
try:
    code = subprocess.call(
        [
            str(python),
            "-m",
            "uvicorn",
            "app.api:app",
            "--app-dir",
            str(ROOT / "backend"),
            "--host",
            host,
            "--port",
            str(args.port),
        ],
        cwd=ROOT,
    )
except KeyboardInterrupt:
    code = 0
sys.exit(code)
