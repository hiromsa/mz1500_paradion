# dump (CLI --dump 出力) を解析: VRAM(D400) と MIRROR(B400) を行単位で比較する
# 使い方: python dumpanalyze.py <vram_dump> <ram_dump>
import sys, re

def read_text(path):
    data = open(path, 'rb').read()
    if data.count(0) > len(data) / 4:        # PowerShell > は UTF-16LE
        return data.decode('utf-16-le', errors='replace')
    return data.decode('utf-8', errors='replace')

def parse(path):
    mem = {}
    for line in read_text(path).splitlines():
        m = re.match(r'^([0-9A-F]{4}): ((?:[0-9A-F]{2} ?)+)', line)
        if m:
            addr = int(m.group(1), 16)
            for i, b in enumerate(m.group(2).split()):
                mem[addr + i] = int(b, 16)
    return mem

vram_path = sys.argv[1] if len(sys.argv) > 1 else r'c:\tools\mz1500action\tmp\dump_vram.txt'
ram_path = sys.argv[2] if len(sys.argv) > 2 else r'c:\tools\mz1500action\tmp\dump_ram.txt'
v = parse(vram_path)
r = parse(ram_path)
print(f'vram bytes: {len(v)}, ram bytes: {len(r)}')
FB = 880
vram = [v.get(0xD400 + i) for i in range(FB)]
mirr = [r.get(0xB400 + i) for i in range(FB)]

print('== VRAM で 00h (黒) のセル ==')
for row in range(22):
    cols = [c for c in range(40) if vram[row*40+c] == 0]
    if cols:
        print(f'  row {row:2d}: {cols}')

print('== ミラーが 00h のセル (消去時に黒を復元する元凶) ==')
for row in range(22):
    cols = [c for c in range(40) if mirr[row*40+c] == 0]
    if cols:
        print(f'  row {row:2d}: {cols}')

print('== VRAM != MIRROR のセル (スプライト描画セル等) ==')
for row in range(22):
    cols = [c for c in range(40) if vram[row*40+c] != mirr[row*40+c]]
    if cols:
        print(f'  row {row:2d}: ' + ', '.join(f'c{c}:V{vram[row*40+c]:02X}/M{mirr[row*40+c]:02X}' for c in cols))

print('== O_TBL (B040, 20slot x 8B) ==')
for s in range(20):
    base = 0xB040 + s*8
    vals = [r.get(base + i) for i in range(8)]
    if None in vals:
        print(f'  slot {s:2d}: dump missing')
        continue
    if vals[0] != 0 or vals[6] or vals[7]:
        print(f'  slot {s:2d}: st={vals[0]} attr={vals[1]:02X} x={vals[2]} y={vals[3]} '
              f'code={vals[4]:02X} t={vals[5]} cell={vals[6] | (vals[7] << 8):04X}')

print('== ワーク主要 ==')
print('  B000 (tick,keys,prev,state):', [r.get(0xB000 + i) for i in range(4)])
print('  B0EF-F5 (breadcrumbs)     :', [r.get(0xB0EF + i) for i in range(7)])
