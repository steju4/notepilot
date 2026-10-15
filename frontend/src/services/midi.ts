import type { Plan } from "./timing";
// Millisecond MIDI ticks at 60 BPM. The AudioWorklet, not UI timers, plays this timeline.
export function planMidi(plan: Plan, program: number, metronome: boolean): ArrayBuffer {
  const events: { tick: number; order: number; bytes: number[] }[] = [
    { tick: 0, order: -2, bytes: [0xff, 0x51, 3, 15, 66, 64] },
  ];
  const channel = (part: number) => {
    const c = part % 15;
    return c >= 9 ? c + 1 : c;
  };
  const channels = new Set(plan.notes.map((n) => channel(n.part)));
  for (const c of channels) events.push({ tick: 0, order: -1, bytes: [0xc0 | c, program] });
  for (const n of plan.notes) {
    if (n.sounding_midi === null) continue;
    const c = channel(n.part);
    events.push({
      tick: Math.round(n.at * 1000),
      order: 1,
      bytes: [0x90 | c, n.sounding_midi, 90],
    });
    events.push({
      tick: Math.round((n.at + n.seconds) * 1000),
      order: 0,
      bytes: [0x80 | c, n.sounding_midi, 0],
    });
  }
  for (const c of plan.clicks)
    if (metronome || c.at < plan.countIn) {
      const pitch = c.accent ? 76 : 77;
      events.push({ tick: Math.round(c.at * 1000), order: 1, bytes: [0x99, pitch, 75] });
      events.push({ tick: Math.round((c.at + 0.025) * 1000), order: 0, bytes: [0x89, pitch, 0] });
    }
  events.push({ tick: Math.round(plan.total * 1000), order: 2, bytes: [0xff, 0x2f, 0] });
  events.sort((a, b) => a.tick - b.tick || a.order - b.order);
  const track: number[] = [];
  let last = 0;
  for (const e of events) {
    let value = Math.max(0, e.tick - last);
    const delta = [value & 127];
    while ((value >>>= 7)) delta.unshift((value & 127) | 128);
    track.push(...delta, ...e.bytes);
    last = e.tick;
  }
  const size = track.length;
  return new Uint8Array([
    77,
    84,
    104,
    100,
    0,
    0,
    0,
    6,
    0,
    0,
    0,
    1,
    3,
    232,
    77,
    84,
    114,
    107,
    (size >>> 24) & 255,
    (size >>> 16) & 255,
    (size >>> 8) & 255,
    size & 255,
    ...track,
  ]).buffer;
}
