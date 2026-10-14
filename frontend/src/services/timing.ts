import type { Score, PlaybackSettings, TimedNote, Occurrence } from "../types";
export interface Plan {
  notes: (TimedNote & { at: number; seconds: number })[];
  measures: (Occurrence & { at: number; seconds: number })[];
  clicks: { at: number; accent: boolean }[];
  total: number;
  countIn: number;
}
export function buildPlan(score: Score, settings: PlaybackSettings): Plan {
  const changes = [{ beat: 0, bpm: score.tempo }];
  score.occurrences.forEach((m) =>
    m.tempos.forEach((t) => changes.push({ beat: m.start + t.offset, bpm: t.bpm })),
  );
  changes.sort((a, b) => a.beat - b.beat);
  const secondsAt = (beat: number) => {
    let seconds = 0,
      last = 0,
      bpm = score.tempo;
    for (const t of changes) {
      if (t.beat > beat) break;
      seconds += ((t.beat - last) * 60) / bpm;
      last = t.beat;
      bpm = t.bpm;
    }
    return (seconds + ((beat - last) * 60) / bpm) / settings.speed;
  };
  const selected = score.occurrences.filter(
    (m) => m.measure >= settings.start && m.measure <= settings.end,
  );
  const first = selected[0];
  if (!first) return { notes: [], measures: [], clicks: [], total: 0, countIn: 0 };
  const intro =
    (settings.countIn * first.time[0] * (4 / first.time[1]) * 60) / score.tempo / settings.speed;
  const measures: Plan["measures"] = [],
    notes: Plan["notes"] = [],
    clicks: Plan["clicks"] = [];
  let at = intro;
  for (const m of selected) {
    const start = secondsAt(m.start),
      end = secondsAt(m.start + m.duration),
      length = end - start;
    measures.push({ ...m, at, seconds: length });
    for (const n of score.timeline) {
      const noteEnd = n.start + n.duration;
      const clippedStart = Math.max(n.start, m.start),
        clippedEnd = Math.min(noteEnd, m.start + m.duration);
      // A tie crossing a loop boundary must start audibly at the selected boundary.
      const beginsHere = n.start >= m.start && n.start < m.start + m.duration;
      const entersSelection =
        n.start < m.start &&
        noteEnd > m.start &&
        (m === first || !selected.some((s) => s.occurrence === m.occurrence - 1));
      if (!beginsHere && !entersSelection) continue;
      // Keep a tied note continuous across adjacent selected occurrences, truncate at selection end.
      let finalBeat = clippedEnd;
      for (const next of selected.filter((s) => s.start >= m.start + m.duration)) {
        if (Math.abs(next.start - finalBeat) > 1e-6 || finalBeat >= noteEnd) break;
        finalBeat = Math.min(noteEnd, next.start + next.duration);
      }
      notes.push({
        ...n,
        at: at + secondsAt(clippedStart) - start,
        seconds: secondsAt(finalBeat) - secondsAt(clippedStart),
      });
    }
    const unit = 4 / m.time[1] / settings.subdivision;
    for (let beat = 0; beat < m.duration - 1e-6; beat += unit)
      clicks.push({
        at: at + secondsAt(m.start + beat) - start,
        accent: beat === 0,
      });
    at += length;
  }
  const unit = ((4 / first.time[1]) * 60) / score.tempo / settings.speed / settings.subdivision;
  for (let i = 0; i < intro - 1e-6; i += unit)
    clicks.unshift({
      at: i,
      accent: Math.round(i / unit) % (first.time[0] * settings.subdivision) === 0,
    });
  return { notes, measures, clicks, total: at, countIn: intro };
}
export const defaults: PlaybackSettings = {
  speed: 1,
  start: 1,
  end: 1,
  loop: false,
  loops: 0,
  gap: 0,
  metronome: false,
  countIn: 1,
  ramp: 0,
  rampEvery: 3,
  target: 1,
  extra_transpose: 0,
  volume: 0.65,
  subdivision: 1,
};
export function germanNote(note: {
  step: string | null;
  alter: number | null;
  octave: number | null;
}) {
  if (!note.step) return "Pause";
  const name = note.step === "B" ? (note.alter === -1 ? "B" : "H") : note.step;
  const accidental =
    note.step === "B" && note.alter === -1
      ? ""
      : ({ "-2": "𝄫", "-1": "♭", "0": "", "1": "♯", "2": "𝄪" }[String(note.alter)] ?? "");
  return `${name}${accidental}${note.octave}`;
}
