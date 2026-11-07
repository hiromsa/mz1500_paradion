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

COLOR = {
    '.': 0, 'K': 0, 'B': 1, 'R': 2, 'M': 3, 'G': 4, 'C': 5, 'Y': 6, 'W': 7,
    'b': 1, 'r': 2, 'm': 3, 'g': 4, 'c': 5, 'y': 6, 'w': 7,
}


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
            assert len(r) == 16, f'{code:#04x}: row len {len(r)}: {r!r}'
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


# ---------------------------------------------------------------- bank 0: tiles & UI
b0 = Bank()

TERRAIN_TILES = {
    1: {"ground": 0x80, "tree": 0x84, "river": 0x88, "bridge": 0x8C,
        "flowers": 0x90, "breakable": 0x94},
    2: {"ground": 0x98, "boulder": 0x9C, "ravine": 0xA0, "bridge": 0xA4,
        "bones": 0xA8, "breakable": 0xAC},
    3: {"ground": 0xB0, "tomb": 0xB4, "swamp": 0xB8, "bridge": 0xBC,
        "dead_tree": 0xC0, "breakable": 0xC4},
    4: {"ground": 0xC8, "rock": 0xCC, "lava": 0xD0, "bridge": 0xD4,
        "crystal": 0xD8, "breakable": 0xDC},
    5: {"ground": 0xE0, "pillar": 0xE4, "moat": 0xE8, "bridge": 0xEC,
        "window": 0xF0, "breakable": 0xF4},
}

