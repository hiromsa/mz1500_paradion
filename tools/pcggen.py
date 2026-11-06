"""PCG pattern generator for Makyou Kishi Paradion (MZ-1500).

Converts ASCII pixel art into MZ-1500 PCG data (3 color planes x 4 banks x 256 chars)
and emits:
  - src/sidea/pcg_data.asm : chunk table + plane-major DB data (Side A loader input)
  - src/include/pcgmap.inc : tile/sprite code equates shared by Side A/B
  - src/sideb/map_data.asm : stage map row tables

Color characters: '.'/'K'=black(0) B=blue(1) R=red(2) M=magenta(3) G=green(4)
                  C=cyan(5) Y=yellow(6) W=white(7)
Usage: python tools/pcggen.py   (run from project root)
"""
import os

COLOR = {'.': 0, 'K': 0, 'B': 1, 'R': 2, 'M': 3, 'G': 4, 'C': 5, 'Y': 6, 'W': 7, 'b': 1, 'r': 2, 'm': 3, 'g': 4, 'c': 5, 'y': 6, 'w': 7}

class Bank:
    def __init__(self):
        self.chars = {}  # code -> list of 8 strings (8x8 art)

    def put(self, code, art):
        assert len(art) == 8, f'char {code:#04x}: need 8 rows, got {len(art)}'
        for r in art:
            assert len(r) == 8, f'char {code:#04x}: row len {len(r)}: {r!r}'
            for ch in r:
                assert ch in COLOR, f'char {code:#04x}: unknown color {ch!r}'
        self.chars[code] = art

    def put16(self, code, art):
        """16x16 art -> 4 chars at code (TL,TR,BL,BR)."""
        assert len(art) == 16, f'16x16 art at {code:#04x}: {len(art)} rows'
        for r in art:
            assert len(r) == 16, f'{code:#04x}: row len {len(r)}'
        for cy in range(2):
            for cx in range(2):
                rows = [row[cx*8:(cx+1)*8] for row in art[cy*8:(cy+1)*8]]
                self.put(code + cy*2 + cx, rows)

    def shift16(self, code_src, code_dst, px):
        """Emit a 16x16 sprite shifted right by px (2/4/6)."""
        art_src = self.pack16(code_src)
        shifted = [('.' * px + row)[:16] for row in art_src]
        self.put16(code_dst, shifted)

    def pack16(self, code):
        tl, tr, bl, br = (self.chars[code+i] for i in range(4))
        return [tl[y] + tr[y] for y in range(8)] + [bl[y] + br[y] for y in range(8)]

# ---------------------------------------------------------------- bank 0: tiles
b0 = Bank()
b0.put(0x01, [  # S1 grass
    "GGGGGGGG", "GGgGGGGG", "GGGGGgGG", "GgGGGGGG",
    "GGGGGGgG", "GGGgGGGG", "GGGGGGGG", "GGgGGGgG"])
b0.put(0x02, [  # S1 tree (solid)
    "gGgGGg.g", "GGggGGgg", "gGGgGGGg", "GGgGGggG",
    "ggGGgGGg", "...WW...", "...WW...", "..WWWW.."])
b0.put(0x03, [  # S1 bush (breakable)
    "........", ".gGGgGG.", "gGRRGGGg", "GGGGgRGG",
    "gGRGGGGg", "GGGgGRGG", ".gGGGgg.", "........"])
b0.put(0x04, [  # S1 flowers
    "GGGGGGGG", "G.Y.GG.Y", "GYGYGY.Y", "G.Y.GG.Y",
    "GGGGGGGG", ".Y..Y..Y", "GY.YGY.Y", "GGGGGGGG"])
b0.put(0x05, [  # S1 rock (solid)
    "........", "..WWWW..", ".WKKWKW.", "WWKWWKWW",
    "WWWWWKWW", ".WWWWWW.", "..WWWW..", "........"])
b0.put(0x08, [  # S2 dry ground
    "WWWWWWWW", "WKKWKWWW", "WWWWKWWW", "WKWWWWWK",
    "WWWWKWWW", "WWWKWWWW", "WKKWWKWW", "WWWWWWWW"])
