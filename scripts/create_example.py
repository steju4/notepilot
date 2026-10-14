"""Generate our own public-domain score and render the OMR reference image (dev dependency)."""

from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring

ROOT = Path(__file__).resolve().parents[1]
root = Element("score-partwise", version="4.0")
SubElement(SubElement(root, "work"), "work-title").text = "Abend am Fluss"
SubElement(
    SubElement(root, "identification"), "creator", type="composer"
).text = "NotePilot · gemeinfreie Übung"
plist = SubElement(root, "part-list")
SubElement(SubElement(plist, "score-part", id="P1"), "part-name").text = "Melodie"
part = SubElement(root, "part", id="P1")
notes = [
    ("C4", "D4", "E4", "G4"),
    ("F4", "E4", "D4", "C4"),
    ("E4", "F4", "G4", "A4"),
    ("G4", "E4", "D4", "C4"),
]
for mi, pitches in enumerate(notes):
    m = SubElement(part, "measure", number=str(mi + 1))
    if mi == 0:
        a = SubElement(m, "attributes")
        SubElement(a, "divisions").text = "4"
        SubElement(SubElement(a, "key"), "fifths").text = "0"
        t = SubElement(a, "time")
        SubElement(t, "beats").text = "4"
        SubElement(t, "beat-type").text = "4"
        c = SubElement(a, "clef")
        SubElement(c, "sign").text = "G"
        SubElement(c, "line").text = "2"
        direction = SubElement(m, "direction")
        SubElement(SubElement(direction, "direction-type"), "words").text = "Ruhig"
        SubElement(direction, "sound", tempo="96")
    for p in pitches:
        n = SubElement(m, "note")
        pitch = SubElement(n, "pitch")
        SubElement(pitch, "step").text = p[0]
        SubElement(pitch, "octave").text = p[1]
        SubElement(n, "duration").text = "4"
        SubElement(n, "type").text = "quarter"
    if mi == 3:
        SubElement(SubElement(m, "barline", location="right"), "bar-style").text = "light-heavy"
xml = tostring(root, encoding="utf-8", xml_declaration=True)
(ROOT / "examples/abend-am-fluss.musicxml").write_bytes(xml)
if __name__ == "__main__":
    import cairosvg
    import verovio

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
    assert toolkit.loadData(xml.decode())
    svg = toolkit.renderToSVG(1)
    cairosvg.svg2png(
        bytestring=svg.encode(),
        write_to=str(ROOT / "examples/omr-reference.png"),
        scale=1.8,
        background_color="white",
    )
