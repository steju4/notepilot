import { useEffect, useState } from "react";
import { X, Volume2, Trash2, Plus } from "lucide-react";
import { germanNote } from "../services/timing";
import type { NoteEvent } from "../types";
export function NoteEditor({
  note,
  busy,
  onClose,
  onChange,
  onAudition,
}: {
  note: NoteEvent;
  busy: boolean;
  onClose: () => void;
  onChange: (action: string, fields: Record<string, unknown>) => void;
  onAudition: () => void;
}) {
  const [step, setStep] = useState(note.step ?? "C"),
    [octave, setOctave] = useState(note.octave ?? 4),
    [alter, setAlter] = useState(note.alter ?? 0),
    [type, setType] = useState(note.type),
    [dots, setDots] = useState(note.dots),
    [rest, setRest] = useState(note.rest),
    [tie, setTie] = useState(note.tie);
  useEffect(() => {
    setStep(note.step ?? "C");
    setOctave(note.octave ?? 4);
    setAlter(note.alter ?? 0);
    setType(note.type);
    setDots(note.dots);
    setRest(note.rest);
    setTie(note.tie);
  }, [note.id]);
  const fields = { step, octave, alter, type, dots, rest, tie };
  return (
    <section className="editor panel">
      <div className="section-heading">
        <div>
          <span className="eyebrow">
            TAKT {note.measure} · STIMME {note.voice}
          </span>
          <h3>{germanNote(note)} bearbeiten</h3>
        </div>
        <button className="icon-button" onClick={onClose} aria-label="Notenbearbeitung schließen">
          <X size={19} />
        </button>
      </div>
      <label className="check">
        <input type="checkbox" checked={rest} onChange={(e) => setRest(e.target.checked)} />
        Pause
      </label>
      <div className="form-grid">
        <label>
          Ton
          <select value={step} disabled={rest} onChange={(e) => setStep(e.target.value)}>
            {["C", "D", "E", "F", "G", "A", "B"].map((s) => (
              <option key={s} value={s}>
                {s === "B" ? "H (B in MusicXML)" : s}
              </option>
            ))}
          </select>
        </label>
        <label>
          Oktave
          <input
            type="number"
            min={0}
            max={9}
            value={octave}
            disabled={rest}
            onChange={(e) => setOctave(+e.target.value)}
          />
        </label>
        <label>
          Vorzeichen
          <select value={alter} disabled={rest} onChange={(e) => setAlter(+e.target.value)}>
            <option value={-2}>Doppelbe</option>
            <option value={-1}>♭ Be</option>
            <option value={0}>♮ Natürlich</option>
            <option value={1}>♯ Kreuz</option>
            <option value={2}>Doppelkreuz</option>
          </select>
        </label>
        <label>
          Notenwert
          <select value={type} onChange={(e) => setType(e.target.value)}>
            {[
              ["whole", "Ganze"],
              ["half", "Halbe"],
              ["quarter", "Viertel"],
              ["eighth", "Achtel"],
              ["16th", "Sechzehntel"],
              ["32nd", "Zweiunddreißigstel"],
            ].map(([v, n]) => (
              <option value={v} key={v}>
                {n}
              </option>
            ))}
          </select>
        </label>
        <label>
          Punktierung
          <select value={dots} onChange={(e) => setDots(+e.target.value)}>
            <option value={0}>Ohne</option>
            <option value={1}>Einfach</option>
            <option value={2}>Doppelt</option>
          </select>
        </label>
        <label>
          Haltebogen
          <select
            value={tie.join(",")}
            disabled={rest}
            onChange={(e) => setTie(e.target.value ? e.target.value.split(",") : [])}
          >
            <option value="">Keiner</option>
            <option value="start">Anfang</option>
            <option value="stop">Ende</option>
            <option value="stop,start">Fortsetzung</option>
          </select>
        </label>
      </div>
      <p className="small muted">
        Geschrieben: MIDI {note.written_midi ?? "–"} · Klingend: MIDI {note.sounding_midi ?? "–"}.
        Nach Änderungen wird die Taktlänge erneut geprüft.
      </p>
      <div className="button-row">
        <button className="primary" disabled={busy} onClick={() => onChange("update", fields)}>
          Änderung speichern
        </button>
        <button className="secondary" disabled={note.sounding_midi === null} onClick={onAudition}>
          <Volume2 size={16} />
          Anhören
        </button>
      </div>
      <div className="button-row">
        <button className="text-button" disabled={busy} onClick={() => onChange("insert", fields)}>
          <Plus size={16} />
          Danach einfügen
        </button>
        <button
          className="text-button danger"
          disabled={busy}
          onClick={() => onChange("delete", {})}
        >
          <Trash2 size={16} />
          Entfernen
        </button>
      </div>
    </section>
  );
}
