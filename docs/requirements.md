# MASTER-PROMPT: NotePilot – Vollständige KI-gestützte Anwendung zur Erkennung, Wiedergabe und zum Üben von Musiknoten

## 0. DEINE ROLLE UND DEIN AUFTRAG

Du bist ein erfahrenes Team aus Full-Stack-Entwicklern, Softwarearchitekten, KI-/Computer-Vision-Entwicklern, Musiksoftware-Experten, UI/UX-Designern und Testingenieuren.

Deine Aufgabe ist die vollständige Konzeption und tatsächliche Entwicklung einer funktionsfähigen, hochwertigen Anwendung namens **NotePilot – Dein digitaler Musik- und Übungspartner**.

Die Anwendung soll insbesondere Musikern in Musikvereinen ermöglichen, gedruckte Noten mit ihrem Smartphone zu fotografieren, einzuscannen oder als PDF hochzuladen, anschließend mithilfe eines **kostenlosen, lokal ausgeführten KI-Modells automatisch erkennen zu lassen** und schließlich mit dem Klang ihres Instruments wiederzugeben.

Die Anwendung soll nicht nur Tonhöhen erkennen, sondern die Notenschrift musikalisch korrekt interpretieren. Dazu gehören ausdrücklich Vorzeichen, Tonarten, Taktarten, Pausen, Notenwerte, Punktierungen, Haltebögen, Wiederholungszeichen und weitere musikalische Symbole.

Entwickle eine reale Anwendung, nicht nur ein visuelles Konzept, eine Landingpage oder einen Prototyp mit simulierten Funktionen.

### Verbindliche Rahmenbedingungen

- Die Anwendung ist ein privat nutzbares, eigenständiges Softwareprojekt.
- Sie benötigt keinerlei Benutzerregistrierung.
- Es gibt keine Benutzerkonten und keine Anmeldung.
- Es wird keine Cloud-Datenbank verwendet.
- Sämtliche Musikstücke, Einstellungen, Erkennungsergebnisse und Übungsdaten werden lokal gespeichert.
- Die KI-Notenerkennung wird vollständig lokal ausgeführt.
- Es dürfen keine kostenpflichtigen KI-APIs erforderlich sein.
- Das Kernprodukt muss ohne laufende Kosten nutzbar sein.
- Die KI-Modelle müssen mit kostenlos verfügbaren, vortrainierten Gewichten nutzbar sein.
- Ein eigenes Training von KI-Modellen darf keine Voraussetzung sein.
- Die Anwendung soll auf gewöhnlicher PC-Hardware ausführbar sein.
- Eine GPU darf die Verarbeitung beschleunigen, muss aber optional bleiben.
- Für die Notenerkennung muss mindestens eine echte Open-Source-KI-Lösung integriert werden.
- Die Anwendung darf niemals so tun, als seien Noten erfolgreich erkannt worden, obwohl nur Demodaten verwendet werden.
- Für die gesamte Entwicklung sind möglichst ausgereifte, kostenlose Open-Source-Technologien zu verwenden.

Die Anwendung soll über eine moderne Weboberfläche bedient werden, während ein lokaler Python-Dienst die aufwendige Bildverarbeitung und KI-Inferenz übernimmt.

Auf dem Smartphone soll die Oberfläche möglichst komfortabel über das lokale Netzwerk erreichbar sein können, sofern der Computer mit dem Backend eingeschaltet ist.

Die erste lauffähige Version soll unter Windows und Linux entwickelt beziehungsweise betrieben werden können. Docker soll als optionale, unkomplizierte Startmöglichkeit unterstützt werden.

---

# 1. PRODUKTVISION

## 1.1 Problemstellung

Viele Musiker in Musikvereinen bekommen regelmäßig neue Notenblätter.

Nicht jeder Musiker kann sich eine unbekannte Melodie allein durch das Lesen der Noten vorstellen.

Besonders schwierig sind:

- unbekannte Melodien;
- komplizierte Rhythmen;
- ungewohnte Tonarten;
- viele Vorzeichen;
- schnelle Läufe;
- Synkopen;
- punktierte Rhythmen;
- Triolen;
- längere Pausen;
- Wiederholungen und musikalische Sprünge;
- schwierige Solopassagen.

Die Anwendung soll ermöglichen, eine entsprechende Stimme ohne Vorbereitung hörbar zu machen.

Der Musiker soll die erkannte Melodie mit der tatsächlichen Rhythmik hören und bei Bedarf einzelne Stellen wiederholt und langsamer abspielen können.

## 1.2 Zentraler Benutzerablauf

Der typische Ablauf soll folgendermaßen aussehen:

1. Anwendung öffnen.
2. „Noten hinzufügen“ auswählen.
3. Ein Notenblatt fotografieren oder eine Datei hochladen.
4. Fotoqualität automatisch prüfen lassen.
5. Falls erforderlich, Foto zuschneiden oder korrigieren.
6. Lokale KI-Notenerkennung starten.
7. Erkannte Noten überprüfen.
8. Das passende Instrument auswählen.
9. Wiedergabe starten.
10. Einzelne Takte oder Passagen üben.
11. Stück lokal speichern und später erneut öffnen.

Dieser Workflow muss möglichst einfach, selbsterklärend und zuverlässig funktionieren.

## 1.3 Zielgruppe

Hauptzielgruppe sind Musiker in:

- Musikvereinen;
- Blasorchestern;
- Jugendkapellen;
- Stadtkapellen;
- Schulorchestern;
- kleinen Ensembles.

Die Anwendung soll auch von Musikschülern und Hobbymusikern verwendet werden können.

## 1.4 Produktqualität

Die Anwendung soll sich wie ein hochwertiges, fertig entwickeltes Produkt anfühlen.

Insbesondere:

- intuitiv;
- modern;
- mobiloptimiert;
- schnell;
- übersichtlich;
- musikalisch korrekt;
- technisch zuverlässig;
- ohne komplizierte Einrichtung für die normale Nutzung.

---

# 2. TECHNISCHER GRUNDAUFBAU

Verwende vorzugsweise folgende Technologien:

**Frontend**

- React;
- TypeScript;
- Vite;
- Tailwind CSS;
- moderne, zugängliche UI-Komponenten;
- OpenSheetMusicDisplay für digitale Noten;
- Tone.js für Audiowiedergabe;
- PWA-Unterstützung.

**Backend**

- Python 3.11 oder 3.12;
- FastAPI;
- Pydantic;
- OpenCV;
- Pillow;
- music21;
- lokale OMR-/KI-Engine;
- Hintergrundverarbeitung für Erkennungsaufträge.

**Speicherung**

- SQLite;
- lokaler Dateispeicher;
- optional IndexedDB für Browser-Caching;
- keine Cloud-Datenbank.

**KI**

- HOMR als bevorzugte KI-Engine;
- Audiveris als ergänzende Engine;
- oemer als mögliche Alternative;
- lokale CPU-Inferenz;
- optionale GPU-Beschleunigung.

**Betrieb**

- lokaler Entwicklungs- und Anwendungsserver;
- optionale Docker-Compose-Konfiguration;
- keine verpflichtenden externen Dienste.

Verwende andere Technologien, falls diese nachweislich besser geeignet sind. Dokumentiere solche Entscheidungen kurz.

---

# 3. VERBINDLICHE KI-NOTENERKENNUNG

Dies ist der technisch wichtigste Bestandteil der Anwendung.

Die Notenerkennung muss durch ein tatsächlich vorhandenes und ausführbares KI-Modell erfolgen.

Es genügt ausdrücklich nicht, einen gewöhnlichen OCR-Dienst für gedruckte Texte einzusetzen. Musiknotation benötigt spezialisierte Optical Music Recognition (OMR).

## 3.1 Bevorzugte KI-Engine: HOMR

Repository:

https://github.com/liebharc/homr

Dokumentation und Paket:

https://pypi.org/project/homr/

HOMR soll zunächst als primäre Notenerkennungsengine untersucht und integriert werden.

Die Engine verwendet eine mehrstufige KI-Pipeline:

1. Bildsegmentierung mithilfe neuronaler Netze.
2. Erkennung von Notensystemen und musikalischen Strukturen.
3. Perspektivische Aufbereitung erkannter Notensysteme.
4. Transformer-basierte Erkennung musikalischer Symbolfolgen.
5. Umwandlung in MusicXML.

HOMR kombiniert unter anderem U-Net-basierte Segmentierung mit einem Transformer-Verfahren, das auf Polyphonic-TrOMR aufbaut.

Das Modell ist für fotografierte und eingescannte Noten geeignet.

### Installation

Prüfe die aktuelle Dokumentation der tatsächlich verwendeten Version.

