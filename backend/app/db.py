import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from uuid import uuid4

from .core import DATA, init_paths


def now():
    return datetime.now(UTC).isoformat()


def uid():
    return uuid4().hex


@contextmanager
def connection():
    con = sqlite3.connect(DATA / "notepilot.sqlite3", timeout=20)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("PRAGMA trusted_schema=OFF")
    try:
        yield con
        con.commit()
    except BaseException:
        con.rollback()
        raise
    finally:
        con.close()


def init_db():
    init_paths()
    with connection() as con:
        con.execute("PRAGMA journal_mode=WAL")
        con.executescript("""
        CREATE TABLE IF NOT EXISTS pieces (
            id TEXT PRIMARY KEY, title TEXT NOT NULL, composer TEXT NOT NULL DEFAULT '',
            instrument TEXT NOT NULL DEFAULT 'piano', notation TEXT NOT NULL DEFAULT 'auto',
            favorite INTEGER NOT NULL DEFAULT 0, collection TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL, last_opened_at TEXT,
            current_version TEXT, playback_settings TEXT NOT NULL DEFAULT '{}'
        );
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY, piece_id TEXT NOT NULL REFERENCES pieces(id) ON DELETE CASCADE,
            filename TEXT NOT NULL, file_type TEXT NOT NULL, path TEXT NOT NULL,
            page_count INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS pages (
            id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            piece_id TEXT NOT NULL REFERENCES pieces(id) ON DELETE CASCADE,
            page_number INTEGER NOT NULL, sort_order INTEGER NOT NULL, image_path TEXT NOT NULL,
            processed_path TEXT, quality TEXT NOT NULL, excluded INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS score_versions (
            id TEXT PRIMARY KEY, piece_id TEXT NOT NULL REFERENCES pieces(id) ON DELETE CASCADE,
            sequence INTEGER NOT NULL, path TEXT NOT NULL, source TEXT NOT NULL, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY, piece_id TEXT NOT NULL REFERENCES pieces(id) ON DELETE CASCADE,
            engine TEXT NOT NULL, status TEXT NOT NULL, stage TEXT NOT NULL,
            created_at TEXT NOT NULL, started_at TEXT, finished_at TEXT,
            error TEXT, details TEXT NOT NULL DEFAULT '{}'
        );
        CREATE TABLE IF NOT EXISTS practice_sections (
            id TEXT PRIMARY KEY, piece_id TEXT NOT NULL REFERENCES pieces(id) ON DELETE CASCADE,
            name TEXT NOT NULL, start_measure INTEGER NOT NULL, end_measure INTEGER NOT NULL,
            settings TEXT NOT NULL, notes TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS practice_sessions (
            id TEXT PRIMARY KEY, piece_id TEXT NOT NULL REFERENCES pieces(id) ON DELETE CASCADE,
            duration REAL NOT NULL, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        """)
        con.execute(
            "UPDATE jobs SET status='failed',stage='Unterbrochen',error='Der Server wurde während der Erkennung beendet.',finished_at=? WHERE status IN ('queued','running')",
            (now(),),
        )


def query(sql, args=(), one=False):
    with connection() as con:
        rows = con.execute(sql, args).fetchall()
    result = [dict(r) for r in rows]
    return (result[0] if result else None) if one else result


def execute(sql, args=()):
    with connection() as con:
        con.execute(sql, args)


def piece_row(row):
    if not row:
        return None
    row["favorite"] = bool(row["favorite"])
    row["playback_settings"] = json.loads(row["playback_settings"])
    return row
