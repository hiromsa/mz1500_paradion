"""Generate original three-voice PSG music for Makyou Kishi Paradion."""
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "src" / "sideb" / "sound_data.asm"

# Note tokens:
#   "A4" etc. : Attack a note (automatic envelope decay on the tail of the step)
#   "~"       : Tie / sustain previous note smoothly without re-attacking
#   "-"       : Rest (silence)
# Drum spec:
#   Can be a string of per-step characters ('.'=rest, 'k'=kick, 's'=snare, 'h'=hi-hat)
#   or a tuple of step indices (backward-compatible).

SCORES = {
    "BGM_FIELD1": {
        "title": "魔界の森 (Stage 1) / A minor, 8-bar Knightmare-style march",
        "ticks": 8,
        "lead": (
            "A4 - C5 - E5 ~ ~ D5 C5 - B4 - C5 - A4 - "
            "F5 ~ ~ E5 D5 - C5 - B4 ~ ~ ~ E5 - - - "
            "A4 - C5 - E5 ~ ~ D5 C5 - B4 - C5 - E5 - "
            "F5 - E5 - D5 - C5 - B4 ~ G#4 ~ A4 ~ ~ - "
        ),
        "harmony": (
            "C4 - E4 - A4 ~ ~ B4 A4 - G#4 - A4 - E4 - "
            "A4 ~ ~ G4 F4 - E4 - G#4 ~ ~ ~ B4 - - - "
            "C4 - E4 - A4 ~ ~ B4 A4 - G#4 - A4 - C5 - "
            "D5 - C5 - B4 - A4 - G#4 ~ E4 ~ C4 ~ ~ - "
        ),
        "bass": (
            "A3 A3 E3 A3 A3 A3 E3 A3 A3 A3 E3 A3 A3 A3 E3 G3 "
            "F3 F3 C3 F3 D3 D3 A3 D3 E3 E3 B2 E3 E3 F3 G3 G#3 "
            "A3 A3 E3 A3 A3 A3 E3 A3 A3 A3 E3 A3 A3 A3 G3 E3 "
            "D3 D3 A3 D3 F3 F3 C3 F3 E3 E3 B2 E3 A3 E3 A3 - "
        ),
        "drums": (
            "k.h.s.h.k.k.s.h."
            "k.h.s.h.k.s.k.s."
            "k.h.s.h.k.k.s.h."
            "k.h.s.h.k.s.k..."
        ),
        "lead_volume": 1,
        "harmony_volume": 4,
        "bass_volume": 2,
        "drum_volume": 6,
    },
    "BGM_FIELD2": {
        "title": "墓地から魔城 (Stage 3-5) / D minor, Baroque gothic theme",
        "ticks": 7,
        "lead": (
            "D5 ~ F5 E5 D5 - A4 - A#4 ~ D5 C5 A#4 - A4 - "
            "G4 - A#4 - D5 - G5 - F5 ~ E5 D5 C#5 - A4 - "
            "D5 ~ F5 E5 D5 - F5 - G5 ~ A#5 A5 G5 - F5 - "
            "E5 - G5 - F5 - D5 - C#5 ~ B4 C#5 D5 ~ ~ - "
        ),
        "harmony": (
            "F4 ~ A4 G4 F4 - F4 - G4 ~ A#4 A4 G4 - F4 - "
            "D4 - G4 - A#4 - D5 - A4 ~ G4 F4 E4 - C#4 - "
            "F4 ~ A4 G4 F4 - A4 - A#4 ~ D5 C5 A#4 - A4 - "
            "G4 - A#4 - A4 - F4 - E4 ~ G4 E4 F4 ~ ~ - "
        ),
        "bass": (
            "D3 D3 A3 D3 D3 D3 A3 D3 G3 G3 D3 G3 G3 G3 D3 F3 "
            "E3 E3 A#2 E3 E3 E3 A#2 E3 A3 A3 E3 A3 A3 G3 F3 E3 "
            "D3 D3 A3 D3 D3 D3 A3 D3 G3 G3 D3 G3 G3 G3 D3 G3 "
            "A3 A3 E3 A3 A#2 A#2 F3 A#2 A3 A3 E3 A3 D3 A3 D3 - "
        ),
        "drums": (
            "k.h.s.h.k.h.s.h."
            "k.h.s.h.k.s.s.s."
            "k.h.s.h.k.h.s.h."
            "k.s.k.s.k.s.k..."
        ),
        "lead_volume": 1,
        "harmony_volume": 5,
        "bass_volume": 2,
        "drum_volume": 6,
    },
    "BGM_BOSS": {
        "title": "ボス戦 / D minor, frantic chromatic battle theme",
        "ticks": 6,
        "lead": (
            "D5 D5 - D5 F5 - D5 - G#5 ~ G5 ~ F5 - D5 - "
            "A#4 A#4 - A#4 D5 - A#4 - E5 ~ F5 ~ E5 - C#5 - "
            "D5 D5 - D5 F5 - D5 - G#5 ~ G5 ~ F5 - D5 - "
            "A#5 - A5 - G5 - F5 - E5 - C#5 - D5 - - - "
        ),
        "harmony": (
            "A4 A4 - A4 D5 - A4 - D5 ~ C#5 ~ D5 - A4 - "
            "F4 F4 - F4 A#4 - F4 - A#4 ~ A4 ~ G4 - E4 - "
            "A4 A4 - A4 D5 - A4 - D5 ~ C#5 ~ D5 - A4 - "
            "D5 - C5 - A#4 - A4 - G4 - E4 - F4 - - - "
        ),
        "bass": (
            "D3 D3 D4 D3 D3 D3 D4 D3 B2 B2 B3 B2 A#2 A#2 A#3 A#2 "
            "G3 G3 G4 G3 G3 G3 G4 G3 A3 A3 A4 A3 A3 G3 F3 E3 "
            "D3 D3 D4 D3 D3 D3 D4 D3 B2 B2 B3 B2 A#2 A#2 A#3 A#2 "
            "G3 G3 F3 F3 E3 E3 D3 D3 A3 A3 A3 A3 D3 - - - "
        ),
        "drums": (
            "k.s.k.s.k.s.k.s."
            "k.s.k.s.k.s.s.s."
            "k.s.k.s.k.s.k.s."
            "k.s.k.s.k.k.s..."
        ),
        "lead_volume": 1,
        "harmony_volume": 4,
        "bass_volume": 2,
        "drum_volume": 5,
    },
    "BGM_ROCK": {
        "title": "荒涼たる岩場 (Stage 2) / E minor, syncopated driving rock",
        "ticks": 7,
        "lead": (
            "E5 - B4 E5 G5 ~ F#5 - E5 - D5 B4 D5 ~ ~ - "
            "C5 - G4 C5 E5 ~ D5 - B4 - A4 G4 B4 ~ ~ - "
            "E5 - B4 E5 G5 ~ A5 - B5 ~ G5 ~ E5 - D5 - "
            "C5 - D5 - E5 - F#5 - G5 ~ F#5 ~ E5 ~ ~ - "
        ),
        "harmony": (
            "B4 - G4 B4 E5 ~ D5 - B4 - F#4 D4 F#4 ~ ~ - "
            "G4 - E4 G4 C5 ~ B4 - G4 - D4 B3 D4 ~ ~ - "
            "B4 - G4 B4 E5 ~ F#5 - G5 ~ E5 ~ B4 - B4 - "
            "E4 - F#4 - G4 - A4 - B4 ~ B4 ~ G4 ~ ~ - "
        ),
        "bass": (
            "E3 E3 B2 E3 E3 E3 D3 E3 D3 D3 A3 D3 D3 D3 A3 D3 "
            "C3 C3 G3 C3 C3 C3 G3 C3 B2 B2 F#3 B2 B2 C3 D3 D#3 "
            "E3 E3 B2 E3 E3 E3 F#3 G3 G3 G3 D3 G3 E3 E3 B2 E3 "
            "C3 C3 D3 D3 E3 E3 F#3 F#3 G3 G3 B2 B2 E3 B2 E3 - "
        ),
        "drums": (
            "k.h.s.h.k.k.s.h."
            "k.h.s.h.k.s.k.s."
            "k.h.s.h.k.k.s.h."
            "k.s.k.s.k.s.k..."
        ),
        "lead_volume": 1,
        "harmony_volume": 4,
        "bass_volume": 2,
        "drum_volume": 6,
    },
    "BGM_CLEAR": {
        "title": "勝利のファンファーレ / C major",
        "durations": (6, 6, 6, 12, 12, 12, 18, 36),
        "lead": "C5 E5 G5 C6 G#5 A#5 C6 ~",
        "harmony": "E4 G4 C5 E5 C5 D5 E5 ~",
        "bass": "C3 C3 C3 E3 G#3 A#3 C3 ~",
        "drums": "s.s.s.k.",
        "lead_volume": 1,
        "harmony_volume": 4,
        "bass_volume": 2,
        "drum_volume": 6,
    },
}

