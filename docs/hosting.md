# Online-Betrieb

Für den vorhandenen Homeserver mit Docker, nginx Proxy Manager und Cloudflare Tunnel liegt eine vollständige [Schritt-für-Schritt-Anleitung](../deploy/README.md) mit vorgeschaltetem Access-Login und Token-Prüfung vor. Besucher benötigen nur den Browser. Der Betreiber führt die Einrichtung selbst durch; es wurde kein Homeserver-Zugriff verbunden und noch kein öffentlicher Link geprüft.

Das Homeserver-Profil liefert HOMR-Modelle im Image mit, hält die Bibliothek in einem dauerhaften Volume, veröffentlicht keine Host-Ports und deaktiviert Offline-Caches der Weboberfläche. Alle freigegebenen Nutzer teilen eine Bibliothek; es gibt keine Benutzertrennung in NotePilot.

# Direkt im Browser testen: Hosting-Voraussetzungen

NotePilot benötigt für Foto-/PDF-Erkennung einen laufenden Python-Prozess mit HOMR. Eine ausschließlich statische Veröffentlichung der Oberfläche ersetzt diesen Prozess nicht. In der aktuellen Codex-Sitzung ist keine Veröffentlichungsschnittstelle für ChatGPT Sites und kein Hosting-Konto verbunden. Es wurde noch kein öffentlicher Testlink erzeugt.

## Vorbereitung der Anwendung

Für eine gehostete Instanz sind zwei explizite Variablen vorgesehen:

```sh
NOTEPILOT_HOSTED_PREVIEW=1
NOTEPILOT_ALLOWED_HOSTS=der-exakte-hostname.example
```

Der Hostname wird zusätzlich zu den bestehenden lokalen Hosts erlaubt; es gibt keine pauschale Wildcard-Freigabe. Fremde Website-Origin-Anfragen bleiben abgelehnt. Die Online-Instanz kennzeichnet in Oberfläche und Upload, dass Noten auf dem Testserver verarbeitet und gespeichert werden. Die lokale Anwendung behält ihre bisherigen privaten Standardeinstellungen.

Ein späterer Betreiber kann den bestehenden Container verwenden, Backend und Gewichte vorab einrichten und danach einen HTTPS-Link bereitstellen. Besucher brauchen dann keine lokale Python-/Node-/Modellinstallation. Das bestehende LAN-/Einzelnutzer-Modell enthält keine Benutzerkonten und keine Trennung zwischen Besuchern. **Verwende deshalb zunächst eine private Testinstanz**, auf die nur der Besitzer und ausdrücklich berechtigte Mitwirkende Zugriff haben. Ein öffentlich zugänglicher Mehrbenutzerdienst ist eine gesonderte Erweiterung. Dauerhafte Bibliotheken benötigen beim Hoster lokalen persistenten Speicher oder eigene Backups.

## Hugging Face: aktuelle Voraussetzungen

Prüfdatum: 14. Oktober 2026. Laut [offizieller Spaces-Übersicht](https://huggingface.co/docs/hub/spaces-overview) benötigen neue Gradio-/Docker-Spaces grundsätzlich einen kostenpflichtigen Plan; „CPU Basic: FREE“ bedeutet keine stündliche Hardwaregebühr und hebt diese Voraussetzung nicht auf. Ein neu angelegter kostenloser Account reicht für einen normalen Docker Space daher nicht aus.

Die dokumentierte Ausnahme sind bis zu zwei [ZeroGPU-Spaces](https://huggingface.co/docs/hub/spaces-zerogpu) für kostenlose persönliche Accounts mit verifizierter E-Mail-Adresse und einem Alter von mehr als 30 Tagen. ZeroGPU setzt den Gradio-SDK voraus. NotePilots jetziger Docker-/FastAPI-/ONNX-CPU-Betrieb ist keine bereits verifizierte ZeroGPU-Bereitstellung; die Kompatibilität muss gesondert vorbereitet und beim Anbieter geprüft werden. Dafür wird keine kostenlose Hosting-Fähigkeit behauptet, bevor sie tatsächlich bestätigt ist.

Hostingzugang wird ausschließlich über eine sichere Verbindung oder Umgebungseinstellungen bereitgestellt; keine Tokens im Chat, im Repository oder in Docker-Layern speichern. Konto-/Planberechtigung muss vor einer Bereitstellung feststehen. Es wird keine kostenpflichtige Hardware oder Subscription ohne ausdrückliche Zustimmung aktiviert.
