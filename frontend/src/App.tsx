import { useEffect, useRef, useState } from "react";
import {
  Music2,
  LayoutDashboard,
  Library,
  Settings2,
  Plus,
  ArrowUpRight,
  Search,
  Star,
  ShieldCheck,
  ScanLine,
  Headphones,
  Repeat2,
  Folder,
  Download,
  Upload,
  WifiOff,
  X,
  LoaderCircle,
  Sun,
  Moon,
} from "lucide-react";
import { api, patch, post, cacheClear } from "./services/api";
import { ImportDialog } from "./components/ImportDialog";
import { Workspace } from "./components/Workspace";
import type { Piece, Instrument, Engine } from "./types";
function ScoreArtwork() {
  return (
    <svg className="hero-art" viewBox="0 0 430 280" aria-hidden="true">
      <defs>
        <pattern id="dots" width="18" height="18" patternUnits="userSpaceOnUse">
          <circle cx="1" cy="1" r="1" fill="#8bac95" opacity=".35" />
        </pattern>
      </defs>
      <rect width="430" height="280" fill="url(#dots)" />
      <g transform="translate(50 34) rotate(-9 155 105)">
        <rect x="8" y="10" width="310" height="220" rx="15" fill="#0e4437" opacity=".12" />
        <rect width="310" height="220" rx="15" fill="#fffdf5" />
        <text x="24" y="31" fill="#3d6657" fontSize="10" letterSpacing="2">
          UNSER NÄCHSTES LIEBLINGSSTÜCK
        </text>
        {[0, 1].map((n) => (
          <g transform={`translate(26 ${66 + n * 80})`} key={n}>
            {[0, 1, 2, 3, 4].map((i) => (
              <path key={i} d={`M0 ${i * 9} H250`} stroke="#9eb8a6" strokeWidth="1" />
            ))}
            <text x="0" y="32" fontSize="62" fill="#164e40">
              𝄞
            </text>
            {[0, 1, 2, 3, 4].map((i) => (
              <g key={i} transform={`translate(${64 + i * 38} ${21 + ((i % 3) - 1) * 9})`}>
                <ellipse
                  rx="7"
                  ry="5"
                  transform="rotate(-20)"
                  fill={i === 2 && n === 0 ? "#88ac48" : "#164e40"}
                />
                <path d="M6 0 V-32" stroke="#164e40" strokeWidth="2" />
              </g>
            ))}
          </g>
        ))}
      </g>
      <g transform="translate(258 182)">
        <rect width="135" height="61" rx="16" fill="#d9f19e" />
        <circle cx="30" cy="30" r="17" fill="#175b47" />
        <path d="m27 22 11 8-11 8Z" fill="#eafaaf" />
        {[12, 23, 32, 18, 27, 13].map((h, i) => (
          <rect key={i} x={60 + i * 9} y={30 - h / 2} width="4" height={h} rx="2" fill="#28644b" />
        ))}
      </g>
    </svg>
  );
}
function App() {
  const [route, setRoute] = useState(location.hash.slice(1) || "home"),
    [pieces, setPieces] = useState<Piece[]>([]),
    [instruments, setInstruments] = useState<Instrument[]>([]),
    [engine, setEngine] = useState<Engine>(),
    [online, setOnline] = useState(true),
    [hosted, setHosted] = useState(import.meta.env.VITE_NOTEPILOT_HOSTED === "1"),
    [importOpen, setImportOpen] = useState(false),
    [error, setError] = useState(""),
    [query, setQuery] = useState(""),
    [filter, setFilter] = useState("all"),
    [instrumentFilter, setInstrumentFilter] = useState(""),
    [sort, setSort] = useState("recent"),
    [dark, setDark] = useState(localStorage.getItem("notepilot-dark") === "true"),
    [busy, setBusy] = useState(false),
    [setup, setSetup] = useState<{ status: string; error?: string }>();
  const restoreInput = useRef<HTMLInputElement>(null);
  const notify = (message: string) => setError(message);
  const go = (path: string) => {
    if (path === "favorites") setFilter("favorites");
    if (path === "library") setFilter("all");
    location.hash = path;
    setRoute(path);
    window.scrollTo({ top: 0 });
  };
  const loadLibrary = () => {
    void api<Piece[]>("/pieces")
      .then(setPieces)
      .catch((e) => notify((e as Error).message));
  };
  useEffect(() => {
    const change = () => setRoute(location.hash.slice(1) || "home");
    window.addEventListener("hashchange", change);
    const status = (event: Event) => setOnline((event as CustomEvent<boolean>).detail);
    window.addEventListener("backend-status", status);
    loadLibrary();
    void api<{ hosted_preview: boolean }>("/runtime")
      .then((value) => setHosted(value.hosted_preview))
      .catch(() => {});
    void api<Instrument[]>("/instruments")
      .then(setInstruments)
      .catch(() => {});
    void api<Engine>("/omr/status")
      .then(setEngine)
      .catch(() => {});
    void api<{ dark?: boolean }>("/settings")
      .then((s) => {
        if (s.dark !== undefined) setDark(s.dark);
      })
      .catch(() => {});
    return () => {
      window.removeEventListener("hashchange", change);
      window.removeEventListener("backend-status", status);
    };
  }, []);
  useEffect(() => {
    document.documentElement.dataset.theme = dark ? "dark" : "light";
    localStorage.setItem("notepilot-dark", String(dark));
  }, [dark]);
  useEffect(() => {
    if (setup?.status !== "running") return;
    const interval = setInterval(() => {
      void api<{ status: string; error?: string }>("/omr/setup")
        .then((result) => {
          setSetup(result);
          if (result.status !== "running") void api<Engine>("/omr/status").then(setEngine);
        })
        .catch((e) => notify((e as Error).message));
    }, 1500);
    return () => clearInterval(interval);
  }, [setup?.status]);
  const run = async (fn: () => Promise<void>) => {
    setBusy(true);
    try {
      await fn();
    } catch (e) {
      notify((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  const sample = () =>
    run(async () => {
      const p = await post<Piece>("/pieces", {
        title: "Abend am Fluss",
        composer: "NotePilot · gemeinfreie Übung",
      });
      const source = await fetch("/example.musicxml");
      if (!source.ok) throw new Error("Beispielpartitur nicht verfügbar.");
      const form = new FormData();
      form.append(
        "file",
        new File([await source.blob()], "abend-am-fluss.musicxml", {
          type: "application/xml",
        }),
      );
      await api(`/pieces/${p.id}/documents`, { method: "POST", body: form });
      loadLibrary();
      go("piece/" + p.id);
    });
  const visible = pieces
    .filter(
      (p) =>
        (p.title + " " + p.composer + " " + p.collection)
          .toLowerCase()
          .includes(query.toLowerCase()) &&
        (filter !== "favorites" || p.favorite) &&
        (!instrumentFilter || p.instrument === instrumentFilter),
    )
    .sort((a, b) =>
      sort === "title"
        ? a.title.localeCompare(b.title, "de")
        : sort === "created"
          ? b.created_at.localeCompare(a.created_at)
          : b.updated_at.localeCompare(a.updated_at),
    );
  const currentPiece = route.startsWith("piece/") ? route.slice(6) : null;
  const toggleDark = () => {
    const value = !dark;
    setDark(value);
    if (online) void patch("/settings", { dark: value }).catch((e) => notify((e as Error).message));
  };
  const pieceCards = (items: Piece[]) => (
    <div className="library-grid">
      {items.map((p, i) => (
        <article className="piece-card" key={p.id}>
          <button
            className={`piece-cover tone-${i % 4}`}
            onClick={() => go("piece/" + p.id)}
            aria-label={`${p.title} öffnen`}
          >
            <div className="sheet-lines">
              <Music2 size={48} strokeWidth={1.3} />
            </div>
            <span className="cover-tag">
              {p.current_version ? "Digitale Partitur" : "Originalnoten"}
            </span>
            <ArrowUpRight size={20} />
          </button>
          <div className="piece-card-body">
            <button className="card-title" onClick={() => go("piece/" + p.id)}>
              {p.title}
            </button>
            <p>
              {instruments.find((i) => i.id === p.instrument)?.name ?? "Instrument"}
              {p.collection && <> · {p.collection}</>}
            </p>
            <div className="card-footer">
              <span>
                {new Date(p.updated_at).toLocaleDateString("de-DE", {
                  day: "numeric",
                  month: "short",
                })}
              </span>
              <button
                className="icon-button"
                disabled={!online}
                aria-label={`${p.title} als Favorit markieren`}
                onClick={() =>
                  run(async () => {
                    await patch(`/pieces/${p.id}`, { favorite: !p.favorite });
                    loadLibrary();
                  })
                }
              >
                <Star size={17} fill={p.favorite ? "#dba854" : "none"} />
              </button>
            </div>
          </div>
        </article>
      ))}
    </div>
  );
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <button className="brand" onClick={() => go("home")}>
          <span className="brand-mark">
            <Music2 size={25} />
          </span>
          <span>
            NotePilot<small>DEIN MUSIKPARTNER</small>
          </span>
        </button>
        <nav aria-label="Hauptnavigation">
          <button
            className={route === "home" ? "nav-item active" : "nav-item"}
            onClick={() => go("home")}
          >
            <LayoutDashboard size={19} />
            Übersicht
          </button>
          <button
            className={route === "library" || currentPiece ? "nav-item active" : "nav-item"}
            onClick={() => go("library")}
          >
            <Library size={19} />
            Meine Noten<span className="nav-count">{pieces.length}</span>
          </button>
          <button
            className={route === "favorites" ? "nav-item active" : "nav-item"}
            onClick={() => {
              setFilter("favorites");
              go("favorites");
            }}
          >
            <Star size={19} />
            Favoriten
          </button>
          <button
            className={route === "settings" ? "nav-item active" : "nav-item"}
            onClick={() => go("settings")}
          >
            <Settings2 size={19} />
            Einstellungen
          </button>
        </nav>
        <div className="sidebar-bottom">
          <div className="privacy-note">
            <ShieldCheck size={23} />
            <strong>{hosted ? "Online-Testversion" : "Deine Musik bleibt bei dir."}</strong>
            <p>
              Keine Anmeldung.
              <br />
              {hosted ? "Verarbeitung auf dem Testserver." : "Keine Cloud. Einfach üben."}
            </p>
          </div>
          <div className="engine-indicator">
            <span className={`status-dot ${!engine?.ready ? "pending" : ""}`} />
            <span>
              {engine?.ready ? "Lokale KI bereit" : "KI-Einrichtung prüfen"}
              <small>{engine?.name ?? "Notenerkennung"} · CPU</small>
            </span>
          </div>
          <span className="sidebar-version">NotePilot 0.1 · mit Musik im Kopf</span>
        </div>
      </aside>
      <div className="app-content">
        <header className="topbar">
          <div className="breadcrumb">
            Dein Raum für Musik <span>/</span>{" "}
            {currentPiece
              ? "Üben"
              : route === "settings"
                ? "Einstellungen"
                : route === "home"
                  ? "Übersicht"
                  : "Meine Noten"}
          </div>
          <div className="button-row">
            <button
              className="icon-button"
              aria-label={dark ? "Helles Design" : "Dunkles Design"}
              onClick={toggleDark}
            >
              {dark ? <Sun size={19} /> : <Moon size={19} />}
            </button>
            <button
              className="primary small"
              disabled={!online}
              onClick={() => setImportOpen(true)}
            >
              <Plus size={17} />
              Noten hinzufügen
            </button>
          </div>
        </header>
        <main>
          {hosted && (
            <div className="notice">
              <ShieldCheck size={22} />
              <div>
                <strong>Online-Testversion</strong>
                <p>
                  Noten und Uploads werden auf diesem Testserver verarbeitet und gespeichert. Der
                  Browser führt die Notenerkennung nicht selbst aus. Die Bibliothek liegt im
                  dauerhaften Datenvolume. Sichere wichtige Ergebnisse zusätzlich per Export.
                </p>
              </div>
            </div>
          )}
          {!online && (
            <div className="notice warning">
              <WifiOff size={22} />
              <div>
                <strong>
                  {hosted
                    ? "Server nicht erreichbar oder Zugangsdaten erforderlich."
                    : "Der lokale Server ist nicht erreichbar."}
                </strong>
                <p>
                  {hosted
                    ? "Lade die Seite neu, um dich erneut anzumelden. Die geschützte Online-Version speichert keine Offline-Partituren im Browser."
                    : "Bereits geöffnete digitale Stücke sind aus dem Browsercache verfügbar. Erkennung und Speichern benötigen den laufenden Computer."}
                </p>
              </div>
              <button
                className="secondary"
                onClick={() => {
                  loadLibrary();
                  void api<Engine>("/omr/status").then(setEngine);
                }}
              >
                Erneut verbinden
              </button>
            </div>
          )}
          {currentPiece ? (
            <Workspace
              hosted={hosted}
              key={currentPiece}
              id={currentPiece}
              instruments={instruments}
              online={online}
              onBack={() => go("library")}
              onError={notify}
              onLibraryChange={loadLibrary}
            />
          ) : route === "settings" ? (
            <>
              <span className="eyebrow">ALLES UNTER DEINER KONTROLLE</span>
              <h1>Dein NotePilot</h1>
              <p className="page-intro">Lokal eingerichtet. Für deine Musik gemacht.</p>
              <div className="settings-grid">
                <section className="panel">
                  <div className="section-heading">
                    <h2>Lokale Notenerkennung</h2>
                    <ScanLine size={22} />
                  </div>
                  <span className={`badge ${engine?.ready ? "success" : ""}`}>
                    {engine?.ready ? "Bereit für CPU-Erkennung" : "Einrichtung erforderlich"}
                  </span>
                  <p>
                    {engine?.name ?? "Die Erkennung"} {engine?.version} verarbeitet gedruckte Noten
                    lokal. Nur die erstmalige Installation benötigt einen Download.
                  </p>
                  {engine?.message && <p>{engine.message}</p>}
                  {engine?.models.map((m) => (
                    <div className="model-row" key={m.name}>
                      <span>
                        {m.name.split("_")[0]}
                        <small>
                          {m.present ? (m.bytes / 1024 / 1024).toFixed(1) + " MB" : "Fehlt"}
                        </small>
                      </span>
                      <span>{m.present ? "✓" : "–"}</span>
                    </div>
                  ))}
                  <button
                    className="primary"
                    disabled={busy || setup?.status === "running" || !online}
                    onClick={() => run(async () => setSetup(await post("/omr/setup")))}
                  >
                    {setup?.status === "running" ? (
                      <>
                        <LoaderCircle className="spin" size={17} />
                        KI-Modell wird eingerichtet …
                      </>
                    ) : (
                      <>
                        <Download size={17} />
                        {engine?.ready
                          ? "Modellinstallation prüfen"
                          : "Lokales KI-Modell einrichten"}
                      </>
                    )}
                  </button>
                  {setup?.error && (
                    <p className="error" role="alert">
                      {setup.error}
                    </p>
                  )}
                  <p className="small muted">
                    AGPL-3.0 · Erkennungsfehler sind möglich. Dynamik, Artikulation und musikalische
                    Sprünge müssen geprüft werden. Keine künstlichen Konfidenzwerte.
                  </p>
                </section>
                <section className="panel">
                  <h2>Deine lokale Bibliothek</h2>
                  <p>
                    Sichere Originaldateien, Partituren, Korrekturversionen, Einstellungen und
                    Übungspassagen in einem Archiv.
                  </p>
                  <a
                    className={`secondary full ${!online ? "disabled" : ""}`}
                    href="/api/v1/backup"
                    download
                  >
                    <Download size={17} />
                    Bibliothek sichern
                  </a>
                  <button
                    className="secondary full"
                    disabled={busy || !online}
                    onClick={() => restoreInput.current?.click()}
                  >
                    <Upload size={17} />
                    Sicherung wiederherstellen
                  </button>
                  <input
                    ref={restoreInput}
                    type="file"
                    accept=".zip"
                    hidden
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file)
                        void run(async () => {
                          const form = new FormData();
                          form.append("file", file);
                          await api("/backup/restore", {
                            method: "POST",
                            body: form,
                          });
                          await cacheClear();
                          loadLibrary();
                        });
                      e.target.value = "";
                    }}
                  />
                  <p className="small muted">
                    Wiederherstellung erfolgt in eine leere Bibliothek. Vorhandene Stücke werden
                    geschützt. Modelle werden separat installiert.
                  </p>
                  <hr />
                  <h3>Darstellung</h3>
                  <button className="secondary" onClick={toggleDark}>
                    {dark ? <Sun size={17} /> : <Moon size={17} />}{" "}
                    {dark ? "Helles Design aktivieren" : "Dunkles Design aktivieren"}
                  </button>
                  <hr />
                  <h3>Smartphone im WLAN</h3>
                  <p className="small">
                    Aktiviere den LAN-Modus im lokalen Startskript. Smartphone und Computer müssen
                    im selben vertrauenswürdigen Netzwerk sein. Die Dateiauswahl unterstützt
                    Kameraaufnahmen; eine Live-Kamera benötigt je nach Browser HTTPS.
                  </p>
                </section>
              </div>
            </>
          ) : (
            <>
              {route === "home" ? (
                <>
                  <section className="hero">
                    <div>
                      <span className="eyebrow">WENIGER GRÜBELN. MEHR MUSIK.</span>
                      <h1>
                        Deine Noten.
                        <br />
                        Dein nächster
                        <br />
                        <em>großer Moment.</em>
                      </h1>
                      <p>
                        Vom Notenblatt zum Lieblingsstück.
                        <br />
                        Erkennen, anhören und in deinem Tempo üben.
                      </p>
                      <div className="button-row">
                        <button
                          className="primary"
                          disabled={!online}
                          onClick={() => setImportOpen(true)}
                        >
                          <Plus size={18} />
                          Neue Noten hinzufügen
                        </button>
                        <button className="text-button" disabled={busy || !online} onClick={sample}>
                          Beispiel ausprobieren <ArrowUpRight size={17} />
                        </button>
                      </div>
                      <div className="hero-trust">
                        <ShieldCheck size={16} />
                        {hosted
                          ? "Direkt im Browser ausprobieren."
                          : "Lokal. Privat. Ohne laufende Kosten."}
                      </div>
                    </div>
                    <ScoreArtwork />
                  </section>
                  <div className="workflow-cards">
                    {[
                      {
                        icon: ScanLine,
                        n: "01",
                        title: "Ein Blatt wird Musik",
                        text: "Foto oder PDF hinzufügen und auf deinem Computer erkennen.",
                      },
                      {
                        icon: Headphones,
                        n: "02",
                        title: "Hör, was vor dir liegt",
                        text: "Noten prüfen, dein Instrument wählen und die Melodie hören.",
                      },
                      {
                        icon: Repeat2,
                        n: "03",
                        title: "Jeder Takt ein Fortschritt",
                        text: "Langsamer starten, Passagen wiederholen und sicherer werden.",
                      },
                    ].map((c) => (
                      <div className="workflow-card" key={c.n}>
                        <span className="workflow-icon">
                          <c.icon size={20} />
                        </span>
                        <span className="workflow-number">{c.n}</span>
                        <h3>{c.title}</h3>
                        <p>{c.text}</p>
                      </div>
                    ))}
                  </div>
                  <div className="section-heading library-heading">
                    <div>
                      <span className="eyebrow">DEINE MUSIK WARTET SCHON</span>
                      <h2>Zuletzt hinzugefügt</h2>
                    </div>
                    <button
                      className="text-button"
                      onClick={() => {
                        setFilter("all");
                        go("library");
                      }}
                    >
                      Alle Noten <ArrowUpRight size={17} />
                    </button>
                  </div>
                  {pieces.length ? (
                    pieceCards(pieces.slice(0, 4))
                  ) : (
                    <section className="empty-library">
                      <span className="round-icon">
                        <Music2 size={30} />
                      </span>
                      <h3>Hier beginnt deine Notensammlung.</h3>
                      <p>
                        Füge dein erstes Stück hinzu oder lerne NotePilot mit unserer gemeinfreien
                        Beispielpartitur kennen.
                      </p>
                      <button className="secondary" disabled={busy || !online} onClick={sample}>
                        „Abend am Fluss“ ausprobieren
                      </button>
                    </section>
                  )}
                </>
              ) : (
                <>
                  <span className="eyebrow">ALLES, WAS DU SPIELEN MÖCHTEST</span>
                  <div className="section-heading">
                    <h1>{route === "favorites" ? "Deine Favoriten" : "Meine Noten"}</h1>
                    <span className="badge">{pieces.length} Stücke · lokal</span>
                  </div>
                  <p className="page-intro">Deine Partituren, deine Passagen, dein Fortschritt.</p>
                  <div className="library-tools">
                    <label className="search">
                      <Search size={18} />
                      <input
                        aria-label="Noten durchsuchen"
                        placeholder="Titel, Komponist oder Sammlung suchen …"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                      />
                    </label>
                    <select
                      aria-label="Instrumentfilter"
                      value={instrumentFilter}
                      onChange={(e) => setInstrumentFilter(e.target.value)}
                    >
                      <option value="">Alle Instrumente</option>
                      {instruments.map((i) => (
                        <option key={i.id} value={i.id}>
                          {i.name}
                        </option>
                      ))}
                    </select>
                    <select
                      aria-label="Sortierung"
                      value={sort}
                      onChange={(e) => setSort(e.target.value)}
                    >
                      <option value="recent">Zuletzt bearbeitet</option>
                      <option value="title">Titel A–Z</option>
                      <option value="created">Importdatum</option>
                    </select>
                  </div>
                  <div className="button-row library-tabs">
                    <button
                      className={filter === "all" ? "tab active" : "tab"}
                      onClick={() => setFilter("all")}
                    >
                      <Folder size={16} />
                      Alle Stücke
                    </button>
                    <button
                      className={filter === "favorites" ? "tab active" : "tab"}
                      onClick={() => setFilter("favorites")}
                    >
                      <Star size={16} />
                      Favoriten
                    </button>
                  </div>
                  {visible.length ? (
                    pieceCards(visible)
                  ) : (
                    <div className="empty-library">
                      <Music2 size={35} />
                      <h3>
                        {pieces.length ? "Keine passenden Stücke." : "Platz für deine Musik."}
                      </h3>
                      <p>
                        {pieces.length
                          ? "Ändere die Suche oder den Filter."
                          : "Füge ein Foto, ein PDF oder eine MusicXML-Partitur hinzu."}
                      </p>
                    </div>
                  )}
                </>
              )}
              <footer>
                <span>Für die Freude am Musikmachen.</span>
                <span>
                  <ShieldCheck size={15} />
                  {hosted ? "Testdaten liegen auf dem Testserver." : "Deine Daten bleiben lokal."}
                </span>
              </footer>
            </>
          )}
        </main>
      </div>
      {importOpen && (
        <ImportDialog
          hosted={hosted}
          onClose={() => setImportOpen(false)}
          onError={notify}
          onImported={(id) => {
            setImportOpen(false);
            loadLibrary();
            go("piece/" + id);
          }}
        />
      )}
      {error && (
        <div className="toast" role="alert">
          <span>{error}</span>
          <button
            className="icon-button"
            aria-label="Hinweis schließen"
            onClick={() => setError("")}
          >
            <X size={18} />
          </button>
        </div>
      )}
    </div>
  );
}
export default App;
