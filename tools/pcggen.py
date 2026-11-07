"""PCG pattern generator for Makyou Kishi Paradion (MZ-1500).

Converts ASCII pixel art into MZ-1500 PCG data (3 color planes x 4 banks x 256 chars)
and emits:
  - src/sidea/pcg_data.asm : chunk table + plane-major DB data (Side A loader input)
  - src/include/pcgmap.inc : tile/sprite code equates shared by Side A/B
  - src/sideb/map_data.asm : stage map row tables

Color characters: '.'/'K'=black(0) B=blue(1) R=red(2) M=magenta(3) G=green(4)
                  C=cyan(5) Y=yellow(6) W=white(7)
Usage: python tools/pcggen.py   (run from project root)

=========================================================================
■ このスクリプトにグラフィック / マップを仕込む人 (別 AI) へのルール
=========================================================================

[基本]
- 絵はすべて 8x8 (Bank.put) か 16x16 (Bank.put16 / center16 + put16) か
  32x32 (center32 + put32) の ASCII 文字列で書く。1 文字 = 1 ピクセル。
- 色文字: '.' または 'K' = 黒(0), B=青(1), R=赤(2), M=マゼンタ(3),
  G=緑(4), C=シアン(5), Y=黄(6), W=白(7)。
- ★黒 ('.'/ 'K') は「透過色」として扱われる。init_stage が実行時に
  バンク 1-3 の黒ピクセルをステージ毎のフィールド色へ一括置換するため、
  キャラクタの輪郭や内部の塗りを黒に頼らないこと (黒は必ず背景に溶ける)。
- スプライトは横移動の位相が 2px 刻みのため、自機のように水平方向に
  動くものは shift16() でシフト済み 4 相を焼くこと (bank1 の自機を参照)。

[バンク割当 (pcgmap.inc の defc と一致させること)]
- bank0 = 地形タイル / 数字 / UI:
    16x16 タイル 1 種 = コード 4 個 (左上 = TERRAIN_TILES のコード)。
    ステージ 1-5 の 6 種 x 5 面 = 80h-F7h。下 2bit は (cy*2+cx)。
    ★「壊せるタイル」のコード (94h, ACh, C4h, DCh, F4h) は変更禁止 —
      src/sideb/data.asm BRK_TABLE と不変の対応がある。
    50h-59h = 数字 0-9, 5Ah = ハート (残機)。
- bank1 = 自機 / 弾 / 爆発 / アイテム:
    00h-0Fh = 自機 歩行フレーム A (phase0-3, 各 4 コード)
    10h-1Fh = 自機 歩行フレーム B (同構成、player.asm が 16 フレーム毎に A/B 切替)
    20h = 自弾, 21h = 敵弾 (8x8)
    22h, 26h, 2Ah, 2Eh = 爆発 4 フレーム (16x16)
    32h = ツインショット, 36h = スピードアップ, 3Ah = シールド,
    3Eh = 1UP (16x16 アイテム。種類が見分けられる絵にすること)
- bank2 = 雑魚敵 6 種 + 宝箱:
    種 N (1-6) の先頭コード = 8 * (N-1)。各種 2 フレーム (+0 と +4)。
    種 1-2 が出題意の基本敵 (ガーゴイル / ウィスプ)、3 以降はステージ 2-5 で
    新規登場する雑魚。種の奇偶で移動パターンが決まる
    (奇数 = ガーゴイル型, 偶数 = ウィスプ型 — src/sideb/enemy.asm)。
    30h = 宝箱 (16x16, アニメなし)。弾を当てるとアイテムを出す。
    ★アイテム持ち敵 (メダル差分) は廃止済み。不要。
- bank3 = ボス 5 種 (32x32, フレーム差分 = +10h):
    00h/10h = ボス 1 (トレント), 40h/50h = ボス 2 (ゴーレム),
    80h/90h = ボス 3 (デスサイズ), C0h/D0h = ボス 4 (ファイアドラゴン),
    20h/30h = ボス 5 形態 1 (ダークロード), A0h/B0h = ボス 5 形態 2。
    コード対応表は src/sideb/data.asm BOSS_CODE_TBL が参照する。

[マップ (MAP_ROWS)]
- 各ステージ = 20 文字 x 11 行の固定レイアウト。1 文字 = 16x16 タイル 1 個。
- glyph -> タイルの対応は MAP_GLYPHS、コード割当は TERRAIN_TILES で定義する。
- 各マップには必ず地形の目印 (川 / 溶岩 / 堀などの帯 + 橋) を含めること。
- 'b' (breakable) は壊せるタイル。コード変更禁止 (前述)。
- マップの地面タイルの主色が、そのステージのフィールド色になる
  (黒置換色: 1=森の緑, 2=岩場の青灰... ではなく data.asm STAGE_TABLE +F 参照。
   タイルの主色と +F の色を合わせるとキャラが自然に馴染む)。
- 生成物を直接編集しないこと (pcg_data.asm / pcgmap.inc / map_data.asm は
  すべてこのスクリプトが上書きする)。絵・マップはこのファイルだけ編集する。
=========================================================================
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
b0.put(0x08, [  # S2 slate floor: cool, low-contrast stone with sparse cracks
    "BBBBBBBB", "BBBKBBBB", "BBCBBBBB", "BBBBBBBB",
    "BBBBKBBB", "BBBBBCBB", "BBBBBBBB", "BBBBBBBB"])
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

# ---------------------------------------------------------------- bank 0: 16x16 terrain tiles
def scale2(art):
    """Scale a hand-drawn 8x8 pattern to a clear 16x16 terrain tile."""
    assert len(art) == 8 and all(len(row) == 8 for row in art)
    return ["".join(pixel * 2 for pixel in row) for row in art for _ in range(2)]

def terrain16(code, art8):
    b0.put16(code, scale2(art8))

WATER_FOREST = [
    "BBBBBBBB", "BBCBBBBB", "BBBBBBBB", "BBBBBBBB",
    "BBBBBBBC", "BBBBBBBB", "BBBBBBBB", "BBCBBBBB"]
BRIDGE_WOOD = [
    "YYYYYYYY", "KKKKKKKK", "YYYYYYYY", "KKKKKKKK",
    "YYYYYYYY", "KKKKKKKK", "YYYYYYYY", "KKKKKKKK"]
CANYON = [
    "KKKKKKKK", "KBBKKBBK", "KKBBBBKK", "BBKKKKBB",
    "BBKKKKBB", "KKBBBBKK", "KBBKKBBK", "KKKKKKKK"]
BRIDGE_STONE = [
    "WWWWWWWW", "KKKKKKKK", "WWWWWWWW", "KKKKKKKK",
    "WWWWWWWW", "KKKKKKKK", "WWWWWWWW", "KKKKKKKK"]
SWAMP = [
    "GGGGGGGG", "GCCGGGGG", "GGGGGGGG", "GGGGGGGG",
    "GGGGCCGG", "GGGGGGGG", "GGGGGGGG", "GCCGGGGG"]
BRIDGE_OLD = [
    "YYYYYYYY", "YKKYKKYK", "YYYYYYYY", "YKKYKKYK",
    "YYYYYYYY", "YKKYKKYK", "YYYYYYYY", "YKKYKKYK"]
BRIDGE_BASALT = [
    "KKKKKKKK", "KWWKKWWK", "KKKKKKKK", "KWWKKWWK",
    "KKKKKKKK", "KWWKKWWK", "KKKKKKKK", "KWWKKWWK"]
CRYSTAL = [
    "KKKKKKKK", "KKKYYKKK", "KKYWWYKK", "KKYWWYKK",
    "KKKYCKKK", "KKKKCKKK", "KKKKKKKK", "KKKKKKKK"]
MOAT = [
    "BBBBBBBB", "BBCBBBBB", "BBBBBBBB", "BBBBBBBB",
    "BBBBBCBB", "BBBBBBBB", "BBBBBBBB", "BBCBBBBB"]
DRAWBRIDGE = [
    "YYYYYYYY", "KKYKKYKK", "YYYYYYYY", "KKYKKYKK",
    "YYYYYYYY", "KKYKKYKK", "YYYYYYYY", "KKYKKYKK"]

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

TERRAIN_ART = {
    1: {"ground": b0.chars[0x01], "tree": b0.chars[0x02], "river": WATER_FOREST,
        "bridge": BRIDGE_WOOD, "flowers": b0.chars[0x04], "breakable": b0.chars[0x03]},
    2: {"ground": b0.chars[0x08], "boulder": b0.chars[0x09], "ravine": CANYON,
        "bridge": BRIDGE_STONE, "bones": b0.chars[0x0B], "breakable": b0.chars[0x0C]},
    3: {"ground": b0.chars[0x0D], "tomb": b0.chars[0x0E], "swamp": SWAMP,
        "bridge": BRIDGE_OLD, "dead_tree": b0.chars[0x0F], "breakable": b0.chars[0x11]},
    4: {"ground": b0.chars[0x12], "rock": b0.chars[0x14], "lava": b0.chars[0x13],
        "bridge": BRIDGE_BASALT, "crystal": CRYSTAL, "breakable": b0.chars[0x15]},
    5: {"ground": b0.chars[0x16], "pillar": b0.chars[0x18], "moat": MOAT,
        "bridge": DRAWBRIDGE, "window": b0.chars[0x19], "breakable": b0.chars[0x1A]},
}
for stage, tiles in TERRAIN_TILES.items():
    for tile_name, code in tiles.items():
        terrain16(code, TERRAIN_ART[stage][tile_name])

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

# ---------------------------------------------------------------- bank 1: player / shots / items
b1 = Bank()
def center16(rows):
    """Center variable-width pixel-art rows in a transparent 16px cell."""
    assert len(rows) == 16
    assert all(len(row) <= 16 for row in rows), [(row, len(row)) for row in rows if len(row) > 16]
    return [row.center(16, '.') for row in rows]

def swap_colors(rows, mapping):
    """Placeholder art helper: remap palette letters in every row."""
    return ["".join(mapping.get(ch, ch) for ch in row) for row in rows]

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
# 自機は後ろ姿。歩行アニメ 2 フレーム x 水平シフト 4 相
#   フレーム A = 0x00-0x0F, フレーム B = 0x10-0x1F (player.asm が 16 フレーム毎に切替)
PALADIN_WALK = PALADIN[:14] + [
    ".....C...C......",       # 軸足
    "...YY......YY...",       # 歩行フレーム B: 脚を開く
]
b1.put16(0x00, PALADIN)       # walk A phase 0 (shift 0)
b1.shift16(0x00, 0x04, 2)     # walk A phase 1 (shift 2px)
b1.shift16(0x00, 0x08, 4)     # walk A phase 2 (shift 4px)
b1.shift16(0x00, 0x0C, 6)     # walk A phase 3 (shift 6px)
b1.put16(0x10, PALADIN_WALK)  # walk B phase 0
b1.shift16(0x10, 0x14, 2)     # walk B phase 1
b1.shift16(0x10, 0x18, 4)     # walk B phase 2
b1.shift16(0x10, 0x1C, 6)     # walk B phase 3
b1.put(0x20, [  # player shot
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
    b1.put16(0x22 + f * 4, art16)
PW_TWIN8 = [
    "KKKKKKKK", "KCCCCCCK", "KC.WWW.K", "KC.WW..K",
    "KC.WWWWK", "KC.W.W.K", "KCCCCCCK", "KKKKKKKK"]
PW_SPEED8 = [
    "KKKKKKKK", "KGGGGGGK", "KG.WW..K", "KG.WW..K",
    "KGWWWW.K", "KG..WW.K", "KGGGGGGK", "KKKKKKKK"]
PW_SHIELD8 = [
    "KKKKKKKK", "KWWWWWWK", "KWCCCCWK", "KWC..CWK",
    "KWC..CWK", "KWCCCCWK", "KWWWWWWK", "KKKKKKKK"]
PW_LIFE8 = [
    "KKKKKKKK", "KGGGGGGK", "KGRRRRGK", "KGRGGKGK",
    "KGRGGGGK", "KGGRRGGK", "KGGGGGGK", "KKKKKKKK"]
# アイテムは 16x16 (2 倍拡大)。種類が一見でわかる絵にすること
b1.put16(0x32, scale2(PW_TWIN8))    # SP_PW_TWIN
b1.put16(0x36, scale2(PW_SPEED8))   # SP_PW_SPEED
b1.put16(0x3A, scale2(PW_SHIELD8))  # SP_PW_SHIELD
b1.put16(0x3E, scale2(PW_LIFE8))    # SP_PW_LIFE

# ---------------------------------------------------------------- bank 2: enemies / chest
# 雑魚敵 6 種 (種 N の先頭コード = 8*(N-1), 2 フレーム = +0/+4) + 宝箱 0x30。
# 種 3-6 は既存パターンの色替えコピー (プレースホルダー)。
# 本グラフィックは別 AI がこのセクションを書き換える。
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

# ---- 種 3-6: プレースホルダー (既存パターンの色替えコピー) ----
# 別 AI が本グラフィックに置き換える。移動パターンは種の奇偶で決まるため
# 見た目だけを変えればよい。
BAT     = swap_colors(GARGOYLE, {'W': 'C', 'M': 'B'})   # 種 3: 青のガーゴイル (岩場)
BAT2    = swap_colors(GARGOYLE2, {'W': 'C', 'M': 'B'})
WILLOW  = swap_colors(WISP, {'C': 'G'})                  # 種 4: 緑の鬼火 (墓地)
WILLOW2 = swap_colors(WISP2, {'C': 'G'})
EMBER   = swap_colors(WISP, {'W': 'Y', 'C': 'R'})        # 種 5: 炎の魂 (火山)
EMBER2  = swap_colors(WISP2, {'W': 'Y', 'C': 'R'})
SHADE   = swap_colors(GARGOYLE, {'W': 'Y', 'M': 'B'})   # 種 6: 金翼の怪 (幻魔城)
SHADE2  = swap_colors(GARGOYLE2, {'W': 'Y', 'M': 'B'})
b2.put16(0x10, BAT)
b2.put16(0x14, BAT2)
b2.put16(0x18, WILLOW)
b2.put16(0x1C, WILLOW2)
b2.put16(0x20, EMBER)
b2.put16(0x24, EMBER2)
b2.put16(0x28, SHADE)
b2.put16(0x2C, SHADE2)

# ---- 宝箱 (0x30, 16x16) ----
# 弾を当てると爆発してアイテムを出す。木胴 + 金帯の意匠。
CHEST = [
    "................",
    "..RRRRRRRRRRRR..",
    ".RRRRRRRRRRRRRR.",
    ".YYYYYYYYYYYYYY.",
    ".RRRRRRRRRRRRRR.",
    ".RRRRRRRRRRRRRR.",
    ".YYYYYYWWYYYYYY.",
    ".RRRRRRWWRRRRRR.",
    ".RRRRRRRRRRRRRR.",
    ".YYYYYYYYYYYYYY.",
    ".RRRRRRRRRRRRRR.",
    ".RRRRRRRRRRRRRR.",
    ".YYYYYYYYYYYYYY.",
    ".RRRRRRRRRRRRRR.",
    "..RRRRRRRRRRRR..",
    "................",
]
b2.put16(0x30, CHEST)

# ---------------------------------------------------------------- bank 3: boss (5 種)
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

# ---- ボス 2-4: プレースホルダー (既存パターンの色替えコピー) ----
# 別 AI が本グラフィックに置き換える。データ側は data.asm BOSS_CODE_TBL が
# ステージ番号 -> 先頭コードを引くだけで、ここ以外の変更は不要。
GOLEM  = swap_colors(TRENT, {'g': 'b', 'G': 'B', 'R': 'Y', 'Y': 'W', 'M': 'C', 'm': 'c'})
GOLEM2 = GOLEM[:3] + [r.replace('WW', 'KK') for r in GOLEM[3:]]     # 目を細める
put32(b3, 0x40, GOLEM)    # ボス 2: ストーンゴーレム (岩場)
put32(b3, 0x50, GOLEM2)
DEATH  = swap_colors(DARKLORD, {'W': 'C', 'R': 'Y', 'M': 'B', 'Y': 'R', 'C': 'G'})
DEATH2 = DEATH[:3] + [r.replace('YY', 'KK') for r in DEATH[3:]]     # 目を細める
put32(b3, 0x80, DEATH)    # ボス 3: デスサイズ (墓地)
put32(b3, 0x90, DEATH2)
DRAGON  = swap_colors(TRENT, {'g': 'r', 'G': 'R', 'R': 'W', 'Y': 'C', 'M': 'Y', 'm': 'y'})
DRAGON2 = DRAGON[:3] + [r.replace('CC', 'KK') for r in DRAGON[3:]]  # 目を細める
put32(b3, 0xC0, DRAGON)   # ボス 4: ファイアドラゴン (火山)
put32(b3, 0xD0, DRAGON2)

# ---- ボス 5 形態 2 (0xA0/0xB0) ----
# 白鎧と紫鎧を反転させた差分。形態変化は boss.asm がコード差し替えで表現する。
DARKLORD_B = swap_colors(DARKLORD, {'W': 'M', 'M': 'W'})
put32(b3, 0xA0, DARKLORD_B)
DARKLORD_B2 = DARKLORD_B[:9] + [r.replace('RR', 'YY') for r in DARKLORD_B[9:15]] + DARKLORD_B[15:]
put32(b3, 0xB0, DARKLORD_B2)

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

# Fixed 20x11 layouts, one glyph per 16x16 tile. Each map has landmarks,
# obstacle groups and a deliberate river/chasm/lava/moat crossing with a bridge.
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
    print('done')
