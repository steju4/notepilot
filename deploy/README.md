# NotePilot privat auf deinem Homeserver

Ziel: **https://notepilot.stengele-home.de**, über **Cloudflare Tunnel → nginx Proxy Manager → NotePilot**. Beim ersten Aufruf fordert das Backend mit HTTP 401 und `WWW-Authenticate: Basic realm="NotePilot", charset="UTF-8"` den normalen Browserdialog für Benutzername und Passwort an. Oberfläche, API, Originalbilder, Dateien und Downloads sind geschützt. Es gibt keine eigene Loginseite und keine Cloudflare-Access-Anmeldung.

Das Profil passt zu Linux x86_64, vier CPU-Kernen und etwa 7,1 GiB RAM: **2 CPU-Kerne, 4 GB RAM-Limit, bestehendes Netz `docker_proxy`**. Es veröffentlicht keinen NotePilot-Host-Port. Alle Zugriffe mit demselben Benutzer teilen eine Bibliothek.

## 1. Repository und Image vorbereiten

Per SSH auf dem Homeserver, Docker mit Compose v2 und Git vorausgesetzt:

```sh
git clone https://github.com/steju4/notepilot.git
cd notepilot
cp deploy/.env.example deploy/.env
chmod 600 deploy/.env
```

Bei einem bestehenden Checkout stattdessen `git pull --ff-only` verwenden; bestehende `.env`-Dateien nicht überschreiben. `deploy/.env` an diese Werte anpassen:

```dotenv
NOTEPILOT_DOMAIN=notepilot.stengele-home.de
NOTEPILOT_PROXY_NETWORK=docker_proxy
NOTEPILOT_AUTH_SECRET_FILE=/etc/notepilot/basic-auth.json
NOTEPILOT_CPUS=2
NOTEPILOT_MEMORY=4g
```

Alte `NOTEPILOT_ACCESS_*`-Werte entfernen. Domain, Netz und Secret-Pfad sind Konfiguration; **kein Passwort oder Hash in `.env` eintragen**. Das Backend verlangt im Hostingprofil ein gültiges Secret und startet bei fehlender, unlesbarer oder ungültiger Datei nicht. Auch alte Access-Variablen werden abgelehnt, damit eine veraltete Konfiguration keinen ungeschützten Betrieb erzeugt.

Prüfen und bauen:

```sh
docker network inspect docker_proxy --format '{{.Name}}'
docker compose --env-file deploy/.env -f deploy/compose.yaml config --quiet
docker compose --env-file deploy/.env -f deploy/compose.yaml build
```

Das Netz wird bereits von NPM und cloudflared verwendet; kein neues Proxy-Netz anlegen. Beim ersten Build werden alle Abhängigkeiten und ungefähr 150 MiB CPU-Modellgewichte installiert. Mehrere GB freien Speicher für Build, Image und Bibliothek vorsehen. Besucher brauchen keine lokale Installation. Erkennung benötigt danach keinen externen KI-Dienst und keine GPU. Die 4-GB-Grenze gilt zur Laufzeit, nicht für den Image-Bau; vorhandene Dienste brauchen zusätzlich RAM.

## 2. Secret außerhalb von Git und Image erstellen

Die Anwendung läuft als UID/GID **10001**. Bereite einen privaten Ordner außerhalb des Repositorys vor:

```sh
sudo install -d -m 750 -o 10001 -g 10001 /etc/notepilot
```

Mit dem gerade gebauten Image Benutzername und Passwort interaktiv abfragen:

```sh
docker run --rm -it --network none --read-only --cap-drop ALL --security-opt no-new-privileges:true \
  --mount type=bind,src=/etc/notepilot,dst=/auth \
  --entrypoint /app/.venv/bin/python \
  notepilot-homeserver:local /app/scripts/create_basic_auth.py --output /auth/basic-auth.json
```

Das Passwort wird verdeckt eingegeben und bestätigt, nicht als Befehlsargument oder Umgebungsvariable übergeben. Wähle mindestens 12 Zeichen. Die Datei enthält genau `username` und einen gesalzenen **scrypt-Passwort-Hash**, kein Klartextpasswort. Es gibt keine Standardzugangsdaten. Dateimodus 0600, Eigentümer UID 10001; nur dieser Benutzer und Host-Administratoren können sie lesen. Compose mountet sie schreibgeschützt unter `/run/secrets/notepilot_basic_auth`. Bei lokalem Compose handelt es sich um eine Datei auf dem Host, nicht um einen verschlüsselten Secret-Vault.

