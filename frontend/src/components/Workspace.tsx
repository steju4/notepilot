import { useCallback, useEffect, useRef, useState } from "react";
import {
  ArrowLeft,
  Play,
  Pause,
  Square,
  Repeat2,
  Volume2,
  Undo2,
  Redo2,
  Download,
  ScanLine,
  SlidersHorizontal,
  Image as ImageIcon,
  Music2,
  LoaderCircle,
  ChevronUp,
  ChevronDown,
  Save,
  Star,
  Copy,
  Trash2,
  CheckCircle2,
  TriangleAlert,
} from "lucide-react";
import { api, patch, post, scoreXml, download, cachePut } from "../services/api";
import { defaults, germanNote, buildPlan } from "../services/timing";
import { Player, type Position } from "../services/player";
import { ScoreView } from "./ScoreView";
import { NoteEditor } from "./NoteEditor";
import { ImageEditor } from "./ImageEditor";
import type {
  Detail,
  Score,
  Instrument,
  PlaybackSettings,
  NoteEvent,
  Page,
  Section,
  Job,
} from "../types";
const emptyPosition: Position = {
  seconds: 0,
  total: 0,
  measure: 1,
  event: null,
  cycle: 1,
  speed: 1,
  state: "stopped",
  counting: false,
};
const time = (seconds: number) =>
  `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, "0")}`;