b0.put(0x09, [  # S2 boulder (solid)
    "..WWWW..", ".WKWWKW.", "WWWWWWKW", "WKWWWWWW",
    "WWKWWWKW", "WWWWWKWW", ".WWWWWW.", "..KKKK.."])
b0.put(0x0A, [  # S2 crag (solid)
    "...WW...", "..WWKW..", ".WWWWWK.", "WWKWWWWW",
    "WWWWWKWW", "WKWWWWWW", "WWWWKWWW", "KKKKKKKK"])
b0.put(0x0B, [  # S2 bones (deco)
    "WWWWWWWW", "KWWWWWWK", "WW.KK.WW", "W.KWWK.W",
    "W.KWWK.W", "WW.KK.WW", "KWWWWWWK", "WWWWWWWW"])
b0.put(0x0C, [  # S2 rubble (breakable)
    "........", ".W.WW.W.", "WWKWWWWW", ".WWWWK.W",
    "WKWWWWWW", ".WWWKWWW", "WWWWWWKW", "........"])
b0.put(0x0D, [  # S3 graveyard ground
    "gggggggg", "gCgggCgg", "gggggggg", "ggCggggg",
    "gggggCgg", "gCgggggg", "gggggggC", "gggggggg"])
b0.put(0x0E, [  # S3 tombstone (solid)
    "..WWWW..", ".WWKKWW.", ".WKWWKW.", ".WWWWWW.",
    ".WKWWWW.", ".WWWWWW.", ".WWWWWW.", "gggggggg"])
b0.put(0x0F, [  # S3 dead tree (solid)
    "W..W...W", "WW.W..WW", ".W.W.WW.", ".WW.WWW.",
    "..WWW...", "...WW...", "...WW...", "..WWWW.."])
b0.put(0x10, [  # S3 fence (deco)
    "W..W..W.", "WWWWWWWW", "WWWWWWWW", "W..W..W.",
    "W..W..W.", "WWWWWWWW", "WWWWWWWW", "g..g..g."])
b0.put(0x11, [  # S3 cursed urn (breakable)
    "........", "..YYYY..", ".YKKKKY.", ".YKKKKY.",
    ".YYKKYY.", "..YYYY..", "...YY...", "........"])
b0.put(0x12, [  # S4 scorched ground
    "RRRRRRRR", "RKKRKKRR", "RRKRRRRR", "RKRKKRKR",
    "RRRRRKRR", "RKRRRRKR", "RRKRRRRR", "RRRRRRRK"])
b0.put(0x13, [  # S4 lava (deco)
    "RRRRRRRR", "RRYYRRYR", "RYYYYYRR", "RYYRRYYR",
    "RRYRRRRR", "RRRRYYRR", "RRYYYRRR", "RRRRRRRR"])
b0.put(0x14, [  # S4 volcanic rock (solid)
    "..KKKK..", ".KWKKWK.", "KKKWWKKK", "KWWKKKKK",
    "KKKKWKKK", "KKWKKKWK", "KKKKKKKK", ".KKKKKK."])
b0.put(0x15, [  # S4 obsidian (breakable)
    "........", ".KKKKKK.", "KKWKKKKK", "KKKKWKKK",
    "KKKKKKWK", "KKWKKKKK", ".KKKKKK.", "........"])
b0.put(0x16, [  # S5 castle floor
    "BBBBBBBB", "BBBKWBBB", "BBBBBBBB", "BWKBBBBB",
    "BBBBBBBB", "BBBBKWBB", "BBBBBBBB", "BBKWBBBB"])
b0.put(0x17, [  # S5 castle wall (solid)
    "WWWWWWWW", "WBBWBBWB", "WBBWBBWB", "WWWWWWWW",
    "WBWBBWBB", "WBWBBWBB", "WWWWWWWW", "WBBWBBWB"])
b0.put(0x18, [  # S5 pillar (solid)
    "WWWWWWWW", "WCCCCCCW", "WCWWWWCW", "WCWKKWCW",
    "WCWKKWCW", "WCWWWWCW", "WCCCCCCW", "WWWWWWWW"])
b0.put(0x19, [  # S5 stained window (deco)
    "BBBBBBBB", "BYYMMYYB", "BYMKKMYB", "BYMKKMYB",
    "BYYMMYYB", "BBBBBBBB", "BBBWWBBB", "BBBBBBBB"])
