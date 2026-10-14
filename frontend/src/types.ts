export interface PlaybackSettings {
  speed: number;
  start: number;
  end: number;
  loop: boolean;
  loops: number;
  gap: number;
  metronome: boolean;
  countIn: number;
  ramp: number;
  rampEvery: number;
  target: number;
  extra_transpose: number;
  volume: number;
  subdivision: number;
}
export interface Piece {
  id: string;
  title: string;
  composer: string;
  instrument: string;
  notation: string;
  favorite: boolean;
  collection: string;
  created_at: string;
  updated_at: string;
  last_opened_at: string | null;
  current_version: string | null;
  playback_settings: Partial<PlaybackSettings>;
}
export interface Page {
  id: string;
  image_path: string;
  processed_path: string | null;
  excluded: number;
  sort_order: number;
  quality: {
    hints: string[];
    width: number;
    height: number;
    sharpness: number;
    brightness: number;
    skew_degrees: number;
  };
}
export interface Version {
  id: string;
  sequence: number;
  source: string;
  created_at: string;
}
export interface Job {
  id: string;
  status: string;
  stage: string;
  error: string | null;
  details: {
    pages?: number;
    page?: number;
    duration_seconds?: number;
    mode?: string;
    version?: string;
  };
}
export interface Detail extends Piece {
  pages: Page[];
  versions: Version[];
  documents: { id: string; filename: string }[];
  jobs: Job[];
}
export interface NoteEvent {
  id: string;
  part: number;
  measure: number;
  voice: string;
  staff: string;
  offset: number;
  duration: number;
  step: string | null;
  octave: number | null;
  alter: number | null;
  written_midi: number | null;
  sounding_midi: number | null;
  rest: boolean;
  type: string;
  dots: number;
  tie: string[];
  chord: boolean;
  transpose: number;
  tuplet: boolean;
}
export interface TimedNote extends NoteEvent {
  start: number;
  occurrence: number;
  ids: string[];
}
export interface Measure {
  index: number;
  number: string;
  duration: number;
  expected_duration: number;
  pickup: boolean;
  time: [number, number];
  fifths: number;
  clef: string;
  events: NoteEvent[];
  tempos: { offset: number; bpm: number }[];
  xml_transpose: number | null;
  repeat_start: boolean;
  repeat_end: boolean;
  endings: { numbers: number[]; type: string }[];
}
export interface Occurrence {
  measure: number;
  occurrence: number;
  start: number;
  duration: number;
  time: [number, number];
  tempos: { offset: number; bpm: number }[];
}
export interface Score {
  title: string;
  parts: { id: string; name: string; measures: Measure[] }[];
  warnings: {
    type: string;
    message: string;
    measure: number | null;
    event: string | null;
    severity: string;
  }[];
  tempo: number;
  timeline: TimedNote[];
  occurrences: Occurrence[];
  duration_beats: number;
  measure_count: number;
  version_id: string;
}
export interface Instrument {
  id: string;
  name: string;
  family: string;
  transpose: number;
  program: number;
  range: [number, number];
  sound: string;
}
export interface Section {
  id: string;
  name: string;
  start_measure: number;
  end_measure: number;
  settings: Partial<PlaybackSettings>;
  notes: string;
}
export interface Engine {
  ready: boolean;
  installed: boolean;
  mode: string;
  version: string;
  message?: string;
  models: { name: string; present: boolean; bytes: number }[];
}
