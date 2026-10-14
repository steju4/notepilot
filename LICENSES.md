# Lizenzen und Herkunft

NotePilot-Quellcode in diesem Repository: **AGPL-3.0-or-later**, vollständiger Text in [LICENSE](LICENSE). Die selbst erstellte Melodie „Abend am Fluss“ und die eigenen musikalischen Referenzen unter `examples/` können unter **CC0-1.0** verwendet werden. Erkennungsausgaben werden ausdrücklich als generierte Ergebnisse gekennzeichnet, nicht als von Hand geprüfte Kompositionen außer im jeweiligen Referenzvergleich.

## Wesentliche Komponenten

| Komponente | Lizenz / Herkunft |
|---|---|
| React, TypeScript, Vite, FastAPI, Tone.js, Mido | MIT |
| OpenSheetMusicDisplay | BSD-3-Clause |
| lucide-react | ISC |
| Vite PWA Plugin | MIT; Workbox Apache-2.0 |
| SQLite | Public Domain |
| OpenCV | Apache-2.0 |
| NumPy, music21 | BSD-3-Clause |
| Pillow | HPND/PIL-Lizenz |
| defusedxml | Python Software Foundation License |
| pypdfium2 / PDFium | Apache-2.0 / BSD-artige PDFium- und Drittkomponentenlizenzen |
| ONNX Runtime | MIT |
| HOMR 0.7.0 | AGPL-3.0, als separater lokaler Prozess |
| HOMR-ONNX-Gewichte | laut Projekt AGPL; Trainingsdatenbedingungen separat beachten |
| RapidOCR / Modelle | Apache-2.0 laut Projekt, lokale mitgelieferte Modellartefakte |
| Verovio / CairoSVG (nur Referenzbilderzeugung) | LGPL-3.0 / LGPL-3.0 |
| Playwright, Vitest (Entwicklung) | Apache-2.0 / MIT |

Konkrete installierte Versionen stehen in den Python-SHA-256-Requirements und `frontend/package-lock.json`. Original-Lizenztexte verbleiben in installierten Paketen; diese Übersicht ersetzt keine Drittanbieter-Lizenztexte. Zur Weitergabe müssen diese Texte und geltende Quellcodepflichten erhalten bleiben.

## Modellgewichte

Quelle: [HOMR ONNX checkpoints](https://github.com/liebharc/homr/releases/tag/onnx_checkpoints), Segmentierung 308 und Transformer 396. Eine lokale SHA-256-Aufstellung wird während der Einrichtung gespeichert. Das stellt lokale Integrität fest, nicht die Lizenzierung der Trainingsdaten.

[HOMR LICENSE_FAQ](https://github.com/liebharc/homr/blob/main/LICENSE_FAQ.md) nennt für ältere Checkpoints wie 396 unter anderem:

- OpenScore Lieder und StringQuartets: CC0.
- GrandStaff: am Originaldownload keine angegebene Lizenz; eine verlinkte Kopie nennt MIT.
- Camera-PrIMuS/PrIMuS: am Originaldownload keine klare Lizenz; eine verlinkte Kopie nennt CC BY-NC 4.0.
- Segmentierung DeepScoresV2: CC BY 4.0 laut Datensatzquelle.

Die private kostenlose Nutzung ist der Projektzweck. Eine kommerzielle Freigabe aller Modell-/Trainingsdatenrechte wird nicht behauptet. Änderungen und Weitergabe von AGPL-Komponenten müssen die jeweiligen Lizenzbedingungen erfüllen.

## Klang und Notenbilder

Es werden keine externen SoundFonts oder Instrumentensamples eingebunden. Audio ist lokale Tone.js-Synthese. Daher gibt es keine unklar lizenzierten Sample-Downloads. Die eigene Beispielpartitur wird als Beispiel ausgewählt, nie als angebliches Foto-Erkennungsergebnis verwendet.

Zum ersten unabhängigen Integrationsversuch wurde das öffentlich zugängliche `figures/tabi.jpg` aus [BreezeWhite/oemer](https://github.com/BreezeWhite/oemer) temporär geladen und lokal erkannt. Das Bild und diese externe Musik wurden nicht in dieses Repository übernommen.