export function Workspace({
  id,
  instruments,
  online,
  onBack,
  onError,
  onLibraryChange,
}: {
  id: string;
  instruments: Instrument[];
  online: boolean;
  onBack: () => void;
  onError: (message: string) => void;
  onLibraryChange: () => void;
}) {
  const [piece, setPiece] = useState<Detail>(),
    [score, setScore] = useState<Score>(),
    [xml, setXml] = useState(""),
    [settings, setSettings] = useState<PlaybackSettings>({ ...defaults }),
    [sections, setSections] = useState<Section[]>([]);
  const [selected, setSelected] = useState<NoteEvent | null>(null),
    [editingPage, setEditingPage] = useState<Page | null>(null),
    [mode, setMode] = useState("digital"),
    [pageIndex, setPageIndex] = useState(0),
    [zoom, setZoom] = useState(0.85),
    [position, setPosition] = useState<Position>(emptyPosition),
    [busy, setBusy] = useState(false),
    [sectionName, setSectionName] = useState("Meine Passage"),
    [rename, setRename] = useState(false),
    [draftTitle, setDraftTitle] = useState(""),
    [measureEdit, setMeasureEdit] = useState(1);
  const player = useRef<Player | null>(null);
  if (!player.current) player.current = new Player();
  const settingsRef = useRef<PlaybackSettings>({ ...defaults });
  const settingsQueue = useRef<Promise<unknown>>(Promise.resolve());
  const initialized = useRef(false),
    alive = useRef(true),
    sessionStart = useRef<number | null>(null),
    sessionDuration = useRef(0);
  const refresh = useCallback(async () => {
    const detail = await api<Detail>(`/pieces/${id}`);
    if (!alive.current) return;
    setPiece(detail);
    setDraftTitle(detail.title);
    if (detail.current_version) {
      const [s, x, p] = await Promise.all([
        api<Score>(`/pieces/${id}/score`),
        scoreXml(id),
        api<Section[]>(`/pieces/${id}/practice-sections`),
      ]);
      if (!alive.current) return;
      setScore(s);
      setXml(x);
      setSections(p);
      if (!initialized.current) {
        const initial = {
          ...defaults,
          end: s.measure_count,
          ...detail.playback_settings,
        };
        settingsRef.current = initial;
        setSettings(initial);
        initialized.current = true;
      }
    }
  }, [id]);
  const run = async (action: () => Promise<void>) => {
    setBusy(true);
    try {
      await action();
    } catch (e) {
      onError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  useEffect(() => {
    alive.current = true;
    void refresh().catch((e) => onError((e as Error).message));
    return () => {
      alive.current = false;
      player.current?.dispose();
    };
  }, [refresh]);
  const job = piece?.jobs.find((j) => j.status === "queued" || j.status === "running");
  useEffect(() => {
    if (!job) return;
    const timer = setInterval(() => {
      void api<Job>(`/recognition-jobs/${job.id}`)
        .then(async (result) => {
          if (!alive.current) return;
          setPiece((old) =>
            old
              ? {
                  ...old,
                  jobs: old.jobs.map((j) => (j.id === result.id ? result : j)),
                }
              : old,
          );
          if (!["queued", "running"].includes(result.status)) {
            await refresh();
            onLibraryChange();
          }
        })
        .catch((e) => {
          clearInterval(timer);
          onError((e as Error).message);
        });
    }, 1200);
    return () => clearInterval(timer);
  }, [job?.id, refresh]);
  useEffect(() => {
    if (position.state === "playing" && sessionStart.current === null)
      sessionStart.current = Date.now();
    if (position.state !== "playing" && sessionStart.current !== null) {
      sessionDuration.current += (Date.now() - sessionStart.current) / 1000;
      sessionStart.current = null;
    }
    if (position.state === "stopped" && sessionDuration.current > 1) {
      const duration = sessionDuration.current;
      sessionDuration.current = 0;
      void post(`/pieces/${id}/practice-sessions`, { duration }).catch(() => {});
    }
  }, [position.state, id]);
  const updateSettings = (changes: Partial<PlaybackSettings>) => {
    player.current?.stop();
    const next = { ...settingsRef.current, ...changes };
    settingsRef.current = next;
    setSettings(next);
    if (piece)
      void cachePut(`/api/v1/pieces/${id}`, {
        ...piece,
        playback_settings: next,
      });
    if (online)
      settingsQueue.current = settingsQueue.current
        .then(() => patch(`/pieces/${id}`, { playback_settings: next }, { keepalive: true }))
        .catch((e) => onError((e as Error).message));
  };
  const select = (note: NoteEvent) => {
    player.current?.stop();
    setSelected(note);
    if (note.sounding_midi !== null)
      void player.current
        ?.audition(note.sounding_midi, piece!.instrument, settings.volume)
        .catch((e) => onError((e as Error).message));
  };
  const changeNote = (action: string, fields: Record<string, unknown>) =>
    run(async () => {
      player.current?.stop();
      await patch(`/pieces/${id}/score`, {
        action,
        event_id: selected!.id,
        fields,
        version_id: score?.version_id,
      });
      setSelected(null);
      await refresh();
      onLibraryChange();
    });
  const start = () => {
    if (!score || !piece) return;
    if (position.state === "paused") {
      player.current?.pause();
      return;
    }
    void player.current
      ?.start(score, settings, piece.instrument, setPosition)
      .catch((e) => onError((e as Error).message));
  };
  const versionIndex = piece?.versions.findIndex((v) => v.id === piece.current_version) ?? -1;
  const version = (offset: number) =>
    run(async () => {
      player.current?.stop();
      await post(`/pieces/${id}/versions/${piece!.versions[versionIndex + offset].id}`);
      setSelected(null);
      await refresh();
    });
  const upload = async (files: FileList | null) => {
    if (!files) return;
    await run(async () => {
      for (const file of Array.from(files)) {
        const form = new FormData();
        form.append("file", file);
        await api(`/pieces/${id}/documents`, { method: "POST", body: form });
      }
      await refresh();
      onLibraryChange();
    });
  };
  const changeInstrument = (instrument: string, notation = piece?.notation) =>
    run(async () => {
      player.current?.stop();
      await patch(`/pieces/${id}`, { instrument, notation });
      await refresh();
      onLibraryChange();
    });
  if (!piece)
    return (
      <div className="loading">
        <LoaderCircle className="spin" />
        Stück wird geladen …
      </div>
    );
  const latestJob = piece.jobs[0],
    original = piece.pages[pageIndex],
    measures = score?.parts[0].measures ?? [],
    plan = score ? buildPlan(score, settings) : undefined;
  return (
    <>
      <div className="workspace-heading">
        <button className="text-button" onClick={onBack}>
          <ArrowLeft size={17} />
          Meine Noten
        </button>
        <div className="button-row">
          <button
            className="icon-button"
            title="Favorit"
            aria-label="Als Favorit markieren"
            disabled={!online}
            onClick={() =>
              run(async () => {
                await patch(`/pieces/${id}`, { favorite: !piece.favorite });
                await refresh();
                onLibraryChange();
              })
            }
          >
            <Star size={19} fill={piece.favorite ? "#dba854" : "none"} />
          </button>
          <button
            className="text-button"
            disabled={!online}
            onClick={() =>
              run(async () => {
                await post(`/pieces/${id}/duplicate`);
                onLibraryChange();
              })
            }
          >
            <Copy size={16} />
            Duplizieren
          </button>
          <button
            className="icon-button danger"
            aria-label="Stück löschen"
            disabled={!!job || !online}
            onClick={() => {
              if (window.confirm(`„${piece.title}“ mit allen lokalen Dateien löschen?`))
                void run(async () => {
                  await api(`/pieces/${id}`, { method: "DELETE" });
                  onLibraryChange();
                  onBack();
                });
            }}
          >
            <Trash2 size={17} />
          </button>
        </div>
      </div>
      <div className="piece-heading">
        <div>
          <span className="eyebrow">DEIN ÜBUNGSRAUM</span>
          {rename ? (
            <div className="button-row">
              <input
                aria-label="Stücktitel"
                value={draftTitle}
                maxLength={200}
                onChange={(e) => setDraftTitle(e.target.value)}
              />
              <button
                className="primary"
                onClick={() =>
                  run(async () => {
                    await patch(`/pieces/${id}`, { title: draftTitle });
                    setRename(false);
                    await refresh();
                    onLibraryChange();
                  })
                }
              >
                Speichern
              </button>
            </div>
          ) : (
            <h1>
              {piece.title}
              <button
                className="text-button small"
                onClick={() => setRename(true)}
                disabled={!online}
              >
                Umbenennen
              </button>
            </h1>
          )}
          <p>
            {piece.composer || "Deine lokale Partitur"} <span className="dot">·</span>{" "}
            {score
              ? `${score.measure_count} Takte · ${score.parts.length} Stimme${score.parts.length === 1 ? "" : "n"}`
              : `${piece.pages.length} Bildseite${piece.pages.length === 1 ? "" : "n"}`}
          </p>
        </div>
        <div className="badge">
          <span className="status-dot" />
          Lokal gespeichert
        </div>
      </div>
      {job && (
        <div className="notice processing">
          <LoaderCircle className="spin" size={22} />
          <div>
            <strong>{job.stage}</strong>
            <p>
              Das Notenbild wird auf diesem Computer verarbeitet. Du kannst währenddessen andere
              Stücke öffnen.
            </p>
          </div>
          <button
            className="secondary"
            onClick={() =>
              run(async () => {
                await post(`/recognition-jobs/${job.id}/cancel`);
                await refresh();
              })
            }
          >
            Abbrechen
          </button>
        </div>
      )}
      {latestJob?.status === "failed" && (
        <div className="notice warning">
          <TriangleAlert size={22} />
          <div>
            <strong>Die Erkennung konnte nicht abgeschlossen werden.</strong>
            <p>{latestJob.error}</p>
          </div>
        </div>
      )}
      {latestJob?.status === "completed" && (
        <div className="notice success">
          <CheckCircle2 size={22} />
          <div>
            <strong>Echte KI-Erkennung abgeschlossen. Bitte das Ergebnis prüfen.</strong>
            <p>
              {latestJob.details.pages} Seite(n) · {latestJob.details.duration_seconds?.toFixed(1)}{" "}
              Sekunden · HOMR {latestJob.details.version} · {latestJob.details.mode}
            </p>
          </div>
        </div>
      )}
      <div className="workspace-grid">
        <div className="score-column">
          <section className="panel score-panel">
            <div className="score-toolbar">
              <div className="segmented">
                <button
                  className={mode === "digital" ? "active" : ""}
                  onClick={() => setMode("digital")}
                >
                  <Music2 size={16} />
                  Digital
                </button>
                <button
                  className={mode === "original" ? "active" : ""}
                  onClick={() => setMode("original")}
                  disabled={!piece.pages.length}
                >
                  <ImageIcon size={16} />
                  Original
                </button>
                <button
                  className={mode === "compare" ? "active" : ""}
                  onClick={() => setMode("compare")}
                  disabled={!piece.pages.length || !score}
                >
                  Vergleich
                </button>
              </div>
              <div className="button-row">
                <button
                  className="icon-button"
                  aria-label="Rückgängig"
                  disabled={busy || versionIndex <= 0 || !online}
                  onClick={() => version(-1)}
                >
                  <Undo2 size={18} />
                </button>
                <button
                  className="icon-button"
                  aria-label="Wiederholen"
                  disabled={
                    busy ||
                    versionIndex < 0 ||
                    versionIndex === piece.versions.length - 1 ||
                    !online
                  }
                  onClick={() => version(1)}
                >
                  <Redo2 size={18} />
                </button>
                <select
                  aria-label="Notenzoom"
                  value={zoom}
                  onChange={(e) => setZoom(+e.target.value)}
                >
                  {[0.65, 0.85, 1, 1.2, 1.5].map((z) => (
                    <option key={z} value={z}>
                      {Math.round(z * 100)} %
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className={mode === "compare" ? "compare-view" : ""}>
              {mode !== "digital" && original && (
                <div className="original-view">
                  <div className="section-heading">
                    <span>
                      Original · Seite {pageIndex + 1}/{piece.pages.length}
                    </span>
                    <div className="button-row">
                      <button
                        className="icon-button"
                        aria-label="Vorherige Originalseite"
                        disabled={pageIndex === 0}
                        onClick={() => setPageIndex((n) => n - 1)}
                      >
                        <ChevronUp size={17} />
                      </button>
                      <button
                        className="icon-button"
                        aria-label="Nächste Originalseite"
                        disabled={pageIndex >= piece.pages.length - 1}
                        onClick={() => setPageIndex((n) => n + 1)}
                      >
                        <ChevronDown size={17} />
                      </button>
                      <button
                        className="secondary small"
                        onClick={() => setEditingPage(original)}
                        disabled={!online}
                      >
                        <SlidersHorizontal size={15} />
                        Verbessern
                      </button>
                    </div>
                  </div>
                  <img
                    src={`/api/v1/pages/${original.id}/image?version=${piece.updated_at}`}
                    alt={`Originalnoten, Seite ${pageIndex + 1}`}
                  />
                  {original.quality.hints.map((h) => (
                    <p className="quality-hint" key={h}>
                      {h}
                    </p>
                  ))}
                </div>
              )}
              {mode !== "original" &&
                (score && xml ? (
                  <ScoreView
                    xml={xml}
                    score={score}
                    active={position.event ?? selected?.id ?? null}
                    zoom={zoom}
                    onSelect={select}
                  />
                ) : (
                  <div className="empty-score">
                    <div className="round-icon">
                      <ScanLine size={34} />
                    </div>
                    <h2>
                      {piece.pages.length
                        ? "Aus deinem Blatt wird Musik."
                        : "Füge deine Noten hinzu."}
                    </h2>
                    <p>
                      {piece.pages.length
                        ? "Prüfe deine Aufnahme und starte die lokale KI-Erkennung. Das Ergebnis erscheint hier."
                        : "Lade eine Partitur, ein Foto oder ein PDF hoch."}
                    </p>
                    {piece.pages.length > 0 && (
                      <button
                        className="primary"
                        disabled={!!job || busy || !online}
                        onClick={() =>
                          run(async () => {
                            await post(`/pieces/${id}/recognition`);
                            await refresh();
                          })
                        }
                      >
                        <ScanLine size={18} />
                        Noten lokal erkennen
                      </button>
                    )}
                  </div>
                ))}
            </div>
          </section>
          {score && (
            <section className="transport panel">
              <div className="transport-main">
                <button
                  className="play-button"
                  aria-label={
                    position.state === "playing" ? "Wiedergabe pausieren" : "Wiedergabe starten"
                  }
                  onClick={() => (position.state === "playing" ? player.current?.pause() : start())}
                >
                  {position.state === "playing" ? (
                    <Pause fill="currentColor" size={22} />
                  ) : (
                    <Play fill="currentColor" size={22} />
                  )}
                </button>
                <button
                  className="icon-button"
                  aria-label="Wiedergabe stoppen"
                  onClick={() => player.current?.stop()}
                >
                  <Square size={19} />
                </button>
                <div className="transport-progress">
                  <div>
                    <strong>
                      {position.counting
                        ? "Einzähler"
                        : `Takt ${position.measure} von ${score.measure_count}`}
                    </strong>
                    <span>
                      {time(position.seconds)} / {time(position.total || plan?.total || 0)}
                    </span>
                  </div>
                  <progress max={position.total || plan?.total || 1} value={position.seconds} />
                </div>
                <button
                  className={`icon-button ${settings.loop ? "selected" : ""}`}
                  aria-label="Wiederholungsschleife"
                  aria-pressed={settings.loop}
                  onClick={() => updateSettings({ loop: !settings.loop })}
                >
                  <Repeat2 size={21} />
                </button>
              </div>
              <div className="transport-bottom">
                <span>
                  {position.state === "playing"
                    ? "Spielt"
                    : position.state === "paused"
                      ? "Pausiert"
                      : "Bereit"}{" "}
                  · Durchlauf {position.cycle}
                </span>
                <span>
                  {Math.round(
                    (position.state === "playing" ? position.speed : settings.speed) * 100,
                  )}{" "}
                  % ·{" "}
                  {Math.round(
                    score.tempo * (position.state === "playing" ? position.speed : settings.speed),
                  )}{" "}
                  BPM
                </span>
                <label>
                  <Volume2 size={16} />
                  <input
                    aria-label="Lautstärke"
                    type="range"
                    min={0}
                    max={1}
                    step={0.05}
                    value={settings.volume}
                    onChange={(e) => updateSettings({ volume: +e.target.value })}
                  />
                </label>
              </div>
            </section>
          )}
          {selected && score && (
            <NoteEditor
              note={selected}
              busy={busy || !online}
              onClose={() => setSelected(null)}
              onChange={changeNote}
              onAudition={() => {
                if (selected.sounding_midi !== null)
                  void player.current?.audition(
                    selected.sounding_midi,
                    piece.instrument,
                    settings.volume,
                  );
              }}
            />
          )}
          {score && (
            <details className="panel note-list">
              <summary>
                Noten prüfen und bearbeiten{" "}
                <span className="muted">
                  ·{" "}
                  {score.parts.reduce(
                    (n, p) => n + p.measures.reduce((n, m) => n + m.events.length, 0),
                    0,
                  )}{" "}
                  Ereignisse
                </span>
              </summary>
              <p className="small muted">
                Klicke eine Note in der Partitur oder wähle sie hier. H ist der deutsche Name für
                B♮; B entspricht B♭.
              </p>
              {score.parts.map((part, pi) => (
                <div key={part.id}>
                  <h4>{part.name}</h4>
                  <div className="measure-chips">
                    {part.measures.map((m) => (
                      <div
                        className={`measure-chip ${position.measure === m.index ? "current" : ""}`}
                        key={m.index}
                      >
                        <button
                          className="measure-label"
                          onClick={() =>
                            updateSettings({
                              start: m.index,
                              end: Math.max(m.index, settings.end),
                            })
                          }
                        >
                          Takt {m.number}
                        </button>
                        <div>
                          {m.events.map((n) => (
                            <button
                              key={n.id}
                              className={
                                selected?.id === n.id || position.event === n.id
                                  ? "note-chip active"
                                  : "note-chip"
                              }
                              title={`${germanNote(n)} · ${n.duration} Viertelschläge · Stimme ${n.voice}`}
                              onClick={() => select({ ...n, part: pi })}
                            >
                              {germanNote(n)}
                              <small>
                                {(
                                  {
                                    whole: "Ganze",
                                    half: "Halbe",
                                    quarter: "Viertel",
                                    eighth: "Achtel",
                                    "16th": "16tel",
                                    "32nd": "32stel",
                                  } as Record<string, string>
                                )[n.type] ?? n.type}
                                {n.dots ? " ·".repeat(n.dots) : ""}
                              </small>
                            </button>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </details>
          )}
          {score && (
            <details className="panel">
              <summary>
                Musikalische Prüfung{" "}
                <span className="badge">
                  {score.warnings.filter((w) => w.severity !== "info").length} Hinweise
                </span>
              </summary>
              {score.warnings.map((w, i) => (
                <div className={`validation-item ${w.severity}`} key={i}>
                  {w.severity === "info" ? <CheckCircle2 size={16} /> : <TriangleAlert size={16} />}
                  <p>{w.message}</p>
                  {w.measure && (
                    <button
                      className="text-button"
                      onClick={() => {
                        updateSettings({ start: w.measure!, end: w.measure! });
                        setMeasureEdit(w.measure!);
                      }}
                    >
                      Takt {w.measure}
                    </button>
                  )}
                </div>
              ))}
            </details>
          )}
          <details className="panel">
            <summary>Stückinformationen</summary>
            <label>
              Komponist
              <input
                defaultValue={piece.composer}
                maxLength={200}
                disabled={!online}
                onBlur={(e) => {
                  const composer = e.target.value;
                  if (composer !== piece.composer)
                    void run(async () => {
                      await patch(`/pieces/${id}`, { composer });
                      await refresh();
                      onLibraryChange();
                    });
                }}
              />
            </label>
            <label>
              Sammlung
              <input
                defaultValue={piece.collection}
                placeholder="Zum Beispiel Konzertprogramm"
                maxLength={200}
                disabled={!online}
                onBlur={(e) => {
                  const collection = e.target.value;
                  if (collection !== piece.collection)
                    void run(async () => {
                      await patch(`/pieces/${id}`, { collection });
                      await refresh();
                      onLibraryChange();
                    });
                }}
              />
            </label>
            <p className="small muted">
              Änderungen werden beim Verlassen des Felds lokal gespeichert. Sammlungen findest du
              über die Bibliothekssuche.
            </p>
          </details>
          <details className="panel">
            <summary>Quelldokumente und Seiten</summary>
            <label className="secondary upload-label">
              <Download size={17} />
              Weitere Dateien hinzufügen
              <input
                type="file"
                accept=".png,.jpg,.jpeg,.webp,.pdf,.xml,.musicxml,.mxl"
                multiple
                hidden
                disabled={busy || !online}
                onChange={(e) => {
                  void upload(e.target.files);
                  e.target.value = "";
                }}
              />
            </label>
            {piece.documents.map((d) => (
              <p className="small" key={d.id}>
                {d.filename}
              </p>
            ))}
            {piece.pages.map((page, i) => (
              <div className="page-row" key={page.id}>
                <img src={`/api/v1/pages/${page.id}/image`} alt={`Seite ${i + 1}`} />
                <span>Seite {i + 1}</span>
                <label className="check">
                  <input
                    type="checkbox"
                    checked={!page.excluded}
                    disabled={!online || !!job}
                    onChange={(e) =>
                      run(async () => {
                        await patch(`/pages/${page.id}`, {
                          excluded: !e.target.checked,
                        });
                        await refresh();
                      })
                    }
                  />
                  Erkennen
                </label>
                <button
                  className="icon-button"
                  disabled={!online || i === 0 || !!job}
                  aria-label={`Seite ${i + 1} nach oben`}
                  onClick={() =>
                    run(async () => {
                      await patch(`/pages/${page.id}`, { sort_order: i - 1 });
                      await patch(`/pages/${piece.pages[i - 1].id}`, {
                        sort_order: i,
                      });
                      await refresh();
                    })
                  }
                >
                  <ChevronUp size={17} />
                </button>
                <button
                  className="text-button"
                  onClick={() => {
                    setPageIndex(i);
                    setMode("original");
                  }}
                >
                  Ansehen
                </button>
              </div>
            ))}
            {piece.pages.length > 0 && (
              <button
                className="secondary"
                disabled={!!job || busy || !online}
                onClick={() =>
                  run(async () => {
                    await post(`/pieces/${id}/recognition`);
                    await refresh();
                  })
                }
              >
                <ScanLine size={17} />
                {score ? "Erneut erkennen" : "Noten lokal erkennen"}
              </button>
            )}
          </details>
        </div>
        <aside className="practice-column">
          <section className="panel">
            <div className="section-heading">
              <h3>Dein Instrument</h3>
              <Music2 size={18} />
            </div>
            <label>
              Instrument
              <select
                value={piece.instrument}
                disabled={busy || !online}
                onChange={(e) => changeInstrument(e.target.value)}
              >
                {instruments.map((i) => (
                  <option key={i.id} value={i.id}>
                    {i.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Notationsvariante
              <select
                value={piece.notation}
                disabled={busy || !online}
                onChange={(e) => changeInstrument(piece.instrument, e.target.value)}
              >
                <option value="auto">Automatisch · MusicXML beachten</option>
                <option value="written">Geschrieben für das Instrument</option>
                <option value="concert">Klingend / C / Bassschlüssel</option>
                <option value="bb-treble">B♭, Violinschlüssel (−14)</option>
                <option value="eb-treble">E♭, Violinschlüssel (−9)</option>
              </select>
            </label>
            <label>
              Zusätzlich transponieren
              <input
                type="number"
                min={-24}
                max={24}
                value={settings.extra_transpose}
                disabled={!online}
                onChange={(e) => {
                  const value = Math.max(-24, Math.min(24, +e.target.value));
                  updateSettings({ extra_transpose: value });
                  void run(async () => {
                    await patch(`/pieces/${id}`, {
                      playback_settings: {
                        ...settings,
                        extra_transpose: value,
                      },
                    });
                    await refresh();
                  });
                }}
              />
            </label>
            <p className="small muted">
              Lokaler Synthesizer · kein realistisches Instrumentensample. Vorhandene
              MusicXML-Transposition wird im automatischen Modus nur einmal angewendet.
            </p>
            <button
              className="text-button"
              onClick={() => void player.current?.audition(69, piece.instrument, settings.volume)}
            >
              <Volume2 size={16} />
              Referenzton A · 440 Hz
            </button>
          </section>
          {score && (
            <>
              <section className="panel practice-panel">
                <div className="section-heading">
                  <h3>In deinem Tempo</h3>
                  <span className="tempo-value">
                    {Math.round(settings.speed * 100)}
                    <small>%</small>
                  </span>
                </div>
                <input
                  aria-label="Tempogeschwindigkeit"
                  type="range"
                  min={0.25}
                  max={2}
                  step={0.05}
                  value={settings.speed}
                  onChange={(e) => updateSettings({ speed: +e.target.value })}
                />
                <div className="tempo-presets">
                  {[0.5, 0.75, 1, 1.25].map((t) => (
                    <button
                      key={t}
                      className={settings.speed === t ? "active" : ""}
                      onClick={() => updateSettings({ speed: t })}
                    >
                      {t * 100}%
                    </button>
                  ))}
                </div>
                <hr />
                <h4>Deine Passage</h4>
                <div className="form-grid">
                  <label>
                    Von Takt
                    <input
                      type="number"
                      min={1}
                      max={settings.end}
                      value={settings.start}
                      onChange={(e) =>
                        updateSettings({
                          start: Math.max(1, Math.min(settings.end, +e.target.value)),
                        })
                      }
                    />
                  </label>
                  <label>
                    Bis Takt
                    <input
                      type="number"
                      min={settings.start}
                      max={score.measure_count}
                      value={settings.end}
                      onChange={(e) =>
                        updateSettings({
                          end: Math.max(
                            settings.start,
                            Math.min(score.measure_count, +e.target.value),
                          ),
                        })
                      }
                    />
                  </label>
                </div>
                <label className="check">
                  <input
                    type="checkbox"
                    checked={settings.loop}
                    onChange={(e) => updateSettings({ loop: e.target.checked })}
                  />
                  Passage wiederholen
                </label>
                {settings.loop && (
                  <div className="form-grid">
                    <label>
                      Durchläufe · 0 = endlos
                      <input
                        type="number"
                        min={0}
                        max={100}
                        value={settings.loops}
                        onChange={(e) => updateSettings({ loops: +e.target.value })}
                      />
                    </label>
                    <label>
                      Pause dazwischen (s)
                      <input
                        type="number"
                        min={0}
                        max={30}
                        value={settings.gap}
                        onChange={(e) => updateSettings({ gap: +e.target.value })}
                      />
                    </label>
                  </div>
                )}
                <label className="check">
                  <input
                    type="checkbox"
                    checked={settings.metronome}
                    onChange={(e) => updateSettings({ metronome: e.target.checked })}
                  />
                  Metronom
                </label>
                <div className="form-grid">
                  <label>
                    Einzähler
                    <select
                      value={settings.countIn}
                      onChange={(e) => updateSettings({ countIn: +e.target.value })}
                    >
                      <option value={0}>Ohne</option>
                      <option value={1}>1 Takt</option>
                      <option value={2}>2 Takte</option>
                    </select>
                  </label>
                  <label>
                    Unterteilung
                    <select
                      value={settings.subdivision}
                      onChange={(e) => updateSettings({ subdivision: +e.target.value })}
                    >
                      <option value={1}>Grundschlag</option>
                      <option value={2}>Zweifach</option>
                      <option value={3}>Dreifach</option>
                    </select>
                  </label>
                </div>
                <details>
                  <summary>Tempo schrittweise steigern</summary>
                  <div className="form-grid">
                    <label>
                      Erhöhung (%)
                      <input
                        type="number"
                        min={0}
                        max={50}
                        step={5}
                        value={Math.round(settings.ramp * 100)}
                        onChange={(e) => updateSettings({ ramp: +e.target.value / 100 })}
                      />
                    </label>
                    <label>
                      Alle Durchläufe
                      <input
                        type="number"
                        min={1}
                        max={20}
                        value={settings.rampEvery}
                        onChange={(e) =>
                          updateSettings({
                            rampEvery: Math.max(1, +e.target.value),
                          })
                        }
                      />
                    </label>
                    <label>
                      Zieltempo (%)
                      <input
                        type="number"
                        min={25}
                        max={200}
                        value={Math.round(settings.target * 100)}
                        onChange={(e) => updateSettings({ target: +e.target.value / 100 })}
                      />
                    </label>
                  </div>
                </details>
                <hr />
                <label>
                  Passage benennen
                  <input
                    value={sectionName}
                    maxLength={100}
                    onChange={(e) => setSectionName(e.target.value)}
                  />
                </label>
                <button
                  className="secondary full"
                  disabled={busy || !online || !sectionName.trim()}
                  onClick={() =>
                    run(async () => {
                      setSections(
                        await post<Section[]>(`/pieces/${id}/practice-sections`, {
                          name: sectionName,
                          start_measure: settings.start,
                          end_measure: settings.end,
                          settings,
                        }),
                      );
                    })
                  }
                >
                  <Save size={16} />
                  Passage speichern
                </button>
                {sections.map((s) => (
                  <div className="saved-section" key={s.id}>
                    <button
                      onClick={() =>
                        updateSettings({
                          ...s.settings,
                          start: s.start_measure,
                          end: s.end_measure,
                        })
                      }
                    >
                      <strong>{s.name}</strong>
                      <small>
                        Takt {s.start_measure}–{s.end_measure}
                      </small>
                    </button>
                    <button
                      className="icon-button"
                      aria-label={`Passage ${s.name} löschen`}
                      disabled={!online}
                      onClick={() =>
                        run(async () => {
                          await api(`/practice-sections/${s.id}`, {
                            method: "DELETE",
                          });
                          setSections(await api(`/pieces/${id}/practice-sections`));
                        })
                      }
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                ))}
              </section>
              <details className="panel">
                <summary>Taktsymbole korrigieren</summary>
                <label>
                  Takt
                  <input
                    type="number"
                    min={1}
                    max={score.measure_count}
                    value={measureEdit}
                    onChange={(e) =>
                      setMeasureEdit(Math.max(1, Math.min(score.measure_count, +e.target.value)))
                    }
                  />
                </label>
                <label>
                  Notenschlüssel
                  <select
                    value={measures[measureEdit - 1]?.clef}
                    disabled={!online}
                    onChange={(e) =>
                      run(async () => {
                        player.current?.stop();
                        await patch(`/pieces/${id}/score`, {
                          action: "measure",
                          measure: measureEdit,
                          fields: { clef: e.target.value },
                          version_id: score.version_id,
                        });
                        await refresh();
                      })
                    }
                  >
                    {[
                      ["G2", "Violinschlüssel"],
                      ["F4", "Bassschlüssel"],
                      ["C3", "Altschlüssel"],
                      ["C4", "Tenorschlüssel"],
                    ].map(([v, n]) => (
                      <option key={v} value={v}>
                        {n}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Tonart · Kreuze (+) / Bes (−)
                  <select
                    value={measures[measureEdit - 1]?.fifths}
                    disabled={!online}
                    onChange={(e) =>
                      run(async () => {
                        player.current?.stop();
                        await patch(`/pieces/${id}/score`, {
                          action: "measure",
                          measure: measureEdit,
                          fields: { fifths: +e.target.value },
                          version_id: score.version_id,
                        });
                        await refresh();
                      })
                    }
                  >
                    {Array.from({ length: 15 }, (_, i) => i - 7).map((v) => (
                      <option value={v} key={v}>
                        {v === 0 ? "C-Dur / a-Moll" : `${Math.abs(v)} ${v > 0 ? "Kreuze" : "Bes"}`}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Taktart
                  <select
                    value={measures[measureEdit - 1]?.time.join("/")}
                    disabled={!online}
                    onChange={(e) =>
                      run(async () => {
                        player.current?.stop();
                        await patch(`/pieces/${id}/score`, {
                          action: "measure",
                          measure: measureEdit,
                          fields: {
                            time: e.target.value.split("/").map(Number),
                          },
                          version_id: score.version_id,
                        });
                        await refresh();
                      })
                    }
                  >
                    {["2/4", "3/4", "4/4", "6/8", "9/8", "12/8", "2/2"].map((v) => (
                      <option key={v}>{v}</option>
                    ))}
                  </select>
                </label>
                {(["repeat_start", "repeat_end"] as const).map((key, i) => (
                  <label className="check" key={key}>
                    <input
                      type="checkbox"
                      checked={measures[measureEdit - 1]?.[key]}
                      disabled={!online}
                      onChange={(e) =>
                        run(async () => {
                          player.current?.stop();
                          await patch(`/pieces/${id}/score`, {
                            action: "measure",
                            measure: measureEdit,
                            fields: { [key]: e.target.checked },
                            version_id: score.version_id,
                          });
                          await refresh();
                        })
                      }
                    />
                    {i === 0 ? "Wiederholungsanfang" : "Wiederholungsende"}
                  </label>
                ))}
                <label>
                  Wiederholungsklammer
                  <select
                    value=""
                    disabled={!online}
                    onChange={(e) =>
                      run(async () => {
                        player.current?.stop();
                        const [number, type] = e.target.value.split("-");
                        await patch(`/pieces/${id}/score`, {
                          action: "measure",
                          measure: measureEdit,
                          fields: { ending: number ? { number, type } : null },
                          version_id: score.version_id,
                        });
                        await refresh();
                      })
                    }
                  >
                    <option value="">Klammer hinzufügen / entfernen …</option>
                    <option value="1-start">1. Klammer: Anfang</option>
                    <option value="1-stop">1. Klammer: Ende</option>
                    <option value="2-start">2. Klammer: Anfang</option>
                    <option value="2-discontinue">2. Klammer: Ende</option>
                    <option value="-">Klammer entfernen</option>
                  </select>
                </label>
              </details>
              <section className="panel">
                <h3>Deine Musik mitnehmen</h3>
                <button
                  className="secondary full"
                  onClick={() =>
                    run(async () =>
                      download(
                        new Blob([await scoreXml(id)], {
                          type: "application/xml",
                        }),
                        piece.title + ".musicxml",
                      ),
                    )
                  }
                >
                  <Download size={16} />
                  MusicXML exportieren
                </button>
                <a
                  className={`secondary full ${!online ? "disabled" : ""}`}
                  href={`/api/v1/pieces/${id}/export/midi`}
                  download
                >
                  <Download size={16} />
                  MIDI exportieren
                </a>
                <p className="small muted">
                  Die Exporte enthalten deine aktuellen Korrekturen. MIDI verwendet klingende
                  Tonhöhen.
                </p>
              </section>
            </>
          )}
        </aside>
      </div>
      {editingPage && (
        <ImageEditor
          page={editingPage}
          onClose={() => setEditingPage(null)}
          onSave={setPiece}
          onError={onError}
        />
      )}
    </>
  );
}
