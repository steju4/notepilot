import xml.etree.ElementTree as ET
import zipfile
from io import BytesIO
from pathlib import Path

import mido
import pytest
from app.services.instruments import transpose_for
from app.services.score import combine_pages, edit_score, midi_bytes, parse_score, read_xml


def note(step="C", octave=4, duration=1, alter=None, accidental=None, tie="", rest=False, extra=""):
    pitch = (
        "<rest/>"
        if rest
        else f"<pitch><step>{step}</step>{f'<alter>{alter}</alter>' if alter is not None else ''}<octave>{octave}</octave></pitch>"
    )
    return f"<note>{pitch}<duration>{duration}</duration>{f'<tie type={chr(34)}{tie}{chr(34)}/>' if tie else ''}<voice>1</voice><type>quarter</type>{f'<accidental>{accidental}</accidental>' if accidental else ''}{extra}</note>"


def score(measures, fifths=0, beats=4, unit=4, transpose=None):
    attrs = f"<attributes><divisions>1</divisions><key><fifths>{fifths}</fifths></key><time><beats>{beats}</beats><beat-type>{unit}</beat-type></time><clef><sign>G</sign><line>2</line></clef>{'' if transpose is None else f'<transpose><chromatic>{transpose}</chromatic></transpose>'}</attributes>"
    return read_xml(
        (
            '<score-partwise version="4.0"><part-list><score-part id="P1"><part-name>Test</part-name></score-part></part-list><part id="P1">'
            + "".join(
                f'<measure number="{i + 1}">{attrs if i == 0 else ""}{m}</measure>'
                for i, m in enumerate(measures)
            )
            + "</part></score-partwise>"
        ).encode()
    )


def pitches(root, **kwargs):
    return [e["written_midi"] for e in parse_score(root, **kwargs)["timeline"]]


@pytest.mark.parametrize(
    ("fifths", "expected"),
    [
        (0, [60, 62, 64, 65, 67, 69, 71, 72]),
        (1, [60, 62, 64, 66, 67, 69, 71, 72]),
        (-1, [60, 62, 64, 65, 67, 69, 70, 72]),
    ],
)
def test_scales_and_key_signatures(fifths, expected):
    root = score(["".join(note(s, 5 if i == 7 else 4) for i, s in enumerate("CDEFGABC"))], fifths=fifths)
    assert pitches(root) == expected


@pytest.mark.parametrize(("accidental", "expected"), [("sharp", 66), ("flat", 64), ("natural", 65)])
def test_accidental_within_bar_and_reset(accidental, expected):
    root = score(
        [note("F", accidental=accidental) + note("F") + note("F", 5) + note("G"), note("F", duration=4)],
        fifths=1 if accidental == "natural" else 0,
    )
    result = pitches(root)
    assert result[:2] == [expected, expected]
    assert result[2] == (78 if accidental == "natural" else 77)
    assert result[-1] == (66 if accidental == "natural" else 65)


def test_natural_after_sharp():
    root = score([note("F", accidental="sharp") + note("F") + note("F", accidental="natural") + note("F")])
    assert pitches(root) == [66, 66, 65, 65]


@pytest.mark.parametrize(
    ("duration", "extra", "expected"),
    [
        (1.5, "<dot/>", 1.5),
        (0.5, "", 0.5),
        (0.25, "", 0.25),
        (
            1 / 3,
            "<time-modification><actual-notes>3</actual-notes><normal-notes>2</normal-notes></time-modification>",
            1 / 3,
        ),
    ],
)
def test_notated_durations(duration, extra, expected):
    root = score([note(duration=duration, extra=extra)])
    assert parse_score(root)["timeline"][0]["duration"] == pytest.approx(expected)


@pytest.mark.parametrize(("beats", "unit", "duration"), [(3, 4, 3), (6, 8, 3), (4, 4, 4)])
def test_time_signatures_and_measure_rests(beats, unit, duration):
    result = parse_score(score([note(rest=True, duration=duration)], beats=beats, unit=unit))
    assert result["parts"][0]["measures"][0]["time"] == [beats, unit]
    assert result["duration_beats"] == duration
    assert result["timeline"] == []
    assert not any(w["type"] == "duration" for w in result["warnings"])


def test_quarter_rest_preserves_silence():
    result = parse_score(score([note() + note(rest=True) + note("E") + note("G")]))
    assert [e["start"] for e in result["timeline"]] == [0, 2, 3]


def test_tie_across_bar_carries_accidental_and_merges_sound():
    result = parse_score(
        score(
            [
                note("F", duration=4, accidental="sharp", tie="start"),
                note("F", duration=4, tie="stop"),
                note("F", duration=4),
            ]
        )
    )
    assert [(e["written_midi"], e["duration"]) for e in result["timeline"]] == [(66, 8), (65, 4)]


def test_slur_does_not_extend_note():
    result = parse_score(
        score(
            [
                note(extra='<notations><slur type="start"/></notations>')
                + note("D", extra='<notations><slur type="stop"/></notations>')
            ]
        )
    )
    assert len(result["timeline"]) == 2
    assert result["timeline"][0]["duration"] == 1


def test_simple_repeat():
    repeat = '<barline location="right"><repeat direction="backward"/></barline>'
    result = parse_score(score([note(duration=4), note("D", duration=4) + repeat]))
    assert [m["measure"] for m in result["occurrences"]] == [1, 2, 1, 2]
    assert result["duration_beats"] == 16