# Native 16x16 terrain tiles (Bank 0 keeps real black 'K' because only Banks 1-3 recolor black)
TERRAIN_ART16 = {
    1: {
        "ground": [
            "GGGGGGGGGGGGGGGG", "GGGGGGGGGGGGGGGG", "GGGCKGGGGGGGGGGG", "GGGGGGGGGGGGGGGG",
            "GGGGGGGGGGGGGGGG", "GGGGGGGGGGGGCKGG", "GGGGGGGGGGGGGGGG", "GGGGGGGGGGGGGGGG",
            "GGGGGGGGGGGGGGGG", "GGGGGGCKGGGGGGGG", "GGGGGGGGGGGGGGGG", "GGGGGGGGGGGGGGGG",
            "GGGGGGGGGGGGGGGG", "GGGGGGGGGGGGGGGG", "GGCKGGGGGGGGGGGG", "GGGGGGGGGGGGGGGG",
        ],
        "tree": [
            "GGGGKKKKKKGGGGGG", "GGKKCCCCCCKKGGGG", "GKCCCWWWWCCCKGGG", "KCCWWCCCCWWCCKGG",
            "KCCWCCCCCCWCCKGG", "KCCCCCCCCCCCCKGG", "GKCCCGGGGCCCKGGG", "GGKKGGGGGGKKGGGG",
            "GKGGGGKKKKGGGGKG", "KGGGGKRRRRKGGGGK", "KGGGGKRRRRKGGGGK", "GKGGGKRRRRKGGGKG",
            "GGKKKKRRRRKKKKGG", "GGGGKRRRRRRKGGGG", "GGGKRKRRRRKRKGGG", "GGKKKKKKKKKKKKGG",
        ],
        "river": [
            "BBBBBBBBBBBBBBBB", "BBCWWCBBBBBBCBBB", "BBBBBBBBBBBBBBBB", "BBBBBBBBBCWWCBBB",
            "BBBBBBBBBBBBBBBB", "BBCBBBBBBBBBBBBB", "BBBBBBCWWCBBBBBB", "BBBBBBBBBBBBBBBB",
            "BBBBBBBBBBBBBBBB", "BBCWWCBBBBBBCBBB", "BBBBBBBBBBBBBBBB", "BBBBBBBBBCWWCBBB",
            "BBBBBBBBBBBBBBBB", "BBCBBBBBBBBBBBBB", "BBBBBBCWWCBBBBBB", "BBBBBBBBBBBBBBBB",
        ],
        "bridge": [
            "KKKKKKKKKKKKKKKK", "YYYYYYYYYYYYYYYY", "RRRRRRRRRRRRRRRR", "KKKKKKKKKKKKKKKK",
            "YYYYKYKYYKYKYYYY", "RRRRKRKRRKRKRRRR", "KKKKKKKKKKKKKKKK", "YYYYKYKYYKYKYYYY",
            "RRRRKRKRRKRKRRRR", "KKKKKKKKKKKKKKKK", "YYYYKYKYYKYKYYYY", "RRRRKRKRRKRKRRRR",
            "KKKKKKKKKKKKKKKK", "YYYYYYYYYYYYYYYY", "RRRRRRRRRRRRRRRR", "KKKKKKKKKKKKKKKK",
        ],
        "flowers": [
            "GGGGGGGGGGGGGGGG", "GGGYWGGGGGGGGGGG", "GGYRWYGGGGGGGGGG", "GGGYWGGGGGGYWGGG",
            "GGGGGGGGGGYMWYGG", "GGGGGGGGGGGYWGGG", "GGGGGGGGGGGGGGGG", "GGGGGGYWGGGGGGGG",
            "GGGGGYRWYGGGGGGG", "GGGGGGYWGGGGGGGG", "GGGGGGGGGGGGGGGG", "GGYWGGGGGGGGGGGG",
            "GYMWYGGGGGGYWGGG", "GGYWGGGGGGYRWYGG", "GGGGGGGGGGGYWGGG", "GGGGGGGGGGGGGGGG",
        ],
        "breakable": [
            "GGGGKKKKKKKKGGGG", "GGKKYYYYYYYYKKGG", "GKYWWWWWWWWWWYKG", "KYWKKKKKKKKKKWYK",
            "KYWKRYYYYYYRKWYK", "KYWKRYWWWWYRKWYK", "KYWKRYYYYYYRKWYK", "KYWKKKKKKKKKKWYK",
            "KYWKRYYYYYYRKWYK", "KYWKRYWWWWYRKWYK", "KYWKRYYYYYYRKWYK", "KYWKKKKKKKKKKWYK",
            "GKYWWWWWWWWWWYKG", "GGKKYYYYYYYYKKGG", "GGGGKKKKKKKKGGGG", "GGGGGGGGGGGGGGGG",
        ],
    },
    2: {
        "ground": [
            "BBBBBBBBBBBBBBBB", "BBBBBBBBBBBBBBBB", "BBBCKBBBBBBBBBBB", "BBBBBBBBBBBBBBBB",
            "BBBBBBBBBBBBBBBB", "BBBBBBBBBBBBCKBB", "BBBBBBBBBBBBBBBB", "BBBBBBBBBBBBBBBB",
            "BBBBBBBBBBBBBBBB", "BBBBBBCKBBBBBBBB", "BBBBBBBBBBBBBBBB", "BBBBBBBBBBBBBBBB",
            "BBBBBBBBBBBBBBBB", "BBBBBBBBBBBBBBBB", "BBCKBBBBBBBBBBBB", "BBBBBBBBBBBBBBBB",
        ],
        "boulder": [
            "BBBBKKKKKKKKBBBB", "BBKKCCCCCCCCKKBB", "BKCCCWWWWWWCCCKB", "KCCWWWWWWWWWWCCK",
            "KCCWWCCCCCCWWCCK", "KCCWCCCCCCCCWCCK", "KCCCCCCCCCCCCCCK", "KCCCBBBBBBBBCCCK",
            "KCCBBBBBBBBBBCCK", "KCCBKKKKKKKKBCCK", "KCCBBBBBBBBBBCCK", "BKBBBBBBBBBBBBKB",
            "BKBBBBKKKKKKKKBB", "BBKKKKBBBBBBBBKB", "BBBBKKKKKKKKKKBB", "BBBBBBBBBBBBBBBB",
        ],
        "ravine": [
            "KKKKKKKKKKKKKKKK", "BBKKKKKKKKKKKKBB", "KBBKKKKKKKKKKBBK", "KKBBKKKKKKKKBBKK",
            "KKKBBKKKKKKBBKKK", "KKKKKKKKKKKKKKKK", "KKKKKKKKKKKKKKKK", "KKKKKKKKKKKKKKKK",
            "KKKKKKKKKKKKKKKK", "KKKKKKKKKKKKKKKK", "KKKKKKKKKKKKKKKK", "KKKBBKKKKKKBBKKK",
            "KKBBKKKKKKKKBBKK", "KBBKKKKKKKKKKBBK", "BBKKKKKKKKKKKKBB", "KKKKKKKKKKKKKKKK",
        ],
        "bridge": [
            "KKKKKKKKKKKKKKKK", "CCCCCCCCCCCCCCCC", "WWWWWWWWWWWWWWWW", "KKKKKKKKKKKKKKKK",
            "CCCCKCKCCKCKCCCC", "WWWWKWKWWKWKWWWW", "KKKKKKKKKKKKKKKK", "CCCCKCKCCKCKCCCC",
            "WWWWKWKWWKWKWWWW", "KKKKKKKKKKKKKKKK", "CCCCKCKCCKCKCCCC", "WWWWKWKWWKWKWWWW",
            "KKKKKKKKKKKKKKKK", "CCCCCCCCCCCCCCCC", "WWWWWWWWWWWWWWWW", "KKKKKKKKKKKKKKKK",
        ],
        "bones": [
            "BBBBBBBBBBBBBBBB", "BBBBKKKKKKKKBBBB", "BBKKWWWWWWWWKKBB", "BKWWWWWWWWWWWWKB",
            "BKWWKKWWWWKKWWKB", "BKWWKKWWWWKKWWKB", "BBKKWWWWWWWWKKBB", "BBBBKKWKWKWWBBBB",
            "BBBBKKKKKKKKBBBB", "BBKKWWBBBBWWKKBB", "BBBBKKWWWWKKBBBB", "BBBBKKWWWWKKBBBB",
            "BBKKWWBBBBWWKKBB", "BBBBKKKKKKKKBBBB", "BBBBBBBBBBBBBBBB", "BBBBBBBBBBBBBBBB",
        ],
        "breakable": [
            "BBBBKKKKKKKKBBBB", "BBKKYYYYYYYYKKBB", "BKYWWWWWWWWWWYKB", "KYWKKKKKKKKKKWYK",
            "KYWKCCCCCCCCKWYK", "KYWKCWWWWWWCKWYK", "KYWKCCCCCCCCKWYK", "KYWKKKKKKKKKKWYK",
            "KYWKCCCCCCCCKWYK", "KYWKCWWWWWWCKWYK", "KYWKCCCCCCCCKWYK", "KYWKKKKKKKKKKWYK",
            "BKYWWWWWWWWWWYKB", "BBKKYYYYYYYYKKBB", "BBBBKKKKKKKKBBBB", "BBBBBBBBBBBBBBBB",
        ],
    },
    3: {
        "ground": [
            "GGGGGGGGGGGGGGGG", "GGGGGGGGGGGGGGGG", "GGGBKGGGGGGGGGGG", "GGGGGGGGGGGGGGGG",
            "GGGGGGGGGGGGGGGG", "GGGGGGGGGGGGBKGG", "GGGGGGGGGGGGGGGG", "GGGGGGGGGGGGGGGG",
            "GGGGGGGGGGGGGGGG", "GGGGGGGBKGGGGGGG", "GGGGGGGGGGGGGGGG", "GGGGGGGGGGGGGGGG",
            "GGGGGGGGGGGGGGGG", "GGGGGGGGGGGGGGGG", "GGBKGGGGGGGGGGGG", "GGGGGGGGGGGGGGGG",
        ],
        "tomb": [
            "GGGGKKKKKKKKGGGG", "GGKKWWWWWWWWKKGG", "GKWWWWWWWWWWWWKG", "KWWWCCCCCCCCWWWK",
            "KWWCCCCWWCCCCWWK", "KWWCCWWWWWWCCWWK", "KWWCCCCWWCCCCWWK", "KWWWCCCWWCCCWWWK",
            "KWWWCCCCCCCCWWWK", "KWWWWWWWWWWWWWWK", "KWWKKKKKKKKKKWWK", "KWWWWWWWWWWWWWWK",
            "KCCCCCCCCCCCCCCK", "GKKKKKKKKKKKKKKG", "GGGGKKKKKKKKGGGG", "GGGGGGGGGGGGGGGG",
        ],
        "swamp": [
            "CCCCCCCCCCCCCCCC", "CCKGGKCCCCCCKCCC", "CCCCCCCCCCCCCCCC", "CCCCCCCCCKGGKCCC",
            "CCCCCCCCCCCCCCCC", "CCKCCCCCCCCCCCCC", "CCCCCCKGGKCCCCCC", "CCCCCCCCCCCCCCCC",
            "CCCCCCCCCCCCCCCC", "CCKGGKCCCCCCKCCC", "CCCCCCCCCCCCCCCC", "CCCCCCCCCKGGKCCC",
            "CCCCCCCCCCCCCCCC", "CCKCCCCCCCCCCCCC", "CCCCCCKGGKCCCCCC", "CCCCCCCCCCCCCCCC",
        ],
        "bridge": [
            "KKKKKKKKKKKKKKKK", "YYYYYYYYYYYYYYYY", "MMMMMMMMMMMMMMMM", "KKKKKKKKKKKKKKKK",
            "YYYYKYKYYKYKYYYY", "MMMMKMKMMKMKMMMM", "KKKKKKKKKKKKKKKK", "YYYYKYKYYKYKYYYY",
            "MMMMKMKMMKMKMMMM", "KKKKKKKKKKKKKKKK", "YYYYKYKYYKYKYYYY", "MMMMKMKMMKMKMMMM",
            "KKKKKKKKKKKKKKKK", "YYYYYYYYYYYYYYYY", "MMMMMMMMMMMMMMMM", "KKKKKKKKKKKKKKKK",
        ],
        "dead_tree": [
            "GGKKGGGGGGGGKKGG", "GKWKGGGGGGGGKWKG", "GKWKGGGKKGGGKWKG", "GGKWKGGKWKGGKWKG",
            "GGGKWKKKWKKKWKGG", "GGGGKWWWWWWWKGGG", "GGGGGKWCCCWKGGGG", "GGGGGKWCWCWKGGGG",
            "GGGGGKWCWCWKGGGG", "GGGGGKWCWCWKGGGG", "GGGGKWWCCCWWKGGG", "GGGKWWCWWWCWWKGG",
            "GGKWWKGGGGKWWKGG", "GKKKKGGGGGGKKKKG", "GGGGGGGGGGGGGGGG", "GGGGGGGGGGGGGGGG",
        ],
        "breakable": [
            "GGGGKKKKKKKKGGGG", "GGKKYYYYYYYYKKGG", "GKYWWWWWWWWWWYKG", "GGKKYYYYYYYYKKGG",
            "GGGGKKMMMMKKGGGG", "GGGKKMMMMMMKKGGG", "GGKKMMWWWWMMKKGG", "GKKMMWYYYYWMMKKG",
            "GKKMMWYYYYWMMKKG", "GKKMMWWWWWWMMKKG", "GGKKMMMMMMMMKKGG", "GGGKKMMMMMMKKGGG",
            "GGGGKKYYYYKKGGGG", "GGGKKYYYYYYKKGGG", "GGGKKKKKKKKKKGGG", "GGGGGGGGGGGGGGGG",
        ],
    },
    4: {
        "ground": [
            "RRRRRRRRRRRRRRRR", "RRRRRRRRRRRRRRRR", "RRRYKRRRRRRRRRRR", "RRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRR", "RRRRRRRRRRRRYKRR", "RRRRRRRRRRRRRRRR", "RRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRR", "RRRRRRYKRRRRRRRR", "RRRRRRRRRRRRRRRR", "RRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRR", "RRRRRRRRRRRRRRRR", "RRYKRRRRRRRRRRRR", "RRRRRRRRRRRRRRRR",
        ],
        "rock": [
            "RRRRKKKKKKKKRRRR", "RRKKMMMMMMMMKKRR", "RKMMMYYYYYYMMMKR", "KMMYYYYYYYYYYMMK",
            "KMMYYMMMMMMYYMMK", "KMMYMMMMMMMMYMMK", "KMMMMMMMMMMMMMMK", "KMMMKKKKKKKKMMMK",
            "KMMKKKKKKKKKKMMK", "KMMKKKKKKKKKKMMK", "KMMKKKKKKKKKKMMK", "RKMMMMMMMMMMMMKR",
            "RKMMMMKKKKKKKKRR", "RRKKKKMMMMMMMMKR", "RRRRKKKKKKKKKKRR", "RRRRRRRRRRRRRRRR",
        ],
        "lava": [
            "YYYYYYYYYYYYYYYY", "YYRWWYRRRRRRYRRR", "YYYYYYYYYYYYYYYY", "YYYYYYYYYRWWYRRR",
            "YYYYYYYYYYYYYYYY", "YYRYYYYYYYYYYYYY", "YYYYYYRWWYYYYYYY", "YYYYYYYYYYYYYYYY",
            "YYYYYYYYYYYYYYYY", "YYRWWYRRRRRRYRRR", "YYYYYYYYYYYYYYYY", "YYYYYYYYYRWWYRRR",
            "YYYYYYYYYYYYYYYY", "YYRYYYYYYYYYYYYY", "YYYYYYRWWYYYYYYY", "YYYYYYYYYYYYYYYY",
        ],
        "bridge": [
            "KKKKKKKKKKKKKKKK", "CCCCCCCCCCCCCCCC", "BBBBBBBBBBBBBBBB", "KKKKKKKKKKKKKKKK",
            "CCCCKCKCCKCKCCCC", "BBBBKBKBBKBKBBBB", "KKKKKKKKKKKKKKKK", "CCCCKCKCCKCKCCCC",
            "BBBBKBKBBKBKBBBB", "KKKKKKKKKKKKKKKK", "CCCCKCKCCKCKCCCC", "BBBBKBKBBKBKBBBB",
            "KKKKKKKKKKKKKKKK", "CCCCCCCCCCCCCCCC", "BBBBBBBBBBBBBBBB", "KKKKKKKKKKKKKKKK",
        ],
        "crystal": [
            "RRRRRRRKKRRRRRRR", "RRRRRRKWWKRRRRRR", "RRRRRKWCCWKRRRRR", "RRRRKWCCCCWKRRRR",
            "RRRRKWCCWCWKRRRR", "RRRKWCWWCCWKRRRR", "RRRKWCCCCCBWKRRR", "RRKWCCCCCCBWKRRR",
            "RRKWCCCCCBWWKRRR", "RRRKWCCCBWWKRRRR", "RRRRKWCBWWKRRRRR", "RRRRRKWBBKRRRRRR",
            "RRRRRRKKKKRRRRRR", "RRRRRRRRRRRRRRRR", "RRRRRRRRRRRRRRRR", "RRRRRRRRRRRRRRRR",
        ],
        "breakable": [
            "RRRRKKKKKKKKRRRR", "RRKKCCCCCCCCKKRR", "RKCCWWWWWWWWCCKR", "KCCWKKKKKKKKWCCK",
            "KCCWKYYYYYYKWCCK", "KCCWKYWWWWYKWCCK", "KCCWKYYYYYYKWCCK", "KCCWKKKKKKKKWCCK",
            "KCCWKYYYYYYKWCCK", "KCCWKYWWWWYKWCCK", "KCCWKYYYYYYKWCCK", "KCCWKKKKKKKKWCCK",
            "RKCCWWWWWWWWCCKR", "RRKKCCCCCCCCKKRR", "RRRRKKKKKKKKRRRR", "RRRRRRRRRRRRRRRR",
        ],
    },
    5: {
        "ground": [
            "BBBBBBBBBBBBBBBB", "BBBBBBBBBBBBBBBB", "BBBMKBBBBBBBBBBB", "BBBBBBBBBBBBBBBB",
            "BBBBBBBBBBBBBBBB", "BBBBBBBBBBBBMKBB", "BBBBBBBBBBBBBBBB", "BBBBBBBBBBBBBBBB",
            "BBBBBBBBBBBBBBBB", "BBBBBBMKBBBBBBBB", "BBBBBBBBBBBBBBBB", "BBBBBBBBBBBBBBBB",
            "BBBBBBBBBBBBBBBB", "BBBBBBBBBBBBBBBB", "BBMKBBBBBBBBBBBB", "BBBBBBBBBBBBBBBB",
        ],
        "pillar": [
            "BBBBKKKKKKKKBBBB", "BBKKWWWWWWWWKKBB", "BKWWWWWWWWWWWWKB", "BBKKCCCCCCCCKKBB",
            "BBBBKWCWWCWKBBBB", "BBBBKWCWWCWKBBBB", "BBBBKWCWWCWKBBBB", "BBBBKWCWWCWKBBBB",
            "BBBBKWCWWCWKBBBB", "BBBBKWCWWCWKBBBB", "BBBBKWCWWCWKBBBB", "BBBBKWCWWCWKBBBB",
            "BBKKCCCCCCCCKKBB", "BKWWWWWWWWWWWWKB", "BBKKKKKKKKKKKKBB", "BBBBBBBBBBBBBBBB",
        ],
        "moat": [
            "KKKKKKKKKKKKKKKK", "KKBCCBKKKKKKBKKK", "KKKKKKKKKKKKKKKK", "KKKKKKKKKBCCBKKK",
            "KKKKKKKKKKKKKKKK", "KKBKKKKKKKKKKKKK", "KKKKKKBCCBKKKKKK", "KKKKKKKKKKKKKKKK",
            "KKKKKKKKKKKKKKKK", "KKBCCBKKKKKKBKKK", "KKKKKKKKKKKKKKKK", "KKKKKKKKKBCCBKKK",
            "KKKKKKKKKKKKKKKK", "KKBKKKKKKKKKKKKK", "KKKKKKBCCBKKKKKK", "KKKKKKKKKKKKKKKK",
        ],
        "bridge": [
            "KKKKKKKKKKKKKKKK", "YYYYYYYYYYYYYYYY", "WWWWWWWWWWWWWWWW", "KKKKKKKKKKKKKKKK",
            "YYYYKYKYYKYKYYYY", "WWWWKWKWWKWKWWWW", "KKKKKKKKKKKKKKKK", "YYYYKYKYYKYKYYYY",
            "WWWWKWKWWKWKWWWW", "KKKKKKKKKKKKKKKK", "YYYYKYKYYKYKYYYY", "WWWWKWKWWKWKWWWW",
            "KKKKKKKKKKKKKKKK", "YYYYYYYYYYYYYYYY", "WWWWWWWWWWWWWWWW", "KKKKKKKKKKKKKKKK",
        ],
        "window": [
            "BBBBKKKKKKKKBBBB", "BBKKYYYYYYYYKKBB", "BKYWWMMMMMMWWYKB", "KYWMMKKKKKKMMWYK",
            "KYWMKRRKKCCKMWYK", "KYWMKRRKKCCKMWYK", "KYWMKKKKKKKKMWYK", "KYWMKGGKKYYKMWYK",
            "KYWMKGGKKYYKMWYK", "KYWMMKKKKKKMMWYK", "BKYWWMMMMMMWWYKB", "BBKKYYYYYYYYKKBB",
            "BBBBKKKKKKKKBBBB", "BBBBBBBBBBBBBBBB", "BBBBBBBBBBBBBBBB", "BBBBBBBBBBBBBBBB",
        ],
        "breakable": [
            "BBBBKKKKKKKKBBBB", "BBKKWWWWWWWWKKBB", "BKWWCCCCCCCCWWKB", "KWWCKKKKKKKKCWWK",
            "KWWCKMMMMMMKCWWK", "KWWCKMYYYYMKCWWK", "KWWCKMMMMMMKCWWK", "KWWCKKKKKKKKCWWK",
            "KWWCKMMMMMMKCWWK", "KWWCKMYYYYMKCWWK", "KWWCKMMMMMMKCWWK", "KWWCKKKKKKKKCWWK",
            "BKWWCCCCCCCCWWKB", "BBKKWWWWWWWWKKBB", "BBBBKKKKKKKKBBBB", "BBBBBBBBBBBBBBBB",
        ],
    },
}

