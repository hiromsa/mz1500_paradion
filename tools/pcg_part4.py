
# ---------------------------------------------------------------- bank 3: boss
b3 = Bank()
TRENT = [  # 大樹の魔物 トレント (32x32)
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

put32(b3, 0x00, TRENT)
# frame 2: eyes squint (YY -> KK on the face rows)
TRENT2 = TRENT[:3] + [r.replace('YY', 'KK') for r in TRENT[3:]]
put32(b3, 0x10, TRENT2)
DARKLORD = [  # 幻魔王ダークロード (32x32)
    "..............WWWW..............",
    ".............WKKKW..............",
    "............WKKKKKW.............",
    "...........WKKKKKKKW............",
    "....WWWWWWWKKKKKKKWWWWWWW.......",
    "...WWKKKKKKKKKKKKKKKKKKWW.......",
    "..WKKKWWKKKKKKKKKKKWWKKKKW......",
    ".WKKWWKKKKKKKKKKKKKKKWWKKKW.....",
    ".WKKKKKKKKKKKKKKKKKKKKKKKKW.....",
    "WKKKKKKKKMMKKKKKMMKKKKKKKKW.....",
    "WKKKKKKKMMMMKKKMMMMKKKKKKKW.....",
    "WKKKKKKKMRRMKKKMRRMKKKKKKKW.....",
    "WKKKKKKKKMMKKKKKMMKKKKKKKKW.....",
    ".WKKKKKKKKKKKKKKKKKKKKKKKW......",
    "..WWKKKKKKKKKKKKKKKKKKKWW.......",
    "....WWKKKKKKKKKKKKKKKWWW........",
    "......WWKKKKKKKKKKKWWW..........",
    "........WKKKKKKKKKW.............",
    "....WKKKKKKKKKKKKKKKKKW.........",
    "...WKKKKKKKKKKKKKKKKKKKW........",
    "..WKKKKKKKKKKKKKKKKKKKKKW.......",
    ".WKKKKKKKKKKKKKKKKKKKKKKKW......",
    ".WKKKKKKKKKKKKKKKKKKKKKKKW......",
    "..WKKKKKKKKKKKKKKKKKKKKKW.......",
    "...WKKKKKKKKKKKKKKKKKKKW........",
    "....WWKKKKKKKKKKKKKKKWW.........",
    "......WWKKKKKKKKKKKWW...........",
    "........WWKKKKKKKWW.............",
    "..........WWKKKWW...............",
    "............WWW.................",
    "............W.W.................",
    ".............W..................",
]
put32(b3, 0x20, DARKLORD)
DARKLORD2 = DARKLORD[:9] + [r.replace('MM', 'RR') for r in DARKLORD[9:15]] + DARKLORD[15:]
put32(b3, 0x30, DARKLORD2)

BANKS = [b0, b1, b2, b3]
