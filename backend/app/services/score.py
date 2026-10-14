"""MusicXML is the source of truth. All playback, corrections and exports derive from it."""

import math
import re
import xml.etree.ElementTree as ET
import zipfile
from copy import deepcopy
from fractions import Fraction
from io import BytesIO

import mido
from defusedxml.ElementTree import fromstring

from .instruments import INSTRUMENTS, transpose_for

TYPES = {"whole": 4, "half": 2, "quarter": 1, "eighth": 0.5, "16th": 0.25, "32nd": 0.125, "64th": 0.0625}
STEPS = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
ACCIDENTALS = {"double-flat": -2, "flat": -1, "natural": 0, "sharp": 1, "double-sharp": 2}
MAX_XML = 12 * 1024 * 1024


def read_xml(data: bytes) -> ET.Element:
    if len(data) > MAX_XML:
        raise ValueError("Die MusicXML-Datei ist zu groß (maximal 12 MB).")
    if data[:2] == b"PK":
        with zipfile.ZipFile(BytesIO(data)) as archive:
            if len(archive.infolist()) > 500 or sum(i.file_size for i in archive.infolist()) > MAX_XML:
                raise ValueError("Das MXL-Archiv ist zu groß.")
            for info in archive.infolist():
                if info.filename.startswith("/") or ".." in info.filename.replace("\\", "/").split("/"):
                    raise ValueError("Unsicherer Dateipfad im MXL-Archiv.")
            if "META-INF/container.xml" not in archive.namelist():
                raise ValueError("MXL enthält keine container.xml.")
            container = fromstring(archive.read("META-INF/container.xml"))
            files = [e.get("full-path") for e in container.iter() if e.tag.split("}")[-1] == "rootfile"]
            if not files or files[0] not in archive.namelist():
                raise ValueError("Keine Partitur im MXL-Archiv gefunden.")
            data = archive.read(files[0])
    try:
        root = fromstring(data, forbid_entities=True, forbid_external=True)
    except Exception as error:
        raise ValueError("MusicXML ist beschädigt oder enthält unsichere XML-Inhalte.") from error
    for node in root.iter():
        node.tag = node.tag.split("}")[-1]
    if root.tag != "score-partwise" or root.find("part") is None:
        raise ValueError("Bitte MusicXML im Format score-partwise importieren.")
    if len(root.findall(".//note")) > 50_000:
        raise ValueError("Zu viele Noten in der Partitur (maximal 50.000).")
    ids = set()
    for pi, part in enumerate(root.findall("part")):
        for mi, measure in enumerate(part.findall("measure")):
            measure.set("id", measure.get("id") or f"m-p{pi}-{mi}")
            for ni, note in enumerate(measure.findall("note")):
                identity = note.get("id") or f"n-p{pi}-m{mi}-{ni}"
                if identity in ids:
                    identity = f"n-p{pi}-m{mi}-{ni}"
                note.set("id", identity)
                ids.add(identity)
    return root


def xml_bytes(root):
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def text(node, path, default=None):
    return node.findtext(path, default)


def numeric(value, default=0):
    try:
        result = float(value)
        return result if math.isfinite(result) else default
    except (ValueError, TypeError):
        return default


def fraction(value, default=0):
    try:
        return Fraction(str(value))
    except (ValueError, ZeroDivisionError):
        return Fraction(default)


def key_alters(fifths):
    order = "FCGDAEB" if fifths > 0 else "BEADGCF"
    return {s: (1 if fifths > 0 else -1) for s in order[: abs(fifths)]}


def warning(kind, message, measure=None, event=None, severity="warning"):
    return dict(type=kind, message=message, measure=measure, event=event, severity=severity)