for stage, tiles in TERRAIN_TILES.items():
    for tile_name, code in tiles.items():
        b0.put16(code, TERRAIN_ART16[stage][tile_name])

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
    "........", ".RR..RR.", "RWW..WWR", "RRRRRRRR",
    "RRRRRRRR", ".RRRRRR.", "..RRRR..", "...RR..."])


# ---------------------------------------------------------------- bank 1: player / shots / items
# ★重要ルール: バンク 1〜3 の '.' と 'K' はステージの地面色に自動置換されるため、
#   スプライト内部の暗部には 'K' を使わず 'B'(青), 'R'(赤), 'M'(紫) を使うこと！
b1 = Bank()

# 主人公パラディion（白銀の兜、黄金の羽飾り、青い肩当て、深紅のマント）
PALADIN = [
    "....YY....YY....",
    "...YWWY..YWWY...",
    "....YWWCCWWY....",
    "....BWWWWWWB....",
    "...BWCCCCCCWB...",
    "..BYYWWWWWWYYB..",
    ".BYYYWRRRRWRYYB.",
    ".BYYRRRRRRRRYYB.",
    ".BBRRRRRRRRRRBB.",
    "..RRRRYYYYRRRR..",
    "..RRRRRRRRRRRR..",
    ".RRRRRMMMMRRRRR.",
    ".RRRR......RRRR.",
    "..RR.BB..BB.RR..",
    "....BWW..WWB....",
    "....BBB..BBB....",
]