Beispiel einer CPU-Ausführung:

`uvx --from 'homr[cpu]' homr notenblatt.png`

Prüfe diesen Befehl praktisch.

Verlasse dich nicht darauf, dass alle veröffentlichten Versionsstände dieselben Parameter unterstützen.

Erstelle einen gekapselten Adapter, der:

- die Verfügbarkeit des Programms prüft;
- die benötigten Modellgewichte initialisiert;
- Eingabedateien übergibt;
- den Erkennungsprozess startet;
- den Prozess überwacht;
- Fehler verarbeitet;
- die erzeugte MusicXML-Datei einliest;
- das Ergebnis validiert;
- die erkannten Noten an die Anwendung zurückliefert.

Die Ausführung darf nicht durch einen künstlichen Platzhalter ersetzt werden.

## 3.2 Lokale Modellgewichte

Die KI muss ohne laufende API-Kosten funktionieren.

Prüfe und dokumentiere:

- Herkunft der Modellgewichte;
- tatsächliche Verfügbarkeit;
- Lizenz;
- Speicherbedarf;
- notwendige Abhängigkeiten;
- Inferenz auf CPU;
- optionale GPU-Unterstützung.

Falls vortrainierte Gewichte beim ersten Start heruntergeladen werden, soll ein verständlicher Einrichtungsprozess dafür existieren.

Beispiel:

„Das KI-Modell wird für die lokale Notenerkennung eingerichtet. Dieser Download ist nur für die erstmalige Einrichtung erforderlich.“

Nach vollständiger Installation der benötigten Komponenten muss die Inferenz ohne Internetverbindung funktionieren.

Nutze einen lokalen Modell-Cache.

Vermeide unnötige wiederholte Downloads.

## 3.3 CPU als Standard

Die Anwendung muss die KI-Erkennung grundsätzlich auch ohne NVIDIA-GPU ausführen können.

Eine längere Bearbeitungsdauer ist akzeptabel.

Der Benutzer muss erkennen können, dass die Verarbeitung noch läuft.

Unterstütze nach Möglichkeit:

- CPU-Inferenz als Standard;
- NVIDIA CUDA bei vorhandener kompatibler Hardware;
- weitere Beschleuniger nur bei tatsächlich unterstützter Umgebung.

Die Anwendung soll die Möglichkeiten der Laufzeitumgebung erkennen und einen passenden Inferenzmodus wählen.

Falls GPU-Treiber oder notwendige Bibliotheken fehlen, soll auf CPU zurückgefallen werden.

## 3.4 Alternative KI-Engine: oemer

Repository:

https://github.com/BreezeWhite/oemer

oemer ist eine weitere lokale OMR-Lösung, die neuronale Netze und ONNX Runtime verwendet und MusicXML erzeugen kann.

Nutze sie als mögliche Alternative.

Beispiel einer Installation:

`pip install oemer`

Die Integration soll nur erfolgen, wenn sie in der tatsächlichen Entwicklungsumgebung zuverlässig lauffähig ist.

Prüfe insbesondere Abhängigkeiten und CPU-Unterstützung.

## 3.5 Ergänzende Engine: Audiveris

Repository:

https://github.com/Audiveris/audiveris

Dokumentation:

https://audiveris.github.io/audiveris/

Audiveris soll als alternative oder ergänzende OMR-Engine berücksichtigt werden.

Audiveris verwendet eine Kombination aus:

- klassischer Bildverarbeitung;
- Symbolanalyse;
- neuronalen Netzen;
- musikalischer Strukturinterpretation.

Es verfügt zudem über Funktionen zur Korrektur erkannter Musiknotation.

Audiveris kann über eine Kommandozeilenschnittstelle im Batch-Modus betrieben werden.

Überprüfe die tatsächlich dokumentierten CLI-Optionen für automatisierte Verarbeitung und MusicXML-Export.

## 3.6 Bevorzugte Gesamtstrategie

Setze folgende Architektur um:

**Primär: HOMR**

Für die KI-gestützte Erkennung gedruckter Noten und die automatische MusicXML-Erzeugung.

**Sekundär: Audiveris**

Als ergänzendes Verfahren, insbesondere für schwierigere Notation oder Fälle, in denen HOMR relevante Informationen nicht richtig erfasst.

**Optional: oemer**

Als zusätzliche Engine, falls sie einen konkreten technischen Vorteil bietet.

Die Anwendung soll nicht zwingend alle drei Engines gleichzeitig ausführen.

Wichtig ist aber eine austauschbare und erweiterbare Architektur.

Erstelle eine gemeinsame Schnittstelle:

`recognize_score(input_document, options) -> RecognitionResult`

Sie soll unabhängig von der verwendeten Engine dieselben grundlegenden Informationen bereitstellen.

## 3.7 Keine unrealistischen Versprechen

Eine Open-Source-Engine wird nicht garantiert jede musikalische Notation korrekt erkennen.

Insbesondere HOMR hat Einschränkungen bei bestimmten Symbolen.

Deshalb gilt:

- Alle unterstützten Symbolkategorien müssen genau dokumentiert sein.
- Nicht unterstützte Elemente müssen gekennzeichnet werden.
- Die Anwendung muss manuelle Korrekturen ermöglichen.
- Falls sinnvoll, soll die ergänzende Engine verwendet werden.
- Fehlende Zeichen dürfen nicht einfach erfunden werden.
- Mehrere unterschiedliche Ergebnisse dürfen nicht ohne nachvollziehbare Regeln kombiniert werden.

Wichtig ist die bestmögliche praktische Notenerkennung, nicht die Behauptung einer unrealistischen Fehlerfreiheit.

---

# 4. ERKENNUNG MUSIKALISCHER ZEICHEN

Die Anwendung muss die Musik als vollständige Notation verstehen und nicht nur einzelne Notenköpfe lokalisieren.

Insbesondere Vorzeichen und Rhythmusinformationen sind für die korrekte Wiedergabe entscheidend.

## 4.1 Notensysteme

Erkenne:

- die fünf Notenlinien;
- einzelne Notensysteme;
- Positionen der Notenlinien;
- Abstände zwischen Notenlinien;
- zusätzliche Hilfslinien;
- Systemanfang und Systemende;
- Anordnung mehrerer Zeilen;
- Systemreihenfolge;
- Taktstriche;
- Seitenwechsel.

Die Tonhöhe muss aus der Position relativ zum gültigen Notenschlüssel bestimmt werden.

## 4.2 Notenschlüssel

Mindestens:

- Violinschlüssel;
- Bassschlüssel.

Zusätzlich, soweit möglich:

- Altschlüssel;
- Tenorschlüssel;
- Percussion-Schlüssel.

Notenschlüsselwechsel innerhalb eines Stücks müssen vom internen Datenmodell unterstützt werden.

Nicht sicher erkannte Notenschlüssel sind als kritisch zu behandeln, da dadurch sämtliche folgenden Tonhöhen falsch interpretiert werden können.

## 4.3 Tonarten

Erkenne die Vorzeichen am Anfang einer Notenzeile beziehungsweise bei einem Tonartwechsel.

Mindestens die üblichen Tonarten mit bis zu sieben Kreuzen oder sieben Bes.

Die Anwendung muss verstehen, dass diese Vorzeichen grundsätzlich für die entsprechenden Tonklassen gelten.

Beispiele:

- G-Dur: Fis;
- D-Dur: Fis und Cis;
- F-Dur: B;
- B-Dur: B und Es;
- Es-Dur: B, Es und As.

Die Zuordnung muss auch bei instrumentenspezifischen Transpositionen korrekt bleiben.

## 4.4 Einzelne Versetzungszeichen

Besonders hohe Priorität haben:

- Kreuz (♯);
- Be (♭);
- Auflösungszeichen (♮).

Soweit möglich zusätzlich:

- Doppelkreuz;
- Doppelbe.

Wichtig:

Das System muss zwischen einem Tonartvorzeichen und einem direkt vor einer Note stehenden Versetzungszeichen unterscheiden.

Ein Versetzungszeichen wirkt nach den relevanten Notationsregeln innerhalb des Takts und muss korrekt interpretiert werden.

Beim folgenden Takt wird die gültige Vorzeichenwirkung entsprechend den musikalischen Regeln zurückgesetzt.

Berücksichtige auch Haltebögen über Taktgrenzen hinweg.

### Konkretes Beispiel

Ein Stück ist in C-Dur.

Im ersten Takt steht vor einer F-Note ein Kreuz.

Diese Note muss als Fis erklingen.

Eine weitere F-Note derselben Oktave im selben Takt erhält entsprechend der üblichen Notationsregeln ebenfalls diese Tonhöhenänderung, sofern kein anderes Vorzeichen eingreift.

