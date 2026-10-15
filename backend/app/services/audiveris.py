"""Audiveris adapter configuration; every inference is local and headless."""

import os
from pathlib import Path

from ..core import ROOT


def installation():
    return Path(
        os.environ.get(
            "NOTEPILOT_AUDIVERIS_DIR",
            "/opt/audiveris" if Path("/opt/audiveris").is_dir() else ROOT / ".audiveris",
        )
    )


def status():
    folder = installation()
    ready = all(
        (folder / name).is_file()
        for name in (
            "bin/Audiveris",
            "lib/app/audiveris.jar",
            "tessdata/eng.traineddata",
            "notepilot-install.json",
        )
    )
    return dict(
        engine="audiveris",
        name="Audiveris",
        installed=ready,
        ready=ready,
        version="5.9.0",
        mode="CPU",
        models=[],
        message="Lokale Erkennung gedruckter Noten bereit."
        if ready
        else "Audiveris ist noch nicht installiert.",
    )


def command(image, data):
    env = os.environ.copy()
    home = data / "audiveris"
    home.mkdir(parents=True, exist_ok=True)
    env.update(
        JAVA_TOOL_OPTIONS=f"-Xmx2g -XX:ActiveProcessorCount=2 -Djava.awt.headless=true -Duser.home={home}",
        XDG_CACHE_HOME=str(home / "cache"),
        XDG_CONFIG_HOME=str(home / "config"),
        TESSDATA_PREFIX=str(installation() / "tessdata"),
    )
    return [
        str(installation() / "bin/Audiveris"),
        "-batch",
        "-transcribe",
        "-export",
        "-output",
        str(image.parent),
        "--",
        str(image),
    ], env
