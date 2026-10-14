import { useEffect, useRef, useState } from "react";
import { OpenSheetMusicDisplay, Pitch } from "opensheetmusicdisplay";
import type { GraphicalNote } from "opensheetmusicdisplay";
import type { NoteEvent, Score } from "../types";
type SvgNote = GraphicalNote & {
  getNoteheadSVGs: () => HTMLElement[];
  getSVGGElement: () => SVGGElement;
};
const steps: Record<string, number> = {
  C: 0,
  D: 2,
  E: 4,
  F: 5,
  G: 7,
  A: 9,
  B: 11,
};
export function ScoreView({
  xml,
  score,
  active,
  zoom,
  onSelect,
}: {
  xml: string;
  score: Score;
  active: string | null;
  zoom: number;
  onSelect: (e: NoteEvent) => void;
}) {
  const element = useRef<HTMLDivElement>(null),
    display = useRef<OpenSheetMusicDisplay | null>(null);
  const notes = useRef(new Map<string, GraphicalNote>()),
    reverse = useRef(new Map<unknown, NoteEvent>());
  const activeRef = useRef(active);
  activeRef.current = active;
  const callback = useRef(onSelect);
  callback.current = onSelect;
  const [error, setError] = useState("");
  useEffect(() => {
    let cancelled = false,
      observer: ResizeObserver | undefined,
      timeout: ReturnType<typeof setTimeout>;
    const mount = element.current!;
    mount.replaceChildren();
    notes.current.clear();
    reverse.current.clear();
    const osmd = new OpenSheetMusicDisplay(mount, {
      backend: "svg",
      autoResize: false,
      drawTitle: true,
      drawComposer: true,
      drawPartNames: true,
      drawMeasureNumbers: true,
      drawTimeSignatures: true,
      drawingParameters: "default",
      pageFormat: "Endless",
    });
    display.current = osmd;
    osmd.Zoom = zoom;
    const render = () => {
      if (cancelled) return;
      try {
        osmd.render();
        notes.current.clear();
        reverse.current.clear();
        osmd.GraphicSheet.MeasureList.forEach((measures, mi) =>
          measures.forEach((measure) =>
            measure.staffEntries.forEach((entry) =>
              entry.graphicalVoiceEntries.forEach((voice) =>
                voice.notes.forEach((graphic) => {
                  const source = graphic.sourceNote,
                    partId = source.ParentVoiceEntry.ParentVoice.Parent.IdString;
                  const pi = score.parts.findIndex((p) => p.id === partId);
                  const events = score.parts[pi]?.measures[mi]?.events ?? [];
                  const pitch = source.Pitch;
                  const event = events.find(
                    (e) =>
                      Math.abs(e.offset - entry.relInMeasureTimestamp.RealValue * 4) < 0.0001 &&
                      String(e.voice) === String(source.ParentVoiceEntry.ParentVoice.VoiceId) &&
                      (e.rest
                        ? source.isRest()
                        : pitch &&
                          steps[e.step!] === pitch.FundamentalNote &&
                          e.octave === pitch.Octave + Pitch.OctaveXmlDifference),
                  );
                  if (event) {
                    notes.current.set(event.id, graphic);
                    reverse.current.set(source, event);
                    const heads = (graphic as SvgNote).getNoteheadSVGs();
                    for (const head of heads) {
                      head.dataset.notepilotEvent = event.id;
                      head.setAttribute("role", "button");
                      head.setAttribute("tabindex", "0");
                      head.setAttribute(
                        "aria-label",
                        `Takt ${event.measure}: ${event.rest ? "Pause" : event.step + String(event.octave)} bearbeiten`,
                      );
                      head.onkeydown = (key) => {
                        if (key.key === "Enter" || key.key === " ") {
                          key.preventDefault();
                          callback.current(event);
                        }
                      };
                    }
                    graphic.setColor(event.id === activeRef.current ? "#169b73" : "#26372f", {
                      applyToNoteheads: true,
                      applyToStem: true,
                    });
                  }
                }),
              ),
            ),
          ),
        );
      } catch {
        setError("Die Partitur konnte nicht gezeichnet werden. Prüfe die MusicXML-Datei.");
      }
    };
    osmd
      .load(xml)
      .then(() => {
        if (cancelled) return;
        setError("");
        render();
        observer = new ResizeObserver(() => {
          clearTimeout(timeout);
          timeout = setTimeout(render, 150);
        });
        observer.observe(mount);
      })
      .catch(() => {
        if (!cancelled) setError("Die Partitur konnte nicht geladen werden.");
      });
    return () => {
      cancelled = true;
      clearTimeout(timeout);
      observer?.disconnect();
      osmd.clear();
      display.current = null;
    };
  }, [xml, score.version_id, zoom]);
  useEffect(() => {
    notes.current.forEach((note, id) =>
      note.setColor(id === active ? "#169b73" : "#26372f", {
        applyToNoteheads: true,
        applyToStem: true,
      }),
    );
    if (active) {
      const note = notes.current.get(active);
      if (note) {
        const head = (note as SvgNote).getNoteheadSVGs()[0];
        const rect = head?.getBoundingClientRect();
        if (rect && (rect.top < 100 || rect.bottom > window.innerHeight - 180))
          window.scrollBy({ top: rect.top - 180, behavior: "smooth" });
      }
    }
  }, [active, zoom]);
  return (
    <div className="score-paper">
      <div
        ref={element}
        className="score-svg"
        role="region"
        aria-label="Digitale Noten; Noten anklicken zum Bearbeiten"
        onClick={(event) => {
          const target = (event.target as Element).closest("[data-notepilot-event]");
          const identity = target?.getAttribute("data-notepilot-event");
          if (identity) {
            const selected = score.parts
              .flatMap((p) => p.measures.flatMap((m) => m.events))
              .find((e) => e.id === identity);
            if (selected) callback.current(selected);
            return;
          }
          // A click next to a head selects by its real SVG bounds, including responsive scaling.
          let nearest: NoteEvent | undefined;
          let distance = 24;
          notes.current.forEach((graphic, id) => {
            for (const head of (graphic as SvgNote).getNoteheadSVGs()) {
              const rect = head.getBoundingClientRect();
              const d = Math.hypot(
                event.clientX - (rect.left + rect.width / 2),
                event.clientY - (rect.top + rect.height / 2),
              );
              if (d < distance) {
                distance = d;
                nearest = score.parts
                  .flatMap((p) => p.measures.flatMap((m) => m.events))
                  .find((e) => e.id === id);
              }
            }
          });
          if (nearest) callback.current(nearest);
        }}
      />
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
    </div>
  );
}
