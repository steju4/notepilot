import time
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import jwt
import pytest
from app import access, api, core, db
from app.services import omr
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient


@pytest.fixture
def protected(tmp_path, monkeypatch):
    for module in (api, core, db, omr):
        monkeypatch.setattr(module, "DATA", tmp_path)
    monkeypatch.setattr(omr, "EXECUTOR", ThreadPoolExecutor(max_workers=1))
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    keys = jwt.PyJWKClient("https://example.cloudflareaccess.com/cdn-cgi/access/certs")
    public = jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key(), as_dict=True)
    public.update(kid="current", alg="RS256", use="sig")
    # Public-key endpoint fixture; JWT parsing, key selection and signature checks are real.
    monkeypatch.setattr(keys, "fetch_data", lambda: {"keys": [public]})
    gate = access.AccessGate(
        "https://example.cloudflareaccess.com", "our-app", frozenset({"owner@example.com"}), keys
    )
    monkeypatch.setattr(access, "GATE", gate)
    monkeypatch.setattr(api, "ALLOWED_HOSTS", frozenset({"notepilot.stengele-home.de"}))
    now = int(time.time())
    claims = dict(
        iss=gate.issuer,
        aud=[gate.audience],
        sub="user-id",
        type="app",
        email="owner@example.com",
        iat=now,
        exp=now + 300,
    )
    with TestClient(api.app, base_url="https://notepilot.stengele-home.de") as client:
        yield SimpleNamespace(client=client, key=key, claims=claims, keys=keys)


def token(p, **changes):
    return jwt.encode(p.claims | changes, p.key, algorithm="RS256", headers={"kid": "current"})


def headers(p, **changes):
    return {"cf-access-jwt-assertion": token(p, **changes)}


@pytest.mark.parametrize(
    "path", ["/", "/icon.svg", "/api/v1/health", "/api/v1/runtime", "/api/v1/pieces", "/api/v1/backup"]
)
def test_every_route_requires_access(protected, path):
    r = protected.client.get(path)
    assert r.status_code == 403
    assert r.headers["cache-control"] == "no-store"
    assert protected.client.post("/api/v1/pieces", json={"title": "hidden"}).status_code == 403
    assert protected.client.get("/api/v1/pieces", headers=headers(protected)).json() == []


def test_valid_login_allows_persistent_workflow(protected):
    p = protected
    r = p.client.get("/api/v1/health", headers=headers(p))
    assert r.status_code == 200 and r.json()["status"] == "ok"
    assert r.headers["cache-control"] == "no-store"
    assert p.client.post("/api/v1/pieces", headers=headers(p), json={"title": "Privat"}).status_code == 201
    assert p.client.get("/api/v1/pieces", headers=headers(p)).json()[0]["title"] == "Privat"


@pytest.mark.parametrize(
    "changes",
    [
        {"aud": "different-app"},
        {"iss": "https://other.cloudflareaccess.com"},
        {"exp": 1},
        {"iat": 4102444800},
        {"email": "stranger@example.com"},
        {"type": "org"},
    ],
)
def test_rejects_invalid_claims(protected, changes):
    assert protected.client.get("/api/v1/pieces", headers=headers(protected, **changes)).status_code == 403


def test_rejects_forged_signature_and_unsigned_token(protected):
    p = protected
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    forged = jwt.encode(p.claims, other, algorithm="RS256", headers={"kid": "current"})
    unsigned = jwt.encode(p.claims, "", algorithm="none", headers={"kid": "current"})
    for value in (forged, unsigned, "broken", "x" * 16385):
        assert p.client.get("/", headers={"cf-access-jwt-assertion": value}).status_code == 403


def test_key_server_failure_fails_closed(protected, monkeypatch):
    def unavailable(*args):
        raise jwt.PyJWKClientConnectionError("No key server")

    monkeypatch.setattr(protected.keys, "fetch_data", unavailable)
    assert protected.client.get("/api/v1/health", headers=headers(protected)).status_code == 403


def test_partial_configuration_never_disables_login(monkeypatch):
    for name in ("TEAM_DOMAIN", "AUD", "EMAILS"):
        monkeypatch.delenv("NOTEPILOT_ACCESS_" + name, raising=False)
    assert access.AccessGate.from_environment() is None
    monkeypatch.setenv("NOTEPILOT_ACCESS_AUD", "our-app")
    with pytest.raises(RuntimeError):
        access.AccessGate.from_environment()
    monkeypatch.setenv("NOTEPILOT_ACCESS_TEAM_DOMAIN", "https://attacker.example")
    monkeypatch.setenv("NOTEPILOT_ACCESS_EMAILS", "owner@example.com")
    with pytest.raises(RuntimeError):
        access.AccessGate.from_environment()
    monkeypatch.setenv("NOTEPILOT_ACCESS_TEAM_DOMAIN", "example.cloudflareaccess.com")
    assert access.AccessGate.from_environment().issuer == "https://example.cloudflareaccess.com"
