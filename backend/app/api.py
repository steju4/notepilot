import ipaddress
import json
import shutil
import tempfile
import zipfile
from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from jwt import PyJWTError
from pydantic import BaseModel, ConfigDict, Field
from starlette.concurrency import run_in_threadpool

from . import access, db
from .core import ALLOWED_HOSTS, DATA, HOSTED_PREVIEW, MAX_UPLOAD, ROOT, local_path
from .services import omr
from .services.images import decode_pages, process_image, quality
from .services.instruments import INSTRUMENTS
from .services.score import edit_score, midi_bytes, parse_score, read_xml, xml_bytes
from .services.storage import save_score


@asynccontextmanager
async def lifespan(app):
    db.init_db()
    yield
    omr.shutdown()


app = FastAPI(title="NotePilot", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
)


@app.middleware("http")
async def local_access(request: Request, call_next):
    host = request.url.hostname or ""
    allowed_host = host in ("localhost", "127.0.0.1", "::1", "testserver") or host.lower() in ALLOWED_HOSTS
    if not allowed_host:
        try:
            ip = ipaddress.ip_address(host)
            allowed_host = ip.is_private and not ip.is_unspecified
        except ValueError:
            allowed_host = False
    if not allowed_host:
        return Response("Unzulässiger Hostname.", status_code=403)
    if access.GATE:
        try:
            await run_in_threadpool(access.GATE.verify, request.headers.get("cf-access-jwt-assertion", ""))
        except (PyJWTError, OSError):
            return Response(
                "Cloudflare-Access-Anmeldung erforderlich.",
                status_code=403,
                headers={"Cache-Control": "no-store"},
            )
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        origin = request.headers.get("origin")
        if origin:
            parsed = urlsplit(origin)
            same = parsed.netloc == request.headers.get("host") and parsed.scheme in ("http", "https")
            dev = origin in ("http://localhost:5173", "http://127.0.0.1:5173") and host in (
                "localhost",
                "127.0.0.1",
            )
            if not same and not dev:
                return Response("Anfrage von einer fremden Website abgelehnt.", status_code=403)
        if request.headers.get("sec-fetch-site") == "cross-site":
            return Response("Anfrage von einer fremden Website abgelehnt.", status_code=403)
    length = request.headers.get("content-length")
    if length and (not length.isdigit() or int(length) > MAX_UPLOAD + 1024 * 1024):
        return Response("Uploadlimit überschritten.", status_code=413)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    if access.GATE:
        response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(zipfile.BadZipFile)
@app.exception_handler(ValueError)
async def value_error(request, error):
    return Response(
        json.dumps({"detail": str(error)}, ensure_ascii=False), status_code=422, media_type="application/json"
    )


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PieceCreate(StrictModel):
    title: str = Field(min_length=1, max_length=200)
    composer: str = Field(default="", max_length=200)
    instrument: str = "piano"