b0.put(0x1A, [  # S5 armor statue (breakable)
    "...WW...", "..WWWW..", ".WKKKKW.", ".WKWWKW.",
    "..WWWW..", ".W.WW.W.", ".W.WW.W.", "..W..W.."])
DIGITS = [
    [".WWWW...", "WW..WW..", "WW..WW..", "WW..WW..", "WW..WW..", "WW..WW..", ".WWWW...", "........"],
    ["...WW...", "..WWW...", "...WW...", "...WW...", "...WW...", "...WW...", ".WWWWW..", "........"],
    [".WWWW...", "WW..WW..", "....WW..", "...WW...", "..WW....", ".WW.....", "WWWWWW..", "........"],
    [".WWWW...", "WW..WW..", "....WW..", "..WWW...", "....WW..", "WW..WW..", ".WWWW...", "........"],
    ["...WW...", "..WWW...", ".WWWW...", "WW.WW...", "WWWWWW..", "...WW...", "...WW...", "........"],
    ["WWWWWW..", "WW......", "WWWWW...", "....WW..", "....WW..", "WW..WW..", ".WWWW...", "........"],
    ["..WWWW..", ".WW.....", "WW......", "WWWWW...", "WW..WW..", "WW..WW..", ".WWWW...", "........"],
    ["WWWWWW..", "....WW..", "...WW...", "..WW....", "..WW....", "..WW....", "..WW....", "........"],
    [".WWWW...", "WW..WW..", "WW..WW..", ".WWWW...", "WW..WW..", "WW..WW..", ".WWWW...", "........"],
    [".WWWW...", "WW..WW..", "WW..WW..", ".WWWWW..", "....WW..", "...WW...", ".WWW....", "........"],
]
for i, d in enumerate(DIGITS):
    b0.put(0x50 + i, d)
b0.put(0x5A, [  # heart (REST icon)
    "........", ".RR..RR.", "RRRRRRRR", "RRRRRRRR",
    "RRRRRRRR", ".RRRRRR.", "..RRRR..", "....RR.."])

# ---------------------------------------------------------------- bank 1: player
b1 = Bank()
def center16(rows):
    """Center variable-width pixel-art rows in a transparent 16px cell."""
    assert len(rows) == 16
    assert all(len(row) <= 16 for row in rows), [(row, len(row)) for row in rows if len(row) > 16]
    return [row.center(16, '.') for row in rows]

PALADIN = center16([
    "Y",                    # crest
    "YYY",
    "YWWY",
    "WWCWWC",               # helmet and visor
    "WWKKWW",
    "CCWWKKWWCC",           # broad pauldrons
    "CWWWWKKWWWWC",
    "CCWWWCWWWWCC",
    "CWWWWCWWCWWWC",
    "CCWWWWYYWWWWCC",       # gold breastplate
    ".CWWWWYYWWWWC.",
    "..CWWWWYYWWC..",
    "...CCWYYYYWCC...",     # split cloak
    "....CCWYYWCC....",
    ".....C....C.....",
    "....YY....YY....",     # boots
])
b1.put16(0x00, PALADIN)       # phase 0 (shift 0)
b1.shift16(0x00, 0x04, 2)     # phase 1 (shift 2px)
b1.shift16(0x00, 0x08, 4)     # phase 2 (shift 4px)
b1.shift16(0x00, 0x0C, 6)     # phase 3 (shift 6px)
b1.put(0x10, [  # player shot
    "...WW...", "..WWWW..", "..WKKW..", "..WWWW..",
    "...WW...", "...WW...", "........", "........"])
b1.put(0x11, [  # enemy shot
    "..RRRR..", ".RKKKKR.", ".RKMMKR.", ".RKMMKR.",
    ".RKKKKR.", "..RRRR..", "........", "........"])