PALADIN_WALK = [
    "....YY....YY....",
    "...YWWY..YWWY...",
    "....YWWCCWWY....",
    "....BWWWWWWB....",
    "...BWCCCCCCWB...",
    "..BYYWWWWWWYYB..",
    ".BYYYWRRRRWRYYB.",
    ".BYYRRRRRRRRYYB.",
    ".BBRRRRRRRRRRBB.",
    "..RRRRYYYYRRRR..",
    "..RRRRRRRRRRRR..",
    ".RRRRRMMMMRRRRR.",
    "..RRRR....RRRR..",
    "...RR.BB..BB.RR.",
    "...BWW....WWB...",
    "...BBB....BBB...",
]

b1.put16(0x00, PALADIN)       # walk A phase 0 (shift 0)
b1.shift16(0x00, 0x04, 2)     # walk A phase 1 (shift 2px)
b1.shift16(0x00, 0x08, 4)     # walk A phase 2 (shift 4px)
b1.shift16(0x00, 0x0C, 6)     # walk A phase 3 (shift 6px)
b1.put16(0x10, PALADIN_WALK)  # walk B phase 0
b1.shift16(0x10, 0x14, 2)     # walk B phase 1
b1.shift16(0x10, 0x18, 4)     # walk B phase 2
b1.shift16(0x10, 0x1C, 6)     # walk B phase 3

# 0x20: 自弾 (光の剣閃)
b1.put(0x20, [
    "...WW...",
    "..WYYW..",
    "..WYYW..",
    ".CWYYWC.",
    ".CCYYCC.",
    "..CWWC..",
    "...CC...",
    "........",
])

# 0x21: 敵弾 (呪いのエネルギー弾 - 旧コードの 0x11 誤記バグを修正！)
b1.put(0x21, [
    "..RRRR..",
    ".RMMMMR.",
    "RMYWWYMR",
    "RMWWWWMR",
    "RMYWWYMR",
    ".RMMMMR.",
    "..RRRR..",
    "........",
])

# 0x22, 0x26, 0x2A, 0x2E: 爆発 4 フレーム (16x16)
EXPL16 = [
    [
        "................", "................", "......YYYY......", "....YYWWWWYY....",
        "...YWWWWWWWWY...", "..YWWWWWWWWWWY..", "..YWWWWWWWWWWY..", "..YWWWWWWWWWWY..",
        "..YWWWWWWWWWWY..", "..YWWWWWWWWWWY..", "...YWWWWWWWWY...", "....YYWWWWYY....",
        "......YYYY......", "................", "................", "................",
    ],
    [
        "....YY....YY....", "..YYRRYYYYRRYY..", ".YRRRRYYYYRRRRY.", ".YRRYYYYYYYYRRY.",
        "YRRYYWWWWWWYYRRY", "YRYWWWWWWWWWWYRY", "YYWWWWWWWWWWWWYY", "YYWWWWWWWWWWWWYY",
        "YYWWWWWWWWWWWWYY", "YYWWWWWWWWWWWWYY", "YRYWWWWWWWWWWYRY", "YRRYYWWWWWWYYRRY",
        ".YRRYYYYYYYYRRY.", ".YRRRRYYYYRRRRY.", "..YYRRYYYYRRYY..", "....YY....YY....",
    ],
    [
        "..RR..YYYY..RR..", ".RRRRYYWWYYRRRR.", "RRRYYWWWWWWYYRRR", "RRYWWWRRRRWWWRYR",
        "YYWWRRRRRRRRWWRY", "YWWWRRMMMMRRWWWY", "YWWWRRMMMMRRWWWY", "YWRRMMMMMMMMRRWY",
        "YWRRMMMMMMMMRRWY", "YWWWRRMMMMRRWWWY", "YWWWRRMMMMRRWWWY", "YYWWRRRRRRRRWWRY",
        "RRYWWWRRRRWWWRYR", "RRRYYWWWWWWYYRRR", ".RRRRYYWWYYRRRR.", "..RR..YYYY..RR..",
    ],
    [
        ".R....Y..Y....R.", "R.R..Y....Y..R.R", "...MM......MM...", "..M..R....R..M..",
        "Y...R......R...Y", ".Y............Y.", "..M..........M..", "...R........R...",
        "...R........R...", "..M..........M..", ".Y............Y.", "Y...R......R...Y",
        "..M..R....R..M..", "...MM......MM...", "R.R..Y....Y..R.R", ".R....Y..Y....R.",
    ],
]
for f, art16 in enumerate(EXPL16):
    b1.put16(0x22 + f * 4, art16)

# 0x32..0x3E: パワーアップ紋章 4種 (16x16, 黒を使わず青・赤ベースで鮮明に描画)
b1.put16(0x32, [  # SP_PW_TWIN (ツインショット: 2本の輝く矢と 'T' エンブレム)
    "..BBBBBBBBBBBB..", ".BCCCCCCCCCCCCB.", "BCWWWWWWWWWWWWCB", "BCWBBBBBBBBBBWCB",
    "BCWBYYBBBBYYBWCB", "BCWYYYYBBYYYYWCB", "BCWBYYBBBBYYBWCB", "BCWBBBBWWBBBBWCB",
    "BCWBBWWWWWWBBWCB", "BCWBBBBWWBBBBWCB", "BCWBBBBWWBBBBWCB", "BCWBBBBWWBBBBWCB",
    "BCWBBBBBBBBBBWCB", "BCWWWWWWWWWWWWCB", ".BCCCCCCCCCCCCB.", "..BBBBBBBBBBBB..",
])
b1.put16(0x36, [  # SP_PW_SPEED (スピードアップ: 黄金の稲妻・ウイングブーツ)
    "..BBBBBBBBBBBB..", ".BGGGGGGGGGGGGB.", "BGWWWWWWWWWWWWGB", "BGWBBBBBBBBBBWGB",
    "BGWBBBBYYYYBBWGB", "BGWBBBYYYYBBBWGB", "BGWBBYYYYYYYYWGB", "BGWBYYYYYYYYBWGB",
    "BGWBBBBYYYYBBWGB", "BGWBBBYYYYBBBWGB", "BGWBBYYYYBBBBWGB", "BGWBYYYYBBBBBWGB",
    "BGWBBBBBBBBBBWGB", "BGWWWWWWWWWWWWGB", ".BGGGGGGGGGGGGB.", "..BBBBBBBBBBBB..",
])
b1.put16(0x3A, [  # SP_PW_SHIELD (シールド: 聖なる十字の盾)
    "..BBBBBBBBBBBB..", ".BYYYYYYYYYYYYB.", "BYWWWWWWWWWWWWYB", "BYWBBBBBBBBBBWYB",
    "BYWBCCCCCCCCBWYB", "BYWBCWWYYWWCBWYB", "BYWBCYYYYYYCBWYB", "BYWBBCCYYCCBBWYB",
    "BYWBBCCYYCCBBWYB", "BYWBBBCCCCBBBWYB", "BYWBBBBCCBBBBWYB", "BYWBBBBBBBBBBWYB",
    "BYWWWWWWWWWWWWYB", ".BYYYYYYYYYYYYB.", "..BBBBBBBBBBBB..", "................",
])
b1.put16(0x3E, [  # SP_PW_LIFE (1UP: 紅白のハート＆黄金クラウン)
    "..BBBBBBBBBBBB..", ".BYYYYYYYYYYYYB.", "BYWWWWWWWWWWWWYB", "BYWBBBBBBBBBBWYB",
    "BYWBRRR..RRRBWYB", "BYWRWWWRRWWWRWYB", "BYWRWWWWWWWWRWYB", "BYWRRRRRRRRRRWYB",
    "BYWBRRRRRRRRBWYB", "BYWBBRRRRRRBBWYB", "BYWBBBRRRRBBBWYB", "BYWBBBBRRBBBBWYB",
    "BYWBBBBBBBBBBWYB", "BYWWWWWWWWWWWWYB", ".BYYYYYYYYYYYYB.", "..BBBBBBBBBBBB..",
])


