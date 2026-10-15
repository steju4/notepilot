# Prüfbericht

Getestete Umgebung: Linux x86_64, Python 3.12.14, Node 24.19.0, npm 11.9.0, Chromium; 15. Oktober 2026. Die Cloud dient der Entwicklung. Die fertige Anwendung braucht lokal keinen Cloud-Dienst.

## Tatsächlich ausgeführte Prüfungen

- Python-Installation nach SHA-256-Requirements, Node `npm ci`, Produktionsbuild und wiederholbare lokale Modellinstallation mit `scripts/install.py --omr --dev`.
- **79 Backend-Tests bestanden.** Backend-Tests: SQLite-Bibliothek, Import, Versionshistorie, konkurrierende Korrektur mit veralteter Version, Speichern, MusicXML/MIDI, Bildbearbeitung, zweitseitiges PDF, MXL, Duplikate einschließlich Originale/Passagen, Backup/Wiederherstellung und fremde Origin/Host-Anfragen.
- Musikreferenzen: C-/G-/F-Dur, lokale Kreuze/Bes/Naturals, oktavspezifische Vorzeichenwirkung und Rücksetzung, Punktierung/Achtel/Sechzehntel, Pausen/Taktpausen, 3/4 und 6/8, Triolen, Tie/Slur, Wiederholung und erste/zweite Endung, Mehrseitigkeit, Schlüssel-/Tonartwechsel, Stimmen/Akkorde und MIDI. Festgelegte Instrumenttranspositionen und Vermeidung doppelter MusicXML-Transposition.
- **13 Frontend-Tests bestanden (6 Zeitachse, 4 Hosting-Zugriff/Cache, 3 Sample-MIDI).** Frontend-Zeitachse: Pausenposition, Geschwindigkeitsänderung ohne Tonhöhenänderung, Tempoänderung während gehaltener Note, Ties über Takte und Abschnittsgrenzen, 6/8-Einzähler und deutsche H/B-Anzeige.
- **4 Playwright-Abläufe bestanden.** Playwright auf Desktop und Pixel-7-Viewport: echte MusicXML-Datei importieren, SVG zeichnen, Note auswählen und Vorzeichen korrigieren, Undo/Redo, B♭-Trompete, Wiedergabe/Pause/Stop, Web-Audio-Signal größer als Null, Tempo/Passage speichern und wieder öffnen, MIDI/MusicXML-Export, kein horizontaler Seitenüberlauf. Vollständig offline geschalteter Browser lädt PWA und gecachte Partitur, Wiedergabe funktioniert. Keine JavaScript-Laufzeitfehler im getesteten Ablauf.
- Echter End-to-End-OMR-API-Job: Notenbild hochladen → Hintergrundprozess → MusicXML → Referenzvergleich; 16/16 Tonhöhen und Dauern korrekt. Beispiel wurde mit Originalbild lokal behalten.
- Zusätzlich echtes externes Notenbild (`oemer/figures/tabi.jpg`) auf CPU verarbeitet: 28 Takte, 346 klingende Ereignisse. Das beweist Verarbeitung, **nicht** deren musikalische Fehlerfreiheit; kein handgeprüfter Referenzvergleich für dieses externe Stück.
- Beide Compose-Konfigurationen geprüft. Homeserver-Image unter Linux x86_64 mit vorinstallierten HOMR-Gewichten gebaut: echter Foto-Upload → CPU-OMR → 16/16 Referenz-Tonhöhen/Dauern → MIDI-Export. Bibliothek und Partitur nach Container-Neustart erhalten. Betrieb als UID 10001 mit entfernten Linux-Capabilities, CPU-/RAM-Limit und no-new-privileges geprüft. Windows/ARM nicht ausgeführt.
- Basic Auth im Backend: fehlende/falsche/richtige Zugangsdaten für Oberfläche, API und statische Datei; Schutz von Originalbildern, MusicXML/MIDI und Backup; HEAD/OPTIONS/Range und beschädigte Auth-Header. Ungeschützte Anfragen liefern 401 mit `WWW-Authenticate: Basic realm="NotePilot", charset="UTF-8"` und `no-store`. Nach Anmeldung bleiben Host-/Origin-Prüfungen aktiv. UTF-8-Benutzernamen und Passwörter mit Doppelpunkt wurden geprüft.
- Secret-Erstellung: gesalzener scrypt-Hash, kein Klartextpasswort in Datei, Modus 0600, ausdrückliches atomisches Ersetzen. Fehlende/ungültige Konfiguration wird in Tests und beim tatsächlichen Containerstart abgelehnt. Laufzeit-Secret und entfernte JWT-Abhängigkeit sind nicht im Image enthalten.
- Neues Homeserver-Profil unter 2 CPUs/4 GiB praktisch gestartet: Secret mit UID 10001 schreibgeschützt gemountet, Healthcheck bestanden. Authentifizierter echter Foto-OMR-Job liefert 16/16 Referenznoten mit korrekten Dauern. Originalbild, MusicXML/MIDI und Backup ohne/falsch 401, richtig 200. `compose down` ohne `-v` und erneutes `up` erhalten die Partitur im Datenvolume. Das unveränderte Deployment-Profil veröffentlicht keinen Host-Port; ausschließlich die Testkonfiguration verwendete einen Loopback-Port.
- Zwei Browserprüfungen des Basic-Auth-Containers (1440px/393px): ohne Zugangsdaten 401-Challenge; Browser-Credentials erlauben die Oberfläche. Kein Abmeldelink, keine Offline-Service-Worker-/Cache-/IndexedDB-Partituren, keine JavaScript-Laufzeitfehler. Die native Dialogdarstellung und der tatsächliche Cloudflare-Tunnel/HTTPS-Host müssen vom Betreiber im Browser geprüft werden.