SE_DATA = r"""; ---- 効果音 ----
; 射撃: 鋭いツイン・レーザー風 (PSG tone 0 / volume register 90h)
SE_SHOT:
        db 3, 3, 085h,006h,090h
        db 3, 3, 08Ah,008h,091h
        db 3, 3, 08Fh,00Bh,092h
        db 3, 3, 084h,010h,094h
        db 3, 3, 08Ch,016h,098h
        db 1, 1, 09Fh
        db 0

; 爆発: 重低音ノイズ減衰 (PSG noise channel 3)
SE_EXPL:
        db 2, 2, 0E6h,0F1h
        db 2, 2, 0E7h,0F2h
        db 2, 2, 0E6h,0F4h
        db 2, 2, 0E7h,0F6h
        db 2, 2, 0E6h,0F9h
        db 2, 2, 0E7h,0FCh
        db 1, 1, 0FFh
        db 0

; パワーアップ: コナミ風きらめきアルペジオ
SE_PWUP:
        db 3, 3, 08Eh,00Bh,091h
        db 3, 3, 087h,009h,091h
        db 3, 3, 08Fh,007h,091h
        db 3, 3, 08Fh,005h,091h
        db 3, 3, 087h,009h,092h
        db 3, 3, 08Fh,007h,092h
        db 3, 3, 08Fh,005h,091h
        db 3, 3, 087h,004h,091h
        db 1, 1, 09Fh
        db 0
"""