class PiecePatch(StrictModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    composer: str | None = Field(default=None, max_length=200)
    instrument: str | None = None
    notation: str | None = None
    favorite: bool | None = None
    collection: str | None = Field(default=None, max_length=200)
    playback_settings: dict | None = None


class ScoreChange(StrictModel):
    action: str
    event_id: str | None = None
    part: int = Field(default=0, ge=0)
    measure: int | None = Field(default=None, ge=1)
    fields: dict = Field(default_factory=dict)
    version_id: str | None = None


class Practice(StrictModel):
    name: str = Field(min_length=1, max_length=100)
    start_measure: int = Field(ge=1)
    end_measure: int = Field(ge=1)
    settings: dict = Field(default_factory=dict)
    notes: str = Field(default="", max_length=2000)


def get_piece(identity):
    piece = db.piece_row(db.query("SELECT * FROM pieces WHERE id=?", (identity,), one=True))
    if not piece:
        raise HTTPException(404, "Dieses Stück wurde nicht gefunden.")
    return piece


def score_root(piece):
    version = db.query(
        "SELECT * FROM score_versions WHERE id=? AND piece_id=?",
        (piece["current_version"], piece["id"]),
        one=True,
    )
    if not version:
        raise HTTPException(404, "Für dieses Stück gibt es noch keine digitale Partitur.")
    return read_xml(local_path(version["path"]).read_bytes())


def piece_score(piece):
    score = parse_score(
        score_root(piece),
        piece["instrument"],
        piece["notation"],
        int(piece["playback_settings"].get("extra_transpose", 0)),
    )
    score["version_id"] = piece["current_version"]
    return score


def job_row(job):
    if job:
        job["details"] = json.loads(job["details"])
    return job


@app.get("/api/v1/runtime")
def runtime():
    return {"hosted_preview": HOSTED_PREVIEW, "storage_location": "testserver" if HOSTED_PREVIEW else "local"}


@app.get("/api/v1/health")
def health():
    with db.connection() as con:
        con.execute("SELECT 1").fetchone()
    return {"status": "ok", "storage": "SQLite / lokale Dateien", "version": "0.1.0"}


@app.get("/api/v1/instruments")
def instruments():
    return list(INSTRUMENTS.values())


@app.get("/api/v1/pieces")
def pieces():
    return [db.piece_row(r) for r in db.query("SELECT * FROM pieces ORDER BY updated_at DESC")]


@app.post("/api/v1/pieces", status_code=201)
def create_piece(body: PieceCreate):
    if body.instrument not in INSTRUMENTS:
        raise ValueError("Unbekanntes Instrument.")
    if not body.title.strip():
        raise ValueError("Bitte einen Titel eingeben.")
    identity, created = db.uid(), db.now()
    db.execute(
        "INSERT INTO pieces (id,title,composer,instrument,created_at,updated_at) VALUES (?,?,?,?,?,?)",
        (identity, body.title.strip(), body.composer, body.instrument, created, created),
    )
    return get_piece(identity)


@app.get("/api/v1/pieces/{identity}")
def piece(identity):
    result = get_piece(identity)
    db.execute("UPDATE pieces SET last_opened_at=? WHERE id=?", (db.now(), identity))
    result["documents"] = db.query("SELECT * FROM documents WHERE piece_id=?", (identity,))
    result["pages"] = db.query(
        "SELECT * FROM pages WHERE piece_id=? ORDER BY sort_order,page_number", (identity,)
    )
    for page in result["pages"]:
        page["quality"] = json.loads(page["quality"])
    result["versions"] = db.query(
        "SELECT * FROM score_versions WHERE piece_id=? ORDER BY sequence", (identity,)
    )
    result["jobs"] = [
        job_row(j)
        for j in db.query("SELECT * FROM jobs WHERE piece_id=? ORDER BY created_at DESC", (identity,))
    ]
    return result


@app.patch("/api/v1/pieces/{identity}")
def patch_piece(identity, body: PiecePatch):
    get_piece(identity)
    fields = body.model_dump(exclude_none=True)
    if "title" in fields:
        fields["title"] = fields["title"].strip()
        if not fields["title"]:
            raise ValueError("Bitte einen Titel eingeben.")
    if fields.get("instrument") and fields["instrument"] not in INSTRUMENTS:
        raise ValueError("Unbekanntes Instrument.")
    if fields.get("notation") and fields["notation"] not in (
        "auto",
        "written",
        "concert",
        "bb-treble",
        "eb-treble",
    ):
        raise ValueError("Unbekannte Notationsvariante.")
    if "playback_settings" in fields:
        if len(json.dumps(fields["playback_settings"])) > 10000:
            raise ValueError("Zu viele Wiedergabeeinstellungen.")
        transposition = fields["playback_settings"].get("extra_transpose", 0)
        if not isinstance(transposition, int) or not -24 <= transposition <= 24:
            raise ValueError("Zusätzliche Transposition muss zwischen −24 und +24 liegen.")
        fields["playback_settings"] = json.dumps(fields["playback_settings"])
    fields["updated_at"] = db.now()
    db.execute(
        "UPDATE pieces SET " + ",".join(k + "=?" for k in fields) + " WHERE id=?",
        tuple(fields.values()) + (identity,),
    )
    return get_piece(identity)


@app.delete("/api/v1/pieces/{identity}", status_code=204)
def delete_piece(identity):
    get_piece(identity)
    active = db.query("SELECT * FROM jobs WHERE piece_id=? AND status IN ('queued','running')", (identity,))
    if active:
        raise HTTPException(409, "Bitte die laufende Erkennung erst abbrechen und ihr Ende abwarten.")
    db.execute("DELETE FROM pieces WHERE id=?", (identity,))
    for folder in ("originals", "processed", "musicxml"):
        shutil.rmtree(DATA / folder / identity, ignore_errors=True)


@app.post("/api/v1/pieces/{identity}/duplicate", status_code=201)
def duplicate_piece(identity):
    source = get_piece(identity)
    new = create_piece(
        PieceCreate(
            title=source["title"][:192] + " (Kopie)",
            composer=source["composer"],
            instrument=source["instrument"],
        )
    )
    try:
        for folder in ("originals", "processed"):
            origin = DATA / folder / identity
            if origin.exists():
                shutil.copytree(origin, DATA / folder / new["id"])
        documents = db.query("SELECT * FROM documents WHERE piece_id=?", (identity,))
        pages = db.query("SELECT * FROM pages WHERE piece_id=?", (identity,))
        mapping = {document["id"]: db.uid() for document in documents}

        def copied_path(path):
            if path is None:
                return None
            parts = Path(path).parts
            if len(parts) < 3 or parts[1] != identity:
                raise ValueError("Originaldateien enthalten einen unerwarteten Pfad.")
            return Path(parts[0], new["id"], *parts[2:]).as_posix()

        with db.connection() as con:
            for d in documents:
                con.execute(
                    "INSERT INTO documents VALUES (?,?,?,?,?,?)",
                    (
                        mapping[d["id"]],
                        new["id"],
                        d["filename"],
                        d["file_type"],
                        copied_path(d["path"]),
                        d["page_count"],
                    ),
                )
            for p in pages:
                con.execute(
                    "INSERT INTO pages VALUES (?,?,?,?,?,?,?,?,?)",
                    (
                        db.uid(),
                        mapping[p["document_id"]],
                        new["id"],
                        p["page_number"],
                        p["sort_order"],
                        copied_path(p["image_path"]),
                        copied_path(p["processed_path"]),
                        p["quality"],
                        p["excluded"],
                    ),
                )
            for section in db.query("SELECT * FROM practice_sections WHERE piece_id=?", (identity,)):
                con.execute(
                    "INSERT INTO practice_sections VALUES (?,?,?,?,?,?,?)",
                    (
                        db.uid(),
                        new["id"],
                        section["name"],
                        section["start_measure"],
                        section["end_measure"],
                        section["settings"],
                        section["notes"],
                    ),
                )
        if source["current_version"]:
            save_score(new["id"], score_root(source), "Duplikat")
        patch_piece(
            new["id"],
            PiecePatch(
                notation=source["notation"],
                collection=source["collection"],
                playback_settings=source["playback_settings"],
            ),
        )
    except Exception:
        delete_piece(new["id"])
        raise
    return get_piece(new["id"])


def upload_bytes(file):
    data = file.file.read(MAX_UPLOAD + 1)
    if not data or len(data) > MAX_UPLOAD:
        raise HTTPException(413, "Die Datei ist leer oder überschreitet das Uploadlimit.")
    return data


@app.post("/api/v1/pieces/{identity}/documents", status_code=201)
def upload_document(identity, file: UploadFile):
    get_piece(identity)
    data = upload_bytes(file)
    filename = Path((file.filename or "noten").replace("\\", "/")).name[:200]
    suffix = Path(filename).suffix.lower()
    if suffix not in (".png", ".jpg", ".jpeg", ".webp", ".pdf", ".musicxml", ".xml", ".mxl"):
        raise ValueError("Unterstützt werden JPG, PNG, WebP, PDF, MusicXML und MXL.")
    doc_id = db.uid()
    folder = DATA / "originals" / identity / doc_id
    folder.mkdir(parents=True)
    relative = f"originals/{identity}/{doc_id}/source{suffix}"
    local_path(relative).write_bytes(data)
    try:
        root = read_xml(data) if suffix in (".musicxml", ".xml", ".mxl") else None
        images = [] if root is not None else decode_pages(data, suffix)
        if (
            len(images)
            + db.query("SELECT count(*) AS n FROM pages WHERE piece_id=?", (identity,), one=True)["n"]
            > 30
        ):
            raise ValueError("Ein Stück darf höchstens 30 Bildseiten enthalten.")
        page_rows = []
        for i, image in enumerate(images):
            path = f"originals/{identity}/{doc_id}/page-{i + 1}.png"
            image.save(local_path(path), "PNG")
            page_rows.append(
                (
                    db.uid(),
                    doc_id,
                    identity,
                    i + 1,
                    len(db.query("SELECT id FROM pages WHERE piece_id=?", (identity,))) + i,
                    path,
                    json.dumps(quality(image)),
                )
            )
        with db.connection() as con:
            con.execute(
                "INSERT INTO documents VALUES (?,?,?,?,?,?)",
                (doc_id, identity, filename, suffix, relative, len(images)),
            )
            for row in page_rows:
                con.execute(
                    "INSERT INTO pages (id,document_id,piece_id,page_number,sort_order,image_path,quality) VALUES (?,?,?,?,?,?,?)",
                    row,
                )
        if root is not None:
            save_score(identity, root, "MusicXML-Import")
    except Exception:
        db.execute("DELETE FROM documents WHERE id=?", (doc_id,))
        shutil.rmtree(folder, ignore_errors=True)
        raise
    return piece(identity)


@app.get("/api/v1/pages/{identity}/image")
def page_image(identity, original: bool = False):
    page = db.query("SELECT * FROM pages WHERE id=?", (identity,), one=True)
    if not page:
        raise HTTPException(404, "Seite nicht vorhanden.")
    return FileResponse(
        local_path(page["image_path"] if original else (page["processed_path"] or page["image_path"])),
        media_type="image/png",
    )


@app.patch("/api/v1/pages/{identity}")
def patch_page(identity, body: dict):
    page = db.query("SELECT * FROM pages WHERE id=?", (identity,), one=True)
    if not page:
        raise HTTPException(404, "Seite nicht vorhanden.")
    if "excluded" in body:
        db.execute("UPDATE pages SET excluded=? WHERE id=?", (bool(body["excluded"]), identity))
    if "sort_order" in body:
        order = int(body["sort_order"])
        if not 0 <= order <= 100:
            raise ValueError("Ungültige Seitenreihenfolge.")
        db.execute("UPDATE pages SET sort_order=? WHERE id=?", (order, identity))
    if body.get("reset"):
        db.execute("UPDATE pages SET processed_path=NULL WHERE id=?", (identity,))
    elif "options" in body:
        path = f"processed/{page['piece_id']}/{identity}.png"
        local_path(path).parent.mkdir(parents=True, exist_ok=True)
        result = process_image(local_path(page["image_path"]), local_path(path), body["options"])
        db.execute(
            "UPDATE pages SET processed_path=?,quality=? WHERE id=?", (path, json.dumps(result), identity)
        )
    return piece(page["piece_id"])


@app.post("/api/v1/pieces/{identity}/recognition", status_code=202)
def recognize(identity):
    get_piece(identity)
    if db.query("SELECT id FROM jobs WHERE piece_id=? AND status IN ('queued','running')", (identity,)):
        raise HTTPException(409, "Für dieses Stück läuft bereits eine Erkennung.")
    if not db.query("SELECT id FROM pages WHERE piece_id=? AND excluded=0", (identity,)):
        raise ValueError("Bitte zuerst ein Bild oder PDF importieren.")
    job = db.uid()
    db.execute(
        "INSERT INTO jobs (id,piece_id,engine,status,stage,created_at) VALUES (?,?,?,?,?,?)",
        (job, identity, "homr", "queued", "Wartet auf lokale Verarbeitung", db.now()),
    )
    omr.EXECUTOR.submit(omr.run_job, job, identity)
    return job_row(db.query("SELECT * FROM jobs WHERE id=?", (job,), one=True))


@app.get("/api/v1/recognition-jobs/{identity}")
def get_job(identity):
    job = db.query("SELECT * FROM jobs WHERE id=?", (identity,), one=True)
    if not job:
        raise HTTPException(404, "Erkennungsauftrag nicht gefunden.")
    return job_row(job)


@app.post("/api/v1/recognition-jobs/{identity}/cancel")
def cancel_job(identity):
    job = get_job(identity)
    if job["status"] in ("queued", "running"):
        omr.cancel(identity)
    return get_job(identity)


@app.get("/api/v1/pieces/{identity}/score")
def get_score(identity):
    return piece_score(get_piece(identity))


@app.patch("/api/v1/pieces/{identity}/score")
def patch_score(identity, body: ScoreChange):
    piece = get_piece(identity)
    if body.version_id and body.version_id != piece["current_version"]:
        raise HTTPException(409, "Die Partitur wurde inzwischen geändert. Bitte neu laden.")
    root = edit_score(score_root(piece), body.model_dump())
    save_score(identity, root, "Manuelle Korrektur")
    return piece_score(get_piece(identity))


@app.post("/api/v1/pieces/{identity}/score/validate")
def validate_score(identity):
    return get_score(identity)["warnings"]


@app.get("/api/v1/pieces/{identity}/warnings")
def score_warnings(identity):
    return validate_score(identity)


@app.post("/api/v1/pieces/{identity}/versions/{version}")
def select_version(identity, version):
    get_piece(identity)
    if not db.query("SELECT id FROM score_versions WHERE id=? AND piece_id=?", (version, identity), one=True):
        raise HTTPException(404, "Partiturversion nicht gefunden.")
    db.execute("UPDATE pieces SET current_version=?,updated_at=? WHERE id=?", (version, db.now(), identity))
    return get_score(identity)


@app.get("/api/v1/pieces/{identity}/export/musicxml")
def export_xml(identity):
    data = xml_bytes(score_root(get_piece(identity)))
    return Response(
        data,
        media_type="application/vnd.recordare.musicxml+xml",
        headers={"Content-Disposition": 'attachment; filename="noten.musicxml"'},
    )


@app.get("/api/v1/pieces/{identity}/export/midi")
def export_midi(identity):
    piece = get_piece(identity)
    return Response(
        midi_bytes(piece_score(piece), piece["instrument"]),
        media_type="audio/midi",
        headers={"Content-Disposition": 'attachment; filename="noten.mid"'},
    )


@app.get("/api/v1/pieces/{identity}/practice-sections")
def practice_sections(identity):
    get_piece(identity)
    result = db.query("SELECT * FROM practice_sections WHERE piece_id=?", (identity,))
    for row in result:
        row["settings"] = json.loads(row["settings"])
    return result


def validate_section(piece_id, body):
    score = get_score(piece_id)
    if body.start_measure > body.end_measure or body.end_measure > score["measure_count"]:
        raise ValueError("Der Übungsabschnitt liegt außerhalb der Partitur.")


@app.post("/api/v1/pieces/{identity}/practice-sections", status_code=201)
def create_practice(identity, body: Practice):
    validate_section(identity, body)
    section = db.uid()
    db.execute(
        "INSERT INTO practice_sections VALUES (?,?,?,?,?,?,?)",
        (
            section,
            identity,
            body.name,
            body.start_measure,
            body.end_measure,
            json.dumps(body.settings),
            body.notes,
        ),
    )
    return practice_sections(identity)


@app.patch("/api/v1/practice-sections/{identity}")
def patch_practice(identity, body: Practice):
    section = db.query("SELECT * FROM practice_sections WHERE id=?", (identity,), one=True)
    if not section:
        raise HTTPException(404, "Übungsabschnitt nicht gefunden.")
    validate_section(section["piece_id"], body)
    db.execute(
        "UPDATE practice_sections SET name=?,start_measure=?,end_measure=?,settings=?,notes=? WHERE id=?",
        (body.name, body.start_measure, body.end_measure, json.dumps(body.settings), body.notes, identity),
    )
    return practice_sections(section["piece_id"])


@app.delete("/api/v1/practice-sections/{identity}", status_code=204)
def delete_practice(identity):
    db.execute("DELETE FROM practice_sections WHERE id=?", (identity,))


@app.post("/api/v1/pieces/{identity}/practice-sessions")
def log_practice(identity, body: dict):
    get_piece(identity)
    duration = float(body.get("duration", 0))
    if not 0 <= duration <= 86400:
        raise ValueError("Ungültige Übungsdauer.")
    db.execute("INSERT INTO practice_sessions VALUES (?,?,?,?)", (db.uid(), identity, duration, db.now()))
    return {"saved": True}


@app.get("/api/v1/settings")
def settings():
    return {r["key"]: json.loads(r["value"]) for r in db.query("SELECT * FROM settings")}


@app.patch("/api/v1/settings")
def save_settings(body: dict):
    if len(json.dumps(body)) > 10000:
        raise ValueError("Einstellungen sind zu groß.")
    with db.connection() as con:
        for key, value in body.items():
            con.execute(
                "INSERT INTO settings VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, json.dumps(value)),
            )
    return settings()


# Model setup is an explicit one-time user action, separate from recognition.
MODEL_SETUP = {"status": "idle"}
MODEL_SETUP_LOCK = __import__("threading").Lock()


def setup_model_worker():
    import subprocess
    import sys

    try:
        log = DATA / "logs" / "model-setup.log"
        with log.open("wb") as output:
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/setup_omr.py")],
                cwd=ROOT,
                stdout=output,
                stderr=subprocess.STDOUT,
                timeout=1800,
            )
        if result.returncode or not omr.engine_status().get("ready"):
            raise RuntimeError(
                "Die KI-Einrichtung ist fehlgeschlagen. Prüfe die Internetverbindung und data/logs/model-setup.log."
            )
        with MODEL_SETUP_LOCK:
            MODEL_SETUP.clear()
            MODEL_SETUP["status"] = "completed"
    except Exception as error:
        with MODEL_SETUP_LOCK:
            MODEL_SETUP.clear()
            MODEL_SETUP.update(status="failed", error=str(error))