Wenn du einen anderen Host-Pfad verwendest, die Ordner-/Mount-Angaben und `NOTEPILOT_AUTH_SECRET_FILE` entsprechend anpassen. Secret weder in Git aufnehmen noch ins Image kopieren. `.gitignore` und `.dockerignore` schließen bekannte Secret-Dateien zusätzlich aus.

## 3. Container starten

```sh
docker compose --env-file deploy/.env -f deploy/compose.yaml up -d
docker compose --env-file deploy/.env -f deploy/compose.yaml ps
docker compose --env-file deploy/.env -f deploy/compose.yaml logs --tail 80 notepilot
```

Das benannte Volume **`notepilot_notepilot-data`** hält Bibliothek und Modelle dauerhaft. Der erste Start übernimmt die geprüften Gewichte aus dem Image. Neustarts und Updates erhalten eigene Dokumente und SQLite-Datenbank. Der interne Healthcheck prüft SQLite und die erwartete HTTP-401-Antwort samt Challenge; er speichert kein Klartextpasswort und öffnet keine Ausnahme für `/api/v1/health`.

## 4. nginx Proxy Manager

Einen neuen Proxy Host erstellen bzw. den vorhandenen NotePilot-Host anpassen:

| Feld | Wert |
|---|---|
| Domain Names | `notepilot.stengele-home.de` |
| Scheme | `http` |
| Forward Hostname / IP | `notepilot` |
| Forward Port | `8000` |
| Cache Assets | aus |
| Access List | `Publicly Accessible` — Anmeldung übernimmt das Backend |
| Websockets Support | nicht erforderlich |

Unter **Advanced**:

```nginx
client_max_body_size 41m;
proxy_read_timeout 120s;
proxy_send_timeout 120s;
```

NPM muss den eingehenden **`Authorization`-Header**, den ursprünglichen Host und die **401-/`WWW-Authenticate`-Antwort** unverändert weiterleiten. Standardmäßig tut es das. Keine zusätzliche NPM-Basic-Auth-Liste, kein `proxy_hide_header WWW-Authenticate`, keine 401-Fehlerumleitung und kein Cache für diesen Host einrichten. Änderungen an Vaultwarden oder anderen Proxy Hosts sind nicht erforderlich.

Bei HTTP vom Tunnel zum NPM **Force SSL in NPM auslassen**, um Umleitungsschleifen zu vermeiden. Browser-HTTPS stellt Cloudflare bereit. Für ein vorhandenes, funktionierendes HTTPS-Tunnelziel die bestehende TLS-Konfiguration verwenden.

## 5. Bestehenden Cloudflare Tunnel ergänzen

Für `notepilot.stengele-home.de` eine Public-hostname/Published-application-Route zum vorhandenen NPM anlegen, etwa `http://NAME_DEINES_NPM_CONTAINERS:80`. NPM und cloudflared hängen bereits in `docker_proxy`. Die DNS-Route muss auf deinen bestehenden Tunnel zeigen. Kein direkter Tunnel zum NotePilot-Port und keine neue Router-Portfreigabe.

Ein gesetzter `HTTP Host Header` muss `notepilot.stengele-home.de` lauten. `Authorization` und die Basic-Challenge unverändert passieren lassen. HTTPS für diesen Host über deine vorhandene Cloudflare-HTTPS-Einstellung oder eine Redirect Rule erzwingen. Basic Auth überträgt Zugangsdaten bei jeder Anfrage und setzt deshalb HTTPS im Browser voraus; intern nutzt dieser Aufbau das HTTP-Docker-Netz.

Falls zuvor Cloudflare Access für NotePilot eingerichtet wurde: **erst den geschützten Container starten**, dann die Access-Anwendung/Policy bzw. Tunnel-Option „Protect with Access“ **nur für diesen Host** entfernen. Eine weiter greifende Access-Regel darf diesen Host ebenfalls nicht mehr abfangen. Sonst erscheint weiterhin die Cloudflare-Loginseite. Andere Dienste und deren Access-Regeln beibehalten.

## 6. Zugriff und Funktion prüfen

Ohne Zugangsdaten müssen Website und API **401**, `WWW-Authenticate: Basic ...` und `Cache-Control: no-store` liefern:

```sh
curl -sS -D - -o /dev/null https://notepilot.stengele-home.de/
curl -sS -D - -o /dev/null https://notepilot.stengele-home.de/api/v1/pieces
```

Für einen authentifizierten Test ersetzt du `DEIN_BENUTZERNAME`; curl fragt das Passwort verdeckt ab:

```sh
curl --user DEIN_BENUTZERNAME -sS -D - -o /dev/null https://notepilot.stengele-home.de/api/v1/health
```