# ---------------------------------------------------------------- bank 2: enemies / chest
b2 = Bank()

# 種1 (0x00/0x04): ガーゴイル (悪魔の翼を持つ魔物)
GARGOYLE = [
    ".M....Y..Y....M.",
    "MM...YY..YY...MM",
    "MMM..MMMMMM..MMM",
    "MMMMMMWWWWMMMMMM",
    "MMMMMWBRRBWMMMMM",
    ".MMMMWWWWWWMMMM.",
    "..MMMBWWWWBMMM..",
    "...MMRRRRRRMM...",
    "..MMRRRRRRRRMM..",
    ".MMB.RRRRRR.BMM.",
    "MM...RYYYYR...MM",
    "M....RRRRRR....M",
    ".....RR..RR.....",
    "....RR....RR....",
    "...YY......YY...",
    "................",
]
GARGOYLE2 = [
    "......Y..Y......",
    ".....YY..YY.....",
    ".....MMMMMM.....",
    "....MMWWWWMM....",
    "...MMWBRRBWMM...",
    "..MMMWWWWWWMMM..",
    ".MMMMBWWWWBMMMM.",
    "MMMMMRRRRRRMMMMM",
    "MMM.MRRRRRRM.MMM",
    "MM...RRRRRR...MM",
    "M....RYYYYR....M",
    ".....RRRRRR.....",
    "....RR....RR....",
    "...YY......YY...",
    "................",
    "................",
]
b2.put16(0x00, GARGOYLE)
b2.put16(0x04, GARGOYLE2)

# 種2 (0x08/0x0C): ウィスプ (蒼白く燃える怨霊スカル)
WISP = [
    ".......CC.......",
    ".....CCWWCC.....",
    "....CWWWWWWC....",
    "...CWWWWWWWWC...",
    "..CWWBBRRBBWWC..",
    "..CWWBRYYRBWWC..",
    "..CWWWWWWWWWWC..",
    "...CWWBBBBWWC...",
    "...CWWBWWBWWC...",
    "....CCCCCCCC....",
    "...CCBBBBBBCC...",
    "..CC..CCCC..CC..",
    "..C....CC....C..",
    ".......CC.......",
    "......C.........",
    "................",
]
WISP2 = [
    "................",
    ".......CC.......",
    ".....CCWWCC.....",
    "....CWWWWWWC....",
    "...CWWWWWWWWC...",
    "..CWWBBRRBBWWC..",
    "..CWWBRYYRBWWC..",
    "..CWWWWWWWWWWC..",
    "...CWWBBBBWWC...",
    "...CWWBWWBWWC...",
    "....CCCCCCCC....",
    "....CCBBBBCC....",
    "...CC..CC..CC...",
    "....C..CC..C....",
    "........C.......",
    "................",
]
b2.put16(0x08, WISP)
b2.put16(0x0C, WISP2)

# 種3 (0x10/0x14): アイアンバット (岩場の鋼鉄コウモリ - 奇数=ガーゴイル型軌道)
BAT = [
    "C..............C",
    "CC....B..B....CC",
    "CCC..BBWWBB..CCC",
    "CCCCBWWWWWWTCCCC".replace('T', 'W'),
    "CCCCBWRRWRWBCCCC",
    ".CCCBBBBBBBBCCC.",
    "..CCCCCCCCCCCC..",
    "...CCBBBBBBCC...",
    "....BBBBBBBB....",
    "...B..BBBB..B...",
    "..B....BB....B..",
    "......Y..Y......",
    "................",
    "................",
    "................",
    "................",
]
BAT2 = [
    "......B..B......",
    ".....BBWWBB.....",
    "....BWWWWWWB....",
    "....BWRRWRWB....",
    "...CCBBBBBBCC...",
    "..CCCCCCCCCCCC..",
    ".CCCCBBBBBBCCCC.",
    "CCC.BBBBBBBB.CCC",
    "CC..B.BBBB.B..CC",
    "C.....Y..Y.....C",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
]
b2.put16(0x10, BAT)
b2.put16(0x14, BAT2)

# 種4 (0x18/0x1C): スケルトンナイト (墓地の骸骨剣士 - 偶数=ウィスプ型軌道)
SKELETON = [
    ".....YYYYYY.....",
    "....WWWWWWWW....",
    "...WWWWWWWWWW...",
    "...WWBBRRBBWW...",
    "...WWWWWWWWWW...",
    "....WWBWWBWW....",
    "..C..WWWWWW..G..",
    ".CWC.BBBBBB.GGG.",
    ".CWC.BWWWWB.GGG.",
    ".CWC.BBBBBB.GGG.",
    ".CCC..WWWW..GGG.",
    "..Y...BBBB......",
    ".....WW..WW.....",
    "....WW....WW....",
    "....BB....BB....",
    "................",
]
SKELETON2 = [
    "..C..YYYYYY.....",
    ".CWCWWWWWWWW....",
    ".CWCWWWWWWWWW...",
    ".CWCWBBRRBBWW...",
    ".CCCWWWWWWWWW...",
    "..Y..WWBWWBWWG..",
    ".....BBBBBB.GGG.",
    ".....BWWWWB.GGG.",
    ".....BBBBBB.GGG.",
    "......WWWW..GGG.",
    "......BBBB......",
    "....WW....WW....",
    "...WW......WW...",
    "...BB......BB...",
    "................",
    "................",
]
b2.put16(0x18, SKELETON)
b2.put16(0x1C, SKELETON2)

# 種5 (0x20/0x24): フレイムエレメンタル (火山の炎魔人 - 奇数=ガーゴイル型軌道)
EMBER = [
    "....R..YY..R....",
    "...RR.YYYY.RR...",
    "..RYYRWWWWYYRR..",
    ".RYYYYWWWWYYYYR.",
    ".RYYBBWWWWBBYYR.",
    "RYYYBWWYYWWBYYYR",
    "RYYYYWWWWWWYYYYR",
    "RRYYYYRRRRYYYYRR",
    ".RRYYRRRRRRYYRR.",
    "..RRRRYYYYRRRR..",
    "...RRRWWWWYYY...",
    "....RRYYYYRR....",
    ".....RRRRRR.....",
    "......RRRR......",
    ".......RR.......",
    "................",
]
EMBER2 = [
    "..R....YY....R..",
    ".RR...YYYY...RR.",
    ".RYY.RWWWWY.YYR.",
    "RYYYYWWWWWWYYYYR",
    "RYYYBBWWWWBBYYYR",
    ".RYYBWWYYWWBYYR.",
    ".RYYYYWWWWYYYYR.",
    "..RRYYRRRRYYRR..",
    "...RRRRRRRRRR...",
    "..RRRRYYYYRRRR..",
    "...RRRWWWWYYY...",
    "....RRRRRRRR....",
    ".....RR..RR.....",
    "....R......R....",
    "................",
    "................",
]
b2.put16(0x20, EMBER)
b2.put16(0x24, EMBER2)

# 種6 (0x28/0x2C): デスアーマー (幻魔城の黄金近衛騎士 - 偶数=ウィスプ型軌道)
SHADE = [
    "..Y..........Y..",
    ".YYY..YYYY..YYY.",
    "..YYYYWWWWYYYY..",
    "...YYWWWWWWYY...",
    "...YBBBBBBBBY...",
    "...YBRRYYRRBY...",
    "..MMYYYYYYYYMM..",
    ".MMMMYYYYYYMMMM.",
    "MMMMMWWWWWWWMMMM",
    "MMMMMYYYYYYMMMMM",
    ".MMMM.YYYY.MMMM.",
    "..MM..BBBB..MM..",
    ".....YYYYYY.....",
    "....YY....YY....",
    "....WW....WW....",
    "................",
]
SHADE2 = [
    "..Y..........Y..",
    ".YYY..YYYY..YYY.",
    "..YYYYWWWWYYYY..",
    "...YYWWWWWWYY...",
    "...YBBBBBBBBY...",
    "...YBRRYYRRBY...",
    ".MMMYYYYYYYYMMM.",
    "MMMMMYYYYYYMMMMM",
    "MMMMWWWWWWWWMMMM",
    ".MMMMYYYYYYMMMM.",
    "..MMM.YYYY.MMM..",
    "......BBBB......",
    "....YYYYYYYY....",
    "...YY......YY...",
    "...WW......WW...",
    "................",
]
b2.put16(0x28, SHADE)
b2.put16(0x2C, SHADE2)

