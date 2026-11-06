
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