Im nächsten Takt gilt wieder F, sofern dort keine neue Änderung vorliegt.

Diese Logik muss korrekt umgesetzt und automatisiert getestet werden.

## 4.5 Notenwerte

Erkenne mindestens:

- Ganze;
- Halbe;
- Viertel;
- Achtel;
- Sechzehntel;
- möglichst Zweiunddreißigstel.

Zusätzlich:

- Punktierungen;
- doppelte Punktierungen, soweit unterstützt;
- Balkenverbindungen;
- einzelne Fähnchen.

Ein punktierter Notenwert muss die korrekte Dauer besitzen.

## 4.6 Pausen

Erkenne die entsprechenden Pausensymbole.

Mindestens:

- Ganze Pause;
- Halbe Pause;
- Viertelpause;
- Achtelpause;
- Sechzehntelpause;
- punktierte Pausen.

Unterscheide ganze Taktpausen von Pausenzeichen mit einem konkret notierten Zeitwert.

## 4.7 Taktarten

Erkenne beispielsweise:

- 2/4;
- 3/4;
- 4/4;
- 6/8;
- 9/8;
- 12/8;
- 2/2;
- C;
- Alla breve.

Berücksichtige Taktartwechsel innerhalb eines Stückes.

Unterscheide Notenwerte, metrische Betonung und gegebenenfalls die zusammengesetzte Zählweise.

## 4.8 Rhythmische Besonderheiten

Unterstütze nach Möglichkeit:

- Triolen;
- andere einfache Tuplets;
- Synkopen;
- übergebundene Noten;
- Auftakte;
- unvollständige Schlusstakte.

Die Audioengine muss die entsprechenden Notendauern korrekt interpretieren.

## 4.9 Haltebögen und Bindebögen

Unterscheide:

**Haltebogen (Tie):**

Verbindet zwei Noten gleicher Tonhöhe zu einem verlängerten Klang.

**Bindebogen (Slur):**

Kennzeichnet die musikalische Artikulation einer Passage.

Beide Symbole dürfen nicht gleichgesetzt werden.

Mindestens Haltebögen müssen für die Wiedergabe korrekt verarbeitet werden.

## 4.10 Wiederholungszeichen

Erkenne, soweit möglich:

- Wiederholungsanfang;
- Wiederholungsende;
- erste Klammer;
- zweite Klammer.

Bereite Unterstützung vor für:

- Da Capo;
- Dal Segno;
- Fine;
- Coda.

Die Erkennungsengine kann einzelne dieser Zeichen möglicherweise nicht zuverlässig liefern.

In solchen Fällen muss das System eine Warnung ausgeben und eine manuelle Ergänzung erlauben.

## 4.11 Weitere musikalische Zeichen

Berücksichtige, soweit die technische Unterstützung vorhanden ist:

- Staccato;
- Tenuto;
- Akzent;
- Marcato;
- Fermate;
- Triller;
- Vorschlagnoten;
- Crescendo;
- Decrescendo;
- Pianissimo;
- Piano;
- Mezzoforte;
- Forte;
- Fortissimo;
- Tempoangaben;
- Ritardando;
- Accelerando;
- Taktzahlen;
- Probenbuchstaben.

Die Anwendung muss unterscheiden, ob ein Zeichen:

1. erkannt wird;
2. korrekt gespeichert wird;
3. sichtbar gerendert wird;
4. die Audiowiedergabe beeinflusst.

Eine erkannte Dynamikangabe muss nicht automatisch in der ersten Version hörbar interpretiert werden.

Entscheidend ist, dass die Anwendung ihre tatsächlichen Fähigkeiten transparent behandelt.

---

# 5. INTELLIGENTE ERGEBNISPRÜFUNG

Nach der KI-Erkennung soll nicht einfach blind das generierte MusicXML abgespielt werden.

Implementiere eine zusätzliche musikalische Validierung.

## 5.1 Taktprüfung

Berechne die Gesamtdauer der erkannten Ereignisse je Takt und Stimme.

Prüfe, ob diese zur Taktart passt.

Berücksichtige legitime Ausnahmen.

Beispiel:

Ein gewöhnlicher 4/4-Takt enthält versehentlich fünf Viertelnoten.

Das System soll diese Auffälligkeit markieren.

## 5.2 Vorzeichenprüfung

Prüfe:

- gültige Vorzeichen;
- Konsistenz mit der Tonart;
- gültige Reihenfolge von Tonartwechseln;
- korrekte Zuordnung zur Note;
- sinnvolle interne Tonhöhenwerte.

Ein ungewöhnlicher Ton darf nicht allein deshalb als falsch markiert werden, weil er nicht zur Tonleiter gehört.

Chromatik und ungewöhnliche Harmonien sind musikalisch erlaubt.

## 5.3 Rhythmusprüfung

Prüfe:

- Noten- und Pausendauern;
- Tuplets;
- Haltebögen;
- überlappende Ereignisse;
- unvollständige Takte;
- Mehrstimmigkeit.

## 5.4 Erkennungswarnungen

Erstelle Warnungen wie:

- „Möglicherweise falsches Vorzeichen“
- „Notenwerte passen nicht zur Taktart“
- „Taktstrich möglicherweise falsch erkannt“
- „Notenschlüssel prüfen“
- „Wiederholungszeichen möglicherweise nicht erkannt“
- „Nicht unterstütztes musikalisches Symbol“

Verwende echte Analyseergebnisse.

Keine künstlichen oder erfundenen Konfidenzwerte.

## 5.5 Zweite Erkennungsengine

Wenn eine Erkennung auffällig ist, soll optional eine erneute Erkennung mit Audiveris möglich sein.

Zeige unterschiedliche Ergebnisse übersichtlich an.

Biete die Möglichkeit, das bessere Ergebnis auszuwählen.

Eine automatische Kombination unterschiedlicher Erkennungsergebnisse darf nur erfolgen, wenn deren Noten, Takte und Positionen zuverlässig zugeordnet werden können.

---

# 6. BILDIMPORT UND KAMERAFUNKTION

## 6.1 Dateiformate

Unterstütze:

- JPG/JPEG;
- PNG;
- WebP;
- PDF;
- MusicXML;
- MXL;
- optional MIDI.

MusicXML-Dateien benötigen keine KI-Erkennung.

## 6.2 Smartphone-Kamera

Erstelle eine mobile Aufnahmefunktion.

Ermögliche:

- Kamera öffnen;
- Foto aufnehmen;
- Vorschau;
- erneut fotografieren;
- weitere Seite aufnehmen;
- Seiten sortieren;
- Seiten entfernen.

Nutze standardisierte Browserfunktionen.

Wenn eine direkte Kameraansicht nicht unterstützt wird, muss das fotografische Hochladen über die Dateiauswahl funktionieren.

Beachte, dass direkte Browser-Kamerazugriffe im lokalen Netzwerk je nach Browser HTTPS beziehungsweise einen sicheren Kontext benötigen.

## 6.3 Bildbearbeitung

Implementiere:

- Zuschneiden;
- Drehen;
- Ausrichten;
- Kontrast;
- Helligkeit;
- Schwarz-Weiß-Optimierung;
- perspektivische Entzerrung.

Der Benutzer muss das Originalbild immer wiederherstellen können.

## 6.4 Automatische Qualitätsanalyse

Prüfe:

- Unschärfe;
- Schräglage;
- schlechte Beleuchtung;
- Schatten;
- zu kleine Notensysteme;
- abgeschnittene Ränder;
- niedrige Auflösung.

Zeige konkrete Hinweise.

## 6.5 Mehrseitige Stücke

Unterstütze:

- mehrere Fotos;
- mehrseitige PDFs;
- Seitenreihenfolge;
- Seitennavigation;
- Zusammenführung erkannter Musikdaten.

Die Zusammenführung darf keine falschen Taktnummern oder fehlerhafte Notenreihenfolgen erzeugen.

---

# 7. KI-VERARBEITUNGSPIPELINE

Der gesamte Verarbeitungsvorgang soll klar strukturiert sein.

## Schritt 1: Import

Datei empfangen, validieren und lokal speichern.

## Schritt 2: Vorverarbeitung

Bei Bedarf:

- PDF-Seiten rendern;
- Bildauflösung anpassen;
- Rauschen reduzieren;
- Perspektive korrigieren;
- Notenbereich erkennen;
- Schräglage korrigieren.

## Schritt 3: KI-Inferenz

HOMR oder die ausgewählte andere lokale Engine ausführen.

## Schritt 4: MusicXML

Das tatsächlich von der Engine erzeugte MusicXML einlesen.

## Schritt 5: Validierung

Musikalische Struktur kontrollieren.

## Schritt 6: Datenmodell

