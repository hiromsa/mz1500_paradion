
# ---------------------------------------------------------------- bank 1: player
b1 = Bank()
SHIP = [
    "......CC........",
    ".....CWKC.......",
    ".....CWKC.......",
    ".C...CWWKC....C.",
    ".CC..CWWKC...CC.",
    ".CCCWWWWWWKCCCC.",
    "CCWWCWWWWWWCWWCC",
    "CWWWWWWWWWWWWWWC",
    "CWWKCWWWWWWKWWWC",
    ".CWKCWWWWWWKWWC.",
    "..CCWWWWWWWWCC..",
    "...CCWWCCWWCC...",
    "....CCWCCWCC....",
    ".....CC..CC.....",
    "....YY....YY....",
    "...YKKY..YKKY...",
]
b1.put16(0x00, SHIP)          # phase 0 (shift 0)
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
GARGOYLE = [
    "MM..........MM..", "MMM........MMM..", "MMMM..KK..MMMM..",
    "MMM..KWWK..MMM..", "MM..KWKKWK..MM..", "M..KKWWWWKK..M..",
    "...KWWKKWWK.....", "..KKWWWWWWKK....", "..KKWKKKKWKK....",
    "...KWKKKKWK.....", "....KWKKWK......", "....KWKKWK......",
    "...KWWKKWWK.....", "...KK....KK.....", "..KK......KK....",
    "..M........M....",
]
GARGOYLE2 = [
    "................", "M............M..", "MM...........MM.",
    ".MMM..KK..MMM...", "..MM.KWWK.MM....", "...KKWWWWKK.....",
    "...KWWKKWWK.....", "..KKWWWWWWKK....", "..KKWKKKKWKK....",
    "M..KWKKKKWK..M..", "MM..KWKKWK..MM..", ".MM.KWKKWK.MM...",
    "..KKWWKKWWKK....", "..KK............", ".KK.............",
    "................",
]
b2.put16(0x00, GARGOYLE)
b2.put16(0x04, GARGOYLE2)
WISP = [
    "................", ".....BBBB.......", "....BWWWWB......",
    "...BWWCCWWB.....", "...BWCCWWCB.....", "..BWWCCCCWWB....",
    "..BWCCWWCCWB....", "..BWCCWWCCWB....", "..BWWCCCCWWB....",
    "...BWCCCCWB.....", "...BBWWWWBB.....", "....BBBBBB......",
    ".....B..B.......", "....B....B......", "...B......B.....",
    "................",
]
WISP2 = [
    "................", ".....BBBB.......", "....BWWWWB......",
    "...BWWCCWWB.....", "...BWCCWWCB.....", "..BWWCCCCWWB....",
    "..BWCCWWCCWB....", "..BWCCWWCCWB....", "..BWWCCCCWWB....",
    "...BWCCCCWB.....", "...BBWWWWBB.....", "....BBBBBB......",
    "......B.B.......", ".....B...B......", "....B.....B.....",
    "................",
]
b2.put16(0x08, WISP)
b2.put16(0x0C, WISP2)
