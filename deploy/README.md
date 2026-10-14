# NotePilot auf deinem Homeserver

Die vollständige Anwendung inklusive CPU-Notenerkennung läuft im Docker-Container. Auf deinem Rechner brauchst du nur einen Browser. Dieses Profil verwendet deinen vorhandenen **Cloudflare Tunnel → nginx Proxy Manager → NotePilot** und veröffentlicht keinen zusätzlichen Host-/Router-Port.

Vorgeschlagene Adresse: `notepilot.stengele-home.de`. Sie wird erst nach deiner Einrichtung erreichbar. Cloudflare Access schützt den gesamten Host. NotePilot prüft zusätzlich Signatur, Ablaufzeit, Team, Application-AUD und erlaubte E-Mail im Access-Token; direkte Aufrufe ohne gültiges Token werden abgelehnt. Alle freigegebenen Adressen teilen dieselbe Bibliothek.

## 1. Voraussetzungen

Docker mit Compose v2, Git und Internetzugriff für den ersten Image-Bau. Getestetes Ziel: Linux **x86_64**; ARM ist ungetestet. Plane etwa 4 GB RAM für NotePilot zusätzlich zu den anderen Diensten und mehrere GB freien Speicher für Build, Image und Noten ein. Keine GPU erforderlich. Beim Build werden Abhängigkeiten und rund 150 MiB Modellgewichte geladen. Die Erkennung benötigt danach keinen externen KI-Dienst. Access braucht weiterhin Internet für Login und gelegentliches Abrufen öffentlicher Signaturschlüssel.

Bestehendes NPM-Netzwerk ermitteln:

```sh
docker ps --format 'table {{.Names}}\t{{.Image}}'
docker inspect --format '{{range $name, $network := .NetworkSettings.Networks}}{{$name}} {{end}}' NAME_DEINES_NPM_CONTAINERS
```

Verwende eines seiner benutzerdefinierten Docker-Netzwerke. Das Standardnetz `bridge` unterstützt die benötigte Namensauflösung nicht. Falls NPM nur dort läuft, lege ein benutzerdefiniertes Netzwerk an und ergänze es dauerhaft in deiner bestehenden NPM-Compose-Konfiguration. NotePilot verändert weder NPM noch Vaultwarden automatisch.

## 2. Cloudflare Access zuerst einrichten

Unter **Zero Trust → Access controls → Applications** eine **Self-hosted**-Anwendung anlegen:

- Name `NotePilot`, Public hostname `notepilot.stengele-home.de`.
- **Kein Pfadfilter**: Schutz für den gesamten Host, einschließlich `/api/` und Dateien.
- **One-time PIN** als Anmeldung aktivieren bzw. auswählen: Login per E-Mail-Code.
- **Allow**-Policy mit Include-Regel **Emails** und deiner exakten E-Mail-Adresse. Keine `Everyone`-/`Bypass`-Regel. Zusätzliche Nutzer nur mit einzelnen ausdrücklich erlaubten Adressen.
- Sitzungsdauer beispielsweise 8 Stunden.

Kopiere den **Team domain**-Hostname aus den Zero-Trust-Einstellungen und den **Application Audience (AUD) Tag** aus den zusätzlichen Einstellungen dieser Anwendung. Das sind Konfigurationswerte, keine API-Tokens. NotePilot speichert keine Login-Passwörter.

Die Access-Anwendung **vor** der Tunnel-Route erstellen: Cloudflare empfiehlt diese Reihenfolge, damit der Host nicht vorübergehend öffentlich erreichbar ist. Die Token-Prüfung im Container bleibt zusätzlich aktiv.

## 3. Repository, Konfiguration und Start

Per SSH in einem neuen Verzeichnis auf dem Homeserver:

```sh
git clone https://github.com/steju4/notepilot.git
cd notepilot
cp deploy/.env.example deploy/.env
chmod 600 deploy/.env
nano deploy/.env
```

Ersetze alle Platzhalter:

```dotenv
NOTEPILOT_DOMAIN=notepilot.stengele-home.de
NOTEPILOT_PROXY_NETWORK=dein_vorhandenes_npm_netzwerk
NOTEPILOT_ACCESS_TEAM_DOMAIN=dein-team.cloudflareaccess.com
NOTEPILOT_ACCESS_AUD=dein_application_audience_tag
NOTEPILOT_ACCESS_EMAILS=deine-adresse@example.com
NOTEPILOT_CPUS=4
NOTEPILOT_MEMORY=4g
```

Team-Hostname ohne `https://`, Pfad oder Slash. Mehrere erlaubte E-Mails durch Kommas trennen; dieselben Adressen müssen in der Cloudflare-Allow-Policy stehen. CPU-/RAM-Limits nach deinem Server anpassen und Ressourcen für die anderen Dienste lassen. Das Profil verlangt die Access-Werte und startet bei unvollständiger Auth-Konfiguration nicht ohne Schutz.

Aus dem Repository-Verzeichnis:

```sh
docker compose --env-file deploy/.env -f deploy/compose.yaml config --quiet
docker compose --env-file deploy/.env -f deploy/compose.yaml up -d --build
docker compose --env-file deploy/.env -f deploy/compose.yaml ps
docker compose --env-file deploy/.env -f deploy/compose.yaml logs --tail 80 notepilot
```

Der erste Build kann einige Minuten dauern. Der Container läuft als UID 10001 ohne zusätzliche Linux-Capabilities. Beim ersten Start kopiert er die geprüften Gewichte ins benannte Volume `notepilot_notepilot-data`. Neustarts erhalten Bibliothek und Modelle. Updates gleichen nur Modellartefakte ab und erhalten deine Dokumente/Datenbank.

## 4. nginx Proxy Manager