# 0x30: 宝箱 (16x16)
CHEST = [
    "................",
    "..BBBBBBBBBBBB..",
    ".BYYYYYYYYYYYYB.",
    "BYWWWWWWWWWWWWYB",
    "BYRRRRRRRRRRRRRYB"[:16],
    "BYRRRRRRRRRRRRYB",
    "BYYYYYYWWYYYYYYB",
    "BYBBBBWWWWBBBBYB",
    "BYBBBBWWWWBBBBYB",
    "BYRRRRYYYYRRRRYB",
    "BYRRRRRRRRRRRRYB",
    "BYRRRRRRRRRRRRYB",
    "BYYYYYYYYYYYYYYB",
    ".BBBBBBBBBBBBBB.",
    "................",
    "................",
]
b2.put16(0x30, CHEST)


# ---------------------------------------------------------------- bank 3: boss (5 種 + 最終形態)
b3 = Bank()


def put32(bank, code, art):
    assert len(art) == 32 and all(len(r) == 32 for r in art), \
        f'32x32 art at {code:#04x}'
    for cy in range(4):
        for cx in range(4):
            rows = [row[cx*8:(cx+1)*8] for row in art[cy*8:(cy+1)*8]]
            bank.put(code + cy*4 + cx, rows)


# ボス1 (0x00/0x10): 大樹の魔物トレント (Stage 1)
TRENT = [
    "....BBBBGGGGGGGGGGGGGGGGBBBB....",
    "..BBGGGGGGGGGGGGGGGGGGGGGGGGBB..",
    ".BGGGGGGCCCCCCCCCCCCCCCCGGGGGGB.",
    "BGGGGGCCCCGGGGGGGGGGGGCCCCGGGGGB",
    "BGGGGCCGGGGGRRRRRRRRRRGGGGCCGGGB",
    "BGGGGGGGGGRRYYYYYYYYYYRRGGGGGGGB",
    ".BGGGGGGGGRYYYYBBBBYYYYRGGGGGGGB",
    "..BBGGGGGGGGGGGGGGGGGGGGGGGGBB..",
    "....BBGGGGBBBBBBBBBBBBBGGGBB....",
    ".....BGGGBRRRRRRRRRRRRRBGGB.....",
    "....BGGBRRYYYYYYYYYYYYYRRBGB....",
    "....BGBRRYYWWBBBBBBBBWWYYRBGB...",
    "....BGBRRRRBBBBBBBBBBBBRRRBGB...",
    "....BGGBRRRRRRRRRRRRRRRRRBGGB...",
    ".....BBRRRRRBBBBBBBBBRRRRRBB....",
    ".....BRRRRRRRRRRRRRRRRRRRRRB....",
    "....BRRBRRRRRRRRRRRRRRRRRBRRB...",
    "...BRRB.BRRBBBBBBBBBBBBRRB.BRRB.",
    "..BRRB..BRBWWRWWWWWRWWBRB..BRRB.",
    ".BRRB...BRBBBBBBBBBBBBBRB...BRRB",
    ".BRB....BRBWWRWWWWWRWWBRB....BRB",
    ".BB.....BRRBBBBBBBBBBBBRB.....BB",
    "........BRRRRRRRRRRRRRRRB.......",
    ".......BRRBRRRRRRRRRRRBRRB......",
    "......BRRB.BRRBRRRBRRB.BRRB.....",
    ".....BRRB..BRRBRRRBRRB..BRRB....",
    "....BRRB..BRRB.RRR.BRRB..BRRB...",
    "...BRRB..BRRB..RRR..BRRB..BRRB..",
    "..BRRB..BRRB...RRR...BRRB..BRRB.",
    ".BRRB..BRRB...BRRRB...BRRB..BRRB",
    ".BRB...BRB....BRRRB....BRB...BRB",
    "..B.....B......BBB......B.....B.",
]
put32(b3, 0x00, TRENT)
TRENT2 = (
    TRENT[:10] +
    [r.replace('YY', 'RR').replace('WWR', 'WWW') for r in TRENT[10:22]] +
    TRENT[22:]
)
put32(b3, 0x10, TRENT2)

# ボス2 (0x40/0x50): ストーンゴーレム (Stage 2)
GOLEM = [
    "......BBBBBBBBBBBBBBBBBBBB......",
    "....BBCCCCCCCCCCCCCCCCCCCCBB....",
    "...BCCWWWWWWWWWWWWWWWWWWWWCCB...",
    "..BCCWWCCCCCCCCCCCCCCCCCCWWCCB..",
    "..BCCWCCCBBBBBBBBBBBBBBCCCWCCB..",
    ".BCCWCCBBYYYYYYYYYYYYYYBBCCWCCB.",
    ".BCCWCCBYWWWWBBBBBBBBWWWWYBCCWCB",
    "BCCWCCBBYYYYYYYYYYYYYYYYBBCCWCCB",
    "BCCWCCCBBBBBBBBBBBBBBBBBBCCCWCCB",
    "BCCWCCCCCCCCCCCCCCCCCCCCCCCCWCCB",
    "BCCWWCCCCCCBBBBBBBBBBCCCCCCWWCCB",
    ".BCCWWWWWWBWWWWWWWWWWBWWWWWWCCB.",
    "..BBBBCCCCBBBBBBBBBBBBCCCCBBBB..",
    ".BCCCCWWWWCCCCCCCCCCCCWWWWCCCCB.",
    "BCCWWWWWWWWCCCCCCCCCCWWWWWWWWCCB",
    "BCWWCCCCCCWWCCCCCCCCWWCCCCCCWWCB",
    "BCWCCCCCCCCWCCYYYYCCWCCCCCCCCWCB",
    "BCWCCCCCCCCWCYWWWWYCWCCCCCCCCWCB",
    "BCWCCCCCCCCWCYWWWWYCWCCCCCCCCWCB",
    "BCWCCCCCCCCWCCYYYYCCWCCCCCCCCWCB",
    "BCWWCCCCCCWWCCCCCCCCWWCCCCCCWWCB",
    ".BCCWWWWWWCCCCCCCCCCCCWWWWWWCCB.",
    "..BBBBCCCCBBBBBBBBBBBBCCCCBBBB..",
    "....BBCCCCCCCCCCCCCCCCCCCCBB....",
    "...BCCWWWWCCBBBBBBBBCCWWWWCCB...",
    "..BCCWWWWWWCCB....BCCWWWWWWCCB..",
    "..BCCWCCCCWCCB....BCCWCCCCWCCB..",
    "..BCCWCCCCWCCB....BCCWCCCCWCCB..",
    "..BCCWWWWWWCCB....BCCWWWWWWCCB..",
    "...BCCCCCCCCB......BCCCCCCCCB...",
    "...BBBBBBBBBB......BBBBBBBBBB...",
    "................................",
]
put32(b3, 0x40, GOLEM)
GOLEM2 = (
    GOLEM[:5] +
    [r.replace('YY', 'RR').replace('WWWW', 'YYYY') for r in GOLEM[5:20]] +
    GOLEM[20:]
)
put32(b3, 0x50, GOLEM2)

# ボス3 (0x80/0x90): デスサイズ (Stage 3 - 大鎌を振るう死神)
DEATH = [
    "....................BBBBBBBBBB..",
    ".................BBBCCCCCCCCCCBB",
    "...............BBCCCWWWWWWWWWWCB",
    "......BBBBBBBB.BCWWWWWWWWWWWWCCB",
    "....BBMMMMMMMMBBCWWWWBBBBBBBBBB.",
    "...BMMMMMMMMMMMBBWWBB...........",
    "..BMMWWWWWWWWMMMBYYB............",
    "..BMWWWWWWWWWWMMBYYB............",
    ".BMWWBBBBBBBBWWMBYYB............",
    ".BMWBBRRWWBBRRWMBYYB............",
    ".BMWBBRRWWBBRRWMBYYB............",
    ".BMWWBBBBBBBBWWMBYYB............",
    "..BMWWWWWWWWWWMMBYYB............",
    "..BMMWWBWWBWWMMMBYYB............",
    "...BMMBBBBBBBBMMBYYB............",
    "..BMMMMMMMMMMMMMBYYB............",
    ".BMMMMRRRRRRRRMMBYYB............",
    "BMMMMRRRRRRRRRRRYYYYB...........",
    "BMMMRRRRYYYYRRRRYYYYB...........",
    "BMMRRRRYYYYYYRRRBYYB............",
    ".BMMRRRRYYYYRRRRBYYB............",
    "..BMMRRRRRRRRRRMBYYB............",
    "..BMMMMMMMMMMMMMBYYB............",
    "...BMMMMMMMMMMMMBYYB............",
    "...BMMMMBMMMMMMMBYYB............",
    "....BMMB.BMMMMMMBYYB............",
    "....BMB...BMMMMMBYYB............",
    ".....B.....BMMMMBYYB............",
    "............BMMB.BB.............",
    ".............BB.................",
    "................................",
    "................................",
]
put32(b3, 0x80, DEATH)
DEATH2 = (
    DEATH[:8] +
    [r.replace('RR', 'YY') for r in DEATH[8:22]] +
    DEATH[22:]
)
put32(b3, 0x90, DEATH2)