PITCH = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5,
         "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}


def divisor(note):
    match = re.fullmatch(r"([A-G]#?)([0-8])", note)
    if not match:
        raise ValueError(f"invalid note: {note!r}")
    name, octave = match.groups()
    midi = (int(octave) + 1) * 12 + PITCH[name]
    hz = 440.0 * 2 ** ((midi - 69) / 12)
    value = round(111860 / hz)
    # If a note is below SN76489's 10-bit divider limit (e.g. A2=1017+), shift up 1 octave
    while value > 1023:
        value //= 2
    if not 1 <= value <= 1023:
        raise ValueError(f"note out of SN76489 range: {note}")
    return value


def fmt(value):
    # z80asm treats A-F-leading tokens as symbols, so prefix every byte with 0.
    return f"0{value:02X}h"


def tone_bytes(channel, note, volume):
    if note == "-":
        return [0x90 + channel * 0x20 + 0x0F]
    value = divisor(note)
    latch = (0x80, 0xA0, 0xC0)[channel]
    volume_latch = (0x90, 0xB0, 0xD0)[channel]
    return [latch | (value & 0x0F), value >> 4, volume_latch | min(volume, 15)]


def resolve_ties(tokens):
    """Replace '~' with the preceding active note pitch."""
    resolved = []
    current = "-"
    for t in tokens:
        if t == "~":
            resolved.append(current)
        else:
            current = t
            resolved.append(t)
    return resolved


