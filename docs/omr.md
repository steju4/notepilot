# HOMR: geprüfte lokale Einrichtung

## Version und Ausführung

Primärengine: [liebharc/homr](https://github.com/liebharc/homr), PyPI **0.7.0**, CPU mit ONNX Runtime. Python 3.11/3.12. Die README des aktuellen Hauptbranches nennt `uvx --from 'homr[cpu]' homr <image>`. Das wurde praktisch untersucht: Version 0.7.0 installiert kein Extra namens `cpu`; ihre Basisabhängigkeit `onnxruntime` enthält bereits die CPU-Engine. Die CLI akzeptiert ein einzelnes Bild oder ein Verzeichnis; wir starten sie einzeln pro Seite. `--init` lädt Modelle. Verzeichnis-/Mehrbildparameter neuerer Versionen werden nicht ungeprüft übernommen.

```sh
python scripts/setup_omr.py
.venv/bin/python scripts/verify_omr.py
.venv/bin/python scripts/verify_omr.py --corpus --report data/omr-testbericht.json
```

`verify_omr.py` führt das installierte Modell tatsächlich in einem separaten Prozess aus. Die Referenzpartitur ist keine Ersatzdatei für die Ausgabe: Die neu erzeugte MusicXML-Datei wird gelesen und ihre Tonhöhen, Dauern, Taktart, Tonart und Taktzahl werden mit der Referenz verglichen. Bei Abweichungen ist der Exitcode 1. Nicht nur Dateierzeugung wird geprüft.

## Gewichte und Platzbedarf

Quelle: `https://github.com/liebharc/homr/releases/tag/onnx_checkpoints`. Das Modell-Setup verwendet HOMRs Downloader mit TLS-Prüfung. CPU-Modelle:

| Modell | Version | Bytes |
|---|---|---:|
| Segmentierung | segnet_308-3296ccd40960f90ca6ab9c035cca945675d30a0f | 57.311.361 |
| Transformer Encoder | pytorch_model_396-f6feedb42ff90087d898b0941a55d040fa6b2903 | 52.861.122 |
| Transformer Decoder | pytorch_model_396-f6feedb42ff90087d898b0941a55d040fa6b2903 | 47.299.551 |

Zusammen 157.472.034 Bytes, etwa 150 MiB. RapidOCR für Titel verwendet seine mitgelieferten Modelle; Titelqualität ist von Notenqualität getrennt. Python-Abhängigkeiten sind mit Versions- und SHA-256-Locks fixiert. Die Setup-Prüfung lädt ONNX-Dateien lokal, anschließend wird ein SHA-256-Manifest unter `data/models/manifest.json` gespeichert. Dieses prüft spätere lokale Veränderungen; es ist **keine Signatur des Modellherausgebers**. Abweichende lokale Gewichte werden beim Setup erneut aus der Herkunftsquelle bezogen.

## Offline und Ressourcen

Die Engine arbeitet mit lokalen PNG-Dateien und MusicXML. Im normalen Inferenzrunner werden Requests-/urllib-HTTP-Anfragen blockiert; nur explizites `--init` darf herunterladen. Damit fehlende Gewichte nicht unbemerkt eine Online-Abhängigkeit erzeugen, wird vor der Erkennung die lokale Integrität geprüft. CPU ist fest gewählt. Maximal ein Job gleichzeitig; native ONNX-Session-Threads maximal vier. Keine NVIDIA-GPU erforderlich. Virtueller Adressraum wird nicht pauschal begrenzt, weil ONNX große Arenen reserviert; Laufzeit ist pro Seite begrenzt.

## Erweiterbarkeit

`recognize_score(input_document, options)` liefert Engine, Version, Modus, reale Dauer und geparste tatsächliche Ausgabe. Weitere Engines können diese Schnittstelle implementieren. Audiveris/oemer wurden als Alternativen recherchiert; sie sind nicht integriert und nicht im UI als nutzbar dargestellt. Ein Vergleich oder eine automatische Kombination von Engines wird nicht behauptet.

## Lizenzen

HOMR-Code und veröffentlichte Gewichte sind laut Projekt AGPL-3.0. Das [HOMR LICENSE_FAQ](https://github.com/liebharc/homr/blob/main/LICENSE_FAQ.md) weist auf Trainingsdatenfragen hin. Checkpoint 396 enthält OpenScore Lieder/StringQuartets (CC0), GrandStaff (am Originaldownload keine klare Lizenz, eine Kopie MIT) und PrIMuS (CC BY-NC 4.0 auf der genannten Kopie). AGPL gewährt keine zusätzlichen Rechte an Trainingsdaten. Dieses Projekt ist als private lokale Anwendung ausgelegt; keine pauschale Zusage für kommerzielle Nutzung der Gewichte. Siehe [LICENSES.md](../LICENSES.md).
