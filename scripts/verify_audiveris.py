"""Compare real Audiveris output against printed reference scores, without fallback scores."""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services import audiveris  # noqa: E402
from app.services.score import parse_score, read_xml  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if not audiveris.status()["ready"]:
        raise SystemExit("Bitte zuerst scripts/setup_audiveris.py ausführen.")
    from PIL import Image, ImageEnhance

    results = []
    with tempfile.TemporaryDirectory(prefix="notepilot-audiveris-test-") as folder:
        folder = Path(folder)
        original = ROOT / "examples/omr-reference.png"
        photo = Image.open(original).convert("RGB")
        photo.rotate(3, expand=True, fillcolor="white").save(folder / "schraeg.png")
        ImageEnhance.Brightness(photo).enhance(0.65).save(folder / "dunkel.png")
        cases = [(original, ROOT / "examples/abend-am-fluss.musicxml")]
        cases.extend(
            (p, p.with_suffix(".musicxml")) for p in sorted((ROOT / "examples/corpus").glob("*.png"))
        )
        cases.extend((folder / n, cases[0][1]) for n in ("schraeg.png", "dunkel.png"))
        for image, reference in cases:
            work = folder / image.stem
            work.mkdir()
            source = work / "input.png"
            source.write_bytes(image.read_bytes())
            command, env = audiveris.command(source, folder / "engine-data")
            with (work / "engine.log").open("wb") as log:
                process = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=180)
            output = source.with_suffix(".mxl")
            expected = parse_score(read_xml(reference.read_bytes()))
            actual = parse_score(read_xml(output.read_bytes())) if output.is_file() else None

            def music(score):
                return [(e["written_midi"], round(e["duration"], 6)) for e in score["timeline"]]

            def structure(score):
                return [[(m["time"], m["fifths"]) for m in p["measures"]] for p in score["parts"]]

            passed = (
                actual is not None
                and music(actual) == music(expected)
                and structure(actual) == structure(expected)
            )
            results.append(
                dict(
                    name=image.stem,
                    passed=passed,
                    exit_code=process.returncode,
                    expected=music(expected),
                    actual=music(actual) if actual else None,
                    structure_matches=actual is not None and structure(actual) == structure(expected),
                )
            )
            print(f"{image.stem}: {'bestanden' if passed else 'FEHLGESCHLAGEN'}", flush=True)
    if args.report:
        args.report.write_text(json.dumps(dict(engine="Audiveris", version="5.9.0", cases=results), indent=2))
    if not all(r["passed"] for r in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
