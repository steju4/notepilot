"""Optional Cloudflare Access origin verification; the local app has no accounts."""

import os
import re
from dataclasses import dataclass

import jwt
from jwt import PyJWKClient


@dataclass
class AccessGate:
    issuer: str
    audience: str
    emails: frozenset[str]
    keys: PyJWKClient

    @classmethod
    def from_environment(cls):
        team = os.environ.get("NOTEPILOT_ACCESS_TEAM_DOMAIN", "").strip().lower()
        audience = os.environ.get("NOTEPILOT_ACCESS_AUD", "").strip()
        emails = frozenset(
            email.strip().lower()
            for email in os.environ.get("NOTEPILOT_ACCESS_EMAILS", "").split(",")
            if email.strip()
        )
        if not any((team, audience, emails)):
            return None
        if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.cloudflareaccess\.com", team):
            raise RuntimeError("Access: den exakten Team-Hostname ohne https:// eintragen.")
        if not audience or not emails or any("@" not in email for email in emails):
            raise RuntimeError("Access: Application AUD und erlaubte E-Mail-Adressen sind erforderlich.")
        issuer = f"https://{team}"
        return cls(
            issuer,
            audience,
            emails,
            PyJWKClient(
                f"{issuer}/cdn-cgi/access/certs",
                timeout=5,
                lifespan=300,
            ),
        )

    def verify(self, token: str):
        # Bound untrusted input before parsing or making a key lookup.
        if not token or len(token) > 16384:
            raise jwt.InvalidTokenError("Missing token")
        header = jwt.get_unverified_header(token)
        if header.get("alg") != "RS256" or not isinstance(header.get("kid"), str):
            raise jwt.InvalidTokenError("Invalid signing header")
        key = self.keys.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            key.key,
            algorithms=["RS256"],
            audience=self.audience,
            issuer=self.issuer,
            options={"require": ["exp", "iat", "iss", "aud", "sub", "type", "email"]},
        )
        if claims["type"] != "app" or str(claims["email"]).lower() not in self.emails:
            raise jwt.InvalidTokenError("User is not allowed")


GATE = AccessGate.from_environment()
