import base64
import json
import secrets
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import pytest
from app import access, api, core, db
from app.services import omr
from fastapi.testclient import TestClient
from PIL import Image


@pytest.fixture(scope="module")
def credentials():
    password = secrets.token_urlsafe(24) + ":ä"
    return {"username": "privat-ü", "password_hash": access.make_password_hash(password)}, password


@pytest.fixture
def protected(tmp_path, monkeypatch, credentials):
    config, password = credentials
    filename = tmp_path / "auth.json"
    filename.write_text(json.dumps(config), encoding="utf-8")
    monkeypatch.setattr(access, "GATE", access.BasicAuthGate.from_file(filename))
    for module in (api, core, db, omr):
        monkeypatch.setattr(module, "DATA", tmp_path)
    monkeypatch.setattr(omr, "EXECUTOR", ThreadPoolExecutor(max_workers=1))
    monkeypatch.setattr(api, "ALLOWED_HOSTS", frozenset({"notepilot.stengele-home.de"}))
    with TestClient(api.app, base_url="https://notepilot.stengele-home.de") as client:
        yield SimpleNamespace(client=client, user=config["username"], password=password)


def headers(p, username=None, password=None):
    raw = f"{p.user if username is None else username}:{p.password if password is None else password}"
    return {"Authorization": "Basic " + base64.b64encode(raw.encode("utf-8")).decode("ascii")}


def challenge(response):
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == access.CHALLENGE
    assert response.headers["Cache-Control"] == "no-store"


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/icon.svg",
        "/audio/TimGM6mb.sf2",
        "/api/v1/health",
        "/api/v1/runtime",
        "/api/v1/pieces",
        "/api/v1/backup",
        "/missing",
    ],
)
def test_missing_wrong_and_correct_credentials(protected, path):
    p = protected
    challenge(p.client.get(path))
    challenge(p.client.get(path, headers=headers(p, password="incorrect")))
    challenge(p.client.get(path, headers=headers(p, username="stranger")))
    response = p.client.get(path, headers=headers(p))
    assert response.status_code == (404 if path == "/missing" else 200)
    assert response.headers["Cache-Control"] == "no-store"
    assert "WWW-Authenticate" not in response.headers


def test_protected_mutations_originals_and_downloads(protected):
    p = protected
    challenge(p.client.post("/api/v1/pieces", json={"title": "Hidden"}))
    identity = p.client.post("/api/v1/pieces", headers=headers(p), json={"title": "Privat"}).json()["id"]
    xml = (Path(__file__).resolve().parents[2] / "examples/abend-am-fluss.musicxml").read_bytes()
    p.client.post(
        f"/api/v1/pieces/{identity}/documents",
        headers=headers(p),
        files={"file": ("notes.musicxml", xml, "application/xml")},
    ).raise_for_status()
    buffer = BytesIO()
    Image.new("RGB", (100, 100), "white").save(buffer, "PNG")
    result = p.client.post(
        f"/api/v1/pieces/{identity}/documents",
        headers=headers(p),
        files={"file": ("notes.png", buffer.getvalue(), "image/png")},
    )
    result.raise_for_status()
    page = p.client.get(f"/api/v1/pieces/{identity}", headers=headers(p)).json()["pages"][0]["id"]
    paths = [
        f"/api/v1/pages/{page}/image",
        f"/api/v1/pieces/{identity}/export/musicxml",
        f"/api/v1/pieces/{identity}/export/midi",
        "/api/v1/backup",
    ]
    for path in paths:
        challenge(p.client.get(path))
        challenge(p.client.get(path, headers=headers(p, password="wrong")))
        response = p.client.get(path, headers=headers(p))
        assert response.status_code == 200 and response.content
        assert response.headers["Cache-Control"] == "no-store"
    challenge(p.client.head("/icon.svg"))
    challenge(p.client.options("/api/v1/pieces"))
    challenge(p.client.get(paths[0], headers={"Range": "bytes=0-30"}))
    assert len(p.client.get("/api/v1/pieces", headers=headers(p)).json()) == 1