Einen **neuen** Proxy Host hinzufügen:

| NPM-Feld | Wert |
|---|---|
| Domain Names | `notepilot.stengele-home.de` |
| Scheme | `http` |
| Forward Hostname / IP | `notepilot` |
| Forward Port | `8000` |
| Cache Assets | aus |
| Websockets Support | nicht erforderlich |

Unter **Advanced**:

```nginx
client_max_body_size 41m;
proxy_read_timeout 120s;
proxy_send_timeout 120s;
```

NPM leitet den eingehenden `Cf-Access-Jwt-Assertion`-Header standardmäßig weiter. Den Header nicht entfernen oder durch einen festen Wert ersetzen; den ursprünglichen Website-Hostnamen erhalten. HTTP zwischen cloudflared/NPM/NotePilot ist für das interne Netz gedacht; der Browser nutzt HTTPS am Cloudflare-Endpunkt. Bei dieser internen HTTP-Route **Force SSL in NPM auslassen**, damit keine Umleitungsschleife entsteht. Wenn dein bestehender Tunnel bereits HTTPS zum NPM nutzt, dessen funktionierende TLS-Konfiguration und ein passendes Zertifikat verwenden.

## 5. Bestehenden Cloudflare Tunnel ergänzen

Eine Published application/Public hostname-Route im vorhandenen Tunnel ergänzen:

- Subdomain `notepilot`, Domain `stengele-home.de`.
- Service zum **vorhandenen NPM**, z. B. `http://DEIN_NPM_CONTAINER:80`, wenn cloudflared im selben Netzwerk läuft. Andernfalls die bereits funktionierende interne NPM-Adresse deiner anderen Routen verwenden.
- Keine direkte Route zu NotePilot und keine Router-Portfreigabe erforderlich.
- Falls `HTTP Host Header` gesetzt ist: `notepilot.stengele-home.de`, nicht die interne NPM-IP. Ohne Override bleibt der angefragte Host erhalten.
- Browser-HTTPS über deine bestehende Cloudflare-Einstellung oder eine Redirect Rule für diesen Host erzwingen.

Bei lokal verwaltetem cloudflared die entsprechende Ingress-Regel vor der abschließenden Catch-all-Regel ergänzen und bestehende Regeln erhalten. DNS muss auf den bestehenden Tunnel zeigen; bei Dashboard-verwalteten Routen wird der Eintrag normalerweise dort angelegt.

## 6. Zugriff und Funktion prüfen

In einem privaten Browserfenster `https://notepilot.stengele-home.de` öffnen: Zuerst muss Access die Anmeldung verlangen. Erst danach erscheint NotePilot. Eine nicht erlaubte Adresse darf keine Bibliothek sehen. Ohne Sitzung:

```sh
curl -I https://notepilot.stengele-home.de/
curl -I https://notepilot.stengele-home.de/api/v1/pieces
```

Erwartet: Access-Anmeldung/Weiterleitung oder Sperre, keine NotePilot-Daten. Der interne Healthcheck prüft SQLite und die Erreichbarkeit des Servers; auch `/api/v1/health` bleibt ohne Access-Token gesperrt. Ein `healthy`-Container bestätigt nicht die externen Tunnel-/Access-Einstellungen: Prüfe diese wie oben mit Browser und nicht erlaubter Adresse.

MusicXML importieren und ein Notenfoto erkennen lassen. Die Modelle sind bereits installiert. Erkennung läuft als Hintergrundjob; Ergebnisse am Original prüfen, insbesondere Auflösungszeichen. Der dokumentierte Referenztest zeigt eine bekannte HOMR-Grenze bei zwei Auflösungszeichen.

Die geschützte Online-Version nutzt **keinen Offline-Service-Worker und keinen Partiturcache in IndexedDB**. Antworten tragen `Cache-Control: no-store`. Bei abgelaufener Sitzung Seite neu laden; **Abmelden** führt zu Cloudflare Access. Bereits angezeigte Daten, andere offene Tabs und Downloads werden durch Abmelden nicht rückwirkend gelöscht.

## Update und Backup

Zunächst unter **Einstellungen → Backup exportieren** sichern und das ZIP außerhalb des Servers aufbewahren. Modelle können aus dem Image wiederhergestellt werden.

```sh
git pull --ff-only
docker compose --env-file deploy/.env -f deploy/compose.yaml up -d --build
```

Stoppen erhält die Bibliothek:

```sh
docker compose --env-file deploy/.env -f deploy/compose.yaml down
```

**Kein `down -v` verwenden**, wenn das Datenvolume erhalten bleiben soll. Für eine vollständige Volume-Sicherung NotePilot stoppen und dein bestehendes Docker-Backup-Verfahren verwenden; keine laufende SQLite-Datei isoliert kopieren.

| Symptom | Prüfen |
|---|---|
| NPM 502 | Gemeinsames Netz, Hostname `notepilot`, Port 8000, Compose-Logs |
| Nach dem Login 403 | Team, AUD dieser Anwendung, identische E-Mail-Allowlisten, JWT-Header-Weiterleitung |
| 403 trotz korrekter Werte | Container muss `https://TEAM.cloudflareaccess.com/cdn-cgi/access/certs` mit gültigem TLS erreichen können |
| Start bricht ab | Alle Platzhalter ersetzt? Netzwerk vorhanden? Access-Werte vollständig? |
| Container endet / OOM | RAM-Limit und freier RAM; größere Bilder benötigen mehr Ressourcen |
| Upload 413 | NPM-Limit; Anwendung erlaubt maximal 40 MiB pro Upload |

Offizielle Referenzen: [Self-hosted Access](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/self-hosted-public-app/), [Access-JWT-Validierung](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/authorization-cookie/validating-json/).