EXPL8 = [
    ["........", "........", "........", "...YY...",
     "..YWWY..", "...YY...", "........", "........"],
    ["........", "..Y..Y..", ".YYWWYY.", "YWWWWWWY",
     ".YWWWWY.", ".YYWWYY.", "..Y..Y..", "........"],
    [".Y..YY..", "YRRWWRRY", "YRWRRWRy", ".YRRWRRY",
     "YRWRRWRy", "YRRWWRRY", "..YY..Y.", "........"],
    ["R..Y..R.", ".R.M.R..", "Y.M.M.Y.", "..M.M...",
     "Y..R..Y.", ".R...R..", "R..Y..R.", "........"],
]
for f, art in enumerate(EXPL8):
    art = [r.replace('y', 'Y') for r in art]
    art16 = [row + row[::-1] for row in art]      # mirror columns
    art16 = [row for row in art16 for _ in range(2)]  # double rows
    b1.put16(0x12 + f * 4, art16)
b1.put(0x22, [  # powerup: TWIN
    "KKKKKKKK", "KCCCCCCK", "KC.WWW.K", "KC.WW..K",
    "KC.WWWWK", "KC.W.W.K", "KCCCCCCK", "KKKKKKKK"])
b1.put(0x23, [  # powerup: SPEED
    "KKKKKKKK", "KGGGGGGK", "KG.WW..K", "KG.WW..K",
    "KGWWWW.K", "KG..WW.K", "KGGGGGGK", "KKKKKKKK"])
b1.put(0x24, [  # powerup: SHIELD
    "KKKKKKKK", "KWWWWWWK", "KWCCCCWK", "KWC..CWK",
    "KWC..CWK", "KWCCCCWK", "KWWWWWWK", "KKKKKKKK"])
b1.put(0x25, [  # powerup: 1UP
    "KKKKKKKK", "KGGGGGGK", "KGRRRRGK", "KGRGGKGK",
    "KGRGGGGK", "KGGRRGGK", "KGGGGGGK", "KKKKKKKK"])

# ---------------------------------------------------------------- bank 2: enemies
b2 = Bank()
GARGOYLE = center16([
    "M..............M",       # horns
    "MM............MM",
    "MMM..WW..WW..MMM",
    "MM..WWWWWWWW..MM",
    "M..WWKKWWKKWW..M",
    "..WWKRRWWRRKWW..",       # eyes in a bat-winged face
    ".MWWKKWWWWKKWWM.",
    "MMWWKKWWWWKKWWMM",
    ".MWWWWKKKKWWWWM.",
    "..WWKKWWKKWWKK..",
    "...WKKKKKKKKW...",
    "...WWKKRRKKWW...",
    "....WWKKKKWW....",
    "...MMWW..WWMM...",       # claws
    "..MM........MM..",
    ".M............M.",
])
GARGOYLE2 = center16([
    "................",
    "M..............M",
    "MM............MM",
    "MMM..WW..WW..MMM",
    "MM..WWWWWWWW..MM",
    "M..WWKKWWKKWW..M",
    "..WWKRRWWRRKWW..",
    ".MWWKKWWWWKKWWM.",
    "MMWWKKWWWWKKWWMM",
    ".MWWWWKKKKWWWWM.",
    "..WWKKWWKKWWKK..",
    "...WKKKKKKKKW...",
    "...WWKKRRKKWW...",
    "....WWKKKKWW....",
    ".....MM..MM.....",       # wings beat upward
    "......M..M......",
])
b2.put16(0x00, GARGOYLE)
b2.put16(0x04, GARGOYLE2)
WISP = center16([
    ".......C........",
    "......CWC.......",
    ".....CWWWC......",
    "....CWWWWWC.....",
    "...CWWKKWWWC....",       # skull and hollow eyes
    "..CWWWRRWWWCC...",
    "..CWWWWWWWWWC...",
    "..CWWWCWWCWWC...",
    "...CWWWWWWWC....",
    "....CWWWWWC.....",
    ".....CCCCCC.....",
    "....CC.CC.CC....",       # curling ghost tail
    "...CC......C....",
    "..C........CC...",
    ".C............C.",
    "................",
])
WISP2 = center16([
    "................",
    ".......C........",
    "......CWC.......",
    ".....CWWWC......",
    "....CWWWWWC.....",
    "...CWWKKWWWC....",
    "..CWWWRRWWWCC...",
    "..CWWWWWWWWWC...",
    "..CWWWCWWCWWC...",
    "...CWWWWWWWC....",
    "....CWWWWWC.....",
    ".....CCCCCC.....",
    "......CC.CC.....",
    ".....CC...CC....",
    "....CC.....CC...",
    "................",
])
b2.put16(0x08, WISP)
b2.put16(0x0C, WISP2)