# ボス4 (0xC0/0xD0): 炎の魔竜ファイアドラゴン (Stage 4)
DRAGON = [
    ".YY..........................YY.",
    ".YWWY......YY......YY......YWWY.",
    "..YWWY....YWWY....YWWY....YWWY..",
    "..BYYWB..BWWWWB..BWWWWB..BWYYB..",
    ".BRRYYWBBWRRRRWBBWRRRRWBBWYYRRB.",
    ".BRRRYYWWRRRRRRRRRRRRRRWWYYRRRB.",
    "BRRRRRRRRRRBBBBBBBBBBRRRRRRRRRRB",
    "BRRRRRRRRRBYYYYYYYYYYBRRRRRRRRRB",
    "BRRYYYYRRRBYWWBBBBWWYBRRRYYYYRRB",
    "BRYYYYYYRRBBBBBBBBBBBBRRYYYYYYRB",
    "BRYYRRRRRRRRRRRRRRRRRRRRRRRRYYRB",
    "BRYRRRRRRRRBBBBBBBBBBRRRRRRRRYRB",
    ".BRRRRRRRRBWWWWWWWWWWBRRRRRRRRB.",
    ".BRRRRRRRRBBBBBBBBBBBBRRRRRRRRB.",
    "..BRRRRRRRRYYYYYYYYYYRRRRRRRRB..",
    "...BBRRRRRRYYYYYYYYYYRRRRRRBB...",
    ".....BBRRRRYYYYYYYYYYRRRRBB.....",
    "....BRRRRRRYYYYWWYYYYRRRRRRB....",
    "...BRRRRRRRYYYWWWWYYYRRRRRRRB...",
    "..BRRRRBBBRRYYWWWWYYRRBBBRRRRB..",
    ".BRRRBB...BRYYYYYYYYRB...BBRRRB.",
    ".BRRB.....BRRYYYYYYRRB.....BRRB.",
    "..BB......BRRRRRRRRRRB......BB..",
    "..........BRRRR..RRRRB..........",
    ".........BRRRRB..BRRRRB.........",
    "........BYYYYB....BYYYYB........",
    ".......BWWWWB......BWWWWB.......",
    "........BBBB........BBBB........",
    "................................",
    "................................",
    "................................",
    "................................",
]
put32(b3, 0xC0, DRAGON)
DRAGON2 = (
    DRAGON[:7] +
    [r.replace('WW', 'YY').replace('YYYYYY', 'WWWWWW') for r in DRAGON[7:21]] +
    DRAGON[21:]
)
put32(b3, 0xD0, DRAGON2)

# ボス5 形態1 (0x20/0x30): 幻魔王ダークロード (Stage 5)
DARKLORD = [
    "..WW........................WW..",
    ".WCCW......................WCCW.",
    ".WCCCW....................WCCCW.",
    "..WCCCW......WWWWWW......WCCCW..",
    "..WCCCCW...WWCCCCCCWW...WCCCCW..",
    "...WCCCCWWWCCCCCCCCCCWWWCCCCW...",
    "....WCCCCCCBBBBBBBBBBCCCCCCW....",
    ".....WCCCCBBBBBBBBBBBBCCCCW.....",
    "......WCCBBRRYYYYYYRRBBCCW......",
    "......WCBBRRYYYYYYYYRRBBCW......",
    ".....WCCBBRRRRRRRRRRRRBBCCW.....",
    "....WMMCBBRRRRBBBBRRRRBBCMMW....",
    "..WWMMMCBBRRRBCCCCBRRRBBCMMMWW..",
    ".WMMMMMMCBBRBCCCCCCBRBBCMMMMMMW.",
    "WMMMMMMMMCBBCCCCCCCCBBCMMMMMMMMW",
    "WMMRRRRMMMCCCCCCCCCCCCMMMRRRRMMW",
    "WMRRRRRRMMCCCCCCCCCCCCMMRRRRRRMW",
    "WMRRYYRRMMBCCCCCCCCCCBMMRRYYRRMW",
    "WMRRRRRRMMBBCCCCCCCCBBMMRRRRRRMW",
    ".WMMRRRMMBBBBCCCCCCBBBBMMRRRMMW.",
    "..WWMMMMBRRRRBCCCCBRRRRBMMMMWW..",
    "...WMMMMBRRRRRBCCBRRRRRBMMMMW...",
    "..WMMMMMBRRRRRRBBRRRRRRBMMMMMW..",
    "..WMMMMBRRRRRRRRRRRRRRRRBMMMMW..",
    ".WMMMMMBRRRRRBBBBBBBRRRRRBMMMMMW",
    ".WMMMMBRRRRBMMMMMMMMBRRRRBMMMMW.",
    "WMMMMMBRRRBMMMMMMMMMMBRRRBMMMMMW",
    "WMMMMBRRRBMMMMB..BMMMMBRRRBMMMMW",
    "WMMMBRRRBMMMMB....BMMMMBRRRBMMMW",
    ".WMMBRRBMMMMB......BMMMMBRRBMMW.",
    "..WMBRBMMMMB........BMMMMBRBMW..",
    "...WBBMMMMB..........BMMMMBBW...",
]
put32(b3, 0x20, DARKLORD)
DARKLORD2 = (
    DARKLORD[:8] +
    [r.replace('YY', 'WW').replace('CC', 'YY') for r in DARKLORD[8:20]] +
    DARKLORD[20:]
)
put32(b3, 0x30, DARKLORD2)

# ボス5 形態2 (0xA0/0xB0): 幻魔王ダークロード・真形態 (黄金と真紅の覚醒形態)
DARKLORD_B = [
    r.replace('C', 'Y').replace('M', 'R') for r in DARKLORD
]
put32(b3, 0xA0, DARKLORD_B)
DARKLORD_B2 = (
    DARKLORD_B[:8] +
    [r.replace('YY', 'WW').replace('RR', 'MM') for r in DARKLORD_B[8:20]] +
    DARKLORD_B[20:]
)
put32(b3, 0xB0, DARKLORD_B2)

# ---------------------------------------------------------------- sideb restore data
def emit_restore_asm(path):
    """bank1-3 の元パターンを sideb 向けに出力する。

    文字ごとに B/R/G プレーンの 8 バイトずつ (24 バイト/文字)、code 0-255 を
    順に並べる。init_stage がこのデータで PCG-RAM (bank1-3) を復元してから
    黒 → フィールド色置換を行うため、面を跨いで透過色が前の面の色のままに
    なるバグがなくなる。
    """
    out = ['; generated by tools/pcggen.py - do not edit',
           '; Sprite PCG restore data (bank1-3): 24 bytes per char (B/R/G x 8 rows).',
           '; Used by video.asm sprite_recolor_field to reset sprite patterns',
           '; before recoloring on every stage change.']
    total = 0
    for bank_idx in (1, 2, 3):
        bank = BANKS[bank_idx]
        out.append(f'RF_SEG_B{bank_idx}:')
        for c in range(256):
            art = bank.chars.get(c)
            vals = []
            if art is not None:
                for plane in range(3):
                    bit = 1 << plane
                    for row in art:
                        v = 0
                        for ch in row:
                            v = (v << 1) | (1 if COLOR[ch] & bit else 0)
                        vals.append(v)
            else:
                vals = [0] * 24
            total += 24
            for i in range(0, 24, 8):
                chunk = vals[i:i + 8]
                out.append('        db ' + ','.join('0%02Xh' % b for b in chunk))
        out.append('')
    with open(path, 'w', newline='\n') as f:
        f.write('\n'.join(out))
    print(f'{path}: {total} bytes restore data (bank1-3)')


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