def parse_score(root, instrument="piano", notation="auto", extra_transpose=0):
    warnings, parts = [], []
    names = {p.get("id"): text(p, "part-name", "Stimme") for p in root.findall("part-list/score-part")}
    global_tempo = 100
    for pi, part in enumerate(root.findall("part")):
        divisions, fifths, beats, beat_type, clef = Fraction(1), 0, 4, 4, "G2"
        xml_transpose = None
        measures, tied_pitches = [], {}
        for mi, measure in enumerate(part.findall("measure")):
            cursor, latest_start, maximum = Fraction(0), Fraction(0), Fraction(0)
            events, accidentals, voice_ends, tempos = [], {}, {}, []
            repeat_start, repeat_end, repeat_times, endings = False, False, 2, []
            for child in measure:
                if child.tag == "attributes":
                    divisions = fraction(text(child, "divisions", str(divisions)), 1)
                    if divisions <= 0:
                        raise ValueError("Ungültige MusicXML divisions.")
                    fifths = int(numeric(text(child, "key/fifths", fifths)))
                    if abs(fifths) > 7:
                        warnings.append(
                            warning("key", "Ungewöhnliche Tonartvorzeichen bitte prüfen.", mi + 1)
                        )
                    beats_raw = text(child, "time/beats", str(beats))
                    beats = sum(int(numeric(v)) for v in beats_raw.split("+"))
                    beat_type = int(numeric(text(child, "time/beat-type", beat_type)))
                    if beats < 1 or beat_type not in (1, 2, 4, 8, 16, 32, 64):
                        raise ValueError("Ungültige Taktart.")
                    clef = text(child, "clef/sign", clef[:1]) + text(child, "clef/line", clef[1:])
                    if child.find("transpose") is not None:
                        xml_transpose = int(numeric(text(child, "transpose/chromatic", 0))) + 12 * int(
                            numeric(text(child, "transpose/octave-change", 0))
                        )
                elif child.tag in ("backup", "forward"):
                    delta = fraction(text(child, "duration", "0")) / divisions
                    cursor += delta * (-1 if child.tag == "backup" else 1)
                    if cursor < 0:
                        warnings.append(
                            warning("voices", "Stimmenposition vor dem Taktanfang; bitte prüfen.", mi + 1)
                        )
                        cursor = Fraction(0)
                    maximum = max(maximum, cursor)
                elif child.tag == "direction":
                    sound = child.find("sound")
                    tempo = numeric(sound.get("tempo")) if sound is not None else 0
                    if not tempo:
                        unit = text(child, "direction-type/metronome/beat-unit", "quarter")
                        dots = len(child.findall("direction-type/metronome/beat-unit-dot"))
                        tempo = (
                            numeric(text(child, "direction-type/metronome/per-minute", 0))
                            * TYPES.get(unit, 1)
                            * sum(0.5**i for i in range(dots + 1))
                        )
                    if tempo > 0:
                        tempos.append(dict(offset=float(cursor), bpm=max(20, min(300, tempo))))
                        if mi == 0 and pi == 0:
                            global_tempo = tempos[-1]["bpm"]
                    if sound is not None and any(
                        sound.get(k) for k in ["dacapo", "dalsegno", "tocoda", "fine"]
                    ):
                        warnings.append(
                            warning(
                                "jump",
                                "Da Capo / Dal Segno / Coda / Fine wird angezeigt, aber nicht automatisch abgespielt.",
                                mi + 1,
                            )
                        )
                elif child.tag == "barline":
                    repeat = child.find("repeat")
                    if repeat is not None:
                        repeat_start |= repeat.get("direction") == "forward"
                        repeat_end |= repeat.get("direction") == "backward"
                        repeat_times = max(2, min(8, int(numeric(repeat.get("times"), 2))))
                    ending = child.find("ending")
                    if ending is not None:
                        endings.append(
                            dict(
                                numbers=[int(n) for n in re.findall(r"\d+", ending.get("number", "1"))],
                                type=ending.get("type"),
                            )
                        )
                elif child.tag == "note":
                    duration = fraction(text(child, "duration", "0")) / divisions
                    typ = text(child, "type", "quarter")
                    dots = len(child.findall("dot"))
                    if child.find("grace") is not None:
                        warnings.append(
                            warning(
                                "grace",
                                "Vorschlagnoten werden dargestellt, aber nicht abgespielt.",
                                mi + 1,
                                child.get("id"),
                            )
                        )
                        duration = Fraction(0)
                    elif duration <= 0:
                        duration = fraction(TYPES.get(typ, 1)) * sum(
                            (Fraction(1, 2) ** i for i in range(dots + 1)), Fraction(0)
                        )
                        actual = numeric(text(child, "time-modification/actual-notes", "1"), 1)
                        normal = numeric(text(child, "time-modification/normal-notes", "1"), 1)
                        duration *= fraction(normal / actual) if actual else 1
                    chord = child.find("chord") is not None
                    start = latest_start if chord else cursor
                    if not chord:
                        latest_start = cursor
                        cursor += duration
                    maximum = max(maximum, start + duration)
                    voice = text(child, "voice", "1")
                    staff = text(child, "staff", "1")
                    voice_ends[(voice, staff)] = max(voice_ends.get((voice, staff), 0), start + duration)
                    tie = [t.get("type") for t in child.findall("tie")]
                    step, octave, alter, midi = None, None, None, None
                    if child.find("pitch") is not None:
                        step = text(child, "pitch/step")
                        octave = int(numeric(text(child, "pitch/octave", 4)))
                        if step not in STEPS or not 0 <= octave <= 9:
                            raise ValueError("Ungültige Tonhöhe im MusicXML.")
                        accidental = text(child, "accidental")
                        key = (step, octave, staff)
                        pitch_alter = text(child, "pitch/alter")
                        if pitch_alter is not None:
                            alter = numeric(pitch_alter)
                        elif accidental in ACCIDENTALS:
                            alter = ACCIDENTALS[accidental]
                        elif "stop" in tie and (voice, key) in tied_pitches:
                            alter = tied_pitches[(voice, key)]
                        else:
                            alter = accidentals.get(key, key_alters(fifths).get(step, 0))
                        if accidental in ACCIDENTALS:
                            accidentals[key] = ACCIDENTALS[accidental]
                        elif pitch_alter is not None:
                            accidentals[key] = alter
                        if "start" in tie:
                            tied_pitches[(voice, key)] = alter
                        elif "stop" in tie:
                            tied_pitches.pop((voice, key), None)
                        midi = 12 * (octave + 1) + STEPS[step] + alter
                    elif child.find("rest") is None:
                        warnings.append(
                            warning(
                                "unpitched",
                                "Unbestimmte Schlagwerk-Tonhöhe wird nicht abgespielt.",
                                mi + 1,
                                child.get("id"),
                            )
                        )
                    transpose = transpose_for(instrument, notation, xml_transpose) + extra_transpose
                    sounding = midi + transpose if midi is not None else None
                    if sounding is not None and (sounding < 0 or sounding > 127 or sounding != int(sounding)):
                        warnings.append(
                            warning(
                                "pitch",
                                "Ton außerhalb des MIDI-Bereichs oder Mikroton; Wiedergabe ausgelassen.",
                                mi + 1,
                                child.get("id"),
                            )
                        )
                        sounding = None
                    event = dict(
                        id=child.get("id"),
                        part=pi,
                        measure=mi + 1,
                        voice=voice,
                        staff=staff,
                        offset=float(start),
                        duration=float(duration),
                        step=step,
                        octave=octave,
                        alter=alter,
                        written_midi=midi,
                        sounding_midi=sounding,
                        rest=child.find("rest") is not None,
                        type=typ,
                        dots=dots,
                        tie=tie,
                        chord=chord,
                        transpose=transpose,
                        tuplet=child.find("time-modification") is not None,
                    )
                    events.append(event)
            expected = Fraction(beats * 4, beat_type)
            pickup = measure.get("implicit") == "yes" or (mi == 0 and 0 < maximum < expected)
            length = maximum if pickup else max(expected, maximum)
            if not pickup and maximum != expected:
                warnings.append(
                    warning(
                        "duration",
                        f"Takt {mi + 1}: {float(maximum):g} statt {float(expected):g} Viertelschläge. Notenwerte prüfen.",
                        mi + 1,
                    )
                )
            for (voice, staff), end in voice_ends.items():
                if end > expected:
                    warnings.append(
                        warning("voice-duration", f"Stimme {voice} überschreitet die Taktlänge.", mi + 1)
                    )
            measures.append(
                dict(
                    index=mi + 1,
                    number=measure.get("number", str(mi + 1)),
                    duration=float(length),
                    expected_duration=float(expected),
                    pickup=pickup,
                    time=[beats, beat_type],
                    fifths=fifths,
                    clef=clef,
                    events=events,
                    tempos=tempos,
                    repeat_start=repeat_start,
                    repeat_end=repeat_end,
                    repeat_times=repeat_times,
                    endings=endings,
                    xml_transpose=xml_transpose,
                )
            )
        parts.append(
            dict(id=part.get("id"), name=names.get(part.get("id"), f"Stimme {pi + 1}"), measures=measures)
        )
    if not any(m["events"] for p in parts for m in p["measures"]):
        raise ValueError("Die Partitur enthält keine Noten oder Pausen.")
    title = text(root, "work/work-title", text(root, "movement-title", "Unbenannt"))
    warnings.append(
        warning(
            "interpretation",
            "Erkennung prüfen: HOMR kann Auflösungszeichen übersehen. Vorzeichen immer mit dem Original vergleichen. Wiederholungen und Bindebögen ebenfalls prüfen. Dynamik und Artikulation werden gespeichert und angezeigt, aber klanglich nicht interpretiert.",
            severity="info",
        )
    )
    order = playback_order(parts[0]["measures"])
    timeline, occurrences, active_ties = [], [], {}
    beat = 0.0
    for occurrence, mi in enumerate(order):
        first = parts[0]["measures"][mi]
        occurrences.append(
            dict(
                measure=mi + 1,
                occurrence=occurrence,
                start=beat,
                duration=first["duration"],
                time=first["time"],
                tempos=first["tempos"],
            )
        )
        for pi, part in enumerate(parts):
            if mi >= len(part["measures"]):
                continue
            for event in part["measures"][mi]["events"]:
                if event["sounding_midi"] is None or event["duration"] <= 0:
                    continue
                e = dict(event, start=beat + event["offset"], occurrence=occurrence, ids=[event["id"]])
                key = (pi, e["voice"], e["staff"], e["sounding_midi"])
                previous = active_ties.get(key)
                if (
                    "stop" in e["tie"]
                    and previous
                    and abs(previous["start"] + previous["duration"] - e["start"]) < 0.00001
                ):
                    previous["duration"] += e["duration"]
                    previous["ids"].append(e["id"])
                    if "start" not in e["tie"]:
                        active_ties.pop(key, None)
                else:
                    timeline.append(e)
                    if "stop" in e["tie"]:
                        warnings.append(
                            warning("tie", "Haltebogen ohne passende vorherige Note.", mi + 1, e["id"])
                        )
                    if "start" in e["tie"]:
                        active_ties[key] = e
                    else:
                        active_ties.pop(key, None)
        beat += first["duration"]
    return dict(
        title=title,
        parts=parts,
        warnings=warnings,
        tempo=global_tempo,
        timeline=timeline,
        occurrences=occurrences,
        duration_beats=beat,
        measure_count=len(parts[0]["measures"]),
    )


