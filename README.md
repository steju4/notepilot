# NotePilot

**Dein digitaler Musik- und Übungspartner.** Gedruckte Noten lokal mit HOMR erkennen, MusicXML prüfen und korrigieren, Melodien anhören und schwierige Passagen üben. Ohne Konten, Cloud-Datenbank oder kostenpflichtige KI-API.

## Schnellstart

Voraussetzungen: **Python 3.11 oder 3.12**, **Node.js 22.12+ (getestet: 24.19)** und npm. Für die Erstinstallation ist Internet nötig. Anschließend laufen MusicXML, Audio und eingerichtete CPU-Erkennung lokal.

```sh
# Im Repository-Verzeichnis:
python scripts/install.py --omr
python scripts/start.py
```

Windows: `py -3.12 scripts/install.py --omr`, danach `start-windows.bat`.
Linux: `python3 scripts/install.py --omr`, danach `./start-linux.sh`.

Die Startausgabe nennt die lokale Adresse (Port 8000). Die gebaute Oberfläche wird vom Python-Dienst ausgeliefert; kein zweiter Server ist im normalen Betrieb erforderlich. **Der Computer muss für Erkennung und Datenbankzugriff eingeschaltet bleiben.**

Ohne `--omr` ist die Anwendung bereits mit MusicXML nutzbar. Das KI-Modell kann später unter **Einstellungen → Lokales KI-Modell einrichten** oder mit `python scripts/setup_omr.py` installiert werden. Standard: CPU. Drei ONNX-Modelle benötigen zusammen etwa **150 MiB**; Python-Pakete benötigen weiteren Speicher. Ein Erkennungsprozess läuft gleichzeitig.

## Was du nutzen kannst

- Deutsche, responsive Oberfläche, Light/Dark Mode, installierbare PWA.
- JPG, PNG, WebP und PDF, mehrere Seiten; direktes MusicXML/MXL ohne KI.
- Kameraaufnahme über die native Dateiauswahl des Smartphones.
- Bildqualität prüfen, zuschneiden, drehen, ausrichten, Kontrast/Helligkeit, Schwarz-Weiß und vierpunktige Perspektivkorrektur; Original bleibt erhalten.
- Echte HOMR-0.7.0-CPU-Erkennung als Hintergrundjob, mit Status, Abbruch und Zeitlimit. Keine Ersatzpartitur bei Fehlern.
- Digitale Partitur mit OpenSheetMusicDisplay, Original und Vergleich; anklickbare Noten, Zoom und aktuelle Notenfarbe während der Wiedergabe.
- Ton/Oktave/Vorzeichen, Notenwert, Punktierung und Haltebogen ändern; Note/Pause einfügen oder entfernen. Tonart, Taktart, Schlüssel, Wiederholung und Klammern bearbeiten.
- Versionshistorie mit Undo/Redo; ursprüngliches Erkennungsergebnis bleibt als Version erhalten.
- Tone.js-Audio, Pause/Fortsetzen/Stop, Tempo, Lautstärke, Referenzton; notierte und klingende Tonhöhen werden getrennt.
- 25 Instrumentprofile, einschließlich B♭-Trompete, Klarinette, E♭-Altsaxophon, Tenorsaxophon und F-Horn. MusicXML-Transposition wird im automatischen Modus nicht doppelt angewendet.
- Taktauswahl, A-B-Loops, Anzahl Durchläufe, Pausen, Metronom, Einzähler, Unterteilung, automatische Temposteigerung und gespeicherte Passagen.
- Lokale SQLite-Bibliothek, Suche, Sortierung, Favoriten, Duplikat und Metadaten.
- MusicXML- und MIDI-Export; MIDI verwendet klingende Tonhöhen und die expandierte Abspielreihenfolge.
- Bibliothek als ZIP sichern und in eine leere Bibliothek wiederherstellen.
- Bereits geöffnete Stücke im IndexedDB-Cache; Offline-Anzeige und synthetische Wiedergabe auch ohne Backend. Änderungen/Erkennung brauchen das Backend.

**Klänge sind lokale Synthesizer, keine realistischen Instrumentensamples.** Erkennung ist fehlbar. Die Fähigkeit, ein Symbol aus MusicXML zu speichern und abzuspielen, bedeutet nicht, dass HOMR es zuverlässig aus Fotos erkennt. Siehe [Fähigkeiten und Grenzen](docs/capabilities.md).

## Entwicklung

```sh
python scripts/install.py --omr --dev
# Terminal 1:
.venv/bin/python -m uvicorn app.api:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
# Terminal 2:
cd frontend
npm run dev
```

Windows: `.venv\Scripts\python.exe` statt `.venv/bin/python`. Vite läuft auf Port 5173 und leitet `/api` an Port 8000 weiter.

