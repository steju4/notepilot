"""Semitone offsets refer to written -> sounding pitch; MIDI programs are zero based."""

PROFILES = [
    ("piano", "Klavier", "Tasten", 0, 0, 21, 108),
    ("keyboard", "Keyboard", "Tasten", 0, 4, 21, 108),
    ("flute", "Querflöte", "Holzbläser", 0, 73, 60, 96),
    ("piccolo", "Piccolo", "Holzbläser", 12, 72, 62, 96),
    ("oboe", "Oboe", "Holzbläser", 0, 68, 58, 91),
    ("bassoon", "Fagott", "Holzbläser", 0, 70, 34, 79),
    ("clarinet", "Klarinette in B♭", "Holzbläser", -2, 71, 50, 94),
    ("bass-clarinet", "Bassklarinette in B♭", "Holzbläser", -14, 71, 48, 89),
    ("soprano-sax", "Sopransaxophon in B♭", "Holzbläser", -2, 64, 58, 89),
    ("alto-sax", "Altsaxophon in E♭", "Holzbläser", -9, 65, 58, 89),
    ("tenor-sax", "Tenorsaxophon in B♭", "Holzbläser", -14, 66, 58, 89),
    ("baritone-sax", "Baritonsaxophon in E♭", "Holzbläser", -21, 67, 57, 89),
    ("trumpet", "Trompete in B♭", "Blechbläser", -2, 56, 54, 86),
    ("flugelhorn", "Flügelhorn in B♭", "Blechbläser", -2, 56, 54, 86),
    ("horn", "Horn in F", "Blechbläser", -7, 60, 48, 89),
    ("tenorhorn", "Tenorhorn (Bassschlüssel, C)", "Blechbläser", 0, 58, 40, 77),
    ("tenorhorn-bb", "Tenorhorn in B♭ (Violinschlüssel)", "Blechbläser", -14, 58, 48, 89),
    ("baritone", "Bariton (Bassschlüssel, C)", "Blechbläser", 0, 58, 34, 77),
    ("euphonium", "Euphonium (Bassschlüssel, C)", "Blechbläser", 0, 58, 34, 77),
    ("trombone", "Posaune", "Blechbläser", 0, 57, 40, 77),
    ("bass-trombone", "Bassposaune", "Blechbläser", 0, 57, 34, 72),
    ("tuba", "Tuba (Bassschlüssel, C)", "Blechbläser", 0, 58, 28, 65),
    ("violin", "Violine", "Streicher", 0, 40, 55, 103),
    ("viola", "Viola", "Streicher", 0, 41, 48, 91),
    ("cello", "Violoncello", "Streicher", 0, 42, 36, 84),
    ("double-bass", "Kontrabass", "Streicher", -12, 43, 40, 79),
]
INSTRUMENTS = {
    p[0]: dict(
        id=p[0],
        name=p[1],
        family=p[2],
        transpose=p[3],
        program=p[4],
        range=[p[5], p[6]],
        sound="Lokale General-MIDI-Samples (TimGM6mb)",
    )
    for p in PROFILES
}


def transpose_for(instrument, notation, xml_transpose):
    if notation == "concert":
        return 0
    if notation == "bb-treble":
        return -14
    if notation == "eb-treble":
        return -9
    if notation == "auto" and xml_transpose is not None:
        return xml_transpose
    return INSTRUMENTS.get(instrument, INSTRUMENTS["piano"])["transpose"]
