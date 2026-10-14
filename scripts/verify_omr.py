"""Run real CPU inference and compare pitches and timing. No network inference or mocks."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.score import parse_score, read_xml  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--corpus", action="store_true", help="Alle musikalischen Referenzbilder und Foto-Varianten prüfen"
    )
    parser.add_argument("--report", type=Path, help="JSON-Bericht speichern")
    args = parser.parse_args()
    python = ROOT / ".omr-venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    inputs = [(ROOT / "examples/omr-reference.png", ROOT / "examples/abend-am-fluss.musicxml")]
    if args.corpus:
        inputs.extend(
            (p, p.with_suffix(".musicxml")) for p in sorted((ROOT / "examples/corpus").glob("*.png"))
        )
    results = []
    with tempfile.TemporaryDirectory(prefix="notepilot-omr-") as temp:
        temp = Path(temp)
        cases = [(image.stem, image, reference) for image, reference in inputs]
        if args.corpus:
            from PIL import Image, ImageEnhance

            source = Image.open(inputs[0][0]).convert("RGB")
            skew = temp / "schraeg.png"
            source.rotate(3, expand=True, fillcolor="white").save(skew)
            dark = temp / "dunkel.png"
            ImageEnhance.Brightness(source).enhance(0.65).save(dark)
            cases.extend([("schraeg-3-grad", skew, inputs[0][1]), ("dunkel-65-prozent", dark, inputs[0][1])])
        for name, image, reference in cases:
            folder = temp / name
            folder.mkdir()
            copied = folder / "input.png"
            shutil.copyfile(image, copied)
            started = time.monotonic()
            with (folder / "engine.log").open("wb") as log:
                result = subprocess.run(
                    [str(python), str(ROOT / "scripts/homr_runner.py"), str(copied)],
                    cwd=folder,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    timeout=900,
                    check=False,
                )
            actual = copied.with_suffix(".musicxml")
            row = {
                "case": name,
                "seconds": round(time.monotonic() - started, 2),
                "exit_code": result.returncode,
                "passed": False,
            }
            if result.returncode == 0 and actual.exists():
                expected = parse_score(read_xml(reference.read_bytes()))
                recognized = parse_score(read_xml(actual.read_bytes()))
                a = [(e["written_midi"], round(e["duration"], 6)) for e in expected["timeline"]]
                b = [(e["written_midi"], round(e["duration"], 6)) for e in recognized["timeline"]]
                row.update(
                    expected_events=len(a),
                    recognized_events=len(b),
                    matching_events=sum(x == y for x, y in zip(a, b)),
                    expected_measures=expected["measure_count"],
                    recognized_measures=recognized["measure_count"],
                    expected_time=expected["parts"][0]["measures"][0]["time"],
                    recognized_time=recognized["parts"][0]["measures"][0]["time"],
                    expected_fifths=expected["parts"][0]["measures"][0]["fifths"],
                    recognized_fifths=recognized["parts"][0]["measures"][0]["fifths"],
                    passed=a == b
                    and expected["measure_count"] == recognized["measure_count"]
                    and expected["parts"][0]["measures"][0]["time"]
                    == recognized["parts"][0]["measures"][0]["time"]
                    and expected["parts"][0]["measures"][0]["fifths"]
                    == recognized["parts"][0]["measures"][0]["fifths"],
                )
                row["expected"] = a
                row["recognized"] = b
            results.append(row)
            print(json.dumps(row, ensure_ascii=False), flush=True)
    if args.report:
        args.report.write_text(
            json.dumps(
                {
                    "engine": "HOMR 0.7.0",
                    "mode": "CPU",
                    "inference_network": "blocked by runner",
                    "cases": results,
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    sys.exit(0 if all(r["passed"] for r in results) else 1)


if __name__ == "__main__":
    main()