# ---------------------------------------------------------------- bank 3: boss
b3 = Bank()
TRENT = [  # 大樹の魔物トレント (32x32)
    "....gGGGGg......gGGGGg..........",
    "..gGGgggGGGg...gGGggGGg.........",
    ".gGGgRRRRgGGg.gGGgRRRgGGg.......",
    "gGGgRRYYRRgGGgGGgRRYYRgGGg......",
    "gGGRRYYYYRRgGGGgRYYYYRRgGGg.....",
    "gGGRRYYYYRRGGgGGRRYYYYRRgGGg....",
    ".gGRRYYYYRRGGGGGRRYYYYRRgGg.....",
    ".ggGRRYYRRgGgGgGRRYYRRgGGgg.....",
    "..ggGRRRRgGg.g.gGRRRRgGgg.......",
    "...ggGGGGgg..g..gGGGGgg.........",
    "....gGGgg.....ggGGggg...........",
    ".....gg...gGGGGg...gg...........",
    ".........gGGGGGGg...............",
    "......gGGGgGGgGGGg..............",
    ".....gGGg...g...gGGg............",
    "....gGGg..gMMm..gGGg............",
    "....gGg...MMMM...gGg............",
    "....gGg..MMMMM...gGg............",
    "....gGg..MMMMM...gGg............",
    "....gGg...MMMM...gGg............",
    "....gGg....MM....gGg............",
    "....gGg....gg....gGg............",
    "....gGg..........gGg............",
    "....gGg....MM....gGg............",
    "....gGg...MMMM...gGg............",
    "....gGg..MMMMMM..gGg............",
    ".....gGg.MMMMMM.gGg.............",
    ".....gGgg.MMMM.ggGg.............",
    "......gGg..MM..gGg..............",
    ".......gg..gg..gg...............",
    "........gg.gg.gg................",
    ".........ggg.ggg................",
]
TRENT = [r.replace('m', 'M') for r in TRENT]

def put32(bank, code, art):
    assert len(art) == 32 and all(len(r) == 32 for r in art), \
        f'32x32 art at {code:#04x}'
    for cy in range(4):
        for cx in range(4):
            rows = [row[cx*8:(cx+1)*8] for row in art[cy*8:(cy+1)*8]]
            bank.put(code + cy*4 + cx, rows)

def center32(rows):
    """Center variable-width pixel-art rows in a transparent 32px cell."""
    assert len(rows) == 32
    assert all(len(row) <= 32 for row in rows), [(row, len(row)) for row in rows if len(row) > 32]
    return [row.center(32, '.') for row in rows]

put32(b3, 0x00, TRENT)
# frame 2: eyes squint (YY -> KK on the face rows)
TRENT2 = TRENT[:3] + [r.replace('YY', 'KK') for r in TRENT[3:]]
put32(b3, 0x10, TRENT2)
DARKLORD = center32([  # 幻魔王ダークロード: 冠・角・赤眼・紫の鎧
    "Y",
    "YYY",
    "..W...W..",
    ".WW...WW.",
    "WWWWWWWWW",
    "WWKKKKKWW",
    ".WWKKKKKWW.",
    "..WWKKKKKWW..",
    "...WWKKKKKWW...",
    "..WWKKKKKKKKWW..",
    ".WWKKKKKKKKKKWW.",
    "WWKKKKKKKKKKKKWW",
    "WWKKKRRKKRRKKKWW",
    "WWKKRRRRKKRRRRKKWW",
    ".WWKKKKKKKKKKKKWW.",
    "..WWKKKKKKKKKKWW..",
    "...WWMMMMMMMMWW...",
    "..WWMMMMMMMMMMWW..",
    ".WWMMMCWWWWCMMMWW.",
    "WWMMMMWWMMMMWWMMMMWW",
    "WWMMMCCWWWWWWCCMMMWW",
    ".WWMMCCWWYYYYWWCCMMWW.",
    "..WWMMWWWWYYWWWWMMWW..",
    "...WWMMWWWWWWWWMMWW...",
    "....WWMMMMMMMMMMWW....",
    "....WWMMMMWWMMMMWW....",
    "...WWMMWW..WWMMWW...",
    "..WWMMWW....WWMMWW..",
    ".WWMMWW......WWMMWW.",
    "WWMMWW..........WWMMWW",
    "..WWWW..........WWWW..",
    "....WW..........WW....",
])
put32(b3, 0x20, DARKLORD)
DARKLORD2 = DARKLORD[:9] + [r.replace('RR', 'YY') for r in DARKLORD[9:15]] + DARKLORD[15:]
put32(b3, 0x30, DARKLORD2)