TERRAIN_LABELS = {
    1: {"T_S1_GRASS": "ground", "T_S1_TREE": "tree", "T_S1_RIVER": "river",
        "T_S1_BRIDGE": "bridge", "T_S1_FLOW": "flowers", "T_S1_BUSH": "breakable"},
    2: {"T_S2_GROUND": "ground", "T_S2_BOULDER": "boulder", "T_S2_RAVINE": "ravine",
        "T_S2_BRIDGE": "bridge", "T_S2_BONES": "bones", "T_S2_RUBBLE": "breakable"},
    3: {"T_S3_GROUND": "ground", "T_S3_TOMB": "tomb", "T_S3_SWAMP": "swamp",
        "T_S3_BRIDGE": "bridge", "T_S3_DEADTREE": "dead_tree", "T_S3_URN": "breakable"},
    4: {"T_S4_GROUND": "ground", "T_S4_ROCK": "rock", "T_S4_LAVA": "lava",
        "T_S4_BRIDGE": "bridge", "T_S4_CRYSTAL": "crystal", "T_S4_OBSID": "breakable"},
    5: {"T_S5_FLOOR": "ground", "T_S5_PILLAR": "pillar", "T_S5_MOAT": "moat",
        "T_S5_BRIDGE": "bridge", "T_S5_WINDOW": "window", "T_S5_ARMOR": "breakable"},
}

MAP_GLYPHS = {
    1: {'.': "ground", 'T': "tree", 'r': "river", '=': "bridge", 'f': "flowers", 'b': "breakable"},
    2: {'.': "ground", 'T': "boulder", 'r': "ravine", '=': "bridge", 'f': "bones", 'b': "breakable"},
    3: {'.': "ground", 'T': "tomb", 'r': "swamp", '=': "bridge", 'f': "dead_tree", 'b': "breakable"},
    4: {'.': "ground", 'T': "rock", 'r': "lava", '=': "bridge", 'f': "crystal", 'b': "breakable"},
    5: {'.': "ground", 'T': "pillar", 'r': "moat", '=': "bridge", 'f': "window", 'b': "breakable"},
}
MAP_DEF = {
    stage: {glyph: TERRAIN_TILES[stage][tile] for glyph, tile in glyphs.items()}
    for stage, glyphs in MAP_GLYPHS.items()
}

MAP_ROWS = {
    1: [
        "....................",
        "..TT...........TT...",
        "..TT...f.......TT...",
        "..........rr........",
        "...T......rr....T...",
        "...T......==....T...",
        "...T......rr....T...",
        "..........rr........",
        "...f...b..rr...b....",
        "....................",
        "..TT...........TT...",
    ],
    2: [
        "....................",
        "..TT............TT..",
        "..TT..b......f..TT..",
        "....T............T..",
        "..rrrrrrrrrrrrrrrr..",
        "..rrrrrr==rrrrrrrr..",
        "..rrrrrr==rrrrrrrr..",
        "..rrrrrrrrrrrrrrrr..",
        "....T....==....T....",
        "..f..TT...b...f.....",
        "..TT............TT..",
    ],
    3: [
        "....................",
        "..TT..f......f..TT..",
        "....T............T..",
        "..rrr...rrr...rrr...",
        "..rrr===rrr...rrr...",
        "..rrr===rrr...rrr...",
        "..rrr...rrr...rrr...",
        "...T......b.....T...",
        "...f..T.....T..f....",
        "...T...........T....",
        "....................",
    ],
    4: [
        "....................",
        "..TT..f......f..TT..",
        "....T............T..",
        "....................",
        "..rrrrrrrrrrrrrrrr..",
        "..rrrrrr==rrrrrrrr..",
        "..rrrrrr==rrrrrrrr..",
        "..rrrrrrrrrrrrrrrr..",
        "...T....b....T......",
        "...f......f.....b...",
        "....TT..........TT..",
    ],
    5: [
        "....................",
        ".T...T...T...T...T..",
        "..f..............f..",
        "..rrr...rrr...rrr...",
        "..rrr===rrr...rrr...",
        "..rrr===rrr...rrr...",
        "..rrr...rrr...rrr...",
        "..T..............T..",
        "...f....f....f......",
        "..T..............T..",
        "....................",
    ],
}


def asm_hex(value):
    digits = f'{value:02X}'
    return ('0' if digits[0] in 'ABCDEF' else '') + digits + 'h'


def emit_map_inc(path):
    lines = ['; generated by tools/pcggen.py - 16x16 tile and PCG code equates', '']
    lines.append('; --- bank 0: each terrain tile is 2x2 characters, top-left code below ---')
    lines.append('defc T_BLANK = 00h')
    for stage, entries in TERRAIN_LABELS.items():
        for name, tile in entries.items():
            lines.append(f'defc {name} = {asm_hex(TERRAIN_TILES[stage][tile])}')
    lines.extend(['defc T_DIGIT0 = 50h', 'defc T_HEART = 5Ah', ''])
    names = {
        1: [('SP_SHIP0', 0x00), ('SP_SHIP1', 0x04), ('SP_SHIP2', 0x08), ('SP_SHIP3', 0x0C),
            ('SP_SHIPB0', 0x10), ('SP_SHIPB1', 0x14), ('SP_SHIPB2', 0x18), ('SP_SHIPB3', 0x1C),
            ('SP_SHOT', 0x20), ('SP_ESHOT', 0x21),
            ('SP_EXPL0', 0x22), ('SP_EXPL1', 0x26), ('SP_EXPL2', 0x2A), ('SP_EXPL3', 0x2E),
            ('SP_PW_TWIN', 0x32), ('SP_PW_SPEED', 0x36), ('SP_PW_SHIELD', 0x3A), ('SP_PW_LIFE', 0x3E)],
        2: [('SP_GARG0', 0x00), ('SP_GARG1', 0x04), ('SP_WISP0', 0x08), ('SP_WISP1', 0x0C),
            ('SP_EN3_0', 0x10), ('SP_EN3_1', 0x14), ('SP_EN4_0', 0x18), ('SP_EN4_1', 0x1C),
            ('SP_EN5_0', 0x20), ('SP_EN5_1', 0x24), ('SP_EN6_0', 0x28), ('SP_EN6_1', 0x2C),
            ('SP_CHEST', 0x30)],
        3: [('SP_BOSS1_0', 0x00), ('SP_BOSS1_1', 0x10),
            ('SP_BOSS2_0', 0x40), ('SP_BOSS2_1', 0x50),
            ('SP_BOSS3_0', 0x80), ('SP_BOSS3_1', 0x90),
            ('SP_BOSS4_0', 0xC0), ('SP_BOSS4_1', 0xD0),
            ('SP_BOSS5_0', 0x20), ('SP_BOSS5_1', 0x30),
            ('SP_BOSS5B_0', 0xA0), ('SP_BOSS5B_1', 0xB0)],
    }
    for bank, entries in names.items():
        lines.append(f'; --- bank {bank} ---')
        for name, code in entries:
            lines.append(f'defc {name} = {asm_hex(code)}')
        lines.append('')
    with open(path, 'w', newline='\n') as f:
        f.write('\n'.join(lines))


def emit_maps(path):
    lines = ['; generated by tools/pcggen.py - 16x16 tile maps expanded to 40x22 characters', '']
    for stage in sorted(MAP_ROWS):
        alpha = MAP_DEF[stage]
        lines.append(f'MAP_ROWS_S{stage}:')
        rows = MAP_ROWS[stage]
        assert len(rows) == 11, f'stage {stage}: need 11 tile rows, got {len(rows)}'
        for tile_row in rows:
            assert len(tile_row) == 20, f'stage {stage}: tile row len {len(tile_row)}: {tile_row!r}'
            upper, lower = [], []
            for glyph in tile_row:
                code = alpha[glyph]
                upper.extend((code, code + 1))
                lower.extend((code + 2, code + 3))
            assert len(upper) == len(lower) == 40
            lines.append('        db ' + ','.join(asm_hex(c) for c in upper))
            lines.append('        db ' + ','.join(asm_hex(c) for c in lower))
        lines.append('')
    with open(path, 'w', newline='\n') as f:
        f.write('\n'.join(lines))


if __name__ == '__main__':
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    emit_asm(os.path.join(root, 'src', 'sidea', 'pcg_data.asm'), 'PCG_DATA_START')
    emit_map_inc(os.path.join(root, 'src', 'include', 'pcgmap.inc'))
    emit_maps(os.path.join(root, 'src', 'sideb', 'map_data.asm'))
    emit_restore_asm(os.path.join(root, 'src', 'sideb', 'pcg_restore.asm'))
    print('done')