def playback_order(measures):
    """Expand bounded MusicXML repeats, including first/second endings, without changing notation."""
    order, stack, counts = [], [], {}
    i, pass_number, active_ending = 0, 1, None
    while i < len(measures) and len(order) < max(1, len(measures)) * 32:
        m = measures[i]
        if m["repeat_start"] and (not stack or stack[-1] != i):
            stack.append(i)
        starts = [e for e in m["endings"] if e["type"] == "start"]
        stops = [e for e in m["endings"] if e["type"] in ("stop", "discontinue")]
        if starts:
            active_ending = starts[0]["numbers"]
        allowed = not active_ending or pass_number in active_ending
        if allowed:
            order.append(i)
        if m["repeat_end"]:
            begin = stack[-1] if stack else 0
            count = counts.get(i, 1)
            if count < m["repeat_times"] and allowed:
                counts[i] = count + 1
                pass_number = count + 1
                active_ending = None
                i = begin
                continue
            if stack:
                stack.pop()
            # Keep pass_number for a following second ending.
        if stops:
            active_ending = None
        i += 1
    return order


def set_child(node, tag, value):
    child = node.find(tag)
    if child is None:
        child = ET.SubElement(node, tag)
    child.text = str(value)
    return child


def edit_score(root, change):
    root = deepcopy(root)
    action = change["action"]
    if action in ("update", "delete", "insert"):
        target = next((n for n in root.findall(".//note") if n.get("id") == change.get("event_id")), None)
        if target is None:
            raise ValueError("Diese Note ist nicht mehr vorhanden. Bitte die Partitur neu laden.")
        measure = next(m for m in root.findall("part/measure") if target in list(m))
        if action == "delete":
            measure.remove(target)
            return root
        if action == "insert":
            new = ET.Element("note", id="n-" + __import__("uuid").uuid4().hex)
            set_child(new, "voice", text(target, "voice", "1"))
            set_child(new, "staff", text(target, "staff", "1"))
            measure.insert(list(measure).index(target) + 1, new)
            target = new
        fields = change.get("fields", {})
        if "rest" in fields or "step" in fields or action == "insert":
            for tag in ["pitch", "rest", "unpitched", "accidental"]:
                for child in target.findall(tag):
                    target.remove(child)
            if fields.get("rest", False):
                target.insert(0, ET.Element("rest"))
            else:
                step = fields.get("step", "C")
                octave = int(fields.get("octave", 4))
                alter = int(fields.get("alter", 0))
                if step not in STEPS or not 0 <= octave <= 9 or not -2 <= alter <= 2:
                    raise ValueError("Ungültige Tonhöhe.")
                pitch = ET.Element("pitch")
                set_child(pitch, "step", step)
                set_child(pitch, "alter", alter)
                set_child(pitch, "octave", octave)
                target.insert(0, pitch)
                set_child(target, "accidental", next(a for a, v in ACCIDENTALS.items() if v == alter))
        if "type" in fields or "dots" in fields or action == "insert":
            typ = fields.get("type", text(target, "type", "quarter"))
            dots = int(fields.get("dots", len(target.findall("dot"))))
            if typ not in TYPES or not 0 <= dots <= 2:
                raise ValueError("Ungültiger Notenwert.")
            # Raise divisions to 960 for every measure of this part. Preserve tuplets and backup/forward.
            part = next(p for p in root.findall("part") if measure in list(p))
            old_divisions = Fraction(1)
            new_divisions = 960
            for m in part.findall("measure"):
                attrs = m.find("attributes")
                if attrs is not None and attrs.find("divisions") is not None:
                    old_divisions = fraction(text(attrs, "divisions", "1"))
                if attrs is None:
                    attrs = ET.Element("attributes")
                    m.insert(0, attrs)
                for duration in m.findall(".//duration"):
                    duration.text = str(int(fraction(duration.text) * new_divisions / old_divisions))
                set_child(attrs, "divisions", new_divisions)
            value = Fraction(str(TYPES[typ])) * sum(
                (Fraction(1, 2) ** i for i in range(dots + 1)), Fraction()
            )
            mod = target.find("time-modification")
            if mod is not None:
                value *= fraction(text(mod, "normal-notes", "1")) / fraction(text(mod, "actual-notes", "1"))
            set_child(target, "duration", int(value * new_divisions))
            set_child(target, "type", typ)
            for dot in target.findall("dot"):
                target.remove(dot)
            for _ in range(dots):
                ET.SubElement(target, "dot")
        if "tie" in fields:
            for child in target.findall("tie"):
                target.remove(child)
            notations = target.find("notations")
            if notations is None:
                notations = ET.SubElement(target, "notations")
            for child in notations.findall("tied"):
                notations.remove(child)
            for value in fields["tie"]:
                if value not in ("start", "stop"):
                    raise ValueError("Ungültiger Haltebogen.")
                ET.SubElement(target, "tie", type=value)
                ET.SubElement(notations, "tied", type=value)
    elif action == "measure":
        pi, mi = int(change.get("part", 0)), int(change["measure"]) - 1
        try:
            measure = root.findall("part")[pi].findall("measure")[mi]
        except IndexError as e:
            raise ValueError("Takt nicht vorhanden.") from e
        fields = change["fields"]
        attrs = measure.find("attributes")
        if attrs is None:
            attrs = ET.Element("attributes")
            measure.insert(0, attrs)
        for key, value in fields.items():
            if key == "fifths":
                if not -7 <= int(value) <= 7:
                    raise ValueError("Ungültige Tonart.")
                keynode = attrs.find("key")
                if keynode is None:
                    keynode = ET.SubElement(attrs, "key")
                set_child(keynode, "fifths", int(value))
            elif key == "time":
                beats, unit = map(int, value)
                if not 1 <= beats <= 32 or unit not in (1, 2, 4, 8, 16, 32):
                    raise ValueError("Ungültige Taktart.")
                timenode = attrs.find("time")
                if timenode is None:
                    timenode = ET.SubElement(attrs, "time")
                set_child(timenode, "beats", beats)
                set_child(timenode, "beat-type", unit)
            elif key == "clef":
                if value not in ("G2", "F4", "C3", "C4"):
                    raise ValueError("Ungültiger Notenschlüssel.")
                node = attrs.find("clef")
                if node is None:
                    node = ET.SubElement(attrs, "clef")
                set_child(node, "sign", value[0])
                set_child(node, "line", value[1])
            elif key in ("repeat_start", "repeat_end", "ending"):
                location = "left" if key == "repeat_start" else "right"
                bar = next(
                    (b for b in measure.findall("barline") if b.get("location", "right") == location), None
                )
                if bar is None:
                    bar = ET.SubElement(measure, "barline", location=location)
                if key == "ending":
                    for old in bar.findall("ending"):
                        bar.remove(old)
                    if value:
                        if value["number"] not in ("1", "2") or value["type"] not in (
                            "start",
                            "stop",
                            "discontinue",
                        ):
                            raise ValueError("Ungültige Wiederholungsklammer.")
                        ET.SubElement(bar, "ending", number=value["number"], type=value["type"])
                else:
                    for old in bar.findall("repeat"):
                        bar.remove(old)
                    if value:
                        ET.SubElement(
                            bar, "repeat", direction="forward" if key == "repeat_start" else "backward"
                        )
    else:
        raise ValueError("Unbekannte Bearbeitungsaktion.")
    # MusicXML schema order of edited note children matters to third-party readers.
    tags = [
        "grace",
        "cue",
        "chord",
        "pitch",
        "unpitched",
        "rest",
        "duration",
        "tie",
        "instrument",
        "footnote",
        "level",
        "voice",
        "type",
        "dot",
        "accidental",
        "time-modification",
        "stem",
        "notehead",
        "notehead-text",
        "staff",
        "beam",
        "notations",
        "lyric",
        "play",
        "listen",
    ]
    for note in root.findall(".//note"):
        note[:] = sorted(note, key=lambda n: tags.index(n.tag) if n.tag in tags else 100)
    return root