Noten, Pausen, Takte und sonstige Ereignisse in ein konsistentes internes Modell übertragen.

## Schritt 7: Darstellung

Digitale Noten rendern.

## Schritt 8: Wiedergabe vorbereiten

Eine zeitlich korrekte Playback-Sequenz erstellen.

## Schritt 9: Ergebnisprüfung

Auffällige Stellen hervorheben und manuelle Korrektur anbieten.

### Fortschrittsanzeige

Zeige verständliche Zustände.

Keine künstlichen Fortschrittsprozente.

Aufwändige Berechnungen müssen in Hintergrundprozessen stattfinden.

Implementiere Timeouts, Abbruchmöglichkeiten und angemessene Fehlerbehandlung.

---

# 8. MANUELLE NOTENKORREKTUR

Die manuelle Korrektur ist eine Pflichtfunktion.

## 8.1 Vergleichsansicht

Zeige:

- links beziehungsweise oben das Original;
- rechts beziehungsweise unten die erkannten digitalen Noten.

Die Anordnung muss responsiv sein.

## 8.2 Einzelne Noten bearbeiten

Ein Klick auf eine Note öffnet ein Bearbeitungsmenü.

Mindestens:

- Tonhöhe;
- Oktave;
- Kreuz;
- Be;
- Auflösungszeichen;
- Notenwert;
- Punktierung;
- Haltebogen.

Zusätzlich:

- Note einfügen;
- Note löschen;
- Pause einfügen;
- Pause ändern;
- Notenschlüssel korrigieren;
- Tonart ändern;
- Taktart ändern.

## 8.3 Intuitive Notenbearbeitung

Erstelle keine Oberfläche, in der Benutzer MusicXML manuell editieren müssen.

Nutze einfache Auswahlmenüs und direktes Bearbeiten in der Notenansicht.

## 8.4 Korrektur von Symbolen

Ermögliche das Hinzufügen beziehungsweise Korrigieren von:

- Vorzeichen;
- Pausen;
- Taktstrichen;
- Haltebögen;
- Wiederholungszeichen;
- ersten und zweiten Endungen.

## 8.5 Sofortige Aktualisierung

Nach einer Korrektur müssen alle betroffenen Komponenten konsistent sein.

Insbesondere:

- interne Noten;
- MusicXML;
- grafische Darstellung;
- Audio;
- MIDI-Export;
- musikalische Validierung.

## 8.6 Versionierung

Speichere:

- ursprüngliches KI-Ergebnis;
- aktuelle bearbeitete Version;
- vorherige Bearbeitungsschritte.

Implementiere Undo und Redo.

---

# 9. INTERNES MUSIKMODELL

Verwende MusicXML als primäres Austauschformat.

Ergänze ein internes Datenmodell für interaktive Funktionen.

Das Modell benötigt mindestens:

- Stück;
- Partitur;
- Instrumentenstimme;
- Takt;
- Note;
- Pause;
- Tonart;
- Taktart;
- Notenschlüssel;
- Tempo;
- Dynamik, soweit unterstützt;
- Wiederholung;
- Transposition;
- Zeitposition;
- Dauer;
- Originalreferenz.

Eine Note muss sowohl ihre notierte als auch ihre klingende Tonhöhe besitzen beziehungsweise zuverlässig daraus ableiten können.

Verwende stabile Referenzen zwischen MusicXML, internem Modell und grafischer Darstellung.

Achte auf die korrekte Unterscheidung der deutschen Notennamen H und B von der internationalen MIDI-/MusicXML-Tonhöhenbezeichnung.

Die interne Musiklogik darf nicht von angezeigten, lokalisierten Notennamen abhängen.

---

# 10. DIGITALE NOTENDARSTELLUNG

Nutze OpenSheetMusicDisplay oder eine vergleichbar geeignete Bibliothek.

Funktionen:

- echte Notenlinien;
- korrekte Notenköpfe;
- Pausen;
- Vorzeichen;
- Taktstriche;
- Tonarten;
- Taktarten;
- mehrere Zeilen;
- mehrere Seiten;
- Zoom;
- automatische Anpassung;
- Auswahl einzelner Takte;
- Auswahl einzelner Noten;
- Hervorhebung während der Wiedergabe.

Die Darstellung soll sowohl auf Smartphones als auch auf größeren Bildschirmen gut lesbar sein.

Biete drei Modi:

1. Originalnoten;
2. digitalisierte Noten;
3. Vergleichsansicht.

---

# 11. INSTRUMENTE UND INSTRUMENTENKLÄNGE

Unterstütze typische Instrumente aus Musikvereinen.

## Holzbläser

- Querflöte;
- Piccolo;
- Oboe;
- Fagott;
- B♭-Klarinette;
- Bassklarinette;
- Sopransaxophon;
- Altsaxophon;
- Tenorsaxophon;
- Baritonsaxophon.

## Blechbläser

- B♭-Trompete;
- Flügelhorn;
- F-Horn;
- Tenorhorn;
- Bariton;
- Euphonium;
- Posaune;
- Bassposaune;
- Tuba.

## Weitere Instrumente

- Klavier;
- Keyboard;
- Violine;
- Viola;
- Violoncello;
- Kontrabass;
- Schlagwerk.

Die tatsächliche Unterstützung für Schlagwerk und komplexe mehrstimmige Instrumente darf anfangs eingeschränkt sein.

## Instrumentenprofile

Jedes Instrument erhält:

- Namen;
- Instrumentenfamilie;
- übliche Notenschlüssel;
- typische Notationsvariante;
- Transpositionsintervall;
- Tonumfang;
- Audio-Sample-Zuordnung;
- MIDI-Instrumentenprogramm.

Verwende geeignete lizenzrechtlich nutzbare Instrumentensamples.

Wenn kein realistischer Klang vorhanden ist, verwende einen nachvollziehbar gekennzeichneten Ersatz, beispielsweise Klavier.

---

# 12. KORREKTE TRANSPOSITION

Dieser Teil muss besonders sorgfältig implementiert und getestet werden.

## 12.1 Notierte und klingende Tonhöhe

Unterscheide:

- notierte Tonhöhe;
- klingende Tonhöhe.

## 12.2 Transponierende Instrumente

Beispiele:

- B♭-Trompete: große Sekunde tiefer;
- B♭-Klarinette: große Sekunde tiefer;
- E♭-Altsaxophon: große Sexte tiefer;
- B♭-Tenorsaxophon: große None tiefer;
- E♭-Baritonsaxophon: große Tredezime tiefer;
- F-Horn: reine Quinte tiefer;
- Piccolo: Oktave höher;
- Kontrabass: Oktave tiefer.

Berücksichtige bei Tenorhorn, Bariton, Euphonium, Posaune und Tuba die jeweils gewählte Notationskonvention.

## 12.3 Einstellungen

Ermögliche:

- Instrument auswählen;
- Notationsvariante auswählen;
- geschriebene Tonhöhe anzeigen;
- klingende Tonhöhe anzeigen;
- Referenzklang wählen;
- zusätzliche Transposition einstellen.

## 12.4 MusicXML-Import

Prüfe, ob importiertes MusicXML bereits Instrumententranspositionsinformationen enthält.

Verhindere eine versehentliche doppelte Transposition.

## 12.5 Tests

Erstelle fest definierte Transpositionstests mit bekannten Referenztönen.

Insbesondere bei Saxophonen müssen die Oktavlagen korrekt sein.

---

# 13. AUDIOPLAYER

Implementiere mit Tone.js beziehungsweise Web Audio API einen tatsächlich funktionierenden Player.

## Grundfunktionen

- Play;
- Pause;
- Stop;
- Neustart;
- Fortschrittsanzeige;
- aktuelle Position;
- Gesamtdauer;
- aktuelle Taktnummer;
- direktes Springen zu einem Takt.

## Musikalische Wiedergabe

Berücksichtige:

- Tonhöhe;
- Notenwert;
- Pausen;
- Tempo;
- punktierte Rhythmen;
- einfache Tuplets;
- Haltebögen;
- Wiederholungszeichen;
- Transposition.

Der Player muss auf einer präzisen musikalischen Zeitachse basieren.

## Tempo

Biete:

- 25 %;
- 50 %;
- 75 %;
- 100 %;
- 125 %;
- 150 %;
- 200 %.

Zusätzlich einen stufenlosen Regler.

Tonhöhe darf sich bei Tempoänderungen nicht verändern.

## Instrumentenklang

Möglichst realistische Instrumentensamples verwenden.

Unterstütze:

- Lautstärke;
- Stummschalten;
- Klangwechsel;
- Referenzton.

## Synchronisierte Notenansicht

