import { describe, it, expect } from "vitest";
import { buildPlan, defaults, germanNote } from "./timing";
import type { Score, TimedNote, Occurrence } from "../types";
const occurrence = (
  measure: number,
  start: number,
  tempos: Occurrence["tempos"] = [],
  time: [number, number] = [4, 4],
): Occurrence => ({
  measure,
  start,
  occurrence: measure - 1,
  duration: 4,
  time,
  tempos,
});
const note = (id: string, start: number, duration: number): TimedNote => ({
  id,
  ids: [id],
  start,
  duration,
  occurrence: Math.floor(start / 4),
  measure: Math.floor(start / 4) + 1,
  part: 0,
  voice: "1",
  staff: "1",
  offset: start % 4,
  step: "C",
  octave: 4,
  alter: 0,
  written_midi: 60,
  sounding_midi: 60,
  rest: false,
  type: "quarter",
  dots: 0,
  tie: [],
  chord: false,
  transpose: 0,
  tuplet: false,
});
const score = (notes: TimedNote[], occurrences: Occurrence[]): Score => ({
  title: "Reference",
  parts: [],
  warnings: [],
  tempo: 120,
  timeline: notes,
  occurrences,
  duration_beats: 8,
  measure_count: 2,
  version_id: "ref",
});
describe("musical timeline", () => {
  it("keeps pitch independent of tempo and preserves rest gaps", () => {
    const s = score([note("a", 0, 1), note("b", 2, 0.5)], [occurrence(1, 0)]);
    const p = buildPlan(s, { ...defaults, countIn: 0, end: 1, speed: 0.5 });
    expect(p.notes.map((n) => n.at)).toEqual([0, 2]);
    expect(p.notes[1].seconds).toBe(0.5);
    expect(p.notes[1].sounding_midi).toBe(60);
    expect(p.total).toBe(4);
  });
  it("integrates a tempo change inside a held note", () => {
    const s = score([note("a", 0, 4)], [occurrence(1, 0, [{ offset: 2, bpm: 60 }])]);
    const p = buildPlan(s, { ...defaults, countIn: 0, end: 1 });
    expect(p.notes[0].seconds).toBe(3);
    expect(p.total).toBe(3);
  });
  it("preserves a tie across adjacent measures without retriggering", () => {
    const s = score([note("tied", 0, 8)], [occurrence(1, 0), occurrence(2, 4)]);
    const p = buildPlan(s, { ...defaults, countIn: 0, end: 2 });
    expect(p.notes).toHaveLength(1);
    expect(p.notes[0].seconds).toBe(4);
  });
  it("starts the audible tail of a tie at a selected loop boundary", () => {
    const s = score([note("tied", 0, 8)], [occurrence(1, 0), occurrence(2, 4)]);
    const p = buildPlan(s, { ...defaults, countIn: 0, start: 2, end: 2 });
    expect(p.notes).toHaveLength(1);
    expect(p.notes[0].at).toBe(0);
    expect(p.notes[0].seconds).toBe(2);
  });
  it("uses the correct count-in length in 6/8 and supports subdivision", () => {
    const m = { ...occurrence(1, 0, [], [6, 8]), duration: 3 };
    const p = buildPlan(score([], [m]), {
      ...defaults,
      countIn: 2,
      end: 1,
      subdivision: 2,
    });
    expect(p.countIn).toBe(3);
    expect(p.total).toBe(4.5);
    expect(p.clicks.filter((c) => c.at >= p.countIn)).toHaveLength(12);
  });
  it("shows German B/H without changing MIDI names", () => {
    expect(germanNote({ step: "B", alter: 0, octave: 4 })).toBe("H4");
    expect(germanNote({ step: "B", alter: -1, octave: 4 })).toBe("B4");
    expect(germanNote({ step: "F", alter: 1, octave: 4 })).toBe("F♯4");
  });
});