def combine_pages(roots):
    """Append pages only when part counts agree; no invented cross-page voice alignment."""
    result = deepcopy(roots[0])
    parts = result.findall("part")
    for root in roots[1:]:
        other = root.findall("part")
        if len(other) != len(parts):
            raise ValueError(
                "Die Seiten haben unterschiedliche Stimmenzahlen. Bitte Seiten einzeln importieren und prüfen."
            )
        for p, o in zip(parts, other):
            for measure in o.findall("measure"):
                p.append(deepcopy(measure))
    for pi, part in enumerate(parts):
        for mi, measure in enumerate(part.findall("measure")):
            measure.set("number", str(mi + 1))
            measure.set("id", f"m-p{pi}-{mi}")
            for ni, note in enumerate(measure.findall("note")):
                note.set("id", f"n-p{pi}-m{mi}-{ni}")
    return result


def midi_bytes(score, instrument="piano"):
    midi = mido.MidiFile(ticks_per_beat=960)
    meta = mido.MidiTrack()
    midi.tracks.append(meta)
    tempo_events = [(0, score["tempo"])]
    for occurrence in score["occurrences"]:
        tempo_events.extend(
            (round((occurrence["start"] + t["offset"]) * 960), t["bpm"]) for t in occurrence["tempos"]
        )
    last = 0
    for tick, bpm in sorted(set(tempo_events)):
        meta.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm), time=tick - last))
        last = tick
    for pi, part in enumerate(score["parts"]):
        track = mido.MidiTrack()
        midi.tracks.append(track)
        channel = pi % 15
        if channel >= 9:
            channel += 1
        track.append(mido.MetaMessage("track_name", name=part["name"]))
        track.append(
            mido.Message("program_change", channel=channel, program=INSTRUMENTS[instrument]["program"])
        )
        changes = []
        for event in score["timeline"]:
            if event["part"] != pi:
                continue
            changes.append(
                (
                    round(event["start"] * 960),
                    1,
                    mido.Message("note_on", channel=channel, note=int(event["sounding_midi"]), velocity=85),
                )
            )
            changes.append(
                (
                    round((event["start"] + event["duration"]) * 960),
                    0,
                    mido.Message("note_off", channel=channel, note=int(event["sounding_midi"]), velocity=0),
                )
            )
        last = 0
        for tick, _, message in sorted(changes, key=lambda item: (item[0], item[1])):
            track.append(message.copy(time=tick - last))
            last = tick
    out = BytesIO()
    midi.save(file=out)
    return out.getvalue()