BANKS = [b0, b1, b2, b3]

# ---------------------------------------------------------------- emission
def emit_bank_plane(bank, plane):
    """Return 2048 bytes for one bank+plane (plane bit 0=B 1=R 2=G)."""
    data = []
    bit = 1 << plane
    for c in range(256):
        art = bank.chars.get(c)
        if art is None:
            data.extend([0] * 8)
            continue
        for row in art:
            v = 0
            for ch in row:
                v = (v << 1) | (1 if COLOR[ch] & bit else 0)
            data.append(v)
    return data

def emit_asm(path, label):
    lines = ['; generated by tools/pcggen.py - do not edit',
             '; PCG pattern data: chunk table + (bank,plane) 2KB segments',
             f'{label}:']
    table = []
    body = []
    offset = 0
    segs = 0
    for bank_idx, bank in enumerate(BANKS):
        for plane in range(3):
            data = emit_bank_plane(bank, plane)
            if not any(data):
                continue  # unused segment: PCG RAM stays zero after reset
            seg_label = f'PCG_SEG_B{bank_idx}_P{plane}'
            table.append(f'        db {plane + 1}            ; bank {bank_idx} plane {"BRG"[plane]}')
            table.append(f'        dw {seg_label}')
            table.append(f'        dw 0{0xD000 + bank_idx * 0x800:04X}h')
            body.append(f'{seg_label}:')
            for i in range(0, len(data), 16):
                chunk = data[i:i+16]
                body.append('        db ' + ','.join('0%02Xh' % b for b in chunk))
            body.append('')
            offset += len(data)
            segs += 1
    table.append('        db 0            ; end of table')
    with open(path, 'w', newline='\n') as f:
        f.write('\n'.join(lines + table + ['', '; --- segment data ---', ''] + body))
    print(f'{path}: {offset} bytes ({offset / 1024:.1f} KB) / {segs} segments')

def emit_map_inc(path):
    lines = ['; generated by tools/pcggen.py - PCG code equates', '']
    names = {
        0: [('T_BLANK', 0x00),
            ('T_S1_GRASS', 0x01), ('T_S1_TREE', 0x02), ('T_S1_BUSH', 0x03),
            ('T_S1_FLOW', 0x04), ('T_S1_ROCK', 0x05),
            ('T_S2_GROUND', 0x08), ('T_S2_BOULDER', 0x09), ('T_S2_CRAG', 0x0A),
            ('T_S2_BONES', 0x0B), ('T_S2_RUBBLE', 0x0C),
            ('T_S3_GROUND', 0x0D), ('T_S3_TOMB', 0x0E), ('T_S3_DEADTREE', 0x0F),
            ('T_S3_FENCE', 0x10), ('T_S3_URN', 0x11),
            ('T_S4_GROUND', 0x12), ('T_S4_LAVA', 0x13), ('T_S4_ROCK', 0x14),
            ('T_S4_OBSID', 0x15),
            ('T_S5_FLOOR', 0x16), ('T_S5_WALL', 0x17), ('T_S5_PILLAR', 0x18),
            ('T_S5_WINDOW', 0x19), ('T_S5_ARMOR', 0x1A),
            ('T_DIGIT0', 0x50), ('T_HEART', 0x5A)],
        1: [('SP_SHIP0', 0x00), ('SP_SHIP1', 0x04), ('SP_SHIP2', 0x08), ('SP_SHIP3', 0x0C),
            ('SP_SHOT', 0x10), ('SP_ESHOT', 0x11),
            ('SP_EXPL0', 0x12), ('SP_EXPL1', 0x16), ('SP_EXPL2', 0x1A), ('SP_EXPL3', 0x1E),
            ('SP_PW_TWIN', 0x22), ('SP_PW_SPEED', 0x23), ('SP_PW_SHIELD', 0x24), ('SP_PW_LIFE', 0x25)],
        2: [('SP_GARG0', 0x00), ('SP_GARG1', 0x04), ('SP_WISP0', 0x08), ('SP_WISP1', 0x0C)],
        3: [('SP_BOSS_F1', 0x00), ('SP_BOSS_F2', 0x10),
            ('SP_BOSS2_F1', 0x20), ('SP_BOSS2_F2', 0x30)],
    }
    for bank, entries in names.items():
        lines.append(f'; --- bank {bank} ---')
        for name, code in entries:
            lines.append('defc ' + name + ' = %02Xh' % code)
        lines.append('')
    with open(path, 'w', newline='\n') as f:
        f.write('\n'.join(lines))

