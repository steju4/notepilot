import xml.etree.ElementTree as ET
from pathlib import Path

import cairosvg
import verovio

root = Path(__file__).resolve().parents[1] / "examples/corpus"
root.mkdir(exist_ok=True)


def generate(name, bars, fifths=0, time=(4, 4)):
    score = ET.Element("score-partwise", version="4.0")
    ET.SubElement(ET.SubElement(score, "work"), "work-title").text = name
    plist = ET.SubElement(score, "part-list")
    ET.SubElement(ET.SubElement(plist, "score-part", id="P1"), "part-name").text = "Referenz"
    part = ET.SubElement(score, "part", id="P1")
    types = {
        4: "whole",
        2: "half",
        1.5: "quarter",
        1: "quarter",
        0.5: "eighth",
        0.25: "16th",
        1 / 3: "eighth",
    }
    for i, bar in enumerate(bars):
        m = ET.SubElement(part, "measure", number=str(i + 1))
        if i == 0:
            a = ET.SubElement(m, "attributes")
            ET.SubElement(a, "divisions").text = "12"
            ET.SubElement(ET.SubElement(a, "key"), "fifths").text = str(fifths)
            t = ET.SubElement(a, "time")
            ET.SubElement(t, "beats").text = str(time[0])
            ET.SubElement(t, "beat-type").text = str(time[1])
            c = ET.SubElement(a, "clef")
            ET.SubElement(c, "sign").text = "G"
            ET.SubElement(c, "line").text = "2"
        accidental_state = {}
        tuplet_index = 0
        for p, d, acc in bar:
            n = ET.SubElement(m, "note")
            if p is None:
                ET.SubElement(n, "rest")
            else:
                pitch = ET.SubElement(n, "pitch")
                ET.SubElement(pitch, "step").text = p[0]
                ET.SubElement(pitch, "alter").text = str(acc)
                ET.SubElement(pitch, "octave").text = p[1]
            ET.SubElement(n, "duration").text = str(round(d * 12))
            ET.SubElement(n, "type").text = types[d]
            if d == 1.5:
                ET.SubElement(n, "dot")
            if p:
                expected = 1 if fifths == 1 and p[0] == "F" else -1 if fifths == -1 and p[0] == "B" else 0
                inherited = accidental_state.get(p, expected)
                if acc or acc != inherited:
                    ET.SubElement(n, "accidental").text = (
                        "sharp" if acc > 0 else "flat" if acc < 0 else "natural"
                    )
                accidental_state[p] = acc
            if d == 1 / 3:
                tm = ET.SubElement(n, "time-modification")
                ET.SubElement(tm, "actual-notes").text = "3"
                ET.SubElement(tm, "normal-notes").text = "2"
                if tuplet_index % 3 in (0, 2):
                    notation = ET.SubElement(n, "notations")
                    ET.SubElement(
                        notation,
                        "tuplet",
                        type="start" if tuplet_index % 3 == 0 else "stop",
                        number="1",
                        bracket="yes",
                    )
                tuplet_index += 1
        if i == len(bars) - 1:
            ET.SubElement(ET.SubElement(m, "barline", location="right"), "bar-style").text = "light-heavy"
    data = ET.tostring(score, encoding="utf-8", xml_declaration=True)
    (root / (name + ".musicxml")).write_bytes(data)
    toolkit = verovio.toolkit()
    toolkit.setOptions(
        {
            "inputFrom": "musicxml",
            "pageWidth": 1800,
            "pageHeight": 650,
            "scale": 65,
            "adjustPageHeight": True,
            "breaks": "none",
        }
    )
    assert toolkit.loadData(data.decode())
    svg = toolkit.renderToSVG(1)
    cairosvg.svg2png(
        bytestring=svg.encode(), write_to=str(root / (name + ".png")), scale=1.8, background_color="white"
    )


generate(
    "g-dur",
    [
        [("G4", 1, 0), ("A4", 1, 0), ("B4", 1, 0), ("C5", 1, 0)],
        [("D5", 1, 0), ("E5", 1, 0), ("F5", 1, 1), ("G5", 1, 0)],
        [("F5", 1, 1), ("E5", 1, 0), ("D5", 1, 0), ("C5", 1, 0)],
        [("B4", 1, 0), ("A4", 1, 0), ("G4", 2, 0)],
    ],
    fifths=1,
)
generate(
    "f-dur",
    [
        [("F4", 1, 0), ("G4", 1, 0), ("A4", 1, 0), ("B4", 1, -1)],
        [("C5", 1, 0), ("D5", 1, 0), ("E5", 1, 0), ("F5", 1, 0)],
        [("E5", 1, 0), ("D5", 1, 0), ("C5", 1, 0), ("B4", 1, -1)],
        [("A4", 1, 0), ("G4", 1, 0), ("F4", 2, 0)],
    ],
    fifths=-1,
)
generate(
    "vorzeichen",
    [
        [("F4", 1, 1), ("F4", 1, 1), ("F4", 1, 0), ("F4", 1, 0)],
        [("B4", 1, -1), ("B4", 1, -1), ("B4", 1, 0), ("B4", 1, 0)],
        [("C5", 1, 1), ("D5", 1, 0), ("E5", 1, -1), ("F5", 1, 0)],
        [("F4", 1, 0), ("G4", 1, 0), ("C5", 2, 0)],
    ],
)
generate(
    "rhythmus-3-4",
    [
        [("C4", 1.5, 0), ("D4", 0.5, 0), ("E4", 1, 0)],
        [(None, 1, 0), ("G4", 0.5, 0), ("A4", 0.5, 0), ("B4", 1, 0)],
        [("C5", 0.5, 0), ("B4", 0.5, 0), ("A4", 0.5, 0), ("G4", 0.5, 0), ("F4", 1, 0)],
        [("E4", 2, 0), (None, 1, 0)],
    ],
    time=(3, 4),
)
generate(
    "triolen-6-8",
    [
        [("C4", 0.5, 0), ("D4", 0.5, 0), ("E4", 0.5, 0), ("F4", 0.5, 0), ("G4", 1, 0)],
        [
            ("C5", 1 / 3, 0),
            ("B4", 1 / 3, 0),
            ("A4", 1 / 3, 0),
            ("G4", 1 / 3, 0),
            ("F4", 1 / 3, 0),
            ("E4", 1 / 3, 0),
            ("D4", 1, 0),
        ],
        [("C4", 1.5, 0), ("G4", 1.5, 0)],
        [("C5", 2, 0), (None, 1, 0)],
    ],
    time=(6, 8),
)
