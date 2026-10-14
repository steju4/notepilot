import json
import os
import shutil
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from .. import db
from ..core import DATA, OMR_PYTHON, OMR_TIMEOUT, ROOT, local_path
from .score import combine_pages, read_xml
from .storage import save_score

EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="local-omr")
PROCESSES = {}
CANCELLED = set()
LOCK = threading.Lock()


def engine_status():
    if not OMR_PYTHON.is_file():
        return dict(
            installed=False,
            ready=False,
            version="0.7.0",
            mode="CPU",
            models=[],
            message="Das lokale KI-Modell ist noch nicht eingerichtet. Bitte das Modell-Setup starten.",
        )
    try:
        result = subprocess.run(
            [str(OMR_PYTHON), str(ROOT / "scripts/homr_runner.py"), "--status"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode:
            return dict(
                installed=False,
                ready=False,
                models=[],
                mode="CPU",
                version="0.7.0",
                message="HOMR konnte nicht geladen werden. Modell-Setup erneut ausführen.",
            )
        return json.loads(result.stdout.strip().splitlines()[-1])
    except Exception:
        return dict(
            installed=False,
            ready=False,
            models=[],
            mode="CPU",
            version="0.7.0",
            message="Der lokale KI-Prozess antwortet nicht.",
        )


def update_job(job, **changes):
    keys = list(changes)
    db.execute(
        "UPDATE jobs SET " + ",".join(k + "=?" for k in keys) + " WHERE id=?",
        tuple(changes[k] for k in keys) + (job,),
    )


def cancel(job):
    with LOCK:
        CANCELLED.add(job)
        process = PROCESSES.get(job)
        if process and process.poll() is None:
            process.terminate()
    update_job(job, status="cancelled", stage="Abgebrochen", finished_at=db.now())


def recognize_score(input_document, options):
    """Public engine adapter. Starts one local CPU process; never generates fallback notation."""
    job = options["job_id"]
    log = DATA / "logs" / f"{job}-{input_document.stem}.log"
    env = os.environ.copy()
    env["NOTEPILOT_DATA_DIR"] = str(DATA)
    start = time.monotonic()
    with log.open("wb") as output:
        with LOCK:
            if job in CANCELLED:
                raise InterruptedError("Die Erkennung wurde abgebrochen.")
            process = subprocess.Popen(
                [str(OMR_PYTHON), str(ROOT / "scripts/homr_runner.py"), str(input_document)],
                stdout=output,
                stderr=subprocess.STDOUT,
                env=env,
                cwd=input_document.parent,
            )
            PROCESSES[job] = process
        try:
            code = process.wait(timeout=OMR_TIMEOUT)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            raise RuntimeError(
                "Die Erkennung hat das Zeitlimit überschritten. Bitte einen kleineren Bildausschnitt versuchen."
            )
        finally:
            with LOCK:
                PROCESSES.pop(job, None)
    if job in CANCELLED:
        raise InterruptedError("Die Erkennung wurde abgebrochen.")
    result = input_document.with_suffix(".musicxml")
    if code or not result.exists():
        raise RuntimeError(
            "HOMR konnte keine Partitur erkennen. Bitte Schärfe, Zuschnitt und Beleuchtung prüfen. Details stehen im lokalen Diagnoseprotokoll."
        )
    root = read_xml(result.read_bytes())
    return dict(
        root=root,
        engine="homr",
        version="0.7.0",
        mode="CPU",
        duration_seconds=round(time.monotonic() - start, 2),
    )


def run_job(job, piece_id):
    work = DATA / "cache" / job
    work.mkdir(parents=True, exist_ok=True)
    try:
        if job in CANCELLED:
            return
        update_job(job, status="running", stage="Lokales KI-Modell wird geprüft", started_at=db.now())
        status = engine_status()
        if not status.get("ready"):
            raise RuntimeError(
                "Die lokalen Modellgewichte fehlen. Bitte zuerst die KI-Einrichtung ausführen."
            )
        pages = db.query(
            "SELECT * FROM pages WHERE piece_id=? AND excluded=0 ORDER BY sort_order,page_number", (piece_id,)
        )
        if not pages:
            raise RuntimeError("Bitte zuerst ein Notenbild oder PDF hinzufügen.")
        roots, duration = [], 0
        for i, page in enumerate(pages):
            if job in CANCELLED:
                return
            update_job(
                job,
                stage=f"Seite {i + 1} von {len(pages)} wird auf diesem Computer erkannt",
                details=json.dumps(dict(page=i + 1, pages=len(pages), mode="CPU", version="0.7.0")),
            )
            source = local_path(page["processed_path"] or page["image_path"])
            image = work / f"page-{i + 1}.png"
            shutil.copyfile(source, image)
            result = recognize_score(image, dict(job_id=job))
            roots.append(result["root"])
            duration += result["duration_seconds"]
        if job in CANCELLED:
            return
        update_job(job, stage="Musikstruktur wird geprüft und gespeichert")
        combined = combine_pages(roots)
        # Cancellation and publication form one critical section.
        with LOCK:
            if job in CANCELLED:
                return
            version = save_score(piece_id, combined, "HOMR 0.7.0 / CPU")
            update_job(
                job,
                status="completed",
                stage="Ergebnis bereit — bitte Noten prüfen",
                finished_at=db.now(),
                details=json.dumps(
                    dict(
                        pages=len(pages),
                        duration_seconds=duration,
                        mode="CPU",
                        version="0.7.0",
                        score_version=version,
                    )
                ),
            )
    except InterruptedError:
        update_job(job, status="cancelled", stage="Abgebrochen", finished_at=db.now())
    except Exception as error:
        if job not in CANCELLED:
            update_job(
                job, status="failed", stage="Erkennung fehlgeschlagen", error=str(error), finished_at=db.now()
            )
    finally:
        shutil.rmtree(work, ignore_errors=True)
        with LOCK:
            CANCELLED.discard(job)


def shutdown():
    with LOCK:
        for job, process in PROCESSES.items():
            CANCELLED.add(job)
            if process.poll() is None:
                process.terminate()
    EXECUTOR.shutdown(wait=False, cancel_futures=True)