@app.get("/api/v1/omr/setup")
def model_setup_status():
    with MODEL_SETUP_LOCK:
        return dict(MODEL_SETUP)


@app.post("/api/v1/omr/setup", status_code=202)
def model_setup():
    import threading

    with MODEL_SETUP_LOCK:
        if MODEL_SETUP["status"] == "running":
            return dict(MODEL_SETUP)
        MODEL_SETUP.clear()
        MODEL_SETUP["status"] = "running"
    threading.Thread(target=setup_model_worker, daemon=True).start()
    return model_setup_status()


@app.get("/api/v1/omr/status")
def omr_status():
    return omr.engine_status()


@app.get("/api/v1/omr/engines")
def engines():
    return [
        dict(
            id="homr",
            name="HOMR",
            **omr.engine_status(),
            license="AGPL-3.0",
            limitations=[
                "Dynamik und Artikulation nicht klanglich interpretiert",
                "Wiederholungen, Haltebögen und Vorzeichen manuell prüfen",
            ],
        )
    ]


@app.get("/api/v1/backup")
def backup():
    if db.query("SELECT id FROM jobs WHERE status IN ('queued','running')"):
        raise HTTPException(409, "Bitte laufende Erkennungen vor der Sicherung beenden.")
    with tempfile.TemporaryDirectory() as temp:
        import sqlite3

        snapshot = Path(temp) / "notepilot.sqlite3"
        with db.connection() as con, sqlite3.connect(snapshot) as target:
            con.backup(target)
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.write(snapshot, "notepilot.sqlite3")
            for folder in ["originals", "processed", "musicxml"]:
                for path in (DATA / folder).rglob("*"):
                    if path.is_file():
                        archive.write(path, path.relative_to(DATA).as_posix())
            archive.writestr("notepilot-backup.json", json.dumps({"format": 1, "created_at": db.now()}))
        return Response(
            buffer.getvalue(),
            media_type="application/zip",
            headers={"Content-Disposition": 'attachment; filename="notepilot-backup.zip"'},
        )


