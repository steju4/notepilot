"""CI smoke test: real printed-score recognition inside the shipped offline container."""

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "/app/backend")
from app.services import audiveris  # noqa: E402
from app.services.score import parse_score, read_xml  # noqa: E402


def main():
    assert audiveris.status()["ready"]
    bank = Path("/app/frontend/dist/audio/TimGM6mb.sf2")
    with bank.open("rb") as file:
        assert (
            hashlib.file_digest(file, "sha256").hexdigest()
            == "c5378b62028c920cb11e4803327983fee2f2cdff5dc89c708e39da417e51c854"
        )
    with tempfile.TemporaryDirectory(dir=os.environ.get("NOTEPILOT_DATA_DIR", "/data")) as folder:
        folder = Path(folder)
        source = folder / "input.png"
        shutil.copyfile("/input/vorzeichen.png", source)
        command, env = audiveris.command(source, folder)
        with (folder / "engine.log").open("wb") as log:
            result = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=180)
        if result.returncode or not source.with_suffix(".mxl").is_file():
            print((folder / "engine.log").read_text(errors="replace"))
            raise SystemExit("Container-Erkennung fehlgeschlagen.")
        actual = parse_score(read_xml(source.with_suffix(".mxl").read_bytes()))
        expected = parse_score(read_xml(Path("/input/vorzeichen.musicxml").read_bytes()))

        def music(score):
            return [(n["written_midi"], n["duration"]) for n in score["timeline"]]

        assert music(actual) == music(expected)
    print("Offline-Container: Audiveris-Vorzeichenreferenz und lokale Instrumentenbank geprüft.")


if __name__ == "__main__":
    main()
