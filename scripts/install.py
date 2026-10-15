"""Portable Python/Node setup. Use --omr for the one-time local model installation."""

import argparse
import os
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--omr", action="store_true", help="Auch das lokale CPU-Modell einrichten")
    parser.add_argument("--dev", action="store_true", help="Auch die Entwicklungs-Prüfwerkzeuge installieren")
    parser.add_argument("--audiveris", action="store_true", help="Audiveris für gedruckte Noten (Linux x86_64)")
    args = parser.parse_args()
    if sys.version_info[:2] not in ((3, 11), (3, 12)):
        raise SystemExit("Bitte Python 3.11 oder 3.12 verwenden.")
    python = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.exists():
        venv.EnvBuilder(with_pip=True).create(ROOT / ".venv")
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
            str(ROOT / ("backend/dev-requirements.txt" if args.dev else "backend/requirements.txt")),
        ],
        check=True,
    )
    npm = "npm.cmd" if os.name == "nt" else "npm"
    subprocess.run([npm, "ci"], cwd=ROOT / "frontend", check=True)
    subprocess.run([npm, "run", "build"], cwd=ROOT / "frontend", check=True)
    if args.omr:
        subprocess.run([str(python), str(ROOT / "scripts/setup_omr.py")], cwd=ROOT, check=True)
    if args.audiveris:
        subprocess.run([str(python), str(ROOT / "scripts/setup_audiveris.py")], cwd=ROOT, check=True)
    print("NotePilot ist installiert. Starte scripts/start.py.", flush=True)


if __name__ == "__main__":
    main()