def test_first_second_ending():
    first = '<barline location="left"><ending number="1" type="start"/></barline>'
    end = '<barline location="right"><ending number="1" type="stop"/><repeat direction="backward"/></barline>'
    second = '<barline location="left"><ending number="2" type="start"/></barline>'
    result = parse_score(
        score([note(duration=4), first + note("D", duration=4) + end, second + note("E", duration=4)])
    )
    assert [m["measure"] for m in result["occurrences"]] == [1, 2, 1, 3]


@pytest.mark.parametrize(
    ("instrument", "expected"),
    [
        ("trumpet", 58),
        ("clarinet", 58),
        ("alto-sax", 51),
        ("tenor-sax", 46),
        ("baritone-sax", 39),
        ("horn", 53),
        ("piccolo", 72),
        ("double-bass", 48),
    ],
)
def test_instrument_transpositions(instrument, expected):
    result = parse_score(score([note(duration=4)]), instrument=instrument)
    assert result["timeline"][0]["sounding_midi"] == expected


def test_xml_transposition_not_applied_twice():
    root = score([note(duration=4)], transpose=-2)
    assert parse_score(root, instrument="trumpet")["timeline"][0]["sounding_midi"] == 58
    assert parse_score(root, instrument="alto-sax")["timeline"][0]["sounding_midi"] == 58
    assert parse_score(root, instrument="alto-sax", notation="written")["timeline"][0]["sounding_midi"] == 51
    assert transpose_for("tuba", "bb-treble", None) == -14


def test_clef_and_key_changes():
    changes = (
        "<attributes><key><fifths>1</fifths></key><clef><sign>F</sign><line>4</line></clef></attributes>"
    )
    result = parse_score(score([note("F", duration=4), changes + note("F", duration=4)]))
    assert pitches(score([note("F", duration=4), changes + note("F", duration=4)])) == [65, 66]
    assert result["parts"][0]["measures"][1]["clef"] == "F4"


def test_backup_polyphonic_chords():
    root = score(
        [
            note(duration=4)
            + note("E", duration=4, extra="<chord/>")
            + "<backup><duration>4</duration></backup>"
            + note("G", duration=4).replace("<voice>1", "<voice>2")
        ]
    )
    result = parse_score(root)
    assert [n["start"] for n in result["timeline"]] == [0, 0, 0]
    assert result["duration_beats"] == 4


def test_overfull_measure_warning_and_legal_chromatic_note():
    result = parse_score(score([note("C", accidental="sharp") + note() + note() + note() + note()]))
    assert any(w["type"] == "duration" for w in result["warnings"])
    assert not any(w["type"] == "key" for w in result["warnings"])


def test_edit_pitch_duration_undo_input_unchanged():
    original = score([note(duration=4)])
    event = parse_score(original)["timeline"][0]["id"]
    modified = edit_score(
        original,
        {
            "action": "update",
            "event_id": event,
            "fields": {"step": "F", "alter": 1, "octave": 5, "type": "quarter", "dots": 1},
        },
    )
    result = parse_score(modified)
    assert result["timeline"][0]["written_midi"] == 78
    assert result["timeline"][0]["duration"] == 1.5
    assert pitches(original) == [60]
    assert read_xml(ET.tostring(modified)).find(".//note").get("id") == event


def test_multiple_pages():
    result = parse_score(combine_pages([score([note(duration=4)]), score([note("D", duration=4)])]))
    assert result["measure_count"] == 2
    assert [e["written_midi"] for e in result["timeline"]] == [60, 62]
    assert len({e["id"] for e in result["timeline"]}) == 2


def test_midi_sounding_pitch_and_timing():
    root = score([note("C", duration=4)])
    result = parse_score(root, instrument="trumpet")
    midi = mido.MidiFile(file=BytesIO(midi_bytes(result, "trumpet")))
    notes = [m for track in midi.tracks for m in track if m.type in ("note_on", "note_off")]
    assert [m.note for m in notes] == [58, 58]
    assert notes[1].time == 4 * 960


def test_entities_rejected():
    with pytest.raises(ValueError):
        read_xml(
            b'<!DOCTYPE score-partwise [<!ENTITY x SYSTEM "file:///etc/passwd">]><score-partwise>&x;</score-partwise>'
        )


def test_zip_traversal_rejected():
    out = BytesIO()
    with zipfile.ZipFile(out, "w") as archive:
        archive.writestr("../evil", "bad")
    with pytest.raises(ValueError):
        read_xml(out.getvalue())


def test_generated_homr_output_matches_reference():
    examples = Path(__file__).resolve().parents[2] / "examples"
    reference = parse_score(read_xml((examples / "abend-am-fluss.musicxml").read_bytes()))
    recognized = parse_score(read_xml((examples / "omr-reference.musicxml").read_bytes()))
    assert [(e["written_midi"], e["duration"]) for e in recognized["timeline"]] == [
        (e["written_midi"], e["duration"]) for e in reference["timeline"]
    ]


def test_valid_compressed_musicxml():
    buffer = BytesIO()
    reference = ET.tostring(score([note(duration=4)]))
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "META-INF/container.xml",
            '<container><rootfiles><rootfile full-path="score.xml"/></rootfiles></container>',
        )
        archive.writestr("score.xml", reference)
    assert pitches(read_xml(buffer.getvalue())) == [60]