Die aktuelle Note beziehungsweise der aktuelle Takt soll während des Abspielens hervorgehoben werden.

Bei längeren Stücken:

- automatisches Scrollen;
- automatischer Seitenwechsel;
- jederzeit manuelles Navigieren.

Die Hervorhebung muss zur tatsächlichen Audiowiedergabe passen.

---

# 14. ÜBUNGSMODUS

Der Übungsmodus ist einer der wichtigsten Produktbestandteile.

## 14.1 Taktauswahl

Der Benutzer kann:

- einen einzelnen Takt;
- mehrere zusammenhängende Takte;
- einen bestimmten Abschnitt;
- das gesamte Stück

auswählen.

## 14.2 Wiederholungsschleifen

Implementiere einen A-B-Loop.

Der Benutzer kann die Wiederholung ein- und ausschalten.

Optionen:

- endlos;
- bestimmte Anzahl Durchläufe;
- optional Pause zwischen Durchläufen.

## 14.3 Tempo schrittweise erhöhen

Beispiel:

Ein Musiker beginnt mit 60 % Geschwindigkeit.

Nach drei Durchläufen wird die Geschwindigkeit auf 70 % erhöht.

Danach auf 80 %, 90 % und schließlich 100 %.

Konfigurierbar:

- Starttempo;
- Zieltempo;
- Erhöhung;
- Anzahl Durchläufe.

## 14.4 Metronom

Implementiere:

- Metronom an/aus;
- Lautstärke;
- Betonung;
- Unterteilung;
- Synchronisation.

## 14.5 Einzähler

Biete:

- kein Einzähler;
- ein Takt;
- zwei Takte.

Berücksichtige die Taktart.

## 14.6 Einzelne Note anhören

Ein Klick auf eine Note soll deren Ton hörbar machen.

Bei transponierenden Instrumenten muss die korrekte klingende Tonhöhe verwendet werden.

## 14.7 Gespeicherte Passagen

Der Benutzer kann schwierige Abschnitte lokal speichern.

Gespeichert werden:

- Name;
- Starttakt;
- Endtakt;
- Tempo;
- Wiederholungseinstellungen;
- optionale Notizen.

---

# 15. LOKALE NOTENBIBLIOTHEK

Die Anwendung benötigt eine übersichtliche lokale Bibliothek.

## 15.1 Einträge

Ein Musikstück enthält:

- Titel;
- Komponist, falls bekannt;
- Instrument;
- Importdatum;
- Anzahl Seiten;
- Anzahl Takte;
- Originaldatei;
- erkannte MusicXML-Datei;
- aktuelle bearbeitete Version;
- zuletzt verwendete Einstellungen.

## 15.2 Funktionen

- Stück öffnen;
- umbenennen;
- löschen;
- duplizieren;
- erneut erkennen;
- exportieren;
- als Favorit markieren.

## 15.3 Suche und Organisation

Implementiere:

- Suchfeld;
- Sortierung;
- Favoriten;
- Ordner beziehungsweise Sammlungen;
- Filter nach Instrument.

Beispielsammlungen:

- Konzertprogramm;
- Marschmusik;
- Neue Stücke;
- Schwierige Stücke.

## 15.4 Zuletzt verwendet

Speichere lokal:

- zuletzt geöffnetes Stück;
- letzte Wiedergabeposition;
- verwendetes Tempo;
- aktiven Übungsabschnitt.

---

# 16. KEINE BENUTZERVERWALTUNG

**Es darf ausdrücklich keine klassische Benutzerverwaltung geben.**

Nicht implementieren:

- Registrierung;
- Login;
- Logout;
- Passwortverwaltung;
- Benutzerprofile;
- Benutzerrollen;
- E-Mail-Verifizierung;
- OAuth;
- Cloud-Synchronisation;
- Account-Dashboard.

Die Anwendung soll beim Start unmittelbar verwendbar sein.

Alle Daten gehören zur lokalen Installation.

Es ist nicht erforderlich, verschiedene Benutzer voneinander zu trennen.

## 16.1 Lokale Einstellungen

Speichere beispielsweise:

- Standardinstrument;
- bevorzugten Klang;
- Standardtempo;
- Designmodus;
- zuletzt geöffnetes Stück;
- Lautstärke;
- Metronomeinstellungen.

## 16.2 Datenbank

Verwende SQLite für lokale Metadaten und Konfiguration.

Originalbilder, PDF und MusicXML werden im lokalen Dateisystem gespeichert.

Verwende keine PostgreSQL-Installation, wenn SQLite für den Anwendungsfall ausreichend ist.

## 16.3 Datenverzeichnis

Definiere einen zentralen, konfigurierbaren Datenordner.

Zum Beispiel:

`./data/`

Unterordner:

- `library/`
- `originals/`
- `processed/`
- `musicxml/`
- `models/`
- `exports/`
- `cache/`
- `logs/`

Der genaue Aufbau darf sinnvoll angepasst werden.

## 16.4 Export und Sicherung

Biete eine einfache Möglichkeit, die gesamte Bibliothek zu sichern.

Idealerweise als exportierbares Archiv mit:

- Datenbank;
- Originaldokumenten;
- MusicXML;
- Übungsabschnitten;
- Einstellungen.

Ein solches Backup soll wieder importiert werden können.

---

# 17. LOKALER BETRIEB UND SMARTPHONE-NUTZUNG

## 17.1 Lokaler Standardbetrieb

Die Anwendung wird auf einem Computer gestartet.

Das Python-Backend führt die KI-Verarbeitung auf diesem Computer aus.

Das Frontend verbindet sich lokal mit dem Backend.

Standardmäßig soll der Dienst nur an `127.0.0.1` gebunden werden.

So werden ungewollte Zugriffe aus dem Netzwerk verhindert.

## 17.2 Zugriff vom Smartphone

Optional soll die Anwendung über das lokale Netzwerk genutzt werden können.

Beispiel:

Ein Computer führt NotePilot aus.

Das Smartphone befindet sich im selben WLAN.

Der Benutzer öffnet die Weboberfläche über die lokale Adresse des Computers.

Er fotografiert seine Noten mit dem Smartphone.

Die Bilder werden ausschließlich an den eigenen Computer im lokalen Netzwerk übertragen.

Dort verarbeitet das KI-Modell die Noten.

Anschließend werden die Ergebnisse im Smartphone-Browser angezeigt.

Es wird keine externe Cloud benötigt.

## 17.3 Sicherheit des Netzwerkzugriffs

Der Netzwerkmodus muss ausdrücklich aktiviert werden.

Prüfe geeignete Schutzmaßnahmen, etwa:

- Einschränkung auf das lokale Netzwerk;
- sichere Verbindung für Browser-Kamerafunktionen;
- optionales Geräte-Pairing ohne Benutzerkonto;
- keine öffentliche Portfreigabe;
- keine ungewollte Erreichbarkeit aus dem Internet.

Ein Pairing darf nicht mit einer klassischen Benutzerverwaltung verwechselt werden.

## 17.4 Smartphone ohne laufenden Computer

Die Anwendung darf nicht suggerieren, dass der Browser allein die vollständige HOMR-KI-Verarbeitung durchführt, wenn diese tatsächlich auf einem Python-Backend angewiesen ist.

Wenn kein lokales Backend erreichbar ist, sollen bereits verfügbare digitale Musikdaten je nach Cache weiterhin angezeigt und abgespielt werden können.

Die optische Notenerkennung muss dann als nicht verfügbar gekennzeichnet werden.

---

# 18. DESIGN UND BENUTZEROBERFLÄCHE

Erstelle ein hochwertiges, modernes Design.

Designmerkmale:

- klare Typografie;
- gut lesbare Noten;
- dezente Akzentfarben;
- großzügige Abstände;
- moderne Icons;
- abgerundete Bedienelemente;
- übersichtliche Navigation;
- hochwertige Karten und Dialoge.

Unterstütze Light Mode und Dark Mode.

## 18.1 Responsive Layout

Besonders wichtig sind:

- Smartphone im Hochformat;
- Smartphone im Querformat;
- Tablet;
- Desktop.

Der Player soll auf dem Smartphone gut bedienbar sein, ohne dass die Noten durch zu viele Bedienelemente verdeckt werden.

## 18.2 Startseite

Elemente:

- NotePilot-Logo;
- „Neue Noten hinzufügen“;
- „Meine Noten“;
- „Zuletzt verwendet“;
- „Weiter üben“;
- „Beispielstück ausprobieren“.

## 18.3 Import-Assistent

Gestalte einen intuitiven Ablauf.

Beispiel:

„Foto aufnehmen oder Datei hochladen“

Danach:

„Aufnahme überprüfen“

Danach:

„Noten erkennen“

Danach:

„Ergebnis überprüfen“

