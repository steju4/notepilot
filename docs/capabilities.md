# Fähigkeiten und bekannte Grenzen

Erkennung, Speicherung, Darstellung und Klang sind verschiedene Fähigkeiten. Kein Ergebnis wird als fehlerfrei bezeichnet; kein Konfidenzwert wird erfunden.

| Notation | MusicXML lesen/speichern | Darstellung | Wiedergabe | HOMR-Fotogenauigkeit |
|---|---|---|---|---|
| Tonhöhen, Kreuze/Bes/Naturals | ja | ja | ja | Kreuze/Bes in Referenzen korrekt; Auflösungszeichen im Corpus teilweise übersehen |
| Tonarten bis ±7 Vorzeichen | ja | ja | ja | prüfen; separater Corpusbericht |
| Violinschlüssel/Bassschlüssel | ja | ja | Tonhöhe aus XML | primäre Engine-Zielschlüssel |
| Alt-/Tenorschlüssel, Schlüsselwechsel | ja | ja | Tonhöhe aus XML | nicht als zuverlässig versprochen |
| Viertel/Achtel/Sechzehntel/Punktierungen | ja | ja | ja | Referenz- und Musikmodelltests |
| Pausen und Taktarten | ja | ja | ja | Ausgabe musikalisch prüfen |
| Tuplets | ja | ja | explizite MusicXML-Dauern | Engine-Ausgabe prüfen |
| Haltebogen vs. Bindebogen | ja | ja | Tie gehalten, Slur ohne Klangwirkung | manuell prüfbar |
| Einfache Wiederholungen / erste und zweite Endung | ja | ja | ja | kann fehlen; manuell ergänzen |
| Verschachtelte Wiederholungen | bewahrt | ja | nicht vollständig abgesichert | keine Genauigkeitszusage |
| D.C., D.S., Coda, Fine | bewahrt | je nach OSMD | keine automatische Sprungausführung, Warnung | manuell zu üben |
| Dynamik, Artikulation, Crescendo, Fermate | bewahrt | je nach OSMD | keine expressive Interpretation | nicht garantiert |
| Vorschlagnoten | bewahrt | ja | ausgelassen, Warnung | nicht garantiert |
| Schlagwerk / Mikrotonalität | bewahrt | eingeschränkt je nach OSMD | unbestimmte/mikrotonale Töne ausgelassen | nicht integriert |
| Doppelkreuze/-bes | importierbar und korrigierbar | ja | ja | laut HOMR-Einschränkungen nicht zuverlässig |

## Absichtlich transparent

- Konkreter HOMR-0.7-Befund: Im Auflösungszeichen-Referenzbild werden zwei Naturals übersehen und vier Noten falsch ausgegeben. Das ist ein Modellfehler, kein bestandener Genauigkeitstest. Vergleichsansicht und manuelle Vorzeichenkorrektur sind die funktionierende Abhilfe.
- Instrumentprofile bestimmen Transposition und MIDI-Programm. Browserklänge sind Synthese mit einfachen Wellenformen, keine echten Instrumentensamples. Es gibt keine externen Sample-Downloads während der Wiedergabe.
- GPU-Modus, Audiveris und oemer sind keine implementierten Auswahloptionen. Die produktive Engine ist HOMR 0.7.0 / CPU; keine bezahlte API oder eigenes Training nötig.
- Einzähler und Metronom verwenden den Taktart-Nenner; bei 6/8 entspricht der Grundschlag einer Achtel. Eine separate punktierte-Viertel-Betonung ist noch nicht konfigurierbar.
- Kameraaufnahme nutzt `capture=environment` der Dateiauswahl. Eine Live-Kamera mit getUserMedia ist nicht implementiert.
- Zuschneiden ist über Prozentfelder möglich. Perspektive verwendet vier geklickte Punkte. Die Vorschau von Helligkeit/Kontrast ist angenähert; endgültige Pixelkorrektur erfolgt auf dem Backend. Keine behauptete automatische Erkennung abgeschnittener Notensysteme.
- Bildhinweise beruhen auf messbaren Schärfe-, Helligkeits-, Auflösungs- und Schräglagewerten; sie sind heuristisch und keine Erkennungskonfidenz.
- Notenlängenänderungen können einen Takt unvollständig oder überfüllt machen. Die Prüfung zeigt das; sie erfindet keine fehlenden Noten.
- Mehrseitige Erkennung hängt von konsistenten Stimmenzahlen ab. Aus unabhängig fotografierten Stimmen entsteht keine automatische Ensemble-Synchronisierung.
- PWA/Offline funktionieren für bereits geöffnete digitale Stücke. Der Browser führt HOMR nicht selbst aus. Fotos, neue Erkennung, MIDI-Export und dauerhaftes Speichern benötigen den Computer.
- Sicherungswiederherstellung nimmt nur leere Bibliotheken an; Sicherung maximal 40 MB Upload/512 MB entpackt. Große Bibliotheken können direkt über den Datenordner gesichert werden.
- PDF-/WAV-/MP3-Export, Mikrofonanalyse und automatisches Mitlesen sind nicht implementiert. MIDI und MusicXML sind implementiert.
- Linux/Python 3.12/Node 24/Chromium und Docker unter Linux x86_64 wurden praktisch geprüft: echter CPU-OMR-Job, dauerhafte SQLite-Bibliothek, Neustart und Access-Token-Schutz. Windows und ARM wurden nicht ausgeführt. Cloudflare-Tunnel/Access auf dem tatsächlichen Homeserver müssen vom Betreiber eingerichtet und extern geprüft werden; dafür liegt ein separates [Deployment-Profil](../deploy/README.md) vor.

Der [Projektauftrag](requirements.md) bleibt die Produktvision. Diese Liste und der [Testbericht](validation.md) beschreiben den tatsächlich gelieferten Stand; sie erklären keine noch offenen Fähigkeiten für abgeschlossen.
