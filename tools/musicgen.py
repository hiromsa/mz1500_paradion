"""Generate original three-voice PSG music for Makyou Kishi Paradion."""

# =========================================================================
# ■ このスクリプトに音楽を仕込む人 (別 AI) へのルール
# =========================================================================
# [出力]
# - 生成物は src/sideb/sound_data.asm (直接編集しないこと。このスクリプトが上書きする)
# - ビルド (build.ps1) が毎回 python tools/musicgen.py を実行する
#
# [必須ラベルと使われ方] (src/sideb/data.asm STAGE_TABLE / stage.asm が dw 参照)
#   BGM_FIELD1 : Stage 1 (魔界の森) 道中曲
#   BGM_ROCK   : Stage 2 (荒涼たる岩場) 道中曲
#   BGM_FIELD2 : Stage 3-5 (墓地 / 火山 / 幻魔城) 道中曲
#   BGM_BOSS   : ボス戦曲 (全ステージ共通)
#   BGM_CLEAR  : ステージクリア / エンディング (BGM_END は BGM_CLEAR への別名)
#   SE_SHOT / SE_EXPL / SE_PWUP : 効果音 (SE_DATA に生 db で記述)
#   ★ラベル名を変えたり削除しないこと。アセンブルが壊れる。
#
# [SCORES の書き方]
#   "ラベル": {
#       "title": ..., "ticks": 1 音符のフレーム数 (15=120BPM, 12=150BPM, 10=180BPM),
#       "lead" / "harmony" / "bass": 空白区切りの音符列 (3 声は同長,
#           音名は C4..B8, # は半音上げ, 休符は "-"),
#       "drums": ノイズを鳴らす音符インデックスのタプル,
#       "lead_volume" / "harmony_volume" / "bass_volume" / "drum_volume":
#           PSG 音量 0-15 (★小さいほど大きい。0=最大, 0Fh=消音),
#       "durations": (省略可) 音符毎の長さを個別指定するタプル
#   }
# - PSG は E9h への書込みで L/R 同時に出る。3 矩形波 + ノイズの 4ch 構成
# - 1 エントリ = [継続フレーム数][書込みバイト数][PSG バイト列...]、
#   末尾の db 0FFh がループ点 (V_BGM_LOOP) になる。曲は必ずループさせること
# - 音域目安: lead C5-C6 / harmony G3-G5 / bass A2-G3 (SN76489 の分周は 12bit)
#
# [SE_DATA の書き方]
#   1 tick 毎に 1 エントリ ([バイト数][PSG バイト列...]) を消費, db 0 = 終端
#   音量レジスタは ch0=90h / ch1=B0h / ch2=D0h / ノイズ=F0h
# =========================================================================
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "src" / "sideb" / "sound_data.asm"