Richtiges Passwort: 200. Falsches Passwort: 401 mit Challenge. Im Browser ein neues privates Fenster öffnen: Der native Dialog erscheint, nach korrekter Eingabe NotePilot. Kein E-Mail-Code und keine eigene Loginseite. Wenn kein Dialog erscheint und sofort die App lädt, kann der Browser noch gültige Basic-Auth-Zugangsdaten gespeichert haben.

MusicXML importieren und ein Notenfoto erkennen lassen. Originalbilder und MIDI-/MusicXML-/Backup-Downloads müssen ebenfalls geschützt sein. Die Modelle sind schon vorhanden. Erkennungsausgaben am Original prüfen, besonders Auflösungszeichen; HOMR hat dort eine dokumentierte Genauigkeitsgrenze.

Die Online-Version nutzt **keinen Offline-Service-Worker und keinen IndexedDB-Partiturcache**; geschützte Antworten einschließlich 401 tragen `no-store`. Einen Abmeldelink gibt es nicht: Browser können Basic-Auth-Zugangsdaten weiter speichern. Tab-Schließen oder Neuladen garantiert kein Abmelden. Zum privaten Testen ein separates Browserprofil/privates Fenster verwenden und danach alle zugehörigen privaten Fenster schließen; gespeicherte Zugangsdaten gegebenenfalls im Browser entfernen. Bereits geladene Tabs, Screenshots und Downloads werden nicht rückwirkend gelöscht.

## Passwort ändern

Das Erstellungswerkzeug erneut mit `--replace` ausführen:

```sh
docker run --rm -it --network none --read-only --cap-drop ALL --security-opt no-new-privileges:true \
  --mount type=bind,src=/etc/notepilot,dst=/auth \
  --entrypoint /app/.venv/bin/python \
  notepilot-homeserver:local /app/scripts/create_basic_auth.py --output /auth/basic-auth.json --replace

docker compose --env-file deploy/.env -f deploy/compose.yaml up -d --force-recreate notepilot
```

Ein Neuerstellen ist notwendig: Die Konfiguration wird beim Prozessstart gelesen, und atomar ersetzte Secret-Dateien benötigen einen neuen Datei-Mount. Das Datenvolume bleibt erhalten. Alte gespeicherte Browserzugangsdaten sind danach ungültig.

## Backup, Update und Abschalten

Vor Updates **Einstellungen → Backup exportieren** nutzen und das ZIP außerhalb des Servers aufbewahren. Das Auth-Secret liegt außerhalb des Datenvolumes; separat sicher aufbewahren oder mit einem neuen Passwort neu erstellen.

```sh
git pull --ff-only
docker compose --env-file deploy/.env -f deploy/compose.yaml up -d --build
```

Einfach abschalten, **mit Datenerhalt**:

```sh
docker compose --env-file deploy/.env -f deploy/compose.yaml down
```

Wieder einschalten: `docker compose --env-file deploy/.env -f deploy/compose.yaml up -d`. **Kein `down -v`**, solange du das Datenvolume behalten willst. Für eine vollständige Volume-Sicherung NotePilot stoppen und dein bestehendes Docker-Backup-Verfahren nutzen; keine laufende SQLite-Datei isoliert kopieren.

| Symptom | Prüfen |
|---|---|
| Start verweigert | Secret-Pfad, JSON/Hash-Format, Eigentümer UID 10001, Leserechte; Logs |
| NPM 502 | Netz `docker_proxy`, Hostname `notepilot`, Port 8000, Containerstatus |
| Ständig 401 | Benutzername/Passwort, Weiterleitung von `Authorization`, neuer Container nach Secret-Wechsel |
| Cloudflare-Loginseite | Noch aktive Access-Regel oder Protect-with-Access für diesen Host |
| Statt 401 eine Loginseite/Weiterleitung | NPM-Fehlerumleitung, vorgeschaltete Auth-Regel oder HTTP→HTTPS-Weiterleitung |
| 403 nach korrektem Login | Host-/Origin-Prüfung; ursprünglichen Hostnamen erhalten |
| Container endet / OOM | Freier RAM zusätzlich zu anderen Diensten; größere Notenbilder brauchen mehr Ressourcen |
| Upload 413 | NPM-Limit; Anwendung erlaubt maximal 40 MiB pro Upload |

Das Image und die Schutzmechanismen werden in der Entwicklungsumgebung geprüft. Dein tatsächlicher Tunnel und die öffentlich erreichbare HTTPS-Adresse müssen nach deiner Einrichtung wie oben geprüft werden.
