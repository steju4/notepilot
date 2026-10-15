import { describe, expect, it } from "vitest";
import { BasicMIDI } from "spessasynth_core";
import { planMidi } from "./midi";
import type { Plan } from "./timing";
const empty = { measures: [], clicks: [], countIn: 0, total: 4 };
const note = (at: number, seconds: number, sounding_midi: number) =>
  ({
    at,
    seconds,
    sounding_midi,
    part: 0,
  }) as Plan["notes"][number];
const events = (plan: Plan) =>
  BasicMIDI.fromArrayBuffer(planMidi(plan, 58, false)).tracks[0].events;
describe("sampled playback MIDI", () => {
  it("does not shorten notes or insert a gap between consecutive measures", () => {
    const messages = events({ ...empty, notes: [note(0, 2, 60), note(2, 2, 62)] } as Plan);
    const notes = messages.filter(
      (e) => (e.statusByte & 0xf0) === 0x90 || (e.statusByte & 0xf0) === 0x80,
    );
    expect(notes.map((e) => [e.ticks, e.statusByte, e.data[0]])).toEqual([
      [0, 0x90, 60],
      [2000, 0x80, 60],
      [2000, 0x90, 62],
      [4000, 0x80, 62],
    ]);
    expect(messages.find((e) => (e.statusByte & 0xf0) === 0xc0)?.data[0]).toBe(58);
  });
  it("sends a tied phrase as a single sustained sound", () => {
    const messages = events({ ...empty, notes: [note(0, 4, 60)] } as Plan);
    expect(messages.filter((e) => (e.statusByte & 0xf0) === 0x90)).toHaveLength(1);
    expect(messages.find((e) => (e.statusByte & 0xf0) === 0x80)?.ticks).toBe(4000);
  });
  it("keeps written silence at the start and includes count-in ticks", () => {
    const plan = {
      ...empty,
      countIn: 1,
      clicks: [{ at: 0, accent: true }],
      notes: [note(2, 1, 60)],
    } as Plan;
    const messages = events(plan);
    expect(messages.find((e) => e.statusByte === 0x90)?.ticks).toBe(2000);
    expect(messages.find((e) => Number(e.statusByte) === 0x99)?.ticks).toBe(0);
  });
});
