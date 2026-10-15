import { Sequencer, WorkletSynthesizer } from "spessasynth_lib";
import processorUrl from "spessasynth_lib/dist/spessasynth_processor.min.js?url";
import { buildPlan } from "./timing";
import { planMidi } from "./midi";
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
  private context?: AudioContext;
  private synth?: WorkletSynthesizer;
  private sequencer?: Sequencer;
  private output?: GainNode;
  private loading?: Promise<void>;
  private timer?: ReturnType<typeof setInterval>;
  private loopTimer?: ReturnType<typeof setTimeout>;
  private auditionTimer?: ReturnType<typeof setTimeout>;
  private score?: Score;
  private settings?: PlaybackSettings;
  private plan?: ReturnType<typeof buildPlan>;
  private cycle = 1;
  private state: Position["state"] = "stopped";
  private callback: (p: Position) => void = () => {};
  private program = 0;
  private generation = 0;
  async init(program: number, volume: number) {
    if (!this.context || this.context.state === "closed") {
      const context = new AudioContext();
      this.context = context;
      this.loading = (async () => {
        if (!context.audioWorklet)
          throw new Error("Instrumentklänge benötigen HTTPS oder einen lokalen Browseraufruf.");
        const response = await fetch("/audio/TimGM6mb.sf2");
        if (!response.ok)
          throw new Error(
            "Die lokale Instrumentenbank konnte nicht geladen werden. Bitte die Seite neu laden.",
          );
        const bank = await response.arrayBuffer();
        await context.audioWorklet.addModule(processorUrl);
        const synth = new WorkletSynthesizer(context);
        synth.setLogLevel(false, false, false);
        await synth.soundBankManager.addSoundBank(bank, "notepilot");
        await synth.isReady;
        if (context.state === "closed") {
          synth.destroy();
          return;
        }
        this.synth = synth;
        this.output = context.createGain();
        synth.connect(this.output);
        this.output.connect(context.destination);
        this.sequencer = new Sequencer(synth, { skipToFirstNoteOn: false });
        this.sequencer.loopCount = 0;
        this.sequencer.eventHandler.addEvent("songChange", "start", () => {
          if (this.state === "playing") this.sequencer?.play();
        });
        this.sequencer.eventHandler.addEvent("songEnded", "end", () => this.finishCycle());
      })().catch((error) => {
        void context.close();
        this.loading = undefined;
        throw error;
      });
    }
    await this.context.resume();
    await this.loading;
    this.program = program;
    if (this.output) this.output.gain.value = Math.max(0, Math.min(1, volume));
  }
  async start(
    score: Score,
    settings: PlaybackSettings,
    program: number,
    callback: (p: Position) => void,
  ) {
    this.stop();
    const generation = this.generation;
    await this.init(program, settings.volume);
    if (generation !== this.generation) return;
    this.score = score;
    this.settings = { ...settings };
    this.callback = callback;
    this.cycle = 1;
    this.schedule();
  }
  private schedule() {
    if (!this.score || !this.settings || !this.sequencer) return;
    this.synth?.stopAll(true);
    this.plan = buildPlan(this.score, this.settings);
    if (!this.plan.total) return;
    this.state = "playing";
    this.sequencer.loadNewSongList([
      {
        binary: planMidi(this.plan, this.program, this.settings.metronome),
        fileName: "NotePilot.mid",
      },
    ]);
    if (this.timer) clearInterval(this.timer);
    this.timer = setInterval(() => this.report(), 50);
    this.report();
  }
  private finishCycle() {
    if (this.state !== "playing" || !this.settings) return;
    const settings = this.settings;
    if (settings.loop && (settings.loops === 0 || this.cycle < settings.loops)) {
      this.cycle++;
      if (settings.ramp > 0 && (this.cycle - 1) % settings.rampEvery === 0)
        settings.speed = Math.min(settings.target, settings.speed + settings.ramp);
      this.loopTimer = setTimeout(() => this.schedule(), Math.max(0, settings.gap) * 1000);
    } else this.stop();
  }
  private report() {
    if (!this.plan || !this.settings) return;
    const seconds = Math.min(this.sequencer?.currentTime ?? 0, this.plan.total);
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
      this.sequencer?.pause();
      this.state = "paused";
      if (this.loopTimer) clearTimeout(this.loopTimer);
    } else if (this.state === "paused") {
      this.sequencer?.play();
      this.state = "playing";
    }
    this.report();
  }
  stop() {
    this.generation++;
    this.state = "stopped";
    this.sequencer?.pause();
    this.synth?.stopAll(true);
    if (this.timer) clearInterval(this.timer);
    if (this.loopTimer) clearTimeout(this.loopTimer);
    if (this.auditionTimer) clearTimeout(this.auditionTimer);
    this.timer = undefined;
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
  async audition(midi: number, program: number, volume: number) {
    const generation = this.generation;
    await this.init(program, volume);
    if (generation !== this.generation) return;
    this.synth?.programChange(0, program);
    this.synth?.noteOn(0, midi, 90);
    this.auditionTimer = setTimeout(() => this.synth?.noteOff(0, midi), 550);
  }
  dispose() {
    this.stop();
    this.synth?.destroy();
    void this.context?.close();
    this.context = undefined;
    this.synth = undefined;
    this.sequencer = undefined;
    this.loading = undefined;
  }
}