```sh
# Entwicklungs-Prüfwerkzeuge:
.venv/bin/python -m pip install -e 'backend[test]'
.venv/bin/python -m pytest backend/tests -q
.venv/bin/ruff check --config ruff.toml backend scripts
npm --prefix frontend test
npm --prefix frontend run build
npm --prefix frontend run test:e2e
# Echter CPU-Test nach Modellinstallation:
.venv/bin/python scripts/verify_omr.py
```

Playwright verwendet `/usr/bin/chromium`, wenn vorhanden, sonst den von Playwright installierten Chromium-Browser (`cd frontend && npx playwright install chromium`). Browsertests starten einen eigenen Server mit temporärer SQLite-Bibliothek. Sie verändern keine Nutzerdaten. Weitere Ergebnisse und reproduzierbare Prüfungen: [Testbericht](docs/validation.md).

## Smartphone und LAN

```sh
python scripts/start.py --lan
```

Die private IP des Computers auf Port 8000 im Smartphone-Browser öffnen. Nur im vertrauenswürdigen WLAN verwenden und per Firewall auf dieses Netz begrenzen; keine Router-Portweiterleitung. Standardmäßig bindet NotePilot ausschließlich an Loopback. LAN bedeutet gemeinsame Bibliothek ohne Konten. Fremde Web-Origin-Anfragen und DNS-Rebinding-Hostnamen werden abgelehnt. Die native Foto-Dateiauswahl funktioniert auch dort, wo Live-Kamerazugriff wegen fehlendem HTTPS nicht verfügbar ist. PWA-Installation/Service Worker benötigen einen sicheren Browserkontext (localhost oder HTTPS).

## Lokale Daten

Standard: `data/` im Repository, von Git ausgeschlossen. Anpassbar über die exportierte Variable `NOTEPILOT_DATA_DIR`. Weitere Optionen stehen in `.env.example`; diese Datei wird **nicht automatisch geladen**.

```
data/
  notepilot.sqlite3       Metadaten, Einstellungen, Jobs und Passagen
  originals/             Originaldateien und gerenderte PDF-Seiten
  processed/             Bildkorrekturen
  musicxml/              Alle Partiturversionen
  models/                ONNX-Gewichte und lokales Integritätsmanifest
  cache/                 Temporäre Erkennungseingaben (nach Jobs entfernt)
  logs/                  Lokale Erkennungs- und Installationsprotokolle
```

Musikdateien und Einstellungen werden nicht an externe Dienste übertragen. Modell-/Paketdownloads erfolgen nur zur Einrichtung. Im Inferenzadapter sind HTTP-Anfragen gesperrt; fehlende Gewichte ergeben einen Fehler. Sicherungen enthalten die Bibliothek einschließlich Metadaten und Übungsdaten, keine Modellgewichte. Vor Wiederherstellung eine eigene Sicherung anlegen; aus Sicherheitsgründen ist sie nur in eine leere Bibliothek möglich. Browsercache separat unter Browser-Websitedaten löschen.

## Optional: Docker

```sh
docker compose up --build
```

Ein lokales Volume hält Datenbank, Dokumente, Modelle und Cache. Die lokale Portbindung bleibt `127.0.0.1:8000`. Nach dem Start unter Einstellungen das KI-Modell einrichten. Das Container-Image wurde unter Linux x86_64 gebaut und mit echter CPU-Erkennung, SQLite und einem Neustart praktisch geprüft.

Für deinen **Homeserver mit Cloudflare Tunnel und nginx Proxy Manager** gibt es ein eigenes Profil mit vorinstallierten Modellen, dauerhaftem Datenvolume und HTTP-Basic-Auth im Backend. Es veröffentlicht keinen Host-Port und prüft Benutzername und scrypt-Passwort-Hash aus einer gemounteten Secret-Datei. Die Online-Version nutzt keinen Offline-Partiturcache. **[Vollständige Einrichtung mit SSH-Befehlen](deploy/README.md)** · [Konfigurationsvorlage](deploy/.env.example).

## Architektur und Lizenzen

[Architektur](docs/architecture.md) · [OMR-Einrichtung](docs/omr.md) · [Fähigkeiten/Grenzen](docs/capabilities.md) · [Tests](docs/validation.md) · [Lizenzen](LICENSES.md) · [Projektauftrag](docs/requirements.md)

NotePilot-Code: AGPL-3.0-or-later. HOMR läuft als getrennter lokaler Prozess und ist AGPL-3.0; Gewichte und Trainingsdaten haben gesondert dokumentierte Herkunfts- und Nutzungsbedingungen. Keine pauschale Freigabe für kommerzielle Modellnutzung. Die eigene Beispielmelodie und Referenzbilder sind CC0.

Ein konkreter Genauigkeitshinweis: Im erweiterten OMR-Corpus bestehen sieben von acht Bildern. HOMR übersieht in der Auflösungszeichen-Referenz zwei Zeichen; vier Noten brauchen manuelle Korrektur. Der Corpus-Test bleibt deshalb fehlgeschlagen und wird nicht als bestandener Test dargestellt.
