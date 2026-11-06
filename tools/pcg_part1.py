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

COLOR = {'.': 0, 'K': 0, 'B': 1, 'R': 2, 'M': 3, 'G': 4, 'C': 5, 'Y': 6, 'W': 7}

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