Danach:

„Jetzt anhören“

## 18.4 Player-Layout

Desktop:

- große Notenansicht;
- darunter Transportsteuerung;
- seitlicher Bereich für Instrument, Tempo und Übungsfunktionen.

Mobile:

- möglichst große Notenansicht;
- kompakte, gut erreichbare Player-Steuerung;
- erweitertes Übungsmenü als ausklappbares Panel.

## 18.5 Sprache

Primäre Oberfläche vollständig auf Deutsch.

Alle Fehlermeldungen müssen verständlich formuliert sein.

---

# 19. PWA-FUNKTIONEN

Entwickle die Oberfläche als Progressive Web App.

Unterstütze:

- Installation auf dem Homescreen;
- App-Icon;
- passende Startansicht;
- Responsive Design;
- sinnvolles Caching;
- lokale Offline-Anzeige bereits verfügbarer Musikdaten;
- Offline-Wiedergabe gecachter Stücke und Samples.

Die lokale KI-Verarbeitung läuft weiterhin auf dem Computer, sofern keine eigenständige mobile KI-Laufzeit implementiert wird.

Dokumentiere diese Abhängigkeit verständlich.

---

# 20. AUDIO- UND MUSIKALISCHE GENAUIGKEIT

Die musikalische Korrektheit muss hohe Priorität haben.

## 20.1 Rhythmik

Die Wiedergabe muss genaue Dauern verwenden.

Ein gewöhnlicher 4/4-Takt muss in der vorgesehenen Zeit abgespielt werden.

## 20.2 Vorzeichen

Überprüfe die korrekte Interpretation von:

- Tonarten;
- einzelnen Kreuzen;
- Bes;
- Auflösungszeichen;
- Wechseln innerhalb eines Taktes;
- Rücksetzung am Taktende;
- Haltebögen über Taktgrenzen.

## 20.3 Tempo

Die Berechnung muss auf musikalischen Zeitwerten basieren.

## 20.4 Wiederholungen

Erzeuge eine tatsächliche Abspielreihenfolge.

Bewahre die ursprüngliche notierte Partitur.

## 20.5 Transposition

Berücksichtige Instrument und Notationsvariante.

Bei importiertem MusicXML müssen vorhandene Transpositionsangaben respektiert werden.

---

# 21. EXPORTFUNKTIONEN

Mindestens:

- MusicXML;
- MIDI.

Optional:

- PDF;
- WAV;
- MP3.

MusicXML soll die tatsächlich korrigierte Partitur enthalten.

MIDI soll die korrekte klingende Tonhöhe und zeitliche Struktur verwenden.

Exportdateien werden lokal erstellt.

---

# 22. OPTIONALE ZUSATZFUNKTIONEN

Diese Funktionen sind mögliche Erweiterungen, sollen die Fertigstellung des Kernprodukts aber nicht blockieren.

## 22.1 Stücksammlungen

Lokale Konzertprogramme und Sammlungen organisieren.

## 22.2 Mehrere Instrumentalstimmen

Mehrere Stimmen eines Musikstücks gemeinsam verwalten.

Beispiel:

- Trompete 1;
- Trompete 2;
- Klarinette 1;
- Tenorhorn;
- Posaune;
- Tuba.

## 22.3 Mehrstimmige Wiedergabe

Falls die Partitur zuverlässig mehrere Stimmen enthält, sollen diese optional gemeinsam abgespielt werden können.

Eine automatische Synchronisation unabhängig fotografierter Instrumentalstimmen ist eine separate spätere Funktion.

## 22.4 Mikrofonanalyse

Perspektivisch kann die Anwendung das Spielen eines Musikers analysieren.

Mögliche Rückmeldungen:

- falscher Ton;
- zu früher Einsatz;
- zu später Einsatz;
- ausgelassene Note.

Eine solche Funktion benötigt echte Audioanalyse und darf nicht simuliert werden.

## 22.5 Automatisches Mitlesen

Später möglich:

Die Anwendung erkennt, wo sich der Musiker gerade innerhalb der Partitur befindet.

Auch das erfordert eine eigenständige technische Umsetzung.

---

# 23. ROBUSTHEIT UND FEHLERBEHANDLUNG

Behandle insbesondere:

- Kamera nicht verfügbar;
- beschädigte Bilddatei;
- beschädigtes PDF;
- unleserliches Notenblatt;
- abgeschnittenes Notensystem;
- KI-Modell nicht installiert;
- Modellgewichte fehlen;
- zu wenig Arbeitsspeicher;
- GPU nicht verfügbar;
- KI-Verarbeitung abgebrochen;
- Verarbeitung dauert ungewöhnlich lange;
- MusicXML ungültig;
- Symbol nicht erkannt;
- Taktstruktur widersprüchlich;
- Instrumentensample fehlt;
- lokaler Server nicht erreichbar.

Erstelle verständliche Fehlermeldungen und Wiederholungsmöglichkeiten.

Beispiele:

„Das KI-Modell konnte nicht gestartet werden. Prüfe die lokale Installation.“

„Die Taktstruktur konnte nicht vollständig erkannt werden. Bitte überprüfe die markierten Takte.“

„Das Foto ist möglicherweise zu unscharf. Versuche eine Aufnahme mit besserer Beleuchtung.“

---

# 24. DATEISICHERHEIT UND DATENSCHUTZ

Obwohl es keine Benutzerkonten gibt, müssen Dateiverarbeitung und Speicherung sicher sein.

Implementiere:

- sichere Dateitypprüfung;
- konfigurierbare Uploadlimits;
- Schutz gegen beschädigte Dateien;
- sichere PDF-Verarbeitung;
- sichere MusicXML-Parser;
- Schutz vor XML External Entity-Angriffen;
- Schutz gegen manipulierte ZIP/MXL-Dateien;
- Ressourcenbegrenzung für KI-Prozesse;
- begrenzte Verarbeitungslaufzeiten;
- sichere temporäre Dateien.

Lösche temporäre Verarbeitungsergebnisse bei Bedarf automatisch.

Musikstücke dürfen nicht unbemerkt an fremde Server übertragen werden.

Prüfe Open-Source-Lizenzen einschließlich separat veröffentlichter Modellgewichte und Instrumentensamples.

Insbesondere die AGPL-3.0-Lizenz von HOMR und Audiveris muss berücksichtigt werden.

---

# 25. LOKALES DATENMODELL

Entwickle ein sauberes SQLite-Schema.

Mögliche Entitäten:

**MusicPiece**

- id;
- title;
- composer;
- instrument;
- notation_variant;
- created_at;
- updated_at;
- last_opened_at.

**SourceDocument**

- id;
- piece_id;
- filename;
- file_type;
- local_path;
- page_count.

**SourcePage**

- id;
- document_id;
- page_number;
- image_path;
- processed_image_path.

**RecognitionJob**

- id;
- piece_id;
- engine;
- engine_version;
- status;
- started_at;
- finished_at;
- error.

**ScoreVersion**

- id;
- piece_id;
- musicxml_path;
- version_number;
- created_at;
- source.

**MusicalPart**

- id;
- score_version_id;
- instrument;
- notation_variant;
- transposition.

**RecognitionWarning**

- id;
- piece_id;
- measure_reference;
- event_reference;
- warning_type;
- severity;
- resolved.

**PracticeSection**

- id;
- piece_id;
- name;
- start_measure;
- end_measure;
- tempo_settings;
- loop_settings.

**PracticeSession**

- id;
- piece_id;
- start_time;
- end_time;
- duration.

**AppSettings**

- key;
- value.

Verwende keine User-Entität.

---

# 26. LOKALE BACKEND-API

Implementiere eine versionierte API.

Beispiele:

- `GET /api/v1/pieces`
- `POST /api/v1/pieces`
- `GET /api/v1/pieces/{id}`
- `PATCH /api/v1/pieces/{id}`
- `DELETE /api/v1/pieces/{id}`

Uploads:

- `POST /api/v1/pieces/{id}/documents`

Erkennung:

- `POST /api/v1/pieces/{id}/recognition`
- `GET /api/v1/recognition-jobs/{jobId}`
- `POST /api/v1/recognition-jobs/{jobId}/cancel`

Noten:

- `GET /api/v1/pieces/{id}/score`
- `PATCH /api/v1/pieces/{id}/score`
- `POST /api/v1/pieces/{id}/score/validate`
- `GET /api/v1/pieces/{id}/warnings`

Export:

- `GET /api/v1/pieces/{id}/export/musicxml`
- `GET /api/v1/pieces/{id}/export/midi`

Übung:

- `GET /api/v1/pieces/{id}/practice-sections`
- `POST /api/v1/pieces/{id}/practice-sections`
- `PATCH /api/v1/practice-sections/{id}`
- `DELETE /api/v1/practice-sections/{id}`