def emit_song(label, score):
    lead_raw = score["lead"].split()
    harm_raw = score["harmony"].split()
    bass_raw = score["bass"].split()
    if not (len(lead_raw) == len(harm_raw) == len(bass_raw)):
        raise ValueError(f"{label}: voice lengths differ")

    lead = resolve_ties(lead_raw)
    harmony = resolve_ties(harm_raw)
    bass = resolve_ties(bass_raw)

    durations = score.get("durations", (score.get("ticks", 8),) * len(lead))
    if len(durations) != len(lead):
        raise ValueError(f"{label}: duration count differs from note count")

    drums = score["drums"]
    if isinstance(drums, str):
        drum_str = drums.ljust(len(lead), ".")
    else:
        if any(index < 0 or index >= len(lead) for index in drums):
            raise ValueError(f"{label}: drum index outside score")
        drum_str = "".join("s" if i in set(drums) else "." for i in range(len(lead)))

    lines = [f"; ---- {score['title']} ----", f"{label}:"]
    for idx, (melody, chord, low, ticks) in enumerate(zip(lead, harmony, bass, durations)):
        rel_ticks = 2 if ticks >= 5 else 1
        atk_ticks = max(1, ticks - rel_ticks)

        lead_tied = (idx + 1 < len(lead_raw)) and (lead_raw[idx + 1] == "~")
        harm_tied = (idx + 1 < len(harm_raw)) and (harm_raw[idx + 1] == "~")

        # Attack phase
        atk_data = []
        atk_data += tone_bytes(0, melody, score["lead_volume"])
        atk_data += tone_bytes(1, chord, score["harmony_volume"])
        atk_data += tone_bytes(2, low, score["bass_volume"])

        d_char = drum_str[idx]
        if d_char == "k":
            atk_data += [0xE6, 0xF0 | score["drum_volume"]]
        elif d_char == "s":
            atk_data += [0xE7, 0xF0 | score["drum_volume"]]
        elif d_char == "h":
            atk_data += [0xE7, 0xF0 | min(15, score["drum_volume"] + 3)]
        else:
            atk_data += [0xFF]

        comment = f" ; {melody}/{chord}/{low}"
        lines.append(f"        db {atk_ticks}, {len(atk_data)}, " + ",".join(map(fmt, atk_data)) + comment)

        # Release / Decay phase
        rel_data = []
        rel_data += tone_bytes(0, melody, score["lead_volume"] + (0 if lead_tied else 2))
        rel_data += tone_bytes(1, chord, score["harmony_volume"] + (0 if harm_tied else 2))
        rel_data += tone_bytes(2, low, score["bass_volume"] + 5)
        if d_char == "s":
            rel_data += [0xE7, 0xF0 | min(15, score["drum_volume"] + 4)]
        else:
            rel_data += [0xFF]

        lines.append(f"        db {rel_ticks}, {len(rel_data)}, " + ",".join(map(fmt, rel_data)))

    lines.append("        db 0FFh                    ; loop")
    lines.append("")
    return lines


def main():
    lines = [
        "; generated by tools/musicgen.py - edit the score in that script",
        "; PSG register map: tone/volume channels 0=80h/90h, 1=A0h/B0h,",
        "; channel 2=C0h/D0h, noise channel 3=E0h/F0h (E9h writes L+R).",
        "; BGM entry: [duration in frames][byte count][PSG writes...], FFh loops.",
        "; Three square-wave voices plus brief noise percussion; rests are explicit.",
        "",
    ]
    for label, score in SCORES.items():
        lines.extend(emit_song(label, score))
    lines.extend(["BGM_END:        dw BGM_CLEAR", ""])
    lines.extend(SE_DATA.rstrip().splitlines())
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write("\n".join(lines) + "\n")
    print(f"{OUTPUT}: {sum(len(score['lead'].split()) for score in SCORES.values())} notes")


if __name__ == "__main__":
    main()