# ---------------------------------------------------- stage maps
# '.'=ground 'T'=solid 'b'=breakable 'f'=deco 'r'=solid (per-stage alphabet)
MAP_DEF = {
    1: {'.': 0x01, 'T': 0x02, 'b': 0x03, 'f': 0x04, 'r': 0x05},
    2: {'.': 0x08, 'T': 0x09, 'b': 0x0C, 'f': 0x0B, 'r': 0x0A},
    3: {'.': 0x0D, 'T': 0x0E, 'b': 0x11, 'f': 0x10, 'r': 0x0F},
    4: {'.': 0x12, 'T': 0x14, 'b': 0x15, 'f': 0x13, 'r': 0x14},
    5: {'.': 0x16, 'T': 0x17, 'b': 0x1A, 'f': 0x19, 'r': 0x18},
}
MAP_ROWS = {
    1: [
        "........................................",
        "..T.....b.....T......T.....b............",
        "........................................",
        "..........f.......b..........f....T.....",
        "....T..................T................",
        ".....................b........b.........",
        "..b.........T.......................b...",
        ".........f..............f...............",
    ],
    2: [
        "........................................",
        ".....r.........r..........r.............",
        "......................b.................",
        "..b..........r.......r..........r.......",
        ".....................b........b.........",
        "........r..................b............",
        "......b.........r...........r...........",
        "........................................",
    ],
    3: [
        "........................................",
        "..T......T.......T..........T.......T...",
        "........................................",
        "....b........b.........b.......b........",
        "..........f...............f.............",
        "..f.....T.........T...........T....b....",
        "........................................",
        "....b..........b..........b..........b..",
    ],
    4: [
        "........................................",
        "....T.......T........T........T.........",
        "...................f........f...........",
        "..b.....f.......b.........b.............",
        "..........T..........T..........T.......",
        "......b.........b..........b............",
        "........................................",
        "..T........T..........T.........T.......",
    ],
    5: [
        "........................................",
        "..T.....T......T.....T......T......T....",
        "........................................",
        "....b.......b........b.........b........",
        "........f..........f...........f........",
        "..f....T......T........T.....T.....b....",
        "........................................",
        "....b.........b..........b........b.....",
    ],
}

def emit_maps(path):
    lines = ['; generated by tools/pcggen.py - stage map row tables (40 bytes per row)', '']
    for st in sorted(MAP_ROWS):
        alpha = MAP_DEF[st]
        lines.append(f'MAP_ROWS_S{st}:')
        for row in MAP_ROWS[st]:
            assert len(row) == 40, f'stage {st} row len {len(row)}'
            codes = [alpha[ch] for ch in row]
            lines.append('        db ' + ','.join(f'{c:02X}h' for c in codes))
        lines.append('')
    with open(path, 'w', newline='\n') as f:
        f.write('\n'.join(lines))

if __name__ == '__main__':
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    emit_asm(os.path.join(root, 'src', 'sidea', 'pcg_data.asm'), 'PCG_DATA_START')
    emit_map_inc(os.path.join(root, 'src', 'include', 'pcgmap.inc'))
    emit_maps(os.path.join(root, 'src', 'sideb', 'map_data.asm'))
    print('done')
