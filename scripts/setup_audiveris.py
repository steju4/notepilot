"""Install a pinned Audiveris Linux bundle and local English OCR data."""

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path

VERSION = "5.9.0"
BUNDLE_URL = (
    "https://github.com/Audiveris/audiveris/releases/download/5.9.0/Audiveris-5.9.0-ubuntu22.04-x86_64.deb"
)
BUNDLE_SHA256 = "75e917b63a1ef4042056804cb26b6a59d35561a2f21529cbd98459b5724fdd15"
OCR_URL = "https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/87416418657359cb625c412a48b6e1d6d41c29bd/eng.traineddata"
OCR_SHA256 = "7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2"


def download(url, path, expected):
    with urllib.request.urlopen(url, timeout=180) as source, path.open("wb") as destination:
        shutil.copyfileobj(source, destination)
    with path.open("rb") as file:
        if hashlib.file_digest(file, "sha256").hexdigest() != expected:
            raise RuntimeError("Audiveris-Download: Prüfsumme stimmt nicht überein.")


def main():
    parser = argparse.ArgumentParser(description="Audiveris für gedruckte Noten installieren")
    parser.add_argument("--target", type=Path, default=Path(__file__).resolve().parents[1] / ".audiveris")
    args = parser.parse_args()
    if platform.system() != "Linux" or platform.machine() not in ("x86_64", "amd64"):
        raise SystemExit("Dieses geprüfte Audiveris-Bundle benötigt Linux x86_64. HOMR bleibt verfügbar.")
    marker = args.target / "notepilot-install.json"
    if marker.is_file() and json.loads(marker.read_text()).get("bundle_sha256") == BUNDLE_SHA256:
        if (args.target / "bin/Audiveris").is_file() and (args.target / "tessdata/eng.traineddata").is_file():
            print("Audiveris 5.9.0 ist installiert.")
            return
    if args.target.exists():
        raise SystemExit(
            "Unvollständiges Audiveris-Ziel. Bitte den Ordner prüfen und separat sichern/entfernen."
        )
    with tempfile.TemporaryDirectory(prefix="notepilot-audiveris-") as temp:
        temp = Path(temp)
        bundle = temp / "audiveris.deb"
        download(BUNDLE_URL, bundle, BUNDLE_SHA256)
        subprocess.run(["dpkg-deb", "-x", str(bundle), str(temp / "extract")], check=True)
        extracted = temp / "extract/opt/audiveris"
        (extracted / "tessdata").mkdir()
        download(OCR_URL, extracted / "tessdata/eng.traineddata", OCR_SHA256)
        shutil.copytree(extracted, args.target)
    marker.write_text(
        json.dumps(
            dict(
                version=VERSION,
                source=BUNDLE_URL,
                bundle_sha256=BUNDLE_SHA256,
                ocr_source=OCR_URL,
                ocr_sha256=OCR_SHA256,
            ),
            indent=2,
        )
    )
    print("Audiveris 5.9.0 für gedruckte Noten ist installiert.")


if __name__ == "__main__":
    main()
