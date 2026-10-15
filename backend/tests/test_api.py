import zipfile
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path

import pytest
from app import api as module
from app import core, db
from app.services import omr
from fastapi.testclient import TestClient
from PIL import Image


@pytest.fixture
def client(tmp_path, monkeypatch):
    for target in (module, core, db, omr):
        monkeypatch.setattr(target, "DATA", tmp_path)
    monkeypatch.setattr(omr, "EXECUTOR", ThreadPoolExecutor(max_workers=1))
    with TestClient(module.app) as client:
        yield client


def create(client):
    response = client.post("/api/v1/pieces", json={"title": "Mein Stück", "instrument": "trumpet"})
    assert response.status_code == 201
    return response.json()["id"]


def xml_file():
    return (Path(__file__).resolve().parents[2] / "examples/abend-am-fluss.musicxml").read_bytes()


def import_score(client, identity):
    response = client.post(
        f"/api/v1/pieces/{identity}/documents",
        files={"file": ("example.musicxml", xml_file(), "application/xml")},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_library_score_correction_versions_export(client):
    identity = create(client)
    detail = import_score(client, identity)
    score = client.get(f"/api/v1/pieces/{identity}/score").json()
    assert score["timeline"][0]["sounding_midi"] == 58
    event = score["timeline"][0]["id"]
    change = {
        "action": "update",
        "event_id": event,
        "version_id": score["version_id"],
        "fields": {"step": "F", "octave": 4, "alter": 1, "type": "quarter", "dots": 0},
    }
    corrected = client.patch(f"/api/v1/pieces/{identity}/score", json=change)
    assert corrected.status_code == 200
    assert corrected.json()["timeline"][0]["sounding_midi"] == 64
    assert client.patch(f"/api/v1/pieces/{identity}/score", json=change).status_code == 409
    versions = client.get(f"/api/v1/pieces/{identity}").json()["versions"]
    assert len(versions) == 2
    reverted = client.post(f"/api/v1/pieces/{identity}/versions/{detail['current_version']}")
    assert reverted.json()["timeline"][0]["written_midi"] == 60
    assert client.get(f"/api/v1/pieces/{identity}/export/musicxml").content.startswith(b"<?xml")
    assert client.get(f"/api/v1/pieces/{identity}/export/midi").content.startswith(b"MThd")
    assert (
        client.patch(
            f"/api/v1/pieces/{identity}", json={"favorite": True, "collection": "Konzert"}
        ).status_code
        == 200
    )
    assert client.get("/api/v1/pieces").json()[0]["favorite"] is True


def test_practice_and_settings_persist(client):
    identity = create(client)
    import_score(client, identity)
    response = client.post(
        f"/api/v1/pieces/{identity}/practice-sections",
        json={"name": "Solo", "start_measure": 2, "end_measure": 3, "settings": {"speed": 0.6, "loop": True}},
    )
    assert response.status_code == 201
    assert client.get(f"/api/v1/pieces/{identity}/practice-sections").json()[0]["settings"]["speed"] == 0.6
    assert (
        client.post(
            f"/api/v1/pieces/{identity}/practice-sections",
            json={"name": "Bad", "start_measure": 3, "end_measure": 8},
        ).status_code
        == 422
    )
    assert client.patch("/api/v1/settings", json={"dark": True}).json() == {"dark": True}
    assert client.get("/api/v1/settings").json()["dark"] is True


def test_photo_import_process_restore(client):
    identity = create(client)
    image = Image.new("RGB", (1000, 1400), "white")
    buffer = BytesIO()
    image.save(buffer, "PNG")
    response = client.post(
        f"/api/v1/pieces/{identity}/documents", files={"file": ("photo.png", buffer.getvalue(), "image/png")}
    )
    assert response.status_code == 201, response.text
    page = response.json()["pages"][0]
    assert page["quality"]["hints"]
    assert client.get(f"/api/v1/pages/{page['id']}/image").status_code == 200
    edited = client.patch(
        f"/api/v1/pages/{page['id']}", json={"options": {"rotate": 90, "contrast": 1.2, "brightness": 10}}
    )
    assert edited.status_code == 200
    assert edited.json()["pages"][0]["processed_path"]
    reset = client.patch(f"/api/v1/pages/{page['id']}", json={"reset": True})
    assert reset.json()["pages"][0]["processed_path"] is None


def test_bad_files_no_partial_documents(client):
    identity = create(client)
    for name, data in [("bad.png", b"not an image"), ("bad.pdf", b"bad pdf"), ("bad.musicxml", b"<bad>")]:
        result = client.post(f"/api/v1/pieces/{identity}/documents", files={"file": (name, data)})
        assert result.status_code == 422, result.text
    assert client.get(f"/api/v1/pieces/{identity}").json()["documents"] == []


def test_missing_model_is_explicit(client, monkeypatch):
    monkeypatch.setenv("NOTEPILOT_AUDIVERIS_DIR", "/does-not-exist")
    monkeypatch.setattr(omr, "OMR_PYTHON", Path("/does-not-exist"))
    assert client.get("/api/v1/omr/status").json()["ready"] is False
    identity = create(client)
    assert client.post(f"/api/v1/pieces/{identity}/recognition").status_code == 422


def test_csrf_and_rebinding_rejected(client):
    assert (
        client.post(
            "/api/v1/pieces", json={"title": "evil"}, headers={"Origin": "https://evil.example"}
        ).status_code
        == 403
    )
    assert client.get("/api/v1/pieces", headers={"Host": "evil.example"}).status_code == 403
    assert (
        client.post(
            "/api/v1/pieces", json={"title": "good"}, headers={"Origin": "http://localhost:5173"}
        ).status_code
        == 403
    )  # testserver is not a dev origin


def test_backup_restore_empty_library(client):
    identity = create(client)
    import_score(client, identity)
    backup = client.get("/api/v1/backup")
    assert backup.status_code == 200
    payload = backup.content
    assert client.post("/api/v1/backup/restore", files={"file": ("backup.zip", payload)}).status_code == 409
    assert client.delete(f"/api/v1/pieces/{identity}").status_code == 204
    response = client.post("/api/v1/backup/restore", files={"file": ("backup.zip", payload)})
    assert response.status_code == 200, response.text
    assert response.json()["pieces"] == 1
    assert client.get(f"/api/v1/pieces/{identity}/score").json()["measure_count"] == 4


def test_backup_traversal(client):
    out = BytesIO()
    with zipfile.ZipFile(out, "w") as archive:
        archive.writestr("notepilot-backup.json", '{"format":1}')
        archive.writestr("notepilot.sqlite3", "bad")
        archive.writestr("../escape.txt", "bad")
    assert (
        client.post("/api/v1/backup/restore", files={"file": ("bad.zip", out.getvalue())}).status_code == 422
    )


def test_multipage_pdf_and_order(client):
    identity = create(client)
    a, b = Image.new("RGB", (700, 900), "white"), Image.new("RGB", (700, 900), "#eeeeee")
    buffer = BytesIO()
    a.save(buffer, "PDF", save_all=True, append_images=[b])
    response = client.post(
        f"/api/v1/pieces/{identity}/documents", files={"file": ("pages.pdf", buffer.getvalue())}
    )
    assert response.status_code == 201, response.text
    pages = response.json()["pages"]
    assert len(pages) == 2
    assert pages[0]["sort_order"] < pages[1]["sort_order"]
    assert client.patch(f"/api/v1/pages/{pages[0]['id']}", json={"excluded": True}).status_code == 200
    assert client.get(f"/api/v1/pieces/{identity}").json()["pages"][0]["excluded"] == 1


def test_duplicate_preserves_originals_and_practice(client):
    identity = create(client)
    import_score(client, identity)
    image = BytesIO()
    Image.new("RGB", (800, 1000), "white").save(image, "PNG")
    uploaded = client.post(
        f"/api/v1/pieces/{identity}/documents", files={"file": ("source.png", image.getvalue())}
    )
    assert uploaded.status_code == 201
    client.post(
        f"/api/v1/pieces/{identity}/practice-sections",
        json={"name": "Solo", "start_measure": 1, "end_measure": 2},
    )
    duplicated = client.post(f"/api/v1/pieces/{identity}/duplicate")
    assert duplicated.status_code == 201, duplicated.text
    target = duplicated.json()["id"]
    detail = client.get(f"/api/v1/pieces/{target}").json()
    assert len(detail["documents"]) == 2
    assert len(detail["pages"]) == 1
    assert client.get(f"/api/v1/pages/{detail['pages'][0]['id']}/image").status_code == 200
    assert client.get(f"/api/v1/pieces/{target}/practice-sections").json()[0]["name"] == "Solo"
    client.delete(f"/api/v1/pieces/{identity}")
    assert client.get(f"/api/v1/pieces/{target}/score").status_code == 200


def test_hosted_preview_requires_explicit_domain(client, monkeypatch):
    assert client.get("/api/v1/runtime").json()["storage_location"] == "local"
    assert client.get("/api/v1/health", headers={"Host": "preview.example"}).status_code == 403
    monkeypatch.setattr(module, "ALLOWED_HOSTS", frozenset({"preview.example"}))
    monkeypatch.setattr(module, "HOSTED_PREVIEW", True)
    assert client.get("/api/v1/runtime", headers={"Host": "preview.example"}).json() == {
        "hosted_preview": True,
        "storage_location": "testserver",
    }
    assert (
        client.post(
            "/api/v1/pieces",
            json={"title": "Online test"},
            headers={"Host": "preview.example", "Origin": "https://preview.example"},
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/api/v1/pieces",
            json={"title": "Wrong origin"},
            headers={"Host": "preview.example", "Origin": "https://evil.example"},
        ).status_code
        == 403
    )