## Korrekturen vom 15. Oktober 2026

- Vor der Korrektur drei gezielte Regressionen nachgewiesen: HOMRs `<notations><tied>` wurde nicht gehalten; kurze Folgetakte bekamen unsichtbare Auffüllpausen; eine Ganz­taktpause ohne duration hatte eine falsche Länge. Alle drei Tests bestehen jetzt. Mehrere Stimmen behalten eine gemeinsame Taktgrenze anhand der längsten tatsächlich notierten Stimme.
- MIDI wird ohne pauschale Notenverkürzung im AudioWorklet geplant. Neue MIDI-Tests prüfen gleiche Zeitpunkte für Note-off/Note-on an einer Taktgrenze sowie einen einzigen Anschlag für eine gehaltene Phrase und erhaltene echte Pausen.
- Zwei zusätzliche Desktop-/Handy-Prüfungen messen den tatsächlich erzeugten Sample-Klang: kein Nullsignal um die geprüften Taktgrenzen bei gebundenen Tenorhornnoten. Die bisherigen zwei Import-/Editor-/Audio-/Offline-Abläufe bestehen weiterhin. Lokales PWA-Precache enthält die Samplebank; der Hosted-Build bleibt ohne Offlinecache.
- Gehosteter Produktionsbuild hinter echtem Backend-Basic-Auth geprüft: Samplebank/Worklet geben Klang aus, Pause/Fortsetzen funktioniert, Samplebank ohne Login 401, keine Offline-Caches. Der Test läuft lokal mit temporären Zugangsdaten, nicht auf dem Homeserver.
- Audiveris 5.9.0: **8/8** Referenzbilder bestehen für Tonhöhen, Dauern, Taktzahl, Taktart und Tonart. Bericht: [audiveris-corpus-results.json](audiveris-corpus-results.json). Die Auflösungszeichen-Referenz wird korrekt erkannt. Eigenständiger echter API-Job: hochgeladenes Referenzbild → Audiveris → 15/15 Vorzeichennoten und Dauern korrekt, Tenorhorn-B-Transposition korrekt. Kein handgeprüftes Ergebnis des konkreten Nutzerfotos verfügbar.
- **Neuer Dockerbuild nicht abgeschlossen:** Diese Cloud-Instanz lief mit `no space left on device` voll. Bereinigung der eigenen alten Test-Images/Buildcaches gibt den verbleibenden Docker-Speicher nicht ausreichend frei. Java-/OCR-Installation und Frontend-Build liefen im Build durch; ein finaler Container-/4-GiB-Lauf der neuen Version ist hier deshalb nicht verifiziert. Die oben beschriebenen Containerprüfungen stammen von der vorherigen Basic-Auth-Version. Ein eigener CI-Job baut das neue Homeserver-Image und führt die Vorzeichen-Erkennung mit gesperrtem Netzwerk und 2 CPUs/4 GiB aus; dessen Ergebnis wird erst nach Ausführung beurteilt.