# One step is an eighth note. The generator writes all three tone channels and
# the noise-channel volume each step, so rests and percussion cannot stick.
SCORES = {
    "BGM_FIELD1": {
        "title": "魔界の森 / A minor, 4-bar adventure theme",
        "ticks": 15,  # eighth note at 120 BPM (60 frames/second)
        "lead": "E5 A5 G5 E5 C5 E5 A4 C5 C5 A4 F4 A4 C5 A4 G4 E4 "
                "G4 C5 E5 G5 E5 D5 C5 G4 D5 B4 G4 B4 D5 C5 B4 G4",
        "harmony": "A4 E5 C5 E5 A4 E5 C5 E5 F4 C5 A4 C5 F4 C5 A4 C5 "
                   "E4 G4 C5 G4 E4 G4 C5 G4 D4 G4 B3 G4 D4 G4 B3 G4",
        "bass": "A2 A2 E3 A2 F3 F3 C3 F3 C3 C3 G3 C3 G3 G3 C3 G3 "
               "G3 G3 D3 G3 E3 E3 B2 E3 D3 D3 A2 D3 B2 G3 D3 G3",
        "drums": (0, 8, 16, 24),
        "lead_volume": 1,
        "harmony_volume": 5,
        "bass_volume": 3,
        "drum_volume": 9,
    },
    "BGM_FIELD2": {
        "title": "墓地から魔城 / D minor, darker 4-bar theme",
        "ticks": 12,  # eighth note at 150 BPM
        "lead": "A4 D5 F5 A5 G5 F5 E5 D5 C5 F5 A5 C6 A5 G5 F5 E5 "
                "D5 A5 D6 C6 A5 F5 G5 A5 E5 C#5 A4 C#5 E5 G5 F5 E5",
        "harmony": "F4 A4 D5 A4 F4 A4 D5 A4 F4 A4 C5 A4 F4 A4 C5 A4 "
                   "F4 A4 D5 A4 F4 A4 D5 A4 E4 G4 C#5 G4 E4 G4 C#5 G4",
        "bass": "D3 D3 A3 D3 A#2 A#2 F3 A#2 F3 F3 C3 F3 C4 C3 F3 C3 "
               "G3 G3 D3 G3 A2 A2 E3 A2 A3 A3 E3 A3 A2 A2 E3 A2",
        "drums": (0, 8, 16, 24),
        "lead_volume": 1,
        "harmony_volume": 6,
        "bass_volume": 3,
        "drum_volume": 8,
    },
    "BGM_BOSS": {
        "title": "ボス戦 / D minor, driving 4-bar battle theme",
        "ticks": 10,  # eighth note at 180 BPM
        "lead": "D5 D5 A4 D5 F5 D5 A4 D5 C5 C5 G4 C5 E5 C5 G4 C5 "
                "A#4 A#4 F4 A#4 D5 A#4 F4 A#4 A4 A4 E4 A4 C#5 A4 E4 A4",
        "harmony": "F4 A4 D5 A4 F4 A4 D5 A4 E4 G4 C5 G4 E4 G4 C5 G4 "
                   "D4 F4 A#4 F4 D4 F4 A#4 F4 C#4 E4 A4 E4 C#4 E4 A4 E4",
        "bass": "D3 D3 D3 D3 A2 A2 A2 A2 C3 C3 C3 C3 G3 G3 G3 G3 "
               "A#2 A#2 A#2 A#2 F3 F3 F3 F3 A2 A2 A2 A2 E3 E3 E3 E3",
        "drums": (0, 4, 8, 12, 16, 20, 24, 28),
        "lead_volume": 1,
        "harmony_volume": 6,
        "bass_volume": 2,
        "drum_volume": 7,
    },
    "BGM_ROCK": {
        "title": "荒涼たる岩場 / E minor, 4-bar rock theme",
        "ticks": 13,  # eighth note at about 138 BPM
        "lead": "E5 B4 E5 G5 F#5 E5 B4 E5 D5 A4 D5 F#5 E5 D5 A4 D5 "
                "C5 G4 C5 E5 D5 C5 G4 C5 B4 F#4 B4 D5 C5 B4 F#4 B4",
        "harmony": "G4 B4 E5 B4 G4 B4 E5 B4 A4 D5 F#5 D5 A4 D5 F#5 D5 "
                   "G4 C5 E5 C5 G4 C5 E5 C5 F#4 B4 D5 B4 F#4 B4 D5 B4",
        "bass": "E3 E3 B2 E3 G3 G3 D3 G3 D3 D3 A2 D3 A2 A2 E3 A2 "
               "C3 C3 G3 C3 G3 G3 D3 G3 B2 B2 F#3 B2 E3 E3 B2 E3",
        "drums": (0, 8, 16, 24),
        "lead_volume": 1,
        "harmony_volume": 5,
        "bass_volume": 3,
        "drum_volume": 8,
    },
    "BGM_CLEAR": {
        "title": "勝利のファンファーレ / C major",
        "durations": (15, 15, 15, 15, 15, 15, 30, 60),
        "lead": "C5 E5 G5 C6 G5 C6 E6 C6",
        "harmony": "G4 C5 E5 G5 E5 G5 C6 G5",
        "bass": "C3 C3 G3 C3 F3 F3 G3 C3",
        "drums": (),
        "lead_volume": 1,
        "harmony_volume": 5,
        "bass_volume": 3,
        "drum_volume": 15,
    },
}

SE_DATA = r"""; ---- 効果音 ----
; 射撃: 短い下降レーザー (PSG tone 0 / volume register 90h)
SE_SHOT:
        db 3, 8Eh,0Fh,91h
        db 3, 8Ch,12h,93h
        db 3, 8Fh,18h,96h
        db 2, 91h,9Ch
        db 1, 9Fh
        db 0

; 爆発: PSG noise channel 3 (noise volume register F0h)
SE_EXPL:
        db 2, 0E7h,0F5h
        db 2, 0E6h,0F7h
        db 2, 0E4h,0F9h
        db 2, 0E2h,0FBh
        db 1, 0FFh
        db 0

; パワーアップ: 上昇アルペジオ
SE_PWUP:
        db 3, 8Bh,06h,91h
        db 3, 87h,08h,93h
        db 3, 87h,04h,95h
        db 3, 83h,03h,91h
        db 1, 9Fh
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
    return [latch | (value & 0x0F), value >> 4, volume_latch | volume]


def emit_song(label, score):
    lead = score["lead"].split()
    harmony = score["harmony"].split()
    bass = score["bass"].split()
    if not (len(lead) == len(harmony) == len(bass)):
        raise ValueError(f"{label}: voice lengths differ")
    durations = score.get("durations", (score.get("ticks", 8),) * len(lead))
    if len(durations) != len(lead):
        raise ValueError(f"{label}: duration count differs from note count")
    drums = set(score["drums"])
    if any(index < 0 or index >= len(lead) for index in drums):
        raise ValueError(f"{label}: drum index outside score")

    lines = [f"; ---- {score['title']} ----", f"{label}:"]
    for index, (melody, chord, low, ticks) in enumerate(zip(lead, harmony, bass, durations)):
        data = []
        data += tone_bytes(0, melody, score["lead_volume"])
        data += tone_bytes(1, chord, score["harmony_volume"])
        data += tone_bytes(2, low, score["bass_volume"])
        if index in drums:
            data += [0xE7, 0xF0 | score["drum_volume"]]
        else:
            data += [0xFF]  # noise channel off between percussion accents
        note_count = len(data)
        comment = f" ; {melody}/{chord}/{low}"
        lines.append(f"        db {ticks}, {note_count}, " + ",".join(map(fmt, data)) + comment)
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