Konfiguration:

- `GET /api/v1/settings`
- `PATCH /api/v1/settings`

KI:

- `GET /api/v1/omr/engines`
- `GET /api/v1/omr/status`

Es werden keine Authentifizierungs-Endpunkte benötigt.

Binde den API-Server standardmäßig ausschließlich an localhost.

Wenn LAN-Zugriff aktiviert wird, berücksichtige geeignete Sicherheitsvorkehrungen.

---

# 27. TESTS

Erstelle automatisierte Tests für die entscheidenden Bereiche.

## 27.1 KI-Notenerkennung

Teste echte Bilddateien mit:

- einfachen Noten;
- Vorzeichen;
- Tonarten;
- Pausen;
- verschiedenen Taktarten;
- Punktierungen;
- mehreren Notensystemen;
- schrägen Smartphoneaufnahmen;
- schlechteren Lichtverhältnissen.

## 27.2 Musikalische Referenztests

Mindestens:

1. C-Dur-Tonleiter.
2. G-Dur-Tonleiter.
3. F-Dur-Tonleiter.
4. Ein Kreuz innerhalb eines Taktes.
5. Ein Be innerhalb eines Taktes.
6. Auflösungszeichen.
7. Vorzeichenwirkung über mehrere Noten.
8. Rücksetzung nach Taktstrich.
9. Punktierte Viertelnote.
10. Achtelnoten.
11. Sechzehntelnoten.
12. Viertelpause.
13. Ganze Taktpause.
14. 3/4-Takt.
15. 6/8-Takt.
16. Triolen.
17. Haltebogen.
18. Einfache Wiederholung.
19. Erste und zweite Endung.
20. Mehrseitige Noten.
21. B♭-Trompete.
22. E♭-Altsaxophon.
23. F-Horn.
24. Notenschlüsselwechsel.
25. Tonartwechsel.

## 27.3 Vergleich mit Referenzdaten

Erstelle für geeignete Tests korrektes Referenz-MusicXML.

Vergleiche das tatsächliche KI-Ergebnis mit den erwarteten Noten und Symbolen.

Teste nicht nur, ob das Modell überhaupt eine Datei erzeugt.

Überprüfe auch, ob die musikalischen Daten sinnvoll und korrekt sind.

## 27.4 Integrations-Tests

Teste:

- Foto hochladen;
- KI-Engine ausführen;
- MusicXML erzeugen;
- Noten rendern;
- Tonhöhe korrigieren;
- Audio abspielen;
- Tempo ändern;
- Loop starten;
- Stück lokal speichern;
- Stück erneut öffnen;
- Export durchführen.

## 27.5 Modellverfügbarkeit

Teste auch:

- Modell nicht installiert;
- Modellinitialisierung;
- CPU-Verarbeitung;
- fehlende Gewichte;
- fehlende externe Abhängigkeiten.

---

# 28. PERFORMANCE

Achte auf eine sinnvolle Ressourcennutzung.

Die Anwendung soll auch ohne leistungsfähige GPU funktionieren.

Implementiere:

- Hintergrundjobs;
- lokale Modell-Caches;
- schonende Bildvorverarbeitung;
- angemessene Auflösungen;
- begrenzte parallele KI-Prozesse;
- zuverlässige Fehlerbehandlung bei Speichermangel;
- wiederverwendbare Erkennungsergebnisse.

Nach der erstmaligen Erkennung dürfen kleine Änderungen am Player oder an den Übungseinstellungen keine erneute KI-Erkennung auslösen.

Auch manuelle Notenkorrekturen sollen nicht standardmäßig das gesamte Bild neu analysieren.

---

# 29. LOKALE DIAGNOSE UND ERKENNUNGSQUALITÄT

Erstelle eine optionale Diagnoseansicht für die Notenerkennung.

Zeige, soweit tatsächlich verfügbar:

- verwendete Engine;
- Modellversion;
- Ausführungsmodus CPU/GPU;
- Verarbeitungsdauer;
- Anzahl erkannter Seiten;
- Anzahl erkannter Notensysteme;
- Anzahl erkannter Takte;
- Anzahl erkannter Noten;
- Anzahl auffälliger Stellen;
- aufgetretene Fehler.

Optional:

- vorverarbeitetes Bild;
- erkannte Notensysteme;
- Segmentierungsdarstellung;
- Vergleich verschiedener Engines.

Nutze reale technische Informationen.

Erfinde keine Konfidenzwerte.

---

# 30. PROJEKTSTRUKTUR

Verwende eine klar strukturierte Architektur.

Beispiel:

`notepilot/`

**Frontend**

- `frontend/src/components/`
- `frontend/src/pages/`
- `frontend/src/features/import/`
- `frontend/src/features/score/`
- `frontend/src/features/playback/`
- `frontend/src/features/practice/`
- `frontend/src/features/library/`
- `frontend/src/features/settings/`
- `frontend/src/services/`
- `frontend/src/store/`
- `frontend/src/types/`

**Backend**

- `backend/app/api/`
- `backend/app/core/`
- `backend/app/models/`
- `backend/app/schemas/`
- `backend/app/services/preprocessing/`
- `backend/app/services/omr/`
- `backend/app/services/musicxml/`
- `backend/app/services/validation/`
- `backend/app/services/transposition/`
- `backend/app/services/export/`
- `backend/app/workers/`
- `backend/app/database/`
- `backend/tests/`

**Weitere Verzeichnisse**

- `examples/`
- `docs/`
- `data/`
- `scripts/`

**Konfigurationsdateien**

- `docker-compose.yml`
- `.env.example`
- `README.md`
- `LICENSES.md`

Passe die Struktur sinnvoll an.

---

# 31. INSTALLATION UND START

Die Anwendung soll möglichst unkompliziert startbar sein.

## 31.1 Entwicklungsbetrieb

Dokumentiere:

- Python-Installation;
- Node.js-Installation;
- Abhängigkeiten;
- Modellinstallation;
- Backend-Start;
- Frontend-Start.

## 31.2 Vereinfachter Start

Erstelle nach Möglichkeit Startskripte.

Beispielsweise:

- `start-windows.bat`
- `start-linux.sh`

Die Skripte sollen die Anwendung starten und die lokale Adresse anzeigen.

## 31.3 Docker

Stelle eine optionale Docker-Compose-Konfiguration bereit.

Sie muss lokale Volumes für Folgendes unterstützen:

- Datenbank;
- Dokumente;
- KI-Modelle;
- Cache.

## 31.4 Keine laufenden Kosten

Die vollständige lokale Kernanwendung soll weder einen bezahlten Server noch externe KI-Dienste benötigen.

Einmalige Downloads für Software und Modelle sind erlaubt.

---

# 32. ENTWICKLUNGSREIHENFOLGE

Arbeite in logisch aufeinander aufbauenden Phasen.

## Phase 1: Grundgerüst

- Projektstruktur;
- Frontend;
- Backend;
- SQLite;
- Designsystem;
- Navigation;
- Dashboard.

## Phase 2: MusicXML und Player

- MusicXML-Import;
- digitale Notenanzeige;
- Audioengine;
- Rhythmus;
- Tempo;
- Hervorhebung;
- Instrumente;
- Transposition.

## Phase 3: Übungsfunktionen

- Taktauswahl;
- A-B-Loops;
- Metronom;
- Einzähler;
- Tempoautomatik;
- gespeicherte Passagen.

## Phase 4: Lokale KI-Notenerkennung

- HOMR installieren und konfigurieren;
- Modellgewichte vorbereiten;
- echten Testlauf durchführen;
- FastAPI-Integration;
- Bildvorverarbeitung;
- KI-Erkennungsjobs;
- MusicXML-Übernahme.

## Phase 5: Musikalische Symbolprüfung

- Tonarten;
- Kreuze;
- Bes;
- Auflösungszeichen;
- Taktarten;
- Notenwerte;
- Pausen;
- Haltebögen;
- Wiederholungen;
- Plausibilitätskontrollen.

## Phase 6: Alternative Engine

- Audiveris integrieren, falls sinnvoll;
- Erkennung erneut durchführen;
- Ergebnisse vergleichen;
- manuelle Engine-Auswahl.

## Phase 7: Korrektur

- Original-/Digitalvergleich;
- Note bearbeiten;
- Symbole korrigieren;
- Undo/Redo;
- Speicherung.

## Phase 8: Bibliothek und PWA

- Stückverwaltung;
- lokale Einstellungen;
- Favoriten;
- Sammlungen;
- Backup;
- Offline-Funktionen.

## Phase 9: Qualitätssicherung

