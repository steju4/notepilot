import * as Tone from "tone";
import { buildPlan } from "./timing";
import type { PlaybackSettings, Score } from "../types";
export interface Position {
  seconds: number;
  total: number;
  measure: number;
  event: string | null;
  cycle: number;
  speed: number;
  state: "playing" | "paused" | "stopped";
  counting: boolean;
}
export class Player {
  private synth: Tone.PolySynth | undefined;
  private click: Tone.Synth | undefined;
  private timer: ReturnType<typeof setInterval> | undefined;
  private loopTimer: ReturnType<typeof setTimeout> | undefined;
  private score: Score | undefined;
  private settings: PlaybackSettings | undefined;
  private plan: ReturnType<typeof buildPlan> | undefined;
  private cycle = 1;
  private state: Position["state"] = "stopped";
  private callback: (p: Position) => void = () => {};
  private instrument = "piano";
  private generation = 0;
  async init(instrument: string, volume: number) {
    await Tone.start();
    if (!this.synth || instrument !== this.instrument) {
      this.synth?.dispose();
      const wave =
        instrument.includes("sax") || instrument === "clarinet"
          ? "square"
          : instrument === "flute" || instrument === "piccolo"
            ? "sine"
            : instrument === "trumpet" || instrument === "horn"
              ? "sawtooth"
              : "triangle";
      this.synth = new Tone.PolySynth(Tone.Synth, {
        oscillator: { type: wave },
        envelope: { attack: 0.015, decay: 0.18, sustain: 0.25, release: 0.16 },
      }).toDestination();
      this.instrument = instrument;
    }
    this.synth.volume.value = Tone.gainToDb(Math.max(0.001, volume)) - 12;
    this.click ??= new Tone.Synth({
      oscillator: { type: "sine" },
      envelope: { attack: 0.001, decay: 0.03, sustain: 0, release: 0.02 },
    }).toDestination();
    this.click.volume.value = -20;
  }
  async start(
    score: Score,
    settings: PlaybackSettings,
    instrument: string,
    callback: (p: Position) => void,
  ) {
    this.stop();
    await this.init(instrument, settings.volume);
    this.score = score;
    this.settings = { ...settings };
    this.callback = callback;
    this.cycle = 1;
    this.schedule();
  }
  private schedule() {
    if (!this.score || !this.settings) return;
    const transport = Tone.getTransport();
    transport.stop();
    transport.cancel();
    transport.seconds = 0;
    this.plan = buildPlan(this.score, this.settings);
    if (!this.plan.total) return;
    const generation = ++this.generation;
    for (const note of this.plan.notes)
      transport.schedule(
        (time) =>
          this.synth?.triggerAttackRelease(
            Tone.Frequency(note.sounding_midi!, "midi").toFrequency(),
            Math.max(0.02, note.seconds - 0.015),
            time,
            0.8,
          ),
        note.at,
      );
    for (const tick of this.plan.clicks) {
      if (this.settings.metronome || tick.at < this.plan.countIn)
        transport.schedule(
          (time) => this.click?.triggerAttackRelease(tick.accent ? "C7" : "C6", 0.025, time),
          tick.at,
        );
    }
    transport.schedule(
      (time) =>
        Tone.getDraw().schedule(() => {
          if (generation !== this.generation) return;
          const settings = this.settings!;
          if (settings.loop && (settings.loops === 0 || this.cycle < settings.loops)) {
            this.cycle++;
            if (settings.ramp > 0 && (this.cycle - 1) % settings.rampEvery === 0)
              settings.speed = Math.min(settings.target, settings.speed + settings.ramp);
            this.loopTimer = setTimeout(() => this.schedule(), Math.max(0, settings.gap) * 1000);
          } else this.stop();
        }, time),
      this.plan.total,
    );
    transport.start("+0.05");
    this.state = "playing";
    if (this.timer) clearInterval(this.timer);
    this.timer = setInterval(() => this.report(), 50);
    this.report();
  }
  private report() {
    if (!this.plan || !this.settings) return;
    const seconds = Math.min(Tone.getTransport().seconds, this.plan.total);
    const m = [...this.plan.measures].reverse().find((m) => m.at <= seconds);
    const event = this.plan.notes.find((n) => seconds >= n.at && seconds < n.at + n.seconds);
    this.callback({
      seconds,
      total: this.plan.total,
      measure: m?.measure ?? this.settings.start,
      event: event?.id ?? null,
      cycle: this.cycle,
      speed: this.settings.speed,
      state: this.state,
      counting: seconds < this.plan.countIn,
    });
  }
  pause() {
    if (this.state === "playing") {
      Tone.getTransport().pause();
      this.synth?.releaseAll();
      this.state = "paused";
      if (this.loopTimer) clearTimeout(this.loopTimer);
      this.report();
    } else if (this.state === "paused") {
      // Retrigger sustained notes at the paused position.
      const at = Tone.getTransport().seconds;
      this.plan?.notes
        .filter((n) => n.at < at && n.at + n.seconds > at)
        .forEach((n) =>
          this.synth?.triggerAttackRelease(
            Tone.Frequency(n.sounding_midi!, "midi").toFrequency(),
            n.at + n.seconds - at,
          ),
        );
      Tone.getTransport().start();
      this.state = "playing";
      this.report();
    }
  }
  stop() {
    this.generation++;
    Tone.getTransport().stop();
    Tone.getTransport().cancel();
    this.synth?.releaseAll();
    if (this.timer) clearInterval(this.timer);
    if (this.loopTimer) clearTimeout(this.loopTimer);
    this.timer = undefined;
    this.state = "stopped";
    this.callback({
      seconds: 0,
      total: this.plan?.total ?? 0,
      measure: this.settings?.start ?? 1,
      event: null,
      cycle: this.cycle,
      speed: this.settings?.speed ?? 1,
      state: "stopped",
      counting: false,
    });
  }
  async audition(midi: number, instrument: string, volume: number) {
    await this.init(instrument, volume);
    this.synth?.triggerAttackRelease(Tone.Frequency(midi, "midi").toFrequency(), 0.55);
  }
  dispose() {
    this.stop();
    this.synth?.dispose();
    this.click?.dispose();
  }
}