## Bild-Corpus mit echter KI

Ausgeführt mit:

```sh
.venv/bin/python scripts/verify_omr.py --corpus --report docs/omr-corpus-results.json
```

Die Bilder sind eigens komponierte und mit Verovio gerenderte Noten. Schräge/dunkle Varianten sind synthetische Aufnahmebedingungen, keine behaupteten Smartphone-Fotos. Erwartete MusicXML-Dateien enthalten sichtbare Auflösungszeichen und Triolenklammern; Referenzen werden von der Engine nie überschrieben. Der Runner verwendet einen temporären Ausgabeordner und HTTP ist in der Inferenz gesperrt.

| Referenz | Tonhöhen/Dauern | Taktzahl, Tonart und Taktart | Ergebnis |
|---|---:|---|---|
| C-Dur / Abend am Fluss | 16/16 | korrekt | bestanden |
| F-Dur | 15/15 | korrekt | bestanden |
| G-Dur | 15/15 | korrekt | bestanden |
| Punktierung, Achtel, Pausen, 3/4 | 12/12 | korrekt | bestanden |
| Triolen und 6/8 | 15/15 | korrekt | bestanden |
| Lokale Vorzeichen und Auflösungszeichen | 11/15 | korrekt | **fehlgeschlagen** |
| Um 3° gedreht | 16/16 | korrekt | bestanden |
| Helligkeit auf 65 % | 16/16 | korrekt | bestanden |

**Der gesamte Corpus-Befehl endet deshalb korrekt mit Exitcode 1.** Zwei sichtbare Auflösungszeichen werden von HOMR 0.7.0 nicht umgesetzt; vier Noten bleiben fälschlich erhöht/erniedrigt. Die tatsächliche Engine-Ausgabe ist unter `examples/recognized/vorzeichen-homr.musicxml` abgelegt. Dies ist eine diagnostizierte Modellgrenze. Es wird weder die Referenz angepasst noch eine richtige Ersatzpartitur anstelle der Erkennung ausgegeben. Nutzer müssen diese Stellen am Original prüfen und können sie im Editor korrigieren. Testreport enthält alle Einzelwerte, keine erfundene Konfidenz.

## Reproduzierbarkeit und Grenzen

Ein Testsatz mit wenigen übersichtlichen Noten ersetzt keinen breiten OMR-Benchmark. Handschrift, komplexe Fotos, verschachtelte Wiederholungen, schwierige Mehrstimmigkeit oder alle Artikulationen sind damit nicht abgesichert. Kein Anspruch auf fehlerfreie Notenerkennung.

Testdatenbanken der automatisierten API-/Browsertests sind temporär. Musikmodelltests verwenden überprüfbare Referenzdaten. Die Anwendung zeigt Erkennungsausgaben und tatsächliche Warnungen; eine fehlgeschlagene Erkennung erzeugt keine Demodaten. Aktuelle Testzahlen und letzte Kommandoergebnisse stehen im Abschlussbericht und in CI; der Corpusbericht ist versioniert.

Screenshots der ausgeführten Oberfläche: [Dashboard](screenshots/dashboard.png) und [mobiler Player](screenshots/player-mobile.png). Diese zeigen tatsächliche lokale Daten bzw. den eindeutig benannten Browser-Test, keine simulierte Erkennung.