@pytest.mark.parametrize(
    "authorization",
    ["Bearer token", "Basic !invalid!", "Basic Og==", "Basic bm8tY29sb24=", "Basic /w==", "x" * 8193],
)
def test_malformed_headers_are_challenged(protected, authorization):
    challenge(protected.client.get("/", headers={"Authorization": authorization}))


def test_host_origin_checks_and_no_store_remain(protected):
    p = protected
    assert p.client.get("/api/v1/health", headers=headers(p) | {"Host": "foreign.example"}).status_code == 403
    response = p.client.post(
        "/api/v1/pieces",
        headers=headers(p) | {"Origin": "https://foreign.example"},
        json={"title": "Blocked"},
    )
    assert response.status_code == 403 and response.headers["Cache-Control"] == "no-store"
    response = p.client.post(
        "/api/v1/pieces",
        headers=headers(p) | {"Origin": "https://notepilot.stengele-home.de"},
        json={"title": "Allowed"},
    )
    assert response.status_code == 201


@pytest.mark.parametrize(
    "value",
    [
        None,
        "not-json",
        "{}",
        '{"username":"a","password":"plaintext"}',
        '{"username":"a","password_hash":"scrypt$999999999$8$3$x$x"}',
        '{"username":"a:b","password_hash":"invalid"}',
        "[1,2]",
    ],
)
def test_invalid_or_missing_secret_refuses_start(tmp_path, monkeypatch, value):
    monkeypatch.setenv("NOTEPILOT_REQUIRE_AUTH", "1")
    monkeypatch.delenv("NOTEPILOT_BASIC_AUTH_FILE", raising=False)
    with pytest.raises(RuntimeError):
        access.BasicAuthGate.from_environment()
    filename = tmp_path / "invalid.json"
    if value is not None:
        filename.write_text(value)
    monkeypatch.setenv("NOTEPILOT_BASIC_AUTH_FILE", str(filename))
    with pytest.raises(RuntimeError):
        access.BasicAuthGate.from_environment()


def test_optional_local_mode_and_valid_secret(tmp_path, monkeypatch, credentials):
    for name in ("NOTEPILOT_REQUIRE_AUTH", "NOTEPILOT_BASIC_AUTH_FILE"):
        monkeypatch.delenv(name, raising=False)
    assert access.BasicAuthGate.from_environment() is None
    config, _ = credentials
    filename = tmp_path / "valid.json"
    filename.write_text(json.dumps(config))
    monkeypatch.setenv("NOTEPILOT_REQUIRE_AUTH", "1")
    monkeypatch.setenv("NOTEPILOT_BASIC_AUTH_FILE", str(filename))
    assert access.BasicAuthGate.from_environment() is not None
    monkeypatch.setenv("NOTEPILOT_REQUIRE_AUTH", "yes")
    with pytest.raises(RuntimeError):
        access.BasicAuthGate.from_environment()


def test_legacy_access_configuration_cannot_silently_open_server(monkeypatch):
    monkeypatch.setenv("NOTEPILOT_ACCESS_AUD", "old-config")
    with pytest.raises(RuntimeError):
        access.BasicAuthGate.from_environment()


def test_secret_creator_never_stores_plaintext_and_requires_explicit_replace(
    tmp_path, monkeypatch, credentials
):
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "create_auth", Path(__file__).resolve().parents[2] / "scripts/create_basic_auth.py"
    )
    creator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(creator)
    destination = tmp_path / "basic-auth.json"
    _, password = credentials
    monkeypatch.setattr("builtins.input", lambda _: "owner")
    monkeypatch.setattr(creator.getpass, "getpass", lambda _: password)
    monkeypatch.setattr(creator.sys, "argv", ["create", "--output", str(destination)])
    creator.main()
    content = destination.read_text()
    assert password not in content and '"password"' not in content
    assert destination.stat().st_mode & 0o777 == 0o600
    gate = access.BasicAuthGate.from_file(destination)
    p = SimpleNamespace(user="owner", password=password)
    assert gate.verify(headers(p)["Authorization"])
    with pytest.raises(SystemExit):
        creator.main()
    monkeypatch.setattr(creator.sys, "argv", ["create", "--output", str(destination), "--replace"])
    creator.main()
    assert destination.read_text() != content