@app.post("/api/v1/backup/restore")
def restore_backup(file: UploadFile):
    # Restore is deliberately only allowed into an empty library; preserves existing work.
    if pieces() or db.query("SELECT id FROM jobs WHERE status IN ('queued','running')"):
        raise HTTPException(
            409,
            "Wiederherstellung ist nur in einer leeren Bibliothek möglich. Sichere die vorhandenen Stücke zuerst.",
        )
    data = upload_bytes(file)
    import sqlite3

    with zipfile.ZipFile(BytesIO(data)) as archive, tempfile.TemporaryDirectory(dir=DATA / "cache") as temp:
        entries = archive.infolist()
        if len(entries) > 10000 or sum(e.file_size for e in entries) > 512 * 1024 * 1024:
            raise ValueError("Die Sicherung ist zu groß.")
        if "notepilot-backup.json" not in archive.namelist() or "notepilot.sqlite3" not in archive.namelist():
            raise ValueError("Keine NotePilot-Sicherung.")
        manifest = json.loads(archive.read("notepilot-backup.json"))
        if manifest.get("format") != 1:
            raise ValueError("Unbekannte Sicherungsversion.")
        for info in entries:
            path = Path(info.filename)
            if path.is_absolute() or ".." in path.parts or "\\" in info.filename:
                raise ValueError("Unsicherer Pfad in der Sicherung.")
            if info.is_dir():
                continue
            if path.parts[0] not in (
                "originals",
                "processed",
                "musicxml",
                "notepilot.sqlite3",
                "notepilot-backup.json",
            ):
                raise ValueError("Unerwartete Datei in der Sicherung.")
            destination = Path(temp) / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(archive.read(info))
        source_db = sqlite3.connect(f"file:{Path(temp) / 'notepilot.sqlite3'}?mode=ro", uri=True)
        try:
            if source_db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Die Datenbank der Sicherung ist beschädigt.")
            required = {
                "pieces",
                "documents",
                "pages",
                "score_versions",
                "jobs",
                "practice_sections",
                "practice_sessions",
                "settings",
            }
            found = {r[0] for r in source_db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if found != required:
                raise ValueError("Die Sicherung enthält ein unbekanntes Datenbankschema.")
            if source_db.execute(
                "SELECT count(*) FROM sqlite_master WHERE type IN ('trigger','view')"
            ).fetchone()[0]:
                raise ValueError("Die Sicherung enthält unerwartete Datenbankobjekte.")
            with db.connection() as live:
                known_schema = {
                    row[0]: row[1]
                    for row in live.execute("SELECT name,sql FROM sqlite_master WHERE type='table'")
                }
            archived_schema = {
                row[0]: row[1]
                for row in source_db.execute("SELECT name,sql FROM sqlite_master WHERE type='table'")
            }
            if archived_schema != known_schema or source_db.execute("PRAGMA foreign_key_check").fetchall():
                raise ValueError("Das Datenbankschema oder die Verknüpfungen der Sicherung sind ungültig.")
            # Inspect all paths, including those stored in the SQLite file.
            for table, column in [
                ("documents", "path"),
                ("pages", "image_path"),
                ("pages", "processed_path"),
                ("score_versions", "path"),
            ]:
                for (stored,) in source_db.execute(f"SELECT {column} FROM {table}"):
                    if stored:
                        local_path(stored)
                        if not (Path(temp) / stored).is_file():
                            raise ValueError("Eine Datei aus der Sicherung fehlt.")
            for folder in ["originals", "processed", "musicxml"]:
                if (Path(temp) / folder).exists():
                    shutil.copytree(Path(temp) / folder, DATA / folder, dirs_exist_ok=True)
            with db.connection() as con:
                source_db.backup(con)
        finally:
            source_db.close()
    return {"restored": True, "pieces": len(pieces())}


# A production build is served from the same local origin; development uses Vite's API proxy.
if (ROOT / "frontend/dist").is_dir():
    app.mount("/", StaticFiles(directory=ROOT / "frontend/dist", html=True), name="frontend")