- Tests;
- musikalische Korrektheit;
- Fehlerbehandlung;
- Sicherheitsprüfung;
- Performance;
- mobile Ansicht.

## Phase 10: Dokumentation

- Installation;
- Start;
- KI-Einrichtung;
- unterstützte Symbole;
- Einschränkungen;
- bekannte Probleme.

---

# 33. DEFINITION OF DONE

Die Kernanwendung gilt erst als funktionsfähig, wenn folgende Anforderungen erfüllt sind.

## Benutzeroberfläche

- Modernes Dashboard vorhanden.
- Navigation funktioniert.
- Importansicht vorhanden.
- Notenplayer vorhanden.
- Übungsmodus vorhanden.
- Mobile Darstellung funktioniert.
- Keine Anmeldung erforderlich.

## Import

- Bilddateien können hochgeladen werden.
- PDFs können importiert werden.
- MusicXML kann direkt importiert werden.
- Mehrere Seiten können verarbeitet werden.

## KI-Erkennung

- Ein echtes kostenloses lokales KI-Modell wird gestartet.
- Es benötigt keine bezahlte API.
- CPU-Inferenz ist möglich.
- Ein reales Notenfoto wird verarbeitet.
- Die Engine erzeugt ein echtes MusicXML-Ergebnis.
- Das Ergebnis wird tatsächlich importiert.
- Fehler werden sauber behandelt.
- Vorzeichen und musikalische Grundsymbole werden berücksichtigt.

## Musikalische Verarbeitung

- Tonhöhen werden korrekt interpretiert.
- Taktarten werden berücksichtigt.
- Notenwerte und Pausen stimmen.
- Tonartvorzeichen wirken korrekt.
- Lokale Versetzungszeichen wirken korrekt.
- Transpositionen funktionieren.
- Haltebögen werden verarbeitet.

## Player

- Hörbare Wiedergabe funktioniert.
- Tempoänderung funktioniert.
- Aktuelle Notenposition wird hervorgehoben.
- Instrumentenklang kann ausgewählt werden.
- Wiedergabe kann pausiert und fortgesetzt werden.

## Übungsmodus

- Taktauswahl funktioniert.
- Loops funktionieren.
- Metronom funktioniert.
- Einzähler funktioniert.
- Tempo kann schrittweise erhöht werden.

## Korrektur

- Tonhöhen können verändert werden.
- Vorzeichen können korrigiert werden.
- Notenwerte können korrigiert werden.
- Änderungen werden in der Wiedergabe wirksam.
- Änderungen werden gespeichert.

## Lokale Speicherung

- SQLite funktioniert.
- Originalbilder werden lokal gespeichert.
- MusicXML wird lokal gespeichert.
- Bibliothek funktioniert.
- Einstellungen bleiben erhalten.
- Keine Benutzerverwaltung vorhanden.
- Keine verpflichtende Cloud-Komponente vorhanden.

## Qualität

- Anwendung lässt sich starten.
- Wesentliche Tests laufen.
- Tatsächliche KI-Integration wurde überprüft.
- Keine Pflichtfunktion wird ausschließlich durch Mock-Daten dargestellt.
- Bekannte Einschränkungen sind dokumentiert.

---

# 34. WICHTIGE ENTWICKLUNGSGRUNDSÄTZE

1. Implementiere eine tatsächlich funktionsfähige Anwendung, keine Demo-Oberfläche.

2. Die KI-Notenerkennung ist ein echter technischer Kernbestandteil.

3. Bevorzuge HOMR als erste KI-Lösung, sofern die reale Integration erfolgreich ist.

4. Nutze Audiveris ergänzend, wenn die Notation dadurch sinnvoller und vollständiger erkannt wird.

5. Verwende ausschließlich kostenlose lokal ausführbare Modelle für die verpflichtende Notenerkennung.

6. Vermeide Cloud-Dienste und laufende Kosten.

7. Implementiere keine Benutzerregistrierung und keine Benutzerprofile.

8. Speichere alle Daten lokal.

9. Prüfe insbesondere Vorzeichen, Tonarten, Rhythmus und Transposition.

10. Behaupte keine Unterstützung von Symbolen, die technisch nicht zuverlässig verarbeitet werden können.

11. Mache fehlerhafte Erkennungen korrigierbar.

12. Entwickle zuerst einen korrekten Musikplayer und verbinde danach die Bild- und KI-Verarbeitung damit.

13. Erstelle eine moderne, einfache und mobilfreundliche Benutzeroberfläche.

14. Verwende eine wartbare und nachvollziehbare Architektur.

15. Teste mit echten Bildern und realen MusicXML-Dateien.

16. Erfinde keine Ergebnisse und keine Konfidenzwerte.

17. Verwende bei fehlenden Funktionen nachvollziehbare Fehlermeldungen statt scheinbar funktionsfähiger Platzhalter.

18. Überprüfe alle Lizenzen, insbesondere von Modellgewichten und Audiosamples.

19. Vermeide unnötige Komplexität.

20. Arbeite eigenständig und setze sinnvolle technische Entscheidungen direkt um.

---

# 35. FINALES BENUTZERSZENARIO

Ein Musiker aus einem Musikverein möchte eine schwierige Passage seiner neuen Trompetenstimme üben.

Er öffnet NotePilot.

Er fotografiert sein Notenblatt mit dem Smartphone oder lädt ein bereits vorhandenes Foto hoch.

Die Anwendung prüft das Bild und übergibt es an die lokale KI-Notenerkennung.

Das Modell erkennt:

- Notensystem;
- Violinschlüssel;
- Tonart;
- Taktart;
- einzelne Noten;
- Vorzeichen;
- Pausen;
- Notenwerte;
- Rhythmus;
- weitere unterstützte musikalische Zeichen.

Aus diesen Informationen entsteht eine digitale MusicXML-Partitur.

Der Musiker überprüft das Ergebnis.

Er entdeckt ein falsch erkanntes Vorzeichen und korrigiert es mit einem Klick.

Danach wählt er „Trompete in B♭“.

NotePilot berücksichtigt die korrekte Transposition und spielt die Melodie in der passenden klingenden Tonhöhe ab.

Die jeweils gespielte Note wird farblich hervorgehoben.

Der Musiker markiert die Takte 16–24.

Er reduziert das Tempo auf 60 % und aktiviert eine Wiederholungsschleife.

Anschließend lässt er das Tempo nach mehreren Durchläufen schrittweise erhöhen.

Sein Stück und die Übungseinstellungen werden lokal gespeichert.

Bei der nächsten Nutzung findet er die Noten sofort wieder.

Das alles funktioniert ohne Registrierung, ohne Cloud-Dienste und ohne kostenpflichtige KI.

---

# 36. KONKRETER STARTAUFTRAG

**Beginne jetzt mit der tatsächlichen Implementierung von NotePilot.**

Prüfe zunächst die Entwicklungsumgebung und den vorhandenen Projektstand.

Überprüfe anschließend, wie HOMR in dieser Umgebung lokal und kostenfrei ausgeführt werden kann.

Führe möglichst früh einen echten Test mit einem Notenbild durch, damit die technische Machbarkeit der KI-Integration bestätigt wird.

Installiere und integriere die notwendigen Open-Source-Komponenten.

Entwickle danach die Anwendung systematisch gemäß den beschriebenen Phasen.

Achte dabei insbesondere auf:

- die zuverlässige Erkennung gedruckter Musiknoten;
- Vorzeichen, Tonarten und sonstige Notationszeichen;
- die korrekte musikalische Interpretation;
- die vollständige lokale Verarbeitung;
- die tatsächliche Audiowiedergabe;
- die Unterstützung verschiedener Blasinstrumente;
- die Korrekturmöglichkeiten;
- den komfortablen Übungsmodus;
- die einfache Bedienbarkeit.

Erstelle die notwendigen Dateien, Implementierungen, Schnittstellen, Tests und Konfigurationen.

Beschränke dich nicht auf einen Architekturplan oder ein visuelles Mockup.

Wenn technische Probleme entstehen, untersuche diese eigenständig und wähle eine geeignete Lösung.

Falls ein konkretes Feature mit der verwendeten Open-Source-Technologie nicht zuverlässig realisierbar ist, erkläre die Einschränkung und stelle eine funktionierende Alternative oder eine manuelle Korrekturmöglichkeit bereit.

Führe abschließend echte Tests durch.

Dokumentiere präzise, welche Funktionen vollständig implementiert und tatsächlich getestet wurden.

**Das endgültige Ziel ist eine vollständig lokal nutzbare, moderne und musikalisch korrekte Übungsplattform, mit der echte fotografierte Noten automatisch erkannt und anschließend intuitiv abgespielt und geübt werden können